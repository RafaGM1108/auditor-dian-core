from importlib.metadata import EntryPoint

import anyio
import duckdb
import pytest
from fabrica import CLIENTE, crear_base_comun
from mcp.client import Client
from typer.testing import CliRunner

import auditor_dian.plugins as plugins
from auditor_dian import informes, ubl
from auditor_dian.base import abrir
from auditor_dian.cli import app
from auditor_dian.servidor import servidor

TIQUETE_XML = """<Tiquete xmlns="urn:ejemplo:tiquete">
  <ID>T1</ID><UUID>tiquete-1</UUID><Fecha>2026-01-10</Fecha>
  <Emisor>900000001</Emisor><Adquirente>900000009</Adquirente><Total>{total}</Total>
</Tiquete>"""


def instalar(monkeypatch, *valores: str) -> None:
    """Simula plugins instalados y deja limpios los registros al terminar la prueba."""
    entradas = [EntryPoint(name=v.split(":")[1], value=v, group=plugins.GRUPO) for v in valores]
    monkeypatch.setattr(plugins, "entry_points", lambda group: entradas)
    monkeypatch.setattr(plugins, "_cargados", None)
    monkeypatch.setattr(informes, "EXTRA", {})
    monkeypatch.setattr(ubl, "LECTORES", {})


@pytest.fixture
def con_plugin(monkeypatch):
    instalar(monkeypatch, "plugin_ejemplo:register")
    yield
    if "contar_documentos" in {h.name for h in anyio.run(servidor.list_tools)}:
        servidor.remove_tool("contar_documentos")


def auditor(*argumentos: str):
    return CliRunner().invoke(app, list(argumentos))


def test_core_funciona_sin_plugins(monkeypatch, tmp_path):
    instalar(monkeypatch)
    crear_base_comun(tmp_path)

    assert plugins.cargar() == []
    resultado = auditor(
        "informe",
        CLIENTE,
        "compras_por_proveedor",
        "--desde",
        "2026-01-01",
        "--hasta",
        "2026-01-31",
    )
    assert resultado.exit_code == 0


def test_el_plugin_agrega_informe_y_lector(con_plugin, tmp_path):
    crear_base_comun(tmp_path)
    (tmp_path / "tiquete.xml").write_text(TIQUETE_XML.format(total="1000.00"), encoding="utf-8")

    ingesta = auditor("ingerir", CLIENTE, str(tmp_path))
    informe = auditor(
        "informe", CLIENTE, "compras_por_tipo", "--desde", "2026-01-01", "--hasta", "2026-01-31"
    )

    assert plugins.cargar() == ["register"]
    assert "1 nuevos" in ingesta.stdout  # solo el tiquete; lo demás ya estaba
    assert informe.exit_code == 0, informe.output
    assert "ejemplo  COP     1           1.000,00" in informe.stdout


@pytest.fixture
def plugin_cargado(con_plugin, tmp_path):
    # Fuera del bucle asíncrono, como en `auditor mcp`: los plugins cargan antes del servidor.
    crear_base_comun(tmp_path)
    plugins.cargar()


@pytest.mark.anyio
async def test_el_plugin_agrega_una_herramienta_mcp(plugin_cargado):

    async with Client(servidor) as cliente:
        herramienta = next(
            h for h in (await cliente.list_tools()).tools if h.name == "contar_documentos"
        )
        r = await cliente.call_tool("contar_documentos", {"cliente": CLIENTE})
        sin_cliente = await cliente.call_tool("contar_documentos", {"cliente": "123"})

    assert herramienta.annotations.read_only_hint
    assert "no existe el cliente 123" in sin_cliente.content[0].text
    assert (
        '"documentos": 7' in r.content[0].text
    )  # fixtures comunes + FV1003, sin la exportación ajena


def test_un_plugin_roto_se_reporta_y_core_sigue(monkeypatch, capsys):
    instalar(monkeypatch, "plugin_ejemplo:roto")

    assert plugins.cargar() == []
    assert "no se cargó el plugin 'roto': falta configuración" in capsys.readouterr().err
    assert plugins.cargar() == []  # se intenta una sola vez


def test_el_fallo_de_un_lector_queda_como_error_de_lectura(con_plugin, tmp_path):
    crear_base_comun(tmp_path)
    plugins.cargar()
    (tmp_path / "malo.xml").write_text(TIQUETE_XML.format(total="mil"), encoding="utf-8")

    resultado = auditor("ingerir", CLIENTE, str(tmp_path))

    assert resultado.exit_code == 0
    assert "Errores de lectura: 1" in resultado.stdout
    with abrir(CLIENTE, solo_lectura=True) as con:
        (detalle,) = con.execute(
            "SELECT detalle FROM advertencias WHERE codigo = 'error_lectura'"
        ).fetchone()
    assert "falló el lector del plugin" in detalle


def test_un_plugin_no_puede_reemplazar_lo_de_core(con_plugin):
    app_plugin = plugins.App()

    with pytest.raises(ValueError, match="ya existe el informe"):
        app_plugin.informe("compras_por_proveedor", "", "SELECT 1", "SELECT 1")
    with pytest.raises(ValueError, match="ya tiene lector"):
        app_plugin.lector(next(iter(ubl.RAICES)), lambda raiz: None)

    def resumen_periodo() -> dict:
        return {}

    with pytest.raises(ValueError, match="ya existe la herramienta"):
        app_plugin.herramienta(resumen_periodo)


def test_abrir_para_escribir_solo_si_se_pide(tmp_path):
    crear_base_comun(tmp_path)
    app_plugin = plugins.App()

    with app_plugin.abrir(CLIENTE, escritura=True) as con:
        con.execute("CREATE TABLE pro_prueba (x INTEGER)")
    with app_plugin.abrir(CLIENTE) as con, pytest.raises(duckdb.InvalidInputException):
        con.execute("INSERT INTO pro_prueba VALUES (1)")


def test_rechaza_herramientas_con_nombres_que_la_api_no_acepta(monkeypatch):
    instalar(monkeypatch)

    def consultar_por_año(cliente: str, año: int) -> dict:
        """Prueba."""
        return {}

    with pytest.raises(ValueError, match=r"\['consultar_por_año', 'año'\].*'anio', no 'año'"):
        plugins.App().herramienta(consultar_por_año)
    assert "consultar_por_año" not in {h.name for h in anyio.run(servidor.list_tools)}
