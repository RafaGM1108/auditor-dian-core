"""Coteja el total de cada documento real (XML) contra el PDF que viene en el mismo ZIP.

Uso: uv run python -I scripts/cotejar_pdf.py <carpeta>   (necesita `pdftotext`, de poppler)

Reemplaza la revisión manual de M3 (SPEC §13): el PDF lo genera el emisor por su cuenta, así que
es una fuente independiente del parser. No es parte de `core`; solo imprime conteos y el número
de los documentos que no coinciden, sin cifras.
"""

import re
import subprocess
import sys
import zipfile
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

from auditor_dian.lector import leer_archivo

NUMERO = re.compile(r"\d[\d.,]*\d|\d")


def valores(texto: str) -> set[Decimal]:
    """Cada cifra del texto leída en formato colombiano (1.234,56) y en inglés (1,234.56)."""
    salida = set()
    for token in NUMERO.findall(texto):
        for miles, decimal in ((".", ","), (",", ".")):
            try:
                salida.add(Decimal(token.replace(miles, "").replace(decimal, ".")))
            except InvalidOperation:
                pass
    return salida


def cotejar(total: Decimal, texto: str) -> str:
    if not texto.strip():
        return "pdf_sin_texto"
    cifras = valores(texto)
    if total in cifras:
        return "coincide"
    # El PDF puede mostrar el total sin centavos o a la decena (Anexo FE 1.9, 5.2.1.2).
    redondeos = {total.quantize(Decimal("1"), ROUND_HALF_UP), (total / 10).quantize(0) * 10}
    return "difiere_por_redondeo" if redondeos & cifras else "no_encontrado"


def _texto_pdf(zf: zipfile.ZipFile) -> str:
    pdfs = [n for n in zf.namelist() if n.lower().endswith(".pdf")]
    if not pdfs:
        return ""
    salida = subprocess.run(
        ["pdftotext", "-layout", "-", "-"], input=zf.read(pdfs[0]), capture_output=True, check=False
    )
    return salida.stdout.decode("utf-8", "replace")


def main(carpeta: Path) -> None:
    assert cotejar(Decimal("427468.066"), "TOTAL 427,468.066") == "coincide"
    assert cotejar(Decimal("3034126"), "Total $ 3.034.130,00") == "difiere_por_redondeo"
    assert cotejar(Decimal("250399.97"), "Total: 250.400") == "difiere_por_redondeo"
    assert cotejar(Decimal("10"), "Total 99") == "no_encontrado"

    resultados = Counter()
    for ruta in sorted(carpeta.rglob("*.zip")):
        with zipfile.ZipFile(ruta) as zf:
            texto = _texto_pdf(zf)
        for leido in leer_archivo(ruta):
            if leido.documento and leido.documento.total_pagar is not None:
                estado = cotejar(leido.documento.total_pagar, texto)
                resultados[estado] += 1
                if estado != "coincide":
                    print(f"{estado}: {ruta.parent.name}/{leido.documento.numero}")
    print(dict(resultados), "de", sum(resultados.values()), "documentos")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
