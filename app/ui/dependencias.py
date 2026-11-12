"""Composición del evaluador real o del ejemplo explícito sin API."""

import json
from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableLambda

from app.llm.proveedores import crear_modelo
from app.services.evaluacion import EvaluadorCV

RAIZ = Path(__file__).resolve().parents[2]


class ModeloEjemplo:
    """Modelo falso del caso ficticio; nunca se ofrece como una llamada real."""

    def with_structured_output(self, esquema: Any) -> RunnableLambda:
        salida = json.loads((RAIZ / "ejemplos/analisis_ejemplo.json").read_text(encoding="utf-8"))
        return RunnableLambda(lambda _: esquema.model_validate(salida))


def evaluador(proveedor: str, modelo: str, clave: str) -> EvaluadorCV:
    return EvaluadorCV(crear_modelo(proveedor, modelo, clave))


def ejemplo() -> tuple[str, str, EvaluadorCV]:
    cv = (RAIZ / "ejemplos/cv_ejemplo.txt").read_text(encoding="utf-8")
    puesto = (RAIZ / "ejemplos/puesto_ejemplo.txt").read_text(encoding="utf-8")
    return cv, puesto, EvaluadorCV(ModeloEjemplo())
