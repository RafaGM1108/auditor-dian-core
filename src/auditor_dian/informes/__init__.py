"""Informes en SQL puro sobre la base del cliente (SPEC §7, decisión 0006).

Cada informe es un par de archivos en esta carpeta:
- `<nombre>.sql`: el detalle, una fila por documento (o por tributo), leyendo de `docs`.
- `<nombre>_resumen.sql`: el resumen, leyendo de `detalle`.

`docs` son los documentos del cliente (el adquirente es él) emitidos en el rango, con `signo`
(-1 para notas crédito y notas de ajuste del documento soporte, +1 para lo demás). Los montos
salen exactos; se redondean solo al presentar.
"""

from dataclasses import dataclass
from datetime import date
from importlib.resources import files

import duckdb

DOCS = """
    SELECT *, CASE WHEN tipo IN ('91', '95') THEN -1 ELSE 1 END AS signo
    FROM documentos
    WHERE fecha_emision BETWEEN $desde AND $hasta
      -- Los que llegaron a nombre de otro (advertencia adquirente_distinto) no son compras suyas.
      AND adquirente_identificacion = (SELECT id FROM cliente)
"""

NOTA_MONEDA = "Los montos van en la moneda de cada documento, sin convertir con la TRM."

NOTAS = {
    "compras_por_proveedor": "Totales por NIT emisor. Las notas crédito y las notas de ajuste "
    "del documento soporte restan; las notas débito suman. " + NOTA_MONEDA,
    "iva_compras_por_bimestre": "IVA (tributo 01) que figura en los documentos, por bimestre y "
    "tarifa, neto de notas crédito. No es una determinación de IVA descontable: eso lo decide "
    "el contador. No incluye otros impuestos (INC, bolsas). " + NOTA_MONEDA,
    "retenciones": "Retenciones que figuran en los documentos, por mes y código de tributo. En "
    "facturas y documento soporte son autorretenciones declaradas por el emisor (Anexo FE 1.9 "
    "FAT01, Anexo DS 1.1 DSAT01), no retenciones practicadas por el cliente. " + NOTA_MONEDA,
    "duplicados_y_anulaciones": "Documentos con el mismo emisor y número pero distinto CUFE, y "
    "facturas citadas por notas crédito: anulada_total si las notas suman su total con ±2,00 "
    "(Anexo FE 1.9, 5.2.1.1), anulada_parcial si no. " + NOTA_MONEDA,
    "facturas_credito": "Documentos con forma de pago crédito; la fecha de vencimiento no "
    "decide, porque hay emisores que la ponen en ventas de contado. Los eventos (aceptación, "
    "endoso) quedan por verificar: este programa no consulta a la DIAN. " + NOTA_MONEDA,
    "no_validadas": "Documentos sin respuesta de validación DIAN en el archivo recibido "
    "(sin_respuesta) o rechazados por la DIAN (rechazada). " + NOTA_MONEDA,
}


# Informes de plugins (SPEC §8): nombre -> (nota, detalle_sql, resumen_sql).
EXTRA: dict[str, tuple[str, str, str]] = {}


class InformeDesconocido(ValueError):
    pass


def disponibles() -> list[str]:
    return sorted({*NOTAS, *EXTRA})


def registrar(nombre: str, nota: str, detalle_sql: str, resumen_sql: str) -> None:
    if nombre in disponibles():
        raise ValueError(f"ya existe el informe {nombre!r}")
    EXTRA[nombre] = (nota, detalle_sql, resumen_sql)


@dataclass(frozen=True)
class Resultado:
    nombre: str
    nota: str
    columnas: list[str]
    filas: list[tuple]
    columnas_resumen: list[str]
    filas_resumen: list[tuple]


def ejecutar(con: duckdb.DuckDBPyConnection, nombre: str, desde: date, hasta: date) -> Resultado:
    if nombre in NOTAS:
        nota, detalle, resumen = (
            NOTAS[nombre],
            leer_sql(f"{nombre}.sql"),
            leer_sql(f"{nombre}_resumen.sql"),
        )
    elif nombre in EXTRA:
        nota, detalle, resumen = EXTRA[nombre]
    else:
        raise InformeDesconocido(
            f"informe desconocido {nombre!r}; disponibles: {', '.join(disponibles())}"
        )
    columnas, filas = consultar(con, detalle, desde, hasta)
    resumen = f"WITH detalle AS ({detalle}) {resumen}"
    return Resultado(nombre, nota, columnas, filas, *consultar(con, resumen, desde, hasta))


def consultar(
    con: duckdb.DuckDBPyConnection, sql: str, desde: date, hasta: date
) -> tuple[list[str], list[tuple]]:
    """Corre `sql` con `docs` definido para el rango; devuelve columnas y filas."""
    sql = sql.strip()
    # DuckDB no admite dos WITH seguidos: el del informe se encadena al de `docs`.
    unido = (
        f"WITH docs AS ({DOCS}), {sql[4:]}"
        if sql[:4].upper() == "WITH"
        else f"WITH docs AS ({DOCS}) {sql}"
    )
    cursor = con.execute(unido, {"desde": desde, "hasta": hasta})
    return [c[0] for c in cursor.description], cursor.fetchall()


def leer_sql(archivo: str) -> str:
    return files(__package__).joinpath(archivo).read_text(encoding="utf-8")
