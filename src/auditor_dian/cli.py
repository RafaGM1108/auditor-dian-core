from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from auditor_dian.base import ErrorCliente, abrir, crear_cliente
from auditor_dian.excel import exportar
from auditor_dian.informes import NOTAS, InformeDesconocido, ejecutar
from auditor_dian.ingesta import ingerir as ingerir_ruta
from auditor_dian.plugins import cargar

app = typer.Typer(
    help="Auditor DIAN: lee facturas electrónicas recibidas. Local, solo lectura frente a la DIAN.",
    no_args_is_help=True,
)
clientes = typer.Typer(help="Crear clientes (una base por cliente).", no_args_is_help=True)
app.add_typer(clientes, name="clientes")


@app.callback()
def principal() -> None:
    cargar()


@clientes.command("crear")
def crear(
    id_cliente: Annotated[
        str, typer.Argument(help="NIT o cédula, como se escriba (con o sin puntos y DV).")
    ],
    nombre: Annotated[str, typer.Option("--nombre", help="Nombre o razón social.")],
) -> None:
    """Crea la base de un cliente nuevo."""
    try:
        ruta = crear_cliente(id_cliente, nombre)
    except ErrorCliente as error:
        _fallar(error)
    typer.echo(f"Cliente {id_cliente} creado en {ruta}")


@app.command()
def ingerir(
    id_cliente: Annotated[str, typer.Argument(help="NIT o cédula del cliente, como se escriba.")],
    ruta: Annotated[
        Path,
        typer.Argument(exists=True, help="Archivo ZIP o XML, o carpeta (se recorre completa)."),
    ],
) -> None:
    """Carga facturas en la base del cliente. Reingerir lo mismo no duplica nada."""
    try:
        con = abrir(id_cliente)
    except ErrorCliente as error:
        _fallar(error)
    with con:
        r = ingerir_ruta(con, id_cliente, ruta)
    typer.echo(f"Archivos: {r.archivos_nuevos} nuevos, {r.archivos_repetidos} ya ingeridos")
    typer.echo(f"Documentos guardados: {r.documentos} ({r.cufes_repetidos} CUFE ya existentes)")
    typer.echo(f"Advertencias: {r.advertencias} · Errores de lectura: {r.errores}")
    if r.advertencias or r.errores:
        typer.echo("El detalle queda en la tabla `advertencias` de la base del cliente.")
    for archivo, error in r.fallidos:
        typer.echo(f"No se pudo guardar {archivo}: {error}", err=True)
    if r.fallidos:
        typer.echo(
            "Esos archivos no quedaron registrados; se reintentan en la próxima ingesta.", err=True
        )
        raise typer.Exit(1)


Fecha = Annotated[datetime, typer.Option(formats=["%Y-%m-%d"], help="AAAA-MM-DD, inclusive.")]


@app.command()
def informe(
    id_cliente: Annotated[str, typer.Argument(help="NIT o cédula del cliente, como se escriba.")],
    nombre: Annotated[str, typer.Argument(help=f"Uno de: {', '.join(sorted(NOTAS))}.")],
    desde: Fecha,
    hasta: Fecha,
    xlsx: Annotated[
        Path | None, typer.Option(help="Guarda también un .xlsx con hojas resumen y detalle.")
    ] = None,
) -> None:
    """Imprime el resumen de un informe por fecha de emisión. Abre la base en solo lectura."""
    if desde > hasta:
        _fallar(ValueError("--desde es posterior a --hasta"))
    try:
        con = abrir(id_cliente, solo_lectura=True)
    except ErrorCliente as error:
        _fallar(error)
    with con:
        try:
            r = ejecutar(con, nombre, desde.date(), hasta.date())
        except InformeDesconocido as error:
            _fallar(error)
    typer.echo(f"{r.nombre} · {desde:%Y-%m-%d} a {hasta:%Y-%m-%d}")
    typer.echo(r.nota)
    typer.echo(_tabla(r.columnas_resumen, r.filas_resumen))
    typer.echo(f"Detalle: {len(r.filas)} filas.")
    if xlsx:
        try:
            exportar(r, desde.date(), hasta.date(), xlsx)
        except OSError as error:
            _fallar(error)
        typer.echo(f"Excel guardado en {xlsx}")


@app.command()
def mcp() -> None:
    """Inicia el servidor MCP por stdio (solo lectura) para un agente como Claude."""
    from auditor_dian.servidor import servidor  # el SDK de MCP solo se carga para este comando

    servidor.run()


def _tabla(columnas: list[str], filas: list[tuple]) -> str:
    celdas = [columnas] + [[_presentar(v) for v in fila] for fila in filas]
    anchos = [max(len(f[i]) for f in celdas) for i in range(len(columnas))]
    return "\n".join("  ".join(c.ljust(a) for c, a in zip(f, anchos, strict=True)) for f in celdas)


def _presentar(valor: object) -> str:
    if isinstance(valor, Decimal):
        texto = f"{valor.quantize(Decimal('0.01'), ROUND_HALF_UP):,.2f}"
        return texto.translate(str.maketrans(",.", ".,"))
    return "" if valor is None else str(valor)


def _fallar(error: Exception) -> NoReturn:
    typer.echo(f"Error: {error}", err=True)
    raise typer.Exit(1)
