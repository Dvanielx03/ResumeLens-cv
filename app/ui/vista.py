"""Interfaz Streamlit: puesto, documento y feedback verificable."""

import hashlib

import streamlit as st

from app.config.settings import MAX_JOB_CHARS
from app.domain.modelos import ETIQUETAS, AnalisisCV
from app.llm.proveedores import PROVEEDORES
from app.services.documentos import ErrorDocumento, extraer_texto
from app.services.evaluacion import ErrorAnalisis
from app.services.informe import como_markdown
from app.ui import dependencias

CSS = """<style>
.block-container {max-width:1140px;padding-top:2.5rem;padding-bottom:3rem;}
.rl-hero {border-top:4px solid #17624D;padding:1.4rem 0 1.6rem;border-bottom:1px solid #C9D2C9;margin-bottom:1.5rem;}
.rl-eyebrow {font-family:monospace;letter-spacing:.16em;font-size:.76rem;color:#426455;}
.rl-hero h1 {font-family:Georgia,serif;font-weight:400;font-size:clamp(2.8rem,7vw,4.5rem);letter-spacing:-.06em;margin:0;line-height:1.15;color:#182E28;}
.rl-hero p {font-size:1.05rem;max-width:650px;color:#426455;margin:.8rem 0 0;}
.rl-score {padding:1rem 0;border-top:1px solid #C9D2C9;border-bottom:1px solid #C9D2C9;margin-bottom:1rem;}
.rl-score strong {font-family:Georgia,serif;font-size:4.5rem;font-weight:400;letter-spacing:-.06em;color:#17624D;line-height:1.2;}
.rl-score span {display:block;color:#426455;}
[data-testid="stSidebar"] h2 {font-family:Georgia,serif;}
@media(max-width:640px){.block-container{padding-top:1.2rem;padding-inline:1rem;}.rl-score strong{font-size:3.7rem;}}
</style>"""


def _cargar_ejemplo() -> None:
    cv, puesto, evaluador = dependencias.ejemplo()
    analisis = evaluador.evaluar(cv, puesto)
    st.session_state.update(
        puesto=puesto,
        resultado=analisis.model_dump(),
        modo_ejemplo=True,
        archivo_epoch=st.session_state.get("archivo_epoch", 0) + 1,
        fuente_cv=cv,
        firma=None,
        modelo_resultado="Modelo falso · ejemplo fijo",
    )


def _limpiar() -> None:
    for clave in ("resultado", "firma", "fuente_cv", "modelo_resultado"):
        st.session_state.pop(clave, None)
    st.session_state.update(
        puesto="",
        modo_ejemplo=False,
        consentimiento=False,
        archivo_epoch=st.session_state.get("archivo_epoch", 0) + 1,
    )


def _nuevo_documento() -> None:
    st.session_state.update(modo_ejemplo=False, resultado=None)


def _firma(cv: str, puesto: str, proveedor: str, modelo: str) -> str:
    return hashlib.sha256("\0".join((cv, puesto, proveedor, modelo)).encode()).hexdigest()


def _resultado(analisis: AnalisisCV, es_ejemplo: bool, modelo: str) -> None:
    st.subheader("Tu resultado")
    if es_ejemplo:
        st.info("Ejemplo ficticio · salida predefinida validada por LangChain. No se llamó a una API.")
    st.markdown(
        f'<div class="rl-score"><strong>{analisis.porcentaje}%</strong><span>Ajuste documental al puesto</span></div>',
        unsafe_allow_html=True,
    )
    st.write(analisis.resumen)
    st.caption(f"Modelo: {modelo}. El porcentaje lo calcula Python, no el modelo.")
    st.markdown("#### Desglose del ajuste")
    for c in analisis.criterios:
        etiqueta = ETIQUETAS[c.codigo]
        titulo = f"{etiqueta} · {c.puntuacion}/100" if c.aplica else f"{etiqueta} · no solicitado"
        with st.expander(titulo):
            if c.aplica:
                st.progress(c.puntuacion / 100)
                st.caption(f"Peso efectivo: {analisis.peso_efectivo(c.codigo):.1f}%")
            else:
                st.caption("Excluido del cálculo; no penaliza el resultado.")
            st.write("**Requisito:**", c.requisito)
            st.write(c.justificacion)
            for cita in c.evidencias:
                st.text(f"«{cita}»")
    for titulo, elementos in [
        ("Fortalezas", analisis.fortalezas),
        ("Brechas documentales", analisis.brechas),
        ("Siguientes pasos", analisis.siguientes_pasos),
    ]:
        st.markdown(f"#### {titulo}")
        for elemento in elementos:
            st.write("• " + elemento)
    st.download_button(
        "Descargar informe",
        como_markdown(analisis, modelo=modelo, ejemplo=es_ejemplo),
        file_name="resumelens-informe.md",
        mime="text/markdown",
    )
    st.caption(
        "Es una orientación sobre el CV presentado, no una decisión ni una probabilidad de contratación."
    )


