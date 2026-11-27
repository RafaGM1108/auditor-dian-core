import base64
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

import anyio
import duckdb
import pytest
from fabrica import CLIENTE, CUFE_FV1001, crear_base_comun
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

from auditor_dian import servidor as modulo
from auditor_dian.servidor import AVISO, servidor

CUFE_FV1002 = CUFE_FV1001[:-2] + "12"
CUDE_NC55 = "cude" + "0" * 88 + "091"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def base(tmp_path):
    crear_base_comun(tmp_path)


@pytest.mark.anyio
async def llamar(herramienta: str, **argumentos) -> dict:
    async with Client(servidor) as cliente:
        r = await cliente.call_tool(herramienta, argumentos)
    assert not r.is_error, r.content[0].text
    respuesta = json.loads(r.content[0].text)
    assert respuesta["aviso"] == AVISO  # SPEC §10: en cada respuesta
    return respuesta


@pytest.mark.anyio
async def error(herramienta: str, **argumentos) -> str:
    async with Client(servidor) as cliente:
        r = await cliente.call_tool(herramienta, argumentos)
    assert r.is_error
    return r.content[0].text


@pytest.mark.anyio
async def test_herramientas_y_cuales_escriben():
    async with Client(servidor) as cliente:
        herramientas = {h.name: h for h in (await cliente.list_tools()).tools}

    assert set(herramientas) == {
        "listar_clientes",
        "historial_cliente",
        "buscar_documentos",
        "resumen_periodo",
        "facturas_credito",
        "duplicados_y_anulaciones",
        "compras_por_proveedor",
        "iva_compras_por_bimestre",
        "no_validadas",
        "exportar_informe",
        "crear_cliente",
        "ingerir_facturas",
        "ingerir_por_cliente",
        "diagnostico",
    }
    assert all(h.description for h in herramientas.values())
    escriben = {n for n, h in herramientas.items() if not h.annotations.read_only_hint}
    assert escriben == {
        "exportar_informe",
        "crear_cliente",
        "ingerir_facturas",
        "ingerir_por_cliente",
    }
    assert not any(herramientas[n].annotations.destructive_hint for n in escriben)


@pytest.mark.anyio
async def test_se_presenta_con_nombre_resumen_y_logo():
    async with Client(servidor) as cliente:
        info = cliente.server_info

    assert (info.name, info.title) == ("auditor-dian", "Auditor DIAN")
    assert "No es un producto oficial de la DIAN" in info.description
    assert info.version == version("auditor-dian-core")
    assert [i.mime_type for i in info.icons] == ["image/png", "image/svg+xml"]
    png = base64.b64decode(info.icons[0].src.removeprefix("data:image/png;base64,"))
    assert png.startswith(b"\x89PNG")


@pytest.mark.anyio
async def test_listar_clientes(base):
    r = await llamar("listar_clientes")

    assert r["clientes"] == [{"id": CLIENTE, "nombre": "Cliente de prueba SAS"}]


@pytest.mark.anyio
async def test_iva_del_bimestre_1_con_sus_cufes(base):
    # La pregunta del criterio de aceptación: "¿cuánto IVA facturado en compras hubo en el
    # bimestre 1?". A mano: FV1001 y FV1002 (19.000 + 1.500 cada una) menos NC55 (500).
    r = await llamar("resumen_periodo", cliente=CLIENTE, desde="2026-01-01", hasta="2026-02-28")

    filas = {(f["concepto"], f["clave"]): f for f in r["filas"]}
    assert filas[("iva_total", "")] == {
        "concepto": "iva_total",
        "clave": "",
        "moneda": "COP",
        "documentos": 3,
        "valor": "40500",
        "cufes": [CUDE_NC55, CUFE_FV1001, CUFE_FV1002],
    }
    assert filas[("iva_por_tarifa", "19.000")]["valor"] == "38000"
    assert filas[("iva_por_tarifa", "5.000")]["valor"] == "2500"
    # 150.500 + 155.500 - 10.500 + 4.500 + 500.000 - 100.000
    assert (filas[("compras_total", "")]["documentos"], filas[("compras_total", "")]["valor"]) == (
        6,
        "700000",
    )
    assert filas[("compras_por_tipo", "91")]["valor"] == "-10500"
    assert filas[("retenciones_por_codigo", "06")]["valor"] == "24000"
    assert filas[("retenciones_por_codigo", "07")]["valor"] == "4830"


