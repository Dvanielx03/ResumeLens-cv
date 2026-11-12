"""Contratos de evaluación y cálculo transparente del ajuste."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Codigo = Literal["experiencia", "habilidades", "formacion", "responsabilidades"]
PESOS: dict[str, int] = {"experiencia": 40, "habilidades": 35, "formacion": 15, "responsabilidades": 10}
ETIQUETAS = {
    "experiencia": "Experiencia relevante",
    "habilidades": "Habilidades técnicas",
    "formacion": "Formación y certificaciones",
    "responsabilidades": "Responsabilidades del puesto",
}


class Criterio(BaseModel):
    """Criterio respaldado por citas literales del CV."""

    model_config = ConfigDict(extra="forbid")
    codigo: Codigo
    aplica: bool
    puntuacion: int = Field(ge=0, le=100, strict=True)
    requisito: str = Field(min_length=5, max_length=600)
    justificacion: str = Field(min_length=10, max_length=1000)
    evidencias: list[str] = Field(max_length=5)

    @model_validator(mode="after")
    def comprobar_evidencias(self) -> "Criterio":
        if not self.aplica and (self.puntuacion != 0 or self.evidencias):
            raise ValueError("Un criterio no solicitado debe tener cero puntos y ninguna evidencia.")
        if self.aplica and self.puntuacion > 0 and not self.evidencias:
            raise ValueError("Una puntuación positiva requiere evidencia literal del CV.")
        if any(len(e.strip()) < 8 for e in self.evidencias):
            raise ValueError("Las citas deben contener al menos ocho caracteres.")
        return self


class AnalisisCV(BaseModel):
    """Salida estructurada del modelo, sin porcentaje global inventado."""

    model_config = ConfigDict(extra="forbid")
    resumen: str = Field(min_length=20, max_length=1200)
    criterios: list[Criterio] = Field(min_length=4, max_length=4)
    fortalezas: list[str] = Field(min_length=1, max_length=5)
    brechas: list[str] = Field(min_length=1, max_length=5)
    siguientes_pasos: list[str] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def comprobar_criterios(self) -> "AnalisisCV":
        if {c.codigo for c in self.criterios} != set(PESOS):
            raise ValueError("Se requieren los cuatro criterios, sin duplicados.")
        if not any(c.aplica for c in self.criterios):
            raise ValueError("El puesto debe contener al menos un criterio evaluable.")
        for lista in (self.fortalezas, self.brechas, self.siguientes_pasos):
            if any(not item.strip() or len(item) > 1000 for item in lista):
                raise ValueError("El feedback debe contener textos útiles de hasta 1000 caracteres.")
        return self

    @property
    def porcentaje(self) -> int:
        activos = [c for c in self.criterios if c.aplica]
        total = sum(PESOS[c.codigo] for c in activos)
        puntos = sum(PESOS[c.codigo] * c.puntuacion for c in activos)
        return int((Decimal(puntos) / Decimal(total)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def peso_efectivo(self, codigo: str) -> float:
        activos = [c for c in self.criterios if c.aplica]
        if codigo not in {c.codigo for c in activos}:
            return 0.0
        return 100 * PESOS[codigo] / sum(PESOS[c.codigo] for c in activos)
