"""Cadena LCEL, comprobación de citas y control de errores."""

import time
from collections.abc import Callable
from queue import Empty, Queue
from threading import Thread
from typing import Any

from langchain_core.exceptions import OutputParserException
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda
from pydantic import ValidationError

from app.config.settings import LLM_TIMEOUT_S, MAX_CV_CHARS, MAX_JOB_CHARS
from app.domain.modelos import AnalisisCV
from app.llm.prompts import prompt_cv


class ErrorAnalisis(ValueError):
    """La evaluación no pudo completarse de forma válida."""


def _invocar(operacion: Callable, timeout: float) -> Any:
    cola: Queue = Queue(maxsize=1)

    def ejecutar() -> None:
        try:
            cola.put((True, operacion()))
        except Exception as error:
            cola.put((False, error))

    Thread(target=ejecutar, daemon=True, name="resumelens-llm").start()
    try:
        correcto, salida = cola.get(timeout=timeout)
    except Empty as error:
        raise TimeoutError("Tiempo de espera agotado.") from error
    if not correcto:
        raise salida
    return salida


def _transitorio(error: Exception) -> bool:
    texto = str(error).lower()
    if "perday" in texto or "per day" in texto or "insufficient_quota" in texto:
        return False
    codigo = getattr(error, "status_code", None) or getattr(error, "code", None)
    return isinstance(error, TimeoutError) or (isinstance(codigo, int) and (codigo == 429 or 500 <= codigo < 600)) or "timeout" in type(error).__name__.lower()


def _normalizar(texto: str) -> str:
    return " ".join(texto.split())


def validar_citas(analisis: AnalisisCV, cv: str) -> AnalisisCV:
    """Exige que cada cita devuelta exista en el documento original."""
    fuente = _normalizar(cv)
    if any(_normalizar(cita) not in fuente for criterio in analisis.criterios for cita in criterio.evidencias):
        raise ValueError("El modelo devolvió citas que no existen en el CV.")
    return analisis


class EvaluadorCV:
    """Orquesta la misma cadena estructurada usada en Garaje, adaptada al CV."""

    def __init__(self, modelo: Any, *, timeout: float = LLM_TIMEOUT_S,
                 esperar: Callable[[float], None] = time.sleep) -> None:
        self.modelo = modelo.with_structured_output(AnalisisCV)
        self.timeout = timeout
        self.esperar = esperar

    def evaluar(self, cv: str, puesto: str) -> AnalisisCV:
        """Valida entradas, ejecuta LCEL y permite una reparación de esquema/citas."""
        cv, puesto = cv.strip(), puesto.strip()
        if not 80 <= len(cv) <= MAX_CV_CHARS:
            raise ErrorAnalisis(f"El CV debe contener entre 80 y {MAX_CV_CHARS:,} caracteres.")
        if not 40 <= len(puesto) <= MAX_JOB_CHARS:
            raise ErrorAnalisis(f"Describe el puesto con entre 40 y {MAX_JOB_CHARS:,} caracteres.")
        entrada = RunnableLambda(lambda datos: {"cv": datos["cv"], "puesto": datos["puesto"]}) | prompt_cv
        prompt = entrada.invoke({"cv": cv, "puesto": puesto})
        validar = RunnableLambda(lambda salida: validar_citas(AnalisisCV.model_validate(salida), cv))
        reparado, reintentos = False, 0
        limite = time.monotonic() + 90
        while True:
            try:
                restante = limite - time.monotonic()
                if restante <= 0:
                    raise ErrorAnalisis("La evaluación superó el plazo total de 90 segundos.")
                salida = _invocar(lambda: self.modelo.invoke(prompt), min(self.timeout, restante))
                return validar.invoke(salida)
            except (ValidationError, OutputParserException, ValueError) as error:
                if isinstance(error, ErrorAnalisis):
                    raise
                if reparado:
                    raise ErrorAnalisis("La respuesta del modelo no cumple el contrato o contiene citas no verificables. Reintenta el análisis.") from error
                reparado = True
                prompt = prompt.__class__(messages=[*prompt.to_messages(), HumanMessage(content=
                    "La salida anterior no cumplió el contrato o sus citas no existen en el CV. "
                    "Responde de nuevo con exactamente los cuatro criterios y citas literales verificables. "
                    "No añadas ningún dato que no figure en el documento.")])
            except Exception as error:
                if _transitorio(error) and reintentos < 2:
                    self.esperar(2 ** reintentos)
                    reintentos += 1
                    continue
                raise ErrorAnalisis("No se pudo consultar al proveedor. Revisa la clave, el modelo y la cuota disponible. No se generó un resultado alternativo.") from error