@pytest.mark.anyio
async def test_buscar_documentos_por_emisor_tipo_y_valor(base):
    r = await llamar("buscar_documentos", cliente=CLIENTE, emisor="proveedor uno", tipo="01")
    assert [f["numero"] for f in r["filas"]] == ["FV1001", "FV1002", "FV1003"]
    assert r["coincidencias"] == 3
    assert r["filas"][0]["total_pagar"] == "150500"

    r = await llamar("buscar_documentos", cliente=CLIENTE, valor_min=150000, valor_max="152000")
    assert [f["numero"] for f in r["filas"]] == ["FV1001", "FV1003"]

    r = await llamar("buscar_documentos", cliente=CLIENTE, emisor="1000000001", desde="2026-02-01")
    assert [f["numero"] for f in r["filas"]] == ["NA3"]

    r = await llamar("buscar_documentos", cliente=CLIENTE, cufe=CUFE_FV1002)
    assert [f["numero"] for f in r["filas"]] == ["FV1002"]

    r = await llamar("buscar_documentos", cliente=CLIENTE, medio_pago="48")
    assert [(f["numero"], f["forma_pago"], f["medios_pago"]) for f in r["filas"]] == [
        ("FV1003", "2", ["48"])
    ]
    r = await llamar("buscar_documentos", cliente=CLIENTE, medio_pago="42")
    assert [f["numero"] for f in r["filas"]] == ["FV1001", "FV1002"]


@pytest.mark.anyio
async def test_buscar_documentos_limita_las_filas_y_cuenta_todas(base, monkeypatch):
    monkeypatch.setattr(modulo, "MAX_FILAS", 2)

    r = await llamar("buscar_documentos", cliente=CLIENTE)

    assert (r["coincidencias"], r["filas_devueltas"]) == (7, 2)  # la exportación no es suya


@pytest.mark.anyio
async def test_buscar_sin_coincidencias(base):
    r = await llamar("buscar_documentos", cliente=CLIENTE, tipo="02")

    assert (r["coincidencias"], r["filas"]) == (0, [])


@pytest.mark.anyio
async def test_facturas_credito_y_duplicados(base):
    r = await llamar("facturas_credito", cliente=CLIENTE, desde="2026-01-01", hasta="2026-03-31")
    assert [(f["documentos"], f["total"]) for f in r["resumen"]] == [(4, "461000")]
    assert {f["eventos"] for f in r["detalle"]} == {"por verificar"}

    r = await llamar(
        "duplicados_y_anulaciones", cliente=CLIENTE, desde="2026-01-01", hasta="2026-01-31"
    )
    assert [(f["hallazgo"], f["numero"], f["valor_notas"]) for f in r["detalle"]] == [
        ("anulada_parcial", "FV1001", "10500")
    ]
    assert "±2,00" in r["nota"]


@pytest.mark.anyio
async def test_compras_por_proveedor_ya_sumadas(base):
    # Las cifras llegan sumadas para que el agente no tenga que sumar filas de buscar_documentos.
    r = await llamar(
        "compras_por_proveedor", cliente=CLIENTE, desde="2026-01-01", hasta="2026-03-31"
    )

    # A mano: 150.500 + 155.500 - 10.500 (NC55) + 4.500 (ND7) + 150.500 (FV1003)
    # y 500.000 (DS20) - 100.000 (NA3).
    assert [(f["emisor_identificacion"], f["documentos"], f["total"]) for f in r["resumen"]] == [
        ("900000001", 5, "450500"),
        ("1000000001", 2, "400000"),
    ]
    assert {f["cufe"] for f in r["detalle"]} >= {CUFE_FV1001, CUFE_FV1002, CUDE_NC55}
    assert "notas débito suman" in r["nota"]


@pytest.mark.anyio
async def test_iva_compras_por_bimestre_y_tarifa(base):
    r = await llamar(
        "iva_compras_por_bimestre", cliente=CLIENTE, desde="2026-01-01", hasta="2026-04-30"
    )

    # Bimestre 1 igual que resumen_periodo (38.000 + 2.500); bimestre 2 es FV1003 de marzo.
    assert [(f["bimestre"], f["tarifa"], f["iva"]) for f in r["resumen"]] == [
        ("2026-01/02", "5", "2500"),
        ("2026-01/02", "19", "38000"),
        ("2026-03/04", "5", "1500"),
        ("2026-03/04", "19", "19000"),
    ]
    assert "No es una determinación de IVA descontable" in r["nota"]


