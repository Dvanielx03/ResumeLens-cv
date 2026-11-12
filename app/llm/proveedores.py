"""Factory de modelos; las claves se reciben sin persistirlas."""

import os
from typing import Any

from app.config.settings import GOOGLE_MODEL, LLM_TIMEOUT_S, OPENAI_MODEL

PROVEEDORES = {"Google Gemini": ("GOOGLE_API_KEY", GOOGLE_MODEL), "OpenAI": ("OPENAI_API_KEY", OPENAI_MODEL)}


def crear_modelo(proveedor: str, modelo: str, clave: str = "") -> Any:
    """Crea el adaptador LangChain elegido, sin reintentos ocultos del SDK."""
    if proveedor not in PROVEEDORES:
        raise ValueError("Proveedor no admitido.")
    variable, predeterminado = PROVEEDORES[proveedor]
    clave = clave.strip() or os.getenv(variable, "").strip()
    if not clave:
        raise ValueError("Introduce una API key o configura la variable del proveedor en .env.")
    modelo = modelo.strip() or predeterminado
    if len(modelo) > 100 or any(c.isspace() for c in modelo):
        raise ValueError("El identificador del modelo no puede contener espacios.")
    if proveedor == "Google Gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=modelo, google_api_key=clave, timeout=LLM_TIMEOUT_S, max_retries=0)
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=modelo, api_key=clave, temperature=0, timeout=LLM_TIMEOUT_S, max_retries=0)
