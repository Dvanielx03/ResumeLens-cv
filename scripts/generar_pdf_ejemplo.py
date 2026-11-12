"""Genera un PDF ficticio con texto seleccionable, sin dependencias adicionales."""

from pathlib import Path
from textwrap import wrap


def generar(destino: Path) -> None:
    fuente = Path(__file__).resolve().parents[1] / "ejemplos/cv_ejemplo.txt"
    lineas = [parte for linea in fuente.read_text(encoding="utf-8").splitlines() for parte in wrap(linea, 85)]
    comandos = ["BT /F1 11 Tf 50 780 Td 16 TL"]
    for linea in lineas:
        comandos += [f"<{linea.encode('cp1252').hex()}> Tj T*"]
    comandos.append("ET")
    contenido = "\n".join(comandos).encode("ascii")
    objetos = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
               f"<< /Length {len(contenido)} >>\nstream\n".encode() + contenido + b"\nendstream"]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for indice, objeto in enumerate(objetos, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{indice} 0 obj\n".encode() + objeto + b"\nendobj\n")
    inicio = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{inicio}\n%%EOF\n".encode())
    destino.write_bytes(pdf)


if __name__ == "__main__":
    generar(Path(__file__).resolve().parents[1] / "ejemplos/cv_ejemplo.pdf")