@pytest.mark.anyio
async def test_no_validadas_con_su_archivo(base):
    r = await llamar("no_validadas", cliente=CLIENTE, desde="2026-01-01", hasta="2026-01-31")

    # Los fixtures son XML sueltos, sin la respuesta de la DIAN que trae el AttachedDocument.
    # En enero: FV1001, FV1002, NC55 y DS20.
    assert [(f["estado"], f["documentos"]) for f in r["resumen"]] == [("sin_respuesta", 4)]
    assert all(f["archivo"] for f in r["detalle"])


@pytest.mark.anyio
async def test_exportar_informe_no_sobrescribe(base, tmp_path):
    ruta = tmp_path / "compras.xlsx"
    argumentos = dict(cliente=CLIENTE, desde="2026-01-01", hasta="2026-02-28", ruta=str(ruta))

    r = await llamar("exportar_informe", informe="compras_por_proveedor", **argumentos)
    assert r["ruta"] == str(ruta) and ruta.exists()

    assert "ya existe" in await error("exportar_informe", informe="retenciones", **argumentos)
    argumentos["ruta"] = str(tmp_path / "no" / "hay.xlsx")
    assert "no existe la carpeta" in await error(
        "exportar_informe", informe="retenciones", **argumentos
    )
    argumentos["ruta"] = str(tmp_path / "otro.xlsx")
    assert "desconocido" in await error("exportar_informe", informe="no_existe", **argumentos)


@pytest.mark.anyio
async def test_errores_se_explican_al_agente(base):
    rango = dict(desde="2026-01-01", hasta="2026-01-31")
    assert "no existe el cliente" in await error("resumen_periodo", cliente="123", **rango)
    assert "posterior" in await error(
        "facturas_credito", cliente=CLIENTE, desde="2026-02-01", hasta="2026-01-01"
    )


@pytest.mark.anyio
async def test_listar_clientes_reporta_una_base_ilegible(base, inicio_temporal):
    (inicio_temporal / "clientes" / "123").mkdir()  # carpeta sin base

    r = await llamar("listar_clientes")

    assert r["clientes"][0]["id"] == "123" and "no existe" in r["clientes"][0]["error"]


@pytest.mark.anyio
async def test_auditor_mcp_responde_por_stdio(base, inicio_temporal):
    # De punta a punta, como lo lanza Claude: el comando `auditor mcp` como subproceso.
    parametros = StdioServerParameters(
        command=str(Path(sys.executable).with_name("auditor")),
        args=["mcp"],
        env={**os.environ, "AUDITOR_DIAN_HOME": str(inicio_temporal)},
    )
    async with Client(parametros) as cliente:
        r = await cliente.call_tool(
            "resumen_periodo", {"cliente": CLIENTE, "desde": "2026-01-01", "hasta": "2026-02-28"}
        )

    filas = json.loads(r.content[0].text)["filas"]
    assert next(f["valor"] for f in filas if f["concepto"] == "iva_total") == "40500"


def test_comando_mcp_inicia_el_servidor(monkeypatch):
    from typer.testing import CliRunner

    from auditor_dian.cli import app

    llamadas = []
    monkeypatch.setattr(servidor, "run", lambda: llamadas.append("stdio"))

    assert CliRunner().invoke(app, ["mcp"]).exit_code == 0
    assert llamadas == ["stdio"]


def test_nombres_de_herramientas_y_parametros_validos_para_la_api_de_claude():
    from auditor_dian.servidor import nombres_invalidos

    for h in anyio.run(servidor.list_tools):
        assert nombres_invalidos(h.name, h.input_schema) == [], h.name


@pytest.mark.parametrize(
    "nombre, esquema, malos",
    [
        ("ok", {"properties": {"anio": {}, "a.b-c_1": {}}}, []),
        ("ok", {"properties": {"año": {}}}, ["año"]),
        ("ok", {"$defs": {"X": {"properties": {"tamaño": {}}}}}, ["tamaño"]),
        ("ok", {"properties": {"x": {"items": [{"properties": {"ñ": {}}}]}}}, ["ñ"]),
        ("consultar_año", {}, ["consultar_año"]),
        ("con espacio", {}, ["con espacio"]),
        ("x" * 65, {"properties": {"y" * 65: {}}}, ["x" * 65, "y" * 65]),
    ],
)
def test_detecta_nombres_que_la_api_rechaza(nombre, esquema, malos):
    from auditor_dian.servidor import nombres_invalidos

    assert nombres_invalidos(nombre, esquema) == malos


