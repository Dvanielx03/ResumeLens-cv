"""Rechazo de documentos inválidos antes de enviar datos a la IA."""

from io import BytesIO

import pytest
from pypdf import PdfWriter

from app.services.documentos import ErrorDocumento, extraer_texto


def test_extrae_txt_utf8() -> None:
    texto = "Experiencia desarrollando aplicaciones Python y APIs REST. " * 4
    assert extraer_texto("cv.TXT", texto.encode("utf-8")) == texto.strip()


@pytest.mark.parametrize(
    "nombre,datos",
    [
        ("cv.pdf", b"no es un pdf"),
        ("cv.txt", b"corto"),
        ("cv.docx", b"contenido"),
        ("cv.txt", b"\xff" * 100),
        ("cv.pdf", b""),
    ],
)
def test_rechaza_archivos_invalidos(nombre: str, datos: bytes) -> None:
    with pytest.raises(ErrorDocumento):
        extraer_texto(nombre, datos)


def test_rechaza_pdf_sin_texto() -> None:
    writer = PdfWriter()
    writer.add_blank_page(612, 792)
    stream = BytesIO()
    writer.write(stream)
    with pytest.raises(ErrorDocumento, match="OCR"):
        extraer_texto("escaneado.pdf", stream.getvalue())


def test_rechaza_tamano_excesivo() -> None:
    with pytest.raises(ErrorDocumento, match="5 MB"):
        extraer_texto("cv.txt", b"a" * (5 * 1024 * 1024 + 1))