def render() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.header("Motor de análisis")
        proveedor = st.selectbox("Proveedor", list(PROVEEDORES))
        modelo = st.text_input("Modelo", value=PROVEEDORES[proveedor][1], key=f"modelo_{proveedor}")
        clave = st.text_input(
            "API key",
            type="password",
            key=f"clave_{proveedor}",
            help="Se usa en esta sesión. También puede configurarse en .env.",
        )
        st.caption(
            "Tu CV y el puesto se envían al proveedor únicamente al pulsar Analizar CV con tu autorización."
        )
        st.divider()
        st.caption("PDF o TXT · hasta 5 MB · 15 páginas · sin OCR")
        st.caption("Sin cuentas, base de datos ni historial persistente. No se habilita trazado externo.")
    st.markdown(
        '<header class="rl-hero"><div class="rl-eyebrow">CV + CONTEXTO → CLARIDAD</div><h1>ResumeLens</h1><p>Entiende cómo encaja tu experiencia con el próximo puesto. Con evidencia, criterio y un siguiente paso.</p></header>',
        unsafe_allow_html=True,
    )
    a, b = st.columns([1, 1])
    with a:
        st.button("Ver ejemplo sin API", on_click=_cargar_ejemplo, use_container_width=True)
    with b:
        st.button("Limpiar análisis", on_click=_limpiar, use_container_width=True)
    izquierda, derecha = st.columns([1, 1.05], gap="large")
    with izquierda:
        st.subheader("01 · Define el puesto")
        puesto = st.text_area(
            "Contexto del puesto",
            key="puesto",
            height=200,
            max_chars=MAX_JOB_CHARS,
            placeholder="Puesto, requisitos obligatorios y deseables, experiencia y responsabilidades…",
        )
        st.caption("Cuanto más concreto sea el puesto, más útil será el análisis. Mínimo 40 caracteres.")
        st.subheader("02 · Añade tu CV")
        archivo = st.file_uploader(
            "Subir hoja de vida",
            type=["pdf", "txt"],
            key=f"archivo_{st.session_state.get('archivo_epoch', 0)}",
            on_change=_nuevo_documento,
        )
        cv = ""
        if archivo:
            try:
                cv = extraer_texto(archivo.name, archivo.getvalue())
                st.success(f"Documento leído · {len(cv):,} caracteres")
            except ErrorDocumento as error:
                st.error(str(error))
        elif st.session_state.get("modo_ejemplo"):
            cv = st.session_state.get("fuente_cv", "")
            st.caption("CV ficticio cargado por el ejemplo.")
        if cv:
            with st.expander("Ver texto extraído"):
                st.text(cv)
        st.checkbox("Autorizo enviar el CV y el puesto al proveedor elegido", key="consentimiento")
        analizar = st.button("Analizar CV", type="primary", use_container_width=True)
        if analizar:
            if not cv or len(puesto.strip()) < 40:
                st.error("Añade un CV válido y describe el puesto con al menos 40 caracteres.")
            elif not st.session_state.get("consentimiento"):
                st.error("Autoriza el envío al proveedor para iniciar el análisis real.")
            else:
                try:
                    with st.spinner("Contrastando el CV con los requisitos…"):
                        resultado = dependencias.evaluador(proveedor, modelo, clave).evaluar(cv, puesto)
                    st.session_state.update(
                        resultado=resultado.model_dump(),
                        modo_ejemplo=False,
                        firma=_firma(cv, puesto, proveedor, modelo),
                        modelo_resultado=modelo,
                    )
                except (ErrorAnalisis, ValueError) as error:
                    st.session_state["resultado"] = None
                    st.error(str(error))
        st.caption(
            "No se guardan documentos en disco. Usa Limpiar análisis al terminar; el proveedor aplica su propia política de datos."
        )
    with derecha:
        datos = st.session_state.get("resultado")
        es_ejemplo = bool(st.session_state.get("modo_ejemplo"))
        vigente = bool(cv) and (
            (es_ejemplo and puesto == dependencias.ejemplo()[1])
            or st.session_state.get("firma") == _firma(cv, puesto, proveedor, modelo)
        )
        if datos and vigente:
            _resultado(AnalisisCV.model_validate(datos), es_ejemplo, st.session_state["modelo_resultado"])
        elif datos:
            st.info("Cambiaste las entradas. Vuelve a analizar para obtener un resultado actualizado.")
        else:
            st.subheader("03 · Descubre el ajuste")
            st.write("Aquí aparecerán el porcentaje, las evidencias y las mejoras sugeridas para ese puesto.")
            st.markdown("**Se evalúan cuatro criterios**")
            st.write("Experiencia · habilidades · formación · responsabilidades")
            st.caption(
                "Pesos base: 40 / 35 / 15 / 10. Un criterio que el puesto no solicita se excluye y los demás pesos se normalizan."
            )
        with st.expander("Cómo se calcula el porcentaje"):
            st.write(
                "La IA valora la cobertura documental de cada criterio de 0 a 100. Python calcula la media ponderada de los criterios solicitados y redondea al entero más cercano."
            )
            st.code("ajuste = Σ(puntuación × peso) / Σ(pesos aplicables)", language=None)
            st.caption(
                "Las citas se comprueban contra el texto del CV; esto no certifica la veracidad de su contenido ni garantiza que la valoración del modelo sea correcta."
            )