@pytest.mark.anyio
async def test_crear_cliente_e_ingerir_desde_el_agente(inicio_temporal, tmp_path):
    from fabrica import fixture

    carpeta = tmp_path / "correo"
    carpeta.mkdir()
    (carpeta / "factura_01.xml").write_text(fixture("factura_01.xml"), encoding="utf-8")
    (carpeta / "nota_credito_91.xml").write_text(fixture("nota_credito_91.xml"), encoding="utf-8")

    creado = await llamar("crear_cliente", cliente=CLIENTE, nombre="Cliente de prueba SAS")
    assert Path(creado["base"]).exists()
    r = await llamar("ingerir_facturas", cliente=CLIENTE, ruta=str(carpeta))
    assert (r["archivos_nuevos"], r["documentos_guardados"], r["no_guardados"]) == (2, 2, [])
    otra = await llamar("ingerir_facturas", cliente=CLIENTE, ruta=str(carpeta / "factura_01.xml"))
    assert (otra["archivos_nuevos"], otra["archivos_ya_cargados"]) == (0, 1)  # no duplica
    assert (await llamar("listar_clientes"))["clientes"][0]["id"] == CLIENTE


@pytest.mark.anyio
async def test_errores_de_carga_se_explican(base, tmp_path, monkeypatch):
    texto = tmp_path / "notas.txt"
    texto.write_text("x")
    assert "identificación inválida" in await error("crear_cliente", cliente="NIT", nombre="Otro")
    assert "no encontré 'facturas'" in await error(
        "ingerir_facturas", cliente=CLIENTE, ruta="facturas"
    )
    assert "no encontré" in await error("ingerir_facturas", cliente=CLIENTE, ruta="/no/existe")
    assert "ni un XML" in await error("ingerir_facturas", cliente=CLIENTE, ruta=str(texto))
    assert "no existe el cliente" in await error("ingerir_facturas", cliente="1", ruta="/tmp")

    def ocupada(*_, **__):
        raise duckdb.IOException("Could not set lock on file")

    monkeypatch.setattr(modulo, "abrir", ocupada)
    assert "abierta en otro programa" in await error(
        "ingerir_facturas", cliente=CLIENTE, ruta=str(tmp_path)
    )


@pytest.mark.anyio
async def test_diagnostico(base, inicio_temporal):
    (inicio_temporal / "clientes" / "123").mkdir()  # carpeta sin base

    r = await llamar("diagnostico")

    assert r["version"] == version("auditor-dian-core")
    assert r["carpeta_de_datos"] == str(inicio_temporal) and isinstance(r["plugins"], list)
    ilegible, cliente = r["clientes"]
    assert "no existe" in ilegible["error"]
    assert (cliente["id"], cliente["documentos"], cliente["archivos_cargados"]) == (
        CLIENTE,
        7,
        8,
    )  # la exportación ajena se lee pero no se guarda
    assert cliente["ultima_carga"] and cliente["advertencias_por_codigo"]
    assert len(cliente["advertencias_recientes"]) == min(
        20, sum(cliente["advertencias_por_codigo"].values())
    )
    assert {"archivo", "miembro", "codigo", "detalle"} == set(cliente["advertencias_recientes"][0])


