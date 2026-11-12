"""Pruebas de contrato y ponderación del ajuste."""

import pytest
from pydantic import ValidationError

from app.domain.modelos import AnalisisCV, PESOS


def salida(puntos: tuple[int, ...] = (80, 90, 70, 60)) -> dict:
    return {
        "resumen": "El CV aporta evidencia parcial para el puesto solicitado.",
        "criterios": [
            {"codigo": c, "aplica": True, "puntuacion": p, "requisito": "Desarrollar APIs REST",
             "justificacion": "Se documenta trabajo relacionado con el requisito.", "evidencias": ["Desarrollo de APIs REST"]}
            for c, p in zip(PESOS, puntos)
        ],
        "fortalezas": ["Experiencia en APIs."], "brechas": ["Faltan métricas de impacto."],
        "siguientes_pasos": ["Añadir resultados medibles."],
    }


def test_calcula_porcentaje_con_pesos() -> None:
    assert AnalisisCV.model_validate(salida()).porcentaje == 80


def test_excluye_requisito_no_solicitado_y_renormaliza() -> None:
    datos = salida((100, 0, 0, 0))
    for c in datos["criterios"][1:]:
        c.update(aplica=False, puntuacion=0, evidencias=[])
    resultado = AnalisisCV.model_validate(datos)
    assert resultado.porcentaje == 100
    assert resultado.peso_efectivo("experiencia") == 100
    assert resultado.peso_efectivo("formacion") == 0


@pytest.mark.parametrize("puntos", [-1, 101, 60.5])
def test_rechaza_puntuacion_invalida(puntos: float) -> None:
    datos = salida()
    datos["criterios"][0]["puntuacion"] = puntos
    with pytest.raises(ValidationError):
        AnalisisCV.model_validate(datos)


def test_rechaza_criterio_duplicado() -> None:
    datos = salida()
    datos["criterios"][0]["codigo"] = "habilidades"
    with pytest.raises(ValidationError):
        AnalisisCV.model_validate(datos)


def test_rechaza_puntos_sin_evidencia() -> None:
    datos = salida()
    datos["criterios"][0]["evidencias"] = []
    with pytest.raises(ValidationError):
        AnalisisCV.model_validate(datos)
