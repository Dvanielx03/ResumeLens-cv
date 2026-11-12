"""Entrada de Streamlit: python -m streamlit run app/app.py."""

import os
import sys
from pathlib import Path

# Streamlit ejecuta el archivo por ruta: añadir la raíz antes de importar app.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Evitar exportar CVs mediante trazado heredado del entorno del desarrollador.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

import streamlit as st  # noqa: E402

from app.ui.vista import render  # noqa: E402

st.set_page_config(
    page_title="ResumeLens · CV y contexto", page_icon=":material/document_search:", layout="wide"
)
render()
