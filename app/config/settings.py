"""Configuración de proveedores y límites de entrada."""

import os

from dotenv import load_dotenv

load_dotenv()

GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-3.5-flash-lite")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LLM_TIMEOUT_S = max(1.0, min(float(os.getenv("LLM_TIMEOUT_S", "30")), 120.0))
MAX_BYTES = 5 * 1024 * 1024
MAX_PAGES = 15
MAX_CV_CHARS = 30_000
MAX_JOB_CHARS = 12_000
