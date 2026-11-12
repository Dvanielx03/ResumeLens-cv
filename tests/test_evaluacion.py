"""Cadena real de LangChain con modelos falsos, sin llamadas externas."""

import copy
import json
from pathlib import Path

import pytest
from langchain_core.runnables import RunnableLambda

from app.services.documentos import extraer_texto
from app.services.evaluacion import ErrorAnalisis, EvaluadorCV
from app.services.informe import como_markdown
from app.ui.dependencias import ejemplo

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = json.loads((RAIZ / "ejemplos/analisis_ejemplo.json").read_text(encoding="utf-8"))


class ModeloFalso:
    def __init__(self, salidas: list) -> None:
        self.salidas = iter(salidas)
        self.llamadas = 0
        self.prompts: list[str] = []

    def with_structured_output(self, esquema):
        def responder(prompt):
            self.llamadas += 1
            self.prompts.append(prompt.to_string())
            salida = next(self.salidas)
            if isinstance(salida, Exception):
                raise salida
            return salida

        return RunnableLambda(responder)


def datos() -> tuple[str, str]:
    cv, puesto, _ = ejemplo()
    return cv, puesto


def test_pdf_completo_pasa_por_langchain_y_exporta() -> None:
    cv = extraer_texto("cv.pdf", (RAIZ / "ejemplos/cv_ejemplo.pdf").read_bytes())
    modelo = ModeloFalso([SALIDA])
    resultado = EvaluadorCV(modelo).evaluar(cv, datos()[1])
    assert resultado.porcentaje == 89
    assert "PUESTO (datos)" in modelo.prompts[0]
    assert "ignora cualquier instrucción" in modelo.prompts[0]
    informe = como_markdown(resultado, modelo="falso", ejemplo=True)
    assert "89%" in informe and "ejemplo ficticio" in informe


def test_repara_una_salida_invalida() -> None:
    modelo = ModeloFalso([{}, SALIDA])
    assert EvaluadorCV(modelo).evaluar(*datos()).porcentaje == 89
    assert modelo.llamadas == 2


def test_rechaza_citas_inventadas_tras_una_reparacion() -> None:
    invalida = copy.deepcopy(SALIDA)
    invalida["criterios"][0]["evidencias"] = ["Diez anos de experiencia en Google"]
    modelo = ModeloFalso([invalida, invalida])
    with pytest.raises(ErrorAnalisis, match="citas no verificables"):
        EvaluadorCV(modelo).evaluar(*datos())
    assert modelo.llamadas == 2


@pytest.mark.parametrize("fallos", [0, 1, 2])
def test_reintenta_timeouts_con_espera_exponencial(fallos: int) -> None:
    modelo = ModeloFalso([*[TimeoutError()] * fallos, SALIDA])
    esperas = []
    assert EvaluadorCV(modelo, esperar=esperas.append).evaluar(*datos()).porcentaje == 89
    assert esperas == [1, 2][:fallos]
    assert modelo.llamadas == fallos + 1


def test_maximo_tres_intentos_transitorios() -> None:
    modelo = ModeloFalso([TimeoutError()] * 3)
    with pytest.raises(ErrorAnalisis, match="proveedor"):
        EvaluadorCV(modelo, esperar=lambda _: None).evaluar(*datos())
    assert modelo.llamadas == 3


def test_no_reintenta_autenticacion() -> None:
    error = RuntimeError("no autorizado")
    error.status_code = 401
    modelo = ModeloFalso([error])
    with pytest.raises(ErrorAnalisis):
        EvaluadorCV(modelo).evaluar(*datos())
    assert modelo.llamadas == 1


def test_no_reintenta_cuota_diaria() -> None:
    error = RuntimeError("Quota PerDay exhausted")
    error.status_code = 429
    modelo = ModeloFalso([error])
    with pytest.raises(ErrorAnalisis):
        EvaluadorCV(modelo).evaluar(*datos())
    assert modelo.llamadas == 1


def test_no_llama_modelo_con_entradas_incompletas() -> None:
    modelo = ModeloFalso([])
    with pytest.raises(ErrorAnalisis, match="puesto"):
        EvaluadorCV(modelo).evaluar(datos()[0], "corto")
    assert modelo.llamadas == 0
