"""Extracción acotada de CV en memoria, sin guardar documentos."""

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.config.settings import MAX_BYTES, MAX_CV_CHARS, MAX_PAGES


class ErrorDocumento(ValueError):
    """Documento no admitido o sin texto utilizable."""


def extraer_texto(nombre: str, contenido: bytes) -> str:
    """Extrae PDF o TXT y rechaza límites, corrupción y documentos escaneados."""
    if not contenido or len(contenido) > MAX_BYTES:
        raise ErrorDocumento("El archivo debe contener datos y pesar como máximo 5 MB.")
    extension = Path(nombre).suffix.lower()
    try:
        if extension == ".txt":
            texto = contenido.decode("utf-8-sig")
        elif extension == ".pdf":
            if not contenido.startswith(b"%PDF-"):
                raise ErrorDocumento("El contenido no es un PDF válido.")
            lector = PdfReader(BytesIO(contenido))
            if lector.is_encrypted:
                raise ErrorDocumento("El PDF está protegido. Sube una copia sin contraseña.")
            if len(lector.pages) > MAX_PAGES:
                raise ErrorDocumento(f"El CV no debe superar {MAX_PAGES} páginas.")
            partes = []
            for pagina in lector.pages:
                stream = pagina.get_contents()
                if stream is not None and len(stream.get_data()) > 10 * 1024 * 1024:
                    raise ErrorDocumento("El PDF es demasiado complejo. Exporta una versión más ligera.")
                partes.append(pagina.extract_text() or "")
                if sum(map(len, partes)) > MAX_CV_CHARS:
                    raise ErrorDocumento(f"El CV supera {MAX_CV_CHARS:,} caracteres.")
            texto = "\n\n".join(partes)
        else:
            raise ErrorDocumento("Usa un PDF con texto seleccionable o un TXT en UTF-8.")
    except ErrorDocumento:
        raise
    except Exception as error:
        raise ErrorDocumento(
            "No se pudo leer el archivo. Exporta de nuevo el CV como PDF o TXT UTF-8."
        ) from error
    texto = texto.replace("\x00", "").strip()
    if len(texto) < 80:
        raise ErrorDocumento("No hay suficiente texto extraíble. Los PDF escaneados necesitan OCR externo.")
    if len(texto) > MAX_CV_CHARS:
        raise ErrorDocumento(f"El CV supera {MAX_CV_CHARS:,} caracteres.")
    return texto