@pytest.mark.anyio
async def test_ingerir_por_cliente_reparte_por_comprador(inicio_temporal, tmp_path):
    from fabrica import fixture

    otro = "800000008"
    correo = tmp_path / "correo"
    (correo / "sub").mkdir(parents=True)
    (correo / "fv1001.xml").write_text(fixture("factura_01.xml"), encoding="utf-8")
    (correo / "sub" / "nc55.xml").write_text(fixture("nota_credito_91.xml"), encoding="utf-8")
    de_otro = (
        fixture("factura_01.xml")
        .replace(">900000009</cbc:CompanyID>", f">{otro}</cbc:CompanyID>")
        .replace(CUFE_FV1001, CUFE_FV1001[:-1] + "9")
    )
    (correo / "de_otro.xml").write_text(de_otro, encoding="utf-8")
    (correo / "nuevo.xml").write_text(
        de_otro.replace(f">{otro}<", ">700000007<").replace(CUFE_FV1001[:-1] + "9", "c" * 96),
        encoding="utf-8",
    )
    (correo / "exportacion.xml").write_text(fixture("factura_exportacion_02.xml"), "utf-8")
    (correo / "roto.xml").write_text("<no-cierra>", encoding="utf-8")
    await llamar("crear_cliente", cliente=CLIENTE, nombre="Cliente de prueba SAS")
    await llamar("crear_cliente", cliente=otro, nombre="Otro cliente SAS")

    r = await llamar("ingerir_por_cliente", ruta=str(correo))

    cargados = {c["cliente"]: c for c in r["cargados"]}
    assert (cargados[CLIENTE]["archivos_nuevos"], cargados[CLIENTE]["documentos_guardados"]) == (
        2,
        2,
    )
    assert cargados[otro]["documentos_guardados"] == 1
    assert [(c["cliente"], c["archivos"]) for c in r["clientes_no_creados"]] == [("700000007", 1)]
    motivos = {Path(s["archivo"]).name: s["motivo"] for s in r["sin_asignar"]}
    assert "XML mal formado" in motivos["roto.xml"]
    assert "no es un NIT ni una cédula" in motivos["exportacion.xml"]
    otra_vez = await llamar("ingerir_por_cliente", ruta=str(correo))
    assert all(c["archivos_nuevos"] == 0 for c in otra_vez["cargados"])  # no duplica
    assert "no encontré" in await error("ingerir_por_cliente", ruta="correo")


@pytest.mark.anyio
async def test_buscar_cliente_e_historial(base):
    assert [
        c["id"]
        for c in (await llamar("listar_clientes", buscar="CLIENTE de prueba s.a.s"))["clientes"]
    ] == [CLIENTE]
    assert (await llamar("listar_clientes", buscar=CLIENTE[:4]))["clientes"][0]["id"] == CLIENTE
    assert (await llamar("listar_clientes", buscar="panadería"))["clientes"] == []

    h = await llamar("historial_cliente", cliente="900.000.009-9")

    assert (h["cliente"], h["nombre"], h["documentos"]) == (CLIENTE, "Cliente de prueba SAS", 7)
    assert sum(h["documentos_por_tipo"].values()) == sum(h["documentos_por_mes"].values()) == 7
    assert h["primera_emision"] <= h["ultima_emision"]
    (carga,) = h["cargas"]
    resumen = (carga["archivos"], carga["documentos"], carga["rechazados_de_otra_persona"])
    assert resumen == (8, 7, 1) and carga["errores"] == 0
    assert "no existe el cliente" in await error("historial_cliente", cliente="1")


@pytest.mark.anyio
async def test_crear_cliente_que_ya_existe_devuelve_su_historial(base):
    r = await llamar("crear_cliente", cliente=CLIENTE, nombre="Otro nombre")
    assert (r["creado"], r["nombre"], r["documentos"]) == (False, "Cliente de prueba SAS", 7)

    nuevo = await llamar("crear_cliente", cliente="900000008", nombre="CLIENTE DE PRUEBA S.A.S.")
    assert nuevo["creado"] and nuevo["otros_con_el_mismo_nombre"][0]["id"] == CLIENTE
    assert "confirme que el NIT" in nuevo["nota"]
    otro = await llamar("crear_cliente", cliente="900.000.007-1", nombre="Panadería Nueva")
    assert "nota" not in otro and otro["cliente"] == "900000007"
    assert "no puede estar vacío" in await error("crear_cliente", cliente="900000006", nombre=" ")


@pytest.fixture
def casa(tmp_path, monkeypatch):
    """Carpeta personal de un usuario con el sistema en inglés: Downloads y Desktop."""
    casa = tmp_path / "casa"
    (casa / "Downloads" / "facturas enero").mkdir(parents=True)
    (casa / "Desktop").mkdir()
    monkeypatch.setenv("HOME", str(casa))
    monkeypatch.setenv("USERPROFILE", str(casa))
    return casa


