from fabrica import fixture
from typer.testing import CliRunner

from auditor_dian.cli import app

runner = CliRunner()


def auditor(*args: str):
    return runner.invoke(app, list(args))


def test_ayuda_responde():
    resultado = auditor("--help")

    assert resultado.exit_code == 0
    assert "solo lectura" in resultado.stdout


def test_crear_cliente(inicio_temporal):
    resultado = auditor("clientes", "crear", "900000009", "--nombre", "Cliente de prueba SAS")

    assert resultado.exit_code == 0
    assert (inicio_temporal / "clientes" / "900000009" / "auditor.duckdb").exists()


def test_crear_cliente_invalido_explica_el_formato():
    resultado = auditor("clientes", "crear", "NIT", "--nombre", "X")

    assert resultado.exit_code == 1
    assert "identificación inválida" in resultado.stderr


def test_ingerir_y_reingerir(tmp_path):
    auditor("clientes", "crear", "900000009", "--nombre", "Cliente")
    (tmp_path / "f.xml").write_text(fixture("factura_01.xml"), encoding="utf-8")
    (tmp_path / "roto.xml").write_bytes(b"<Invoice>")

    primera = auditor("ingerir", "900000009", str(tmp_path))
    segunda = auditor("ingerir", "900000009", str(tmp_path))

    assert primera.exit_code == 0
    assert "Archivos: 2 nuevos, 0 ya ingeridos" in primera.stdout
    assert "Documentos guardados: 1 (0 CUFE ya existentes)" in primera.stdout
    assert "Errores de lectura: 1" in primera.stdout
    assert segunda.exit_code == 0
    assert "Archivos: 0 nuevos, 2 ya ingeridos" in segunda.stdout


def test_ingerir_cliente_inexistente(tmp_path):
    resultado = auditor("ingerir", "900000009", str(tmp_path))

    assert resultado.exit_code == 1
    assert "clientes crear" in resultado.stderr


def test_ingerir_ruta_inexistente(tmp_path):
    auditor("clientes", "crear", "900000009", "--nombre", "Cliente")

    resultado = auditor("ingerir", "900000009", str(tmp_path / "no-existe"))

    assert resultado.exit_code == 2


def test_archivo_que_no_se_pudo_guardar_termina_con_error(tmp_path):
    auditor("clientes", "crear", "900000009", "--nombre", "Cliente")
    xml = fixture("nota_debito_92.xml").replace(
        ">4500.00</cbc:PayableAmount>", ">1E+16</cbc:PayableAmount>"
    )
    (tmp_path / "nd.xml").write_text(xml, encoding="utf-8")

    resultado = auditor("ingerir", "900000009", str(tmp_path))

    assert resultado.exit_code == 1
    assert "No se pudo guardar" in resultado.stderr
    assert "se reintentan" in resultado.stderr
