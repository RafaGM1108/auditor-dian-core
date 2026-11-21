from datetime import date
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from auditor_dian.informes import Resultado

FORMATO_MONTO = "#,##0.00"  # el valor va exacto; solo la vista redondea a 2 decimales
FORMATO_FECHA = "yyyy-mm-dd"


def exportar(r: Resultado, desde: date, hasta: date, ruta: Path) -> Path:
    libro = Workbook()
    resumen = libro.active
    resumen.title = "resumen"
    resumen.append([r.nombre])
    resumen["A1"].font = Font(bold=True)
    resumen.append([f"Fecha de emisión del {desde:%Y-%m-%d} al {hasta:%Y-%m-%d}"])
    resumen.append([r.nota])
    resumen.append([])
    _tabla(resumen, r.columnas_resumen, r.filas_resumen)
    _tabla(libro.create_sheet("detalle"), r.columnas, r.filas)
    libro.save(ruta)
    return ruta


def _tabla(hoja: Worksheet, columnas: list[str], filas: list[tuple]) -> None:
    hoja.append(columnas)
    encabezado = hoja.max_row
    for celda in hoja[encabezado]:
        celda.font = Font(bold=True)
    hoja.freeze_panes = f"A{encabezado + 1}"  # texto: hoja.cell() crearía una fila vacía
    for fila in filas:
        hoja.append(list(fila))
        for celda in hoja[hoja.max_row]:
            if isinstance(celda.value, Decimal):
                celda.number_format = FORMATO_MONTO
            elif isinstance(celda.value, date):
                celda.number_format = FORMATO_FECHA
    for i, nombre in enumerate(columnas, start=1):
        hoja.column_dimensions[get_column_letter(i)].width = max(12, len(nombre) + 2)
