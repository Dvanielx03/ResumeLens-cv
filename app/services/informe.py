"""Exportación legible del análisis que permanece en la sesión."""

from app.domain.modelos import ETIQUETAS, AnalisisCV


def como_markdown(analisis: AnalisisCV, *, modelo: str, ejemplo: bool = False) -> str:
    lineas = ["# ResumeLens · Informe de ajuste", "", f"**Ajuste documental: {analisis.porcentaje}%**",
              f"Modelo: {modelo}", "Modo: ejemplo ficticio sin API" if ejemplo else "Modo: proveedor de IA", "", analisis.resumen, ""]
    for c in analisis.criterios:
        lineas += [f"## {ETIQUETAS[c.codigo]}",
                   f"Puntuación: {c.puntuacion}/100 · Peso efectivo: {analisis.peso_efectivo(c.codigo):.1f}%" if c.aplica else "No solicitado; excluido del cálculo.",
                   f"Requisito: {c.requisito}", c.justificacion, *[f"> {e}" for e in c.evidencias], ""]
    for titulo, items in [("Fortalezas", analisis.fortalezas), ("Brechas documentales", analisis.brechas), ("Siguientes pasos", analisis.siguientes_pasos)]:
        lineas += [f"## {titulo}", *[f"- {item}" for item in items], ""]
    lineas += ["El porcentaje es una medida orientativa de ajuste documental, no una probabilidad de contratación."]
    return "\n".join(lineas)
