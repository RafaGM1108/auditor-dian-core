"""Servidor MCP por stdio con las herramientas de SPEC §10.

Cada llamada abre la base del cliente y la cierra al terminar, así una ingesta puede correr
entre dos preguntas del agente. Las consultas la abren en solo lectura; solo las herramientas de
carga escriben, y solo agregan (decisión 0010). Los montos salen como texto
decimal exacto ("150500.5"), nunca como float, y cada respuesta lleva el aviso del SPEC.
"""

import base64
import inspect
import os
import re
import secrets
import unicodedata
from datetime import date
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, Any

import duckdb
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import Icon, ToolAnnotations
from pydantic import Field

from auditor_dian.base import (
    ErrorCliente,
    abrir,
    digito_verificacion,
    inicio,
    normalizar_id,
    ruta_base,
    ruta_exacta,
)
from auditor_dian.base import crear_cliente as crear_base
from auditor_dian.excel import exportar
from auditor_dian.informes import InformeDesconocido, consultar, ejecutar, leer_sql
from auditor_dian.ingesta import ingerir, ingerir_lecturas, separar
from auditor_dian.parametros import Cliente, Desde, Hasta

# Documentos guardados donde el cliente no es comprador ni vendedor (bases cargadas antes de la
# decisión 0011). Los informes ya los excluyen; se cuentan para avisar.
AJENOS_SQL = (
    "SELECT count(*) FROM documentos WHERE (SELECT id FROM cliente)"
    " NOT IN (adquirente_identificacion, coalesce(emisor_identificacion, ''))"
)
AVISO = "Cifras calculadas a partir de los documentos cargados. Requiere revisión del contador."
MAX_FILAS = 200
LECTURA = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
AGREGA = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False)
AGREGA_REPETIBLE = AGREGA.model_copy(update={"idempotent_hint": True})
EXTENSIONES = {".zip", ".xml"}
# Comprador genérico cuando no se identifica (Anexo Técnico FE 1.9, Res. DIAN 000165 de 2023,
# campos FAK21 y CAK62: "consumidor final ... documento 222222222222").
CONSUMIDOR_FINAL = "222222222222"
# Carpetas comunes en español o inglés (según el idioma del sistema), por nombre en minúscula.
CARPETAS = {
    nombre.lower(): par
    for par in (("Descargas", "Downloads"), ("Escritorio", "Desktop"), ("Documentos", "Documents"))
    for nombre in par
}
# Lo que acepta la API de Claude: con otros caracteres (p. ej. "año") Claude Desktop descarta la
# herramienta en silencio. https://docs.claude.com/en/docs/agents-and-tools/tool-use/implement-tool-use
NOMBRE_HERRAMIENTA = re.compile(r"[a-zA-Z0-9_-]{1,64}")
NOMBRE_PARAMETRO = re.compile(r"[a-zA-Z0-9_.-]{1,64}")


TOKEN = re.compile(r"[A-Za-z0-9_-]{32,}")