@pytest.mark.anyio
async def test_rutas_como_las_dice_un_usuario(base, casa):
    from fabrica import fixture

    carpeta = casa / "Downloads" / "facturas enero"
    (carpeta / "fv.xml").write_text(fixture("factura_01.xml"), encoding="utf-8")
    for dicha in ("descargas/facturas enero", "facturas enero", " 'Downloads/facturas enero' "):
        r = await llamar("ingerir_facturas", cliente=CLIENTE, ruta=dicha)
        assert r["archivos_nuevos"] + r["archivos_ya_cargados"] == 1, dicha
    assert "Descargas, Escritorio" in await error("ingerir_facturas", cliente=CLIENTE, ruta="otra")

    argumentos = dict(cliente=CLIENTE, desde="2026-01-01", hasta="2026-02-28")
    r = await llamar("exportar_informe", informe="retenciones", ruta="Escritorio/ret", **argumentos)
    assert r["ruta"] == str(casa / "Desktop" / "ret.xlsx")
    r = await llamar("exportar_informe", informe="retenciones", ruta="ret.xlsx", **argumentos)
    assert r["ruta"] == str(casa / "ret.xlsx")


@pytest.mark.anyio
async def test_sin_ruta_reparte_lo_que_hay_en_descargas(base, casa):
    from fabrica import fixture

    (casa / "Downloads" / "fv.xml").write_text(fixture("factura_01.xml"), encoding="utf-8")
    r = await llamar("ingerir_por_cliente")
    assert [c["cliente"] for c in r["cargados"]] == [CLIENTE]
    for c in ("Downloads", "Desktop"):
        (casa / c).rename(casa / f"{c}-no")
    assert "Descargas" in await error("ingerir_por_cliente")


@pytest.mark.anyio
async def test_cada_herramienta_se_explica_sola():
    """Como en los conectores bien hechos: título legible, cuándo usarla con frases del usuario y
    cada parámetro descrito. Claude Desktop muestra el título; el agente lee el resto."""
    for h in await servidor.list_tools():
        assert h.title and h.title[0].isupper(), h.name
        assert "Úsela cuando el usuario" in h.description, h.name
        assert "\n " not in h.description, h.name  # sin la sangría ni los cortes del código
        sin_describir = [
            p for p, e in h.input_schema["properties"].items() if not e.get("description")
        ]
        assert not sin_describir, (h.name, sin_describir)


@pytest.mark.anyio
async def test_el_manifiesto_de_la_extension_lista_las_mismas_herramientas():
    import json

    manifiesto = json.loads((Path(__file__).parents[1] / "mcpb" / "manifest.json").read_text())
    esperadas = [(h.name, h.description.split("\n\n")[0]) for h in await servidor.list_tools()]
    assert [(t["name"], t["description"]) for t in manifiesto["tools"]] == esperadas


@pytest.mark.anyio
async def test_casos_limite_de_rutas(base, casa):
    from fabrica import fixture

    carpeta = casa / "Downloads" / "facturas enero"
    (carpeta / "fv.xml").write_text(fixture("factura_01.xml"), encoding="utf-8")
    (carpeta / "fv.pdf").write_bytes(b"%PDF-1.4")
    (casa / "Downloads" / "vacia").mkdir()

    for dicha in (
        "DESCARGAS/FACTURAS ENERO",  # mayúsculas distintas a las del disco
        "~/Downloads/facturas enero/",  # con ~ y barra final
        "«facturas enero»".strip("«»"),
        str(carpeta / "fv.xml"),  # un XML suelto
    ):
        r = await llamar("ingerir_facturas", cliente=CLIENTE, ruta=dicha)
        assert r["archivos_nuevos"] + r["archivos_ya_cargados"] == 1, dicha

    for vacia in ("", "   ", "''"):
        assert "falta la carpeta" in await error("ingerir_facturas", cliente=CLIENTE, ruta=vacia)
    for toda in ("~", str(casa), "/"):
        assert "carpeta personal completa" in await error(
            "ingerir_facturas", cliente=CLIENTE, ruta=toda
        ), toda
    assert "representación gráfica" in await error(
        "ingerir_facturas", cliente=CLIENTE, ruta="descargas/facturas enero/fv.pdf"
    )
    r = await llamar("ingerir_facturas", cliente=CLIENTE, ruta="vacia")
    assert r["archivos_nuevos"] == 0 and "No encontré archivos ZIP ni XML" in r["nota"]
    r = await llamar("ingerir_por_cliente", ruta="vacia")
    assert "No encontré archivos ZIP ni XML" in r["nota"]


