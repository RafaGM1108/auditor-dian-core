"""Guarda en la base del cliente lo que entrega el lector, sin duplicar (SPEC §6).

Idempotencia en dos niveles: un archivo cuyo SHA-256 ya está en `archivos_ingeridos` se salta
completo, y un CUFE ya guardado no se inserta de nuevo (queda la advertencia `cufe_repetido`).
Cada archivo se guarda en una transacción: si algo falla, no queda marcado y se reintenta en
la siguiente ingesta.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from itertools import chain, groupby
from pathlib import Path

import duckdb

from auditor_dian.base import normalizar_id
from auditor_dian.lector import leer_ruta
from auditor_dian.modelos import Advertencia, Documento, Lectura, Tributo

DECIMALES_MONTO = 6  # DECIMAL(21,6) en schema.sql
DECIMALES_TARIFA = 3  # DECIMAL(9,3) en schema.sql


@dataclass
class Resumen:
    archivos_nuevos: int = 0
    archivos_repetidos: int = 0
    documentos: int = 0
    cufes_repetidos: int = 0
    advertencias: int = 0
    errores: int = 0  # lecturas sin documento o documentos sin CUFE
    fallidos: list[tuple[str, str]] = field(default_factory=list)  # (ruta, error) sin guardar
    # Documentos que no se guardan porque el cliente no es su comprador ni su vendedor, por
    # identificación del comprador (decisión 0011).
    ajenos: dict[str, int] = field(default_factory=dict)


def ingerir(con: duckdb.DuckDBPyConnection, id_cliente: str, ruta: Path) -> Resumen:
    return ingerir_lecturas(con, id_cliente, leer_ruta(ruta))


@dataclass
class Separacion:
    por_comprador: dict[str, list[Lectura]] = field(default_factory=dict)  # id -> lecturas
    nombres: dict[str, str | None] = field(default_factory=dict)  # id -> nombre en el XML
    sin_asignar: list[tuple[str, str]] = field(default_factory=list)  # (archivo, motivo)


def separar(*rutas: Path) -> Separacion:
    """Reparte los archivos de `rutas` por la identificación del comprador (adquirente) de sus
    documentos, para cargar en un solo paso facturas de varios clientes. Un archivo no se parte:
    si no trae documentos legibles o trae de varios compradores, queda sin asignar."""
    s = Separacion()
    for (archivo, _), grupo in groupby(
        chain.from_iterable(map(leer_ruta, rutas)), key=lambda lec: (lec.ruta, lec.sha256)
    ):
        lecturas = list(grupo)
        compradores = {lec.documento.adquirente for lec in lecturas if lec.documento}
        ids = {c.identificacion for c in compradores}
        if not ids:
            errores = sorted({lec.error for lec in lecturas if lec.error})
            s.sin_asignar.append((archivo, "sin documentos legibles: " + "; ".join(errores)))
            continue
        if len(ids) > 1:
            varios = ", ".join(sorted(i for i in ids if i))
            s.sin_asignar.append(
                (
                    archivo,
                    f"trae documentos de varios compradores ({varios}): "
                    "cárguelo en cada cliente registrado con ingerir_facturas; en cada uno solo "
                    "entran sus documentos y los de otra persona se rechazan solos, así que no "
                    "hace falta separarlos a mano",
                )
            )
            continue
        if None in ids:
            s.sin_asignar.append((archivo, "el comprador no tiene identificación"))
            continue
        (comprador,) = ids
        s.por_comprador.setdefault(comprador, []).extend(lecturas)
        s.nombres.setdefault(comprador, next(c.nombre for c in compradores))
    return s


def ingerir_lecturas(con: duckdb.DuckDBPyConnection, id_cliente: str, lecturas) -> Resumen:
    id_cliente = normalizar_id(id_cliente)
    resumen = Resumen()
    for (archivo, sha), grupo in groupby(lecturas, key=lambda lec: (lec.ruta, lec.sha256)):
        lecturas = list(grupo)
        if _existe(con, "archivos_ingeridos", "sha256", sha):
            resumen.archivos_repetidos += 1
            continue
        parcial = Resumen(archivos_nuevos=1)
        con.begin()
        try:
            _guardar_archivo(con, id_cliente, archivo, sha, lecturas, parcial)
            con.commit()
        except (duckdb.Error, ArithmeticError) as error:
            con.rollback()
            resumen.fallidos.append((archivo, str(error)))
            continue
        for campo in (
            "archivos_nuevos",
            "documentos",
            "cufes_repetidos",
            "advertencias",
            "errores",
        ):
            setattr(resumen, campo, getattr(resumen, campo) + getattr(parcial, campo))
        for otro, n in parcial.ajenos.items():
            resumen.ajenos[otro] = resumen.ajenos.get(otro, 0) + n
    return resumen


def _guardar_archivo(con, id_cliente, archivo, sha, lecturas: list[Lectura], r: Resumen):
    con.execute(
        "INSERT INTO archivos_ingeridos (sha256, ruta, documentos, errores) VALUES (?, ?, ?, ?)",
        [
            sha,
            archivo,
            sum(1 for lec in lecturas if lec.documento),
            sum(1 for lec in lecturas if lec.documento is None),
        ],
    )
    for lec in lecturas:
        doc = lec.documento
        if doc is None:
            r.errores += 1
            _advertencias(con, sha, lec.miembro, None, [Advertencia("error_lectura", lec.error)])
            continue
        if doc.cufe is None:
            r.errores += 1
            sin_cufe = Advertencia(
                "documento_sin_cufe", "no se guarda: sin CUFE no hay idempotencia"
            )
            _advertencias(con, sha, lec.miembro, None, [*doc.advertencias, sin_cufe])
            continue
        if _existe(con, "documentos", "cufe", doc.cufe):
            r.cufes_repetidos += 1
            repetido = Advertencia("cufe_repetido", "el documento ya estaba guardado")
            _advertencias(con, sha, lec.miembro, doc.cufe, [repetido])
            continue
        if id_cliente not in (doc.adquirente.identificacion, doc.emisor.identificacion):
            comprador = str(doc.adquirente.identificacion)
            r.ajenos[comprador] = r.ajenos.get(comprador, 0) + 1
            ajeno = Advertencia(
                "documento_ajeno",
                f"no se guarda: el comprador es {comprador!r} y el vendedor "
                f"{doc.emisor.identificacion!r}, ninguno es el cliente {id_cliente!r}",
            )
            _advertencias(con, sha, lec.miembro, None, [ajeno])
            continue
        advertencias = list(doc.advertencias)
        if doc.adquirente.identificacion != id_cliente:  # el cliente es el vendedor
            advertencias.append(
                Advertencia(
                    "adquirente_distinto",
                    f"adquirente {doc.adquirente.identificacion!r}, cliente {id_cliente!r}",
                )
            )
        _guardar_documento(con, doc, sha, lec.miembro, advertencias)
        _advertencias(con, sha, lec.miembro, doc.cufe, advertencias)
        r.documentos += 1
        r.advertencias += len(advertencias)


def _guardar_documento(con, doc: Documento, sha, miembro, advertencias: list[Advertencia]):
    def monto(valor, campo):
        return _ajustar(valor, DECIMALES_MONTO, campo, advertencias)

    _insertar(
        con,
        "documentos",
        {
            "cufe": doc.cufe,
            "esquema_cufe": doc.esquema_cufe,
            "tipo": doc.tipo,
            "prefijo": doc.prefijo,
            "numero": doc.numero,
            "fecha_emision": doc.fecha_emision,
            "hora_emision": doc.hora_emision.isoformat() if doc.hora_emision else None,
            "fecha_vencimiento": doc.fecha_vencimiento,
            "forma_pago": doc.forma_pago,
            "medios_pago": list(doc.medios_pago),
            "moneda": doc.moneda,
            "trm": monto(doc.trm, "trm"),
            "emisor_tipo_identificacion": doc.emisor.tipo_identificacion,
            "emisor_identificacion": doc.emisor.identificacion,
            "emisor_dv": doc.emisor.dv,
            "emisor_nombre": doc.emisor.nombre,
            "adquirente_tipo_identificacion": doc.adquirente.tipo_identificacion,
            "adquirente_identificacion": doc.adquirente.identificacion,
            "adquirente_dv": doc.adquirente.dv,
            "adquirente_nombre": doc.adquirente.nombre,
            "subtotal": monto(doc.subtotal, "subtotal"),
            "base_gravable": monto(doc.base_gravable, "base_gravable"),
            "total_impuestos_incluidos": monto(
                doc.total_impuestos_incluidos, "total_impuestos_incluidos"
            ),
            "descuentos": monto(doc.descuentos, "descuentos"),
            "cargos": monto(doc.cargos, "cargos"),
            "anticipos": monto(doc.anticipos, "anticipos"),
            "redondeo": monto(doc.redondeo, "redondeo"),
            "total_pagar": monto(doc.total_pagar, "total_pagar"),
            "validado_dian": doc.validado_dian,
            "sha256": sha,
            "miembro": miembro,
        },
    )
    for orden, ref in enumerate(doc.referencias, start=1):
        _insertar(
            con,
            "referencias",
            {
                "cufe": doc.cufe,
                "orden": orden,
                "numero": ref.numero,
                "cufe_referenciado": ref.cufe,
                "fecha": ref.fecha,
            },
        )
    for tabla, tributos in (("impuestos", doc.impuestos), ("retenciones", doc.retenciones)):
        for orden, t in enumerate(tributos, start=1):
            _insertar(
                con, tabla, {"cufe": doc.cufe, "orden": orden, **_tributo(t, tabla, advertencias)}
            )
    for orden, li in enumerate(doc.lineas, start=1):
        _insertar(
            con,
            "lineas",
            {
                "cufe": doc.cufe,
                "orden": orden,
                "numero": li.numero,
                "descripcion": li.descripcion,
                "cantidad": monto(li.cantidad, f"linea {orden}.cantidad"),
                "unidad": li.unidad,
                "valor_unitario": monto(li.valor_unitario, f"linea {orden}.valor_unitario"),
                "valor_total": monto(li.valor_total, f"linea {orden}.valor_total"),
            },
        )
        for sub, t in enumerate(li.impuestos, start=1):
            fila = {"cufe": doc.cufe, "linea": orden, "orden": sub}
            fila |= _tributo(t, f"linea {orden}.impuestos", advertencias)
            _insertar(con, "impuestos_linea", fila)


def _tributo(t: Tributo, campo: str, advertencias: list[Advertencia]) -> dict:
    return {
        "codigo": t.codigo,
        "tarifa": _ajustar(t.tarifa, DECIMALES_TARIFA, f"{campo}.tarifa", advertencias),
        "base": _ajustar(t.base, DECIMALES_MONTO, f"{campo}.base", advertencias),
        "valor": _ajustar(t.valor, DECIMALES_MONTO, f"{campo}.valor", advertencias),
    }


def _ajustar(valor: Decimal | None, decimales: int, campo: str, advertencias: list[Advertencia]):
    # DuckDB redondea en silencio lo que no cabe en la columna; aquí se redondea a la vista.
    if valor is None:
        return None
    ajustado = valor.quantize(Decimal(1).scaleb(-decimales))
    if ajustado != valor:
        advertencias.append(Advertencia("valor_redondeado", f"{campo}: {valor} → {ajustado}"))
    return ajustado


def _advertencias(con, sha, miembro, cufe, advertencias: list[Advertencia]):
    for a in advertencias:
        _insertar(
            con,
            "advertencias",
            {
                "sha256": sha,
                "miembro": miembro,
                "cufe": cufe,
                "codigo": a.codigo,
                "detalle": a.detalle,
            },
        )


def _insertar(con, tabla: str, fila: dict):
    # Tablas y columnas son constantes de este módulo, nunca datos del XML.
    # La hora va como texto ISO: el binding de DuckDB 2.0 no acepta offsets negativos (0004).
    marcas = ", ".join("CAST(? AS TIMETZ)" if c == "hora_emision" else "?" for c in fila)
    con.execute(f"INSERT INTO {tabla} ({', '.join(fila)}) VALUES ({marcas})", list(fila.values()))


def _existe(con, tabla: str, columna: str, valor: str) -> bool:
    return con.execute(f"SELECT 1 FROM {tabla} WHERE {columna} = ?", [valor]).fetchone() is not None