def token_http() -> str:
    """Secreto de la URL del servidor HTTP (decisión 0014): `AUDITOR_DIAN_TOKEN`, o uno de 256
    bits que se crea la primera vez en la carpeta de datos, legible solo por su dueño."""
    if token := os.environ.get("AUDITOR_DIAN_TOKEN", "").strip():
        if not TOKEN.fullmatch(token):
            raise ValueError("AUDITOR_DIAN_TOKEN debe tener 32 o más letras, números, - o _")
        return token
    archivo = inicio() / "token-mcp"
    if not archivo.exists():
        archivo.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(archivo, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as f:
            f.write(secrets.token_urlsafe(32))
    return archivo.read_text(encoding="utf-8").strip()


def nombres_invalidos(nombre: str, esquema: dict) -> list[str]:
    """Nombre de la herramienta y de cada parámetro (también anidados) que la API rechazaría."""
    malos = [] if NOMBRE_HERRAMIENTA.fullmatch(nombre) else [nombre]
    pendientes = [esquema]
    while pendientes:
        nodo = pendientes.pop()
        if isinstance(nodo, list):
            pendientes += nodo
        elif isinstance(nodo, dict):
            malos += [p for p in nodo.get("properties", {}) if not NOMBRE_PARAMETRO.fullmatch(p)]
            pendientes += list(nodo.values())
    return malos


def _icono(nombre: str, tipo: str, tamaño: str) -> Icon:
    # Embebido como data URI: el servidor no hace llamadas de red ni depende de una URL pública.
    datos = base64.b64encode((Path(__file__).parent / nombre).read_bytes()).decode()
    return Icon(src=f"data:{tipo};base64,{datos}", mime_type=tipo, sizes=[tamaño])


servidor = MCPServer(
    "auditor-dian",
    title="Auditor DIAN",
    description=(
        "Facturas electrónicas DIAN recibidas por cada cliente, convertidas en una base local: "
        "carga de ZIP y XML, búsqueda de documentos, resumen del periodo (compras, IVA y "
        "retenciones con sus CUFE), facturas a crédito, duplicados y anulaciones, y "
        "exportación a Excel. "
        "No es un producto oficial de la DIAN."
    ),
    version=version("auditor-dian-core"),
    icons=[_icono("logo.png", "image/png", "256x256"), _icono("logo.svg", "image/svg+xml", "any")],
    instructions=(
        "Carga y consulta las facturas electrónicas DIAN que recibió cada cliente. Para cargar: "
        "crear_cliente (una vez) e ingerir_facturas con la ruta de un ZIP, XML o carpeta; si la "
        "carpeta trae facturas de varios clientes, o el usuario no dice dónde están, "
        "ingerir_por_cliente las reparte (sin ruta revisa Descargas). Para saber "
        "si un cliente ya está registrado: listar_clientes con buscar; historial_cliente dice "
        "qué meses tiene cargados. "
        "Si algo falla o una cifra no cuadra, diagnostico resume el estado para reportarlo. "
        "Las cifras ya vienen calculadas: cítelas tal cual con sus CUFE, sin sumarlas ni "
        "redondearlas. Los montos son texto decimal exacto en la moneda de cada documento. "
        "Fechas en formato AAAA-MM-DD; los rangos son inclusivos y por fecha de emisión. "
        "El usuario puede no tener conocimientos técnicos: pídale la carpeta por su nombre (por "
        "ejemplo 'facturas-enero, en Descargas'), no una ruta; pase el NIT o la cédula tal "
        "como lo escribió, el servidor lo interpreta; responda en lenguaje sencillo, sin "
        "mencionar herramientas, JSON ni códigos internos salvo que lo pida. "
        f"Diga siempre al usuario: {AVISO}"
    ),
)


def descripcion(doc: str) -> str:
    """Docstring a texto corrido, como lo muestra Claude Desktop: une las líneas que el ancho del
    código partió y conserva párrafos y viñetas."""
    parrafos = []
    for parrafo in inspect.cleandoc(doc).split("\n\n"):
        lineas: list[str] = []
        for linea in parrafo.splitlines():
            if linea.startswith("- ") or not lineas:
                lineas.append(linea)
            else:
                lineas[-1] += " " + linea.strip()
        parrafos.append("\n".join(lineas))
    return "\n\n".join(parrafos)


def herramienta(titulo: str, anotaciones: ToolAnnotations):
    def registrar(funcion):
        texto = descripcion(funcion.__doc__)
        return servidor.tool(title=titulo, description=texto, annotations=anotaciones)(funcion)

    return registrar


@herramienta("Buscar clientes", LECTURA)
def listar_clientes(
    buscar: Annotated[
        str | None,
        Field(
            description="Parte del NIT o del nombre, como lo diga el usuario. No importan "
            "mayúsculas, tildes, espacios ni puntos ('S.A.S.' = 'sas'). Sin él, lista todos."
        ),
    ] = None,
) -> dict:
    """Lista los clientes registrados en este equipo (NIT o cédula y nombre), o busca uno.

    Úsela cuando el usuario pregunte, por ejemplo:
    - "¿Ya tengo registrada a Panadería La Espiga?"
    - "¿Qué clientes tengo?"
    - Antes de cualquier consulta en la que el usuario nombre al cliente por su razón social y
      no por su NIT, para obtener el NIT.

    Para ver qué meses tiene cargados un cliente use historial_cliente."""
    clientes = _clientes()
    if buscar:
        b = _normalizar(buscar)
        clientes = [c for c in clientes if b in c["id"] or b in _normalizar(c.get("nombre", ""))]
    return {"aviso": AVISO, "clientes": clientes}


@herramienta("Historial del cliente", LECTURA)
def historial_cliente(cliente: Cliente) -> dict:
    """Ficha de un cliente registrado: nombre, fecha de registro, cuántos documentos tiene por
    tipo y por mes de emisión, primera y última fecha de emisión, y cada día en que se cargaron
    facturas con sus archivos, documentos y errores.

    Úsela cuando el usuario pregunte, por ejemplo:
    - "¿Qué tengo cargado de Panadería La Espiga?"
    - "¿Me faltan meses de este cliente?" / "¿Hasta qué fecha tengo facturas?"
    - "¿Cuándo cargué las facturas de marzo?"

    No trae montos: para cifras use resumen_periodo."""
    return {"aviso": AVISO, **_historial(cliente)}


def _clientes() -> list[dict]:
    clientes = []
    for carpeta in sorted((inicio() / "clientes").glob("*")):
        try:
            with abrir(carpeta.name, solo_lectura=True) as con:
                nombre = con.execute("SELECT nombre FROM cliente").fetchone()[0]
            clientes.append({"id": carpeta.name, "nombre": nombre})
        except ErrorCliente as error:
            clientes.append({"id": carpeta.name, "error": str(error)})
    return clientes


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", sin_tildes.lower())


def _historial(cliente: str) -> dict:
    with abrir_cliente(cliente) as con:
        cliente = con.execute("SELECT id FROM cliente").fetchone()[0]
        nombre, creado = con.execute("SELECT nombre, creado FROM cliente").fetchone()
        ajenos = con.execute(AJENOS_SQL).fetchone()[0]
        primera, ultima = con.execute(
            "SELECT min(fecha_emision), max(fecha_emision) FROM documentos"
        ).fetchone()
        por_tipo = con.execute("SELECT tipo, count(*) FROM documentos GROUP BY 1 ORDER BY 1")
        por_tipo = por_tipo.fetchall()
        por_mes = con.execute(
            "SELECT strftime(fecha_emision, '%Y-%m'), count(*) FROM documentos"
            " WHERE fecha_emision IS NOT NULL GROUP BY 1 ORDER BY 1"
        ).fetchall()
        cargas = con.execute(
            "SELECT CAST(a.fecha_ingesta AS DATE), count(*), coalesce(sum(d.n), 0),"
            " coalesce(sum(v.n), 0), sum(a.errores)"
            " FROM archivos_ingeridos a"
            " LEFT JOIN (SELECT sha256, count(*) n FROM documentos GROUP BY 1) d USING (sha256)"
            " LEFT JOIN (SELECT sha256, count(*) n FROM advertencias"
            "   WHERE codigo = 'documento_ajeno' GROUP BY 1) v USING (sha256)"
            " GROUP BY 1 ORDER BY 1"
        ).fetchall()
    return {
        "cliente": cliente,
        "nombre": nombre,
        "registrado": _json(creado),
        "documentos": sum(n for _, n in por_tipo),
        "documentos_por_tipo": dict(por_tipo),
        "documentos_de_otra_persona": ajenos,
        "primera_emision": _json(primera),
        "ultima_emision": _json(ultima),
        "documentos_por_mes": dict(por_mes),
        "cargas": [
            {
                "dia": _json(d),
                "archivos": a,
                "documentos": int(n),
                "rechazados_de_otra_persona": int(v),
                "errores": int(e),
            }
            for d, a, n, v, e in cargas
        ],
    }


@herramienta("Buscar facturas", LECTURA)
def buscar_documentos(
    cliente: Cliente,
    emisor: Annotated[
        str | None, Field(description="Proveedor: NIT exacto o parte de su nombre.")
    ] = None,
    desde: Annotated[
        date | None, Field(description="Desde esta fecha de emisión, AAAA-MM-DD.")
    ] = None,
    hasta: Annotated[
        date | None, Field(description="Hasta esta fecha de emisión, AAAA-MM-DD.")
    ] = None,
    valor_min: Annotated[
        Decimal | None, Field(description="Total a pagar mínimo, en pesos, sin separadores.")
    ] = None,
    valor_max: Annotated[Decimal | None, Field(description="Total a pagar máximo.")] = None,
    tipo: Annotated[
        str | None,
        Field(
            description="01 factura, 02 exportación, 03 talonario (contingencia), 04 factura "
            "tipo 04, 05 documento soporte, 91 nota crédito, 92 nota débito, 95 nota de ajuste."
        ),
    ] = None,
    cufe: Annotated[str | None, Field(description="CUFE, CUDE o CUDS completo.")] = None,
    medio_pago: Annotated[
        str | None,
        Field(
            description="Código DIAN (tabla 13.3.4.2): 10 efectivo, 42 consignación, 47 "
            "transferencia, 48 tarjeta crédito, 49 tarjeta débito, ZZZ otro."
        ),
    ] = None,
) -> dict:
    """Busca facturas y notas que recibió el cliente, combinando filtros: proveedor, fechas,
    valor, tipo de documento, CUFE o medio de pago.

    Úsela cuando el usuario pida documentos puntuales, por ejemplo:
    - "Muéstrame las facturas de Claro de este año"
    - "¿Qué facturas de más de 5 millones llegaron en marzo?"
    - "Busca la factura con este CUFE" / "¿Cuáles pagué con tarjeta de crédito?"

    No la use para totales (use resumen_periodo, compras_por_proveedor o
    iva_compras_por_bimestre): aquí no se suma.
    Devuelve hasta 200 documentos y cuántos coinciden en total; si son más, pida acotar."""
    filtros = [
        (
            "(emisor_identificacion = $emisor OR emisor_nombre ILIKE '%' || $emisor || '%')",
            "emisor",
            emisor,
        ),
        ("fecha_emision >= $desde", "desde", desde),
        ("fecha_emision <= $hasta", "hasta", hasta),
        ("total_pagar >= $valor_min", "valor_min", valor_min),
        ("total_pagar <= $valor_max", "valor_max", valor_max),
        ("tipo = $tipo", "tipo", tipo),
        ("cufe = $cufe", "cufe", cufe),
        ("list_contains(medios_pago, $medio_pago)", "medio_pago", medio_pago),
    ]
    usados = [(condicion, nombre, v) for condicion, nombre, v in filtros if v is not None]
    sql = f"""
        SELECT fecha_emision, tipo, numero, cufe, emisor_identificacion, emisor_nombre, moneda,
               total_pagar, forma_pago, medios_pago, validado_dian,
               count(*) OVER () AS coincidencias
        FROM documentos
        WHERE adquirente_identificacion = (SELECT id FROM cliente)
          {"".join(f" AND {condicion}" for condicion, _, _ in usados)}
        ORDER BY fecha_emision, numero
        LIMIT {MAX_FILAS}
    """
    with abrir_cliente(cliente) as con:
        cursor = con.execute(sql, {nombre: v for _, nombre, v in usados})
        columnas = [c[0] for c in cursor.description]
        filas = cursor.fetchall()
    total = filas[0][-1] if filas else 0
    return {
        "aviso": AVISO,
        "coincidencias": total,
        "filas_devueltas": len(filas),
        "filas": [_fila(columnas[:-1], f[:-1]) for f in filas],
    }


@herramienta("Resumen de compras, IVA y retenciones", LECTURA)
def resumen_periodo(cliente: Cliente, desde: Desde, hasta: Hasta) -> dict:
    """Totales del periodo con los CUFE que los respaldan: compras (total y por tipo de
    documento), IVA (total y por tarifa) y retenciones por tipo. Las notas crédito y de ajuste
    restan.

    Úsela cuando el usuario pregunte cifras, por ejemplo:
    - "¿Cuánto IVA en compras hubo en el bimestre 1?"
    - "¿Qué retenciones traen las facturas del primer semestre?"
    - "¿Cuánto compró en 2025?"

    Es el IVA que figura en los documentos, no una determinación de IVA descontable. Las
    retenciones de facturas y documentos soporte son autorretenciones que declara el emisor
    (Anexo FE 1.9, FAT01): no diga que se las practicaron al cliente ni que el cliente las
    practicó. Cite las cifras tal cual vienen, sin sumarlas ni redondearlas."""
    _validar_rango(desde, hasta)
    with abrir_cliente(cliente) as con:
        columnas, filas = consultar(con, leer_sql("resumen_periodo.sql"), desde, hasta)
    return {
        "aviso": AVISO,
        "desde": desde.isoformat(),
        "hasta": hasta.isoformat(),
        "filas": [_fila(columnas, f) for f in filas],
    }


@herramienta("Facturas a crédito", LECTURA)
def facturas_credito(cliente: Cliente, desde: Desde, hasta: Hasta) -> dict:
    """Facturas recibidas con forma de pago a crédito en el periodo, con proveedor, valor y
    vencimiento.

    Úsela cuando el usuario pregunte, por ejemplo:
    - "¿Qué facturas a crédito llegaron en marzo?"
    - "¿Qué le debo a proveedores?" (solo lo que dicen las facturas, no si ya se pagó)

    Los eventos (acuse, aceptación, endoso) quedan "por verificar": este servidor no consulta
    a la DIAN."""
    return _informe(cliente, "facturas_credito", desde, hasta)


@herramienta("Facturas repetidas y anuladas", LECTURA)
def duplicados_y_anulaciones(cliente: Cliente, desde: Desde, hasta: Hasta) -> dict:
    """Facturas del mismo proveedor y número con distinto CUFE (posibles duplicados) y facturas
    anuladas total o parcialmente por notas crédito (tolerancia de 2 pesos). Si una nota cita
    varias facturas y no se sabe cuánto le toca a cada una, sale como anulada_sin_repartir: pídale
    al usuario que la revise.

    Úsela cuando el usuario pregunte, por ejemplo:
    - "¿Hay facturas repetidas?"
    - "¿Qué facturas me anularon con nota crédito?"
    - Antes de cerrar un periodo, para revisar que no se cuente dos veces una compra."""
    return _informe(cliente, "duplicados_y_anulaciones", desde, hasta)


@herramienta("Compras por proveedor", LECTURA)
def compras_por_proveedor(cliente: Cliente, desde: Desde, hasta: Hasta) -> dict:
    """Cuánto le compró el cliente a cada proveedor (NIT) en el periodo, ya sumado: documentos,
    subtotal y total, con las notas crédito y de ajuste restadas y las notas débito sumadas. El
    detalle trae cada documento con su CUFE.

    Úsela cuando el usuario pregunte, por ejemplo:
    - "¿Cuánto le compró a cada proveedor en el primer semestre?"
    - "¿Quiénes son sus principales proveedores este año?"
    - "¿Cuánto le facturó Claro en 2025?"

    Cite los totales del resumen tal cual: no sume filas del detalle."""
    return _informe(cliente, "compras_por_proveedor", desde, hasta)


@herramienta("IVA en compras por bimestre", LECTURA)
def iva_compras_por_bimestre(cliente: Cliente, desde: Desde, hasta: Hasta) -> dict:
    """IVA en compras por bimestre y tarifa, ya sumado y neto de notas crédito, con base y
    número de documentos. El detalle trae cada documento y tarifa con su CUFE.

    Úsela cuando el usuario pregunte por varios bimestres o por tarifa, por ejemplo:
    - "¿Cuánto IVA hubo en cada bimestre de 2025?"
    - "¿Cuánto IVA al 5 % y cuánto al 19 % en el bimestre 3?"

    Para el IVA total de un solo periodo basta resumen_periodo. Es el IVA que figura en los
    documentos, no una determinación de IVA descontable: eso lo decide el contador."""
    return _informe(cliente, "iva_compras_por_bimestre", desde, hasta)


@herramienta("Facturas sin validación DIAN", LECTURA)
def no_validadas(cliente: Cliente, desde: Desde, hasta: Hasta) -> dict:
    """Documentos que llegaron sin la respuesta de validación de la DIAN (sin_respuesta) o que
    la DIAN rechazó (rechazada), con el archivo de donde salieron para ubicarlos.

    Úsela cuando el usuario pregunte, por ejemplo:
    - "¿Hay facturas que la DIAN no haya validado?"
    - "¿Me llegó alguna factura rechazada?"
    - Antes de cerrar un periodo, para no contar documentos sin validar.

    Sin respuesta no significa inválida: puede que el emisor no la haya incluido en el ZIP."""
    return _informe(cliente, "no_validadas", desde, hasta)


@herramienta("Exportar informe a Excel", AGREGA)
def exportar_informe(
    cliente: Cliente,
    informe: Annotated[
        str,
        Field(
            description="compras_por_proveedor, iva_compras_por_bimestre, retenciones, "
            "duplicados_y_anulaciones, facturas_credito o no_validadas (sin validación DIAN)."
        ),
    ],
    desde: Desde,
    hasta: Hasta,
    ruta: Annotated[
        str,
        Field(
            description="Dónde guardarlo, como lo diga el usuario: una carpeta ('Escritorio', y "
            "el nombre se pone solo), 'Escritorio/retenciones' o solo un nombre de archivo (queda "
            "en la carpeta personal). Se agrega .xlsx si falta."
        ),
    ],
) -> dict:
    """Guarda un informe del periodo en un Excel nuevo, con una hoja de resumen y otra de
    detalle con los CUFE.

    Úsela cuando el usuario pida, por ejemplo:
    - "Exporta las retenciones del primer semestre a Excel"
    - "Pásame a un Excel las compras por proveedor de 2025, en el escritorio"

    Nunca sobrescribe: si el archivo ya existe, proponga otro nombre. Devuelve dónde quedó."""
    if not ruta.strip().strip("\"'"):
        raise ToolError(
            "falta dónde guardar el Excel: pregúntele al usuario (p. ej. el Escritorio)"
        )
    carpeta = next((c for c in _candidatas(ruta) if c.is_dir()), None)
    if carpeta:  # "guárdalo en el Escritorio": nombre automático dentro de esa carpeta
        ruta = str(carpeta / f"{informe}_{desde}_{hasta}.xlsx")
    elif not ruta.strip().lower().endswith(".xlsx"):
        ruta = ruta.strip() + ".xlsx"
    candidatas = _candidatas(ruta)
    destino = next((c for c in candidatas if c.parent.is_dir()), candidatas[0])
    if destino.exists():
        raise ToolError(f"{destino} ya existe; no se sobrescriben archivos")
    if not destino.parent.is_dir():
        raise ToolError(f"no existe la carpeta {destino.parent}")
    _validar_rango(desde, hasta)
    with abrir_cliente(cliente) as con:
        resultado = _ejecutar(con, informe, desde, hasta)
    exportar(resultado, desde, hasta, destino)
    return {"aviso": AVISO, "ruta": str(destino)}


@herramienta("Registrar cliente", AGREGA_REPETIBLE)
def crear_cliente(
    cliente: Cliente,
    nombre: Annotated[str, Field(description="Nombre o razón social del cliente.")],
) -> dict:
    """Registra un cliente nuevo en este equipo para poder cargar y consultar sus facturas.

    Úsela cuando el usuario diga, por ejemplo:
    - "Crea el cliente 900.000.009-9, Mi Cliente SAS"
    - "Sí, créalos" después de que ingerir_por_cliente informe compradores sin cliente: use el
      NIT y el nombre que esa herramienta devolvió.

    Si el cliente ya existe no cambia nada y devuelve su historial (`creado: false`). Si otro
    cliente tiene el mismo nombre con otro NIT, lo avisa: puede ser un NIT mal escrito y
    conviene confirmarlo con el usuario."""
    try:
        cliente = normalizar_id(cliente)
        existe = ruta_base(cliente).exists()
    except ErrorCliente as error:
        raise ToolError(str(error)) from error
    if existe:
        nota = "El cliente ya estaba registrado; no se cambió nada."
        return {"aviso": AVISO, "creado": False, "nota": nota, **_historial(cliente)}
    clave = _normalizar(nombre)  # vacía si el nombre es solo signos: no compara
    mismo_nombre = [c for c in _clientes() if clave and _normalizar(c.get("nombre", "")) == clave]
    try:
        ruta = crear_base(cliente, nombre)
    except ErrorCliente as error:
        raise ToolError(str(error)) from error
    r = {"aviso": AVISO, "creado": True, "cliente": cliente, "base": str(ruta)}
    notas = []
    if mismo_nombre:
        r["otros_con_el_mismo_nombre"] = mismo_nombre
        notas.append(
            "Ya había un cliente con ese nombre y otro NIT: confirme que el NIT es correcto."
        )
    nit_de_empresa = len(cliente) == 9 and cliente[0] in "89"  # 9 dígitos: ya viene sin DV
    if not nit_de_empresa and int(cliente[-1]) == digito_verificacion(cliente[:-1] or "0"):
        # p. ej. la cédula 1234567 con su DV 2 pegado se ve igual que la cédula 12345672
        notas.append(
            f"Si el último dígito ({cliente[-1]}) es el de verificación, la identificación "
            f"sería {cliente[:-1]} y las facturas no coincidirán con este cliente: confírmelo "
            "con el usuario."
        )
    if notas:
        r["nota"] = " ".join(notas)
    return r


@herramienta("Cargar facturas de un cliente", AGREGA_REPETIBLE)
def ingerir_facturas(
    cliente: Cliente,
    ruta: Annotated[
        str,
        Field(
            description="El ZIP, XML o carpeta, como lo nombre el usuario: 'facturas enero', "
            "'Descargas/facturas enero' o una ruta completa. Se busca en la carpeta personal, "
            "Descargas, Escritorio y Documentos."
        ),
    ],
) -> dict:
    """Carga en un cliente las facturas electrónicas de un ZIP o XML (como llegan por correo) o
    de una carpeta completa.

    Úsela cuando el usuario diga a qué cliente van, por ejemplo:
    - "Carga las facturas de la carpeta 'facturas enero' para Mi Cliente SAS"

    Si no dice de qué cliente son, o la carpeta trae facturas de varios clientes, use
    ingerir_por_cliente. Solo agrega: lo ya cargado se salta y nada se duplica. Devuelve
    cuántos archivos y documentos entraron y los errores de lectura."""
    origen = _origen(ruta)
    with _abrir_para_cargar(cliente) as con:
        r = ingerir(con, cliente, origen)
    notas = []
    if r.archivos_nuevos + r.archivos_repetidos == 0:
        notas.append(f"No encontré archivos ZIP ni XML en {origen}.")
    if r.ajenos:
        notas.append(
            f"{sum(r.ajenos.values())} documentos NO se cargaron porque no son de este cliente: "
            "no es ni el comprador ni el vendedor. Dígaselo al usuario; si son de otros clientes, "
            "se cargan con ingerir_por_cliente."
        )
    notas.append("El detalle de advertencias y errores está en la herramienta diagnostico.")
    return {"aviso": AVISO, **_resumen(r), "nota": " ".join(notas)}


@herramienta("Cargar facturas y repartir por cliente", AGREGA_REPETIBLE)
def ingerir_por_cliente(
    ruta: Annotated[
        str | None,
        Field(
            description="Carpeta, ZIP o XML como lo nombre el usuario. Omítala si no dice "
            "dónde están: se revisa la carpeta de Descargas."
        ),
    ] = None,
) -> dict:
    """Carga facturas de varios clientes a la vez: cada archivo va al cliente que aparece como
    comprador en la factura.

    Úsela cuando el usuario diga, por ejemplo:
    - "Carga mis facturas" / "Ya descargué las facturas, cárgalas" (sin ruta)
    - "Reparte por cliente las facturas de la carpeta 'correo noviembre'"

    Solo carga en clientes ya registrados. `clientes_no_creados` trae el NIT y el nombre de los
    compradores sin registrar: muéstreselos al usuario, pregunte si los crea (crear_cliente) y
    vuelva a llamar; lo ya cargado no se duplica. `sin_asignar` lista archivos que no son
    facturas legibles o traen varios compradores, con el motivo."""
    origenes = [_origen(ruta)] if ruta else _descargas()
    separacion = separar(*origenes)
    cargados, no_creados = [], []
    sin_asignar = [{"archivo": a, "motivo": m} for a, m in separacion.sin_asignar]
    for comprador, lecturas in sorted(separacion.por_comprador.items()):
        archivos = len({lec.sha256 for lec in lecturas})
        if comprador == CONSUMIDOR_FINAL:
            sin_asignar += [
                {
                    "archivo": a,
                    "motivo": "factura a consumidor final: no dice quién compró, así que no se "
                    "puede asignar a un cliente",
                }
                for a in sorted({lec.ruta for lec in lecturas})
            ]
            continue
        # La identificación del XML se compara exacta: "EXT-000123" no es el cliente 000123.
        if not re.fullmatch(r"[0-9]+", comprador):
            sin_asignar += [
                {"archivo": a, "motivo": f"comprador {comprador!r}: no es un NIT ni una cédula"}
                for a in sorted({lec.ruta for lec in lecturas})
            ]
            continue
        if not ruta_exacta(comprador).exists():
            nombre = separacion.nombres[comprador]
            falta = {"cliente": comprador, "nombre": nombre, "archivos": archivos}
            con_dv = comprador + str(digito_verificacion(comprador))
            if ruta_exacta(con_dv).exists():
                falta["nota"] = (
                    f"Parece que este comprador se registró como {con_dv}, con el dígito de "
                    "verificación pegado: confírmelo con el usuario antes de crear otro cliente."
                )
            no_creados.append(falta)
            continue
        with _abrir_para_cargar(comprador) as con:
            cargados.append(
                {"cliente": comprador, **_resumen(ingerir_lecturas(con, comprador, lecturas))}
            )
    r = {
        "aviso": AVISO,
        "cargados": cargados,
        "clientes_no_creados": no_creados,
        "sin_asignar": sin_asignar,
    }
    if not (cargados or no_creados or sin_asignar):
        r["nota"] = "No encontré archivos ZIP ni XML en " + ", ".join(map(str, origenes)) + "."
    return r


def _candidatas(ruta: str) -> list[Path]:
    """Dónde puede estar `ruta`. Una ruta relativa se busca en la carpeta personal y en
    Descargas, Escritorio y Documentos (en español o inglés, sin importar mayúsculas): un usuario
    no técnico dice "la carpeta facturas de Descargas", no una ruta completa."""
    p = Path(ruta.strip().strip("\"'")).expanduser()
    if p.is_absolute():
        return [p]
    casa = Path.home()
    candidatas = [casa / p]
    if p.parts and p.parts[0].lower() in CARPETAS:
        candidatas += [casa / c / Path(*p.parts[1:]) for c in CARPETAS[p.parts[0].lower()]]
    nombres = dict.fromkeys(c for pares in CARPETAS.values() for c in pares)
    return candidatas + [casa / c / p for c in nombres]


def _descargas() -> list[Path]:
    carpetas = [Path.home() / c for c in CARPETAS["descargas"] if (Path.home() / c).is_dir()]
    if not carpetas:
        raise ToolError("no encontré la carpeta de Descargas: pregúntele al usuario dónde están")
    return carpetas


def _sin_mayusculas(ruta: Path) -> Path | None:
    """`ruta` sin importar mayúsculas en ningún tramo ("facturas enero" = "Facturas Enero"),
    para sistemas de archivos que sí distinguen (Linux)."""
    actual = Path(ruta.anchor)
    for parte in ruta.parts[1:]:
        if (actual / parte).exists():
            actual = actual / parte
            continue
        try:
            actual = next(h for h in actual.iterdir() if h.name.lower() == parte.lower())
        except (StopIteration, OSError):
            return None
    return actual


def _origen(ruta: str) -> Path:
    if not ruta.strip().strip("\"'"):
        raise ToolError("falta la carpeta: pregúntele al usuario dónde guardó las facturas")
    candidatas = _candidatas(ruta)
    origen = next((c for c in candidatas if c.exists()), None) or next(
        filter(None, map(_sin_mayusculas, candidatas)), None
    )
    if origen is None:
        donde = candidatas[0] if len(candidatas) == 1 else Path.home()
        raise ToolError(
            f"no encontré {ruta!r} (busqué en {donde} y en sus carpetas Descargas, Escritorio y "
            "Documentos). Pregúntele al usuario en qué carpeta guardó los archivos."
        )
    casa = Path.home().resolve()
    if origen.is_dir() and (origen.resolve() == casa or origen.resolve() in casa.parents):
        raise ToolError(
            f"{origen} es la carpeta personal completa: revisarla toda cargaría cualquier ZIP del "
            "equipo. Pregúntele al usuario en qué carpeta están las facturas (p. ej. Descargas)."
        )
    if origen.is_file() and origen.suffix.lower() == ".pdf":
        raise ToolError(
            f"{origen.name} es el PDF de la factura, que es solo su representación gráfica. Lo "
            "que se carga es el ZIP que llegó en el correo junto al PDF, o el XML que trae dentro."
        )
    if origen.is_file() and origen.suffix.lower() not in EXTENSIONES:
        raise ToolError(f"{origen.name} no es un ZIP ni un XML de factura electrónica")
    return origen


def _abrir_para_cargar(cliente: str):
    try:
        return abrir(cliente)
    except ErrorCliente as error:
        raise ToolError(str(error)) from error
    except duckdb.IOException as error:
        raise ToolError(f"la base de {cliente} está abierta en otro programa: {error}") from error


def _resumen(r) -> dict:
    return {
        "archivos_nuevos": r.archivos_nuevos,
        "archivos_ya_cargados": r.archivos_repetidos,
        "documentos_guardados": r.documentos,
        "cufes_ya_existentes": r.cufes_repetidos,
        "advertencias": r.advertencias,
        "errores_de_lectura": r.errores,
        "no_guardados": [{"archivo": a, "error": e} for a, e in r.fallidos],
        "rechazados_de_otra_persona": r.ajenos,
    }


@herramienta("Diagnóstico para soporte", LECTURA)
def diagnostico() -> dict:
    """Estado de la instalación para reportar un problema: versión, carpeta de datos, plugins
    y, por cliente, documentos, archivos cargados, última carga y advertencias de lectura (las
    últimas 20). No incluye montos ni contenido de las facturas, así que se puede compartir.

    Úsela cuando el usuario diga, por ejemplo:
    - "Algo no funciona" / "No me cargó una factura" / "Una cifra no me cuadra"
    - "Dame el diagnóstico de Auditor DIAN"

    Explique en palabras sencillas lo que encuentre y, si hay que reportarlo, entréguele el
    resultado completo para que lo copie."""
    from auditor_dian import plugins

    clientes = []
    for carpeta in sorted((inicio() / "clientes").glob("*")):
        try:
            with abrir(carpeta.name, solo_lectura=True) as con:
                documentos, archivos, ultima = con.execute(
                    "SELECT (SELECT count(*) FROM documentos), count(*), max(fecha_ingesta)"
                    " FROM archivos_ingeridos"
                ).fetchone()
                ajenos = con.execute(AJENOS_SQL).fetchone()[0]
                codigos = con.execute(
                    "SELECT codigo, count(*) FROM advertencias GROUP BY 1 ORDER BY 2 DESC, 1"
                ).fetchall()
                recientes = con.execute(
                    "SELECT a.ruta, v.miembro, v.codigo, v.detalle FROM advertencias v"
                    " JOIN archivos_ingeridos a USING (sha256)"
                    " ORDER BY a.fecha_ingesta DESC, a.ruta, v.miembro LIMIT 20"
                ).fetchall()
        except (ErrorCliente, duckdb.Error) as error:
            clientes.append({"id": carpeta.name, "error": str(error)})
            continue
        clientes.append(
            {
                "id": carpeta.name,
                "documentos": documentos,
                "archivos_cargados": archivos,
                "documentos_de_otra_persona": ajenos,
                "ultima_carga": _json(ultima),
                "advertencias_por_codigo": dict(codigos),
                "advertencias_recientes": [
                    {"archivo": Path(r).name, "miembro": m, "codigo": c, "detalle": d}
                    for r, m, c, d in recientes
                ],
            }
        )
    return {
        "aviso": AVISO,
        "version": version("auditor-dian-core"),
        "carpeta_de_datos": str(inicio()),
        "plugins": plugins.cargar(),
        "clientes": clientes,
    }


def _informe(cliente: str, nombre: str, desde: date, hasta: date) -> dict:
    _validar_rango(desde, hasta)
    with abrir_cliente(cliente) as con:
        r = _ejecutar(con, nombre, desde, hasta)
    return {
        "aviso": AVISO,
        "nota": r.nota,
        "resumen": [_fila(r.columnas_resumen, f) for f in r.filas_resumen],
        "detalle": [_fila(r.columnas, f) for f in r.filas],
    }


def abrir_cliente(cliente: str):
    try:
        return abrir(cliente, solo_lectura=True)
    except ErrorCliente as error:
        raise ToolError(str(error)) from error


def _ejecutar(con, nombre: str, desde: date, hasta: date):
    try:
        return ejecutar(con, nombre, desde, hasta)
    except InformeDesconocido as error:
        raise ToolError(str(error)) from error


def _validar_rango(desde: date, hasta: date) -> None:
    if desde > hasta:
        raise ToolError("`desde` es posterior a `hasta`")


def _fila(columnas: list[str], fila: tuple) -> dict:
    return {c: _json(v) for c, v in zip(columnas, fila, strict=True)}


def _json(valor: Any) -> Any:
    if isinstance(valor, Decimal):
        return f"{valor.normalize():f}"  # exacto y sin ceros sobrantes: "150500", "0.5"
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, list):
        return [_json(v) for v in valor]
    return valor