@pytest.mark.anyio
async def test_facturas_de_otra_persona_no_entran_al_cliente(base, tmp_path):
    """Si el contador carga en un cliente facturas que no son suyas, no se guardan: así no
    pueden terminar en sus cifras ni en su declaración."""
    from fabrica import fixture

    antes = (await llamar("historial_cliente", cliente=CLIENTE))["documentos"]
    de_otro = (
        fixture("factura_01.xml")
        .replace(">900000009</cbc:CompanyID>", ">800000008</cbc:CompanyID>")
        .replace(CUFE_FV1001, "d" * 96)
    )
    (tmp_path / "otro.xml").write_text(de_otro, encoding="utf-8")
    (tmp_path / "cf.xml").write_text(
        de_otro.replace(">800000008<", ">222222222222<").replace("d" * 96, "e" * 96), "utf-8"
    )

    r = await llamar("ingerir_facturas", cliente=CLIENTE, ruta=str(tmp_path))

    assert r["documentos_guardados"] == 0
    assert r["rechazados_de_otra_persona"] == {"800000008": 1, "222222222222": 1}
    assert "NO se cargaron" in r["nota"]
    assert (await llamar("historial_cliente", cliente=CLIENTE))["documentos"] == antes
    assert (await llamar("buscar_documentos", cliente=CLIENTE, cufe="d" * 96))["coincidencias"] == 0

    reparto = await llamar("ingerir_por_cliente", ruta=str(tmp_path / "cf.xml"))
    assert "consumidor final" in reparto["sin_asignar"][0]["motivo"]
    assert reparto["clientes_no_creados"] == []


@pytest.mark.anyio
async def test_exportar_a_una_carpeta_sin_nombre_de_archivo(base, casa):
    argumentos = dict(cliente=CLIENTE, desde="2026-01-01", hasta="2026-02-28")
    r = await llamar("exportar_informe", informe="retenciones", ruta="escritorio", **argumentos)
    assert r["ruta"] == str(casa / "Desktop" / "retenciones_2026-01-01_2026-02-28.xlsx")
    assert "ya existe" in await error(
        "exportar_informe", informe="retenciones", ruta="Escritorio", **argumentos
    )
    assert "falta dónde" in await error(
        "exportar_informe", informe="retenciones", ruta=" ", **argumentos
    )
    assert "no existe la carpeta" in await error(
        "exportar_informe", informe="retenciones", ruta="Escritorio/no hay/x", **argumentos
    )


@pytest.mark.anyio
async def test_casos_limite_de_clientes(inicio_temporal):
    vacio = await llamar("crear_cliente", cliente="NIT 900.000.009-0", nombre="Recién Creado SAS")
    assert (vacio["creado"], vacio["cliente"]) == (True, "900000009")
    h = await llamar("historial_cliente", cliente="9000000090")  # sin guion, con DV
    assert (h["documentos"], h["primera_emision"], h["documentos_por_mes"], h["cargas"]) == (
        0,
        None,
        {},
        [],
    )
    otra_vez = await llamar("crear_cliente", cliente="900000009-0", nombre="Otro Nombre")
    assert (otra_vez["creado"], otra_vez["nombre"]) == (False, "Recién Creado SAS")
    assert len((await llamar("listar_clientes", buscar="..."))["clientes"]) == 1  # sin texto útil
    assert (await llamar("listar_clientes", buscar="RECIEN creado"))["clientes"]
    assert "identificación inválida" in await error("historial_cliente", cliente="Recién")


@pytest.mark.anyio
async def test_cedula_corta_con_dv_pegado_se_advierte(inicio_temporal, tmp_path):
    """1234567 con su DV 2 pegado (12345672) se ve igual que una cédula de 8 dígitos: no se
    puede adivinar, así que se advierte al crear y al repartir."""
    from fabrica import fixture

    from auditor_dian.base import digito_verificacion

    cedula = "1234567"
    pegado = cedula + str(digito_verificacion(cedula))
    r = await llamar("crear_cliente", cliente=pegado, nombre="Persona")
    assert r["cliente"] == pegado and f"sería {cedula}" in r["nota"]
    assert "nota" not in await llamar("crear_cliente", cliente="900000009", nombre="Empresa")

    xml = fixture("factura_01.xml").replace(
        ">900000009</cbc:CompanyID>", f">{cedula}</cbc:CompanyID>"
    )
    (tmp_path / "f.xml").write_text(xml, encoding="utf-8")
    (falta,) = (await llamar("ingerir_por_cliente", ruta=str(tmp_path)))["clientes_no_creados"]
    assert falta["cliente"] == cedula and pegado in falta["nota"]
