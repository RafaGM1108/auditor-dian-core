import duckdb
import pytest

from auditor_dian.base import (
    VERSION_ESQUEMA,
    ErrorCliente,
    abrir,
    crear_cliente,
    digito_verificacion,
    normalizar_id,
)


def test_crear_cliente_en_auditor_dian_home(inicio_temporal):
    ruta = crear_cliente("900000009", "Cliente de prueba SAS")

    assert ruta == inicio_temporal / "clientes" / "900000009" / "auditor.duckdb"
    with abrir("900000009") as con:
        assert con.execute("SELECT id, nombre FROM cliente").fetchall() == [
            ("900000009", "Cliente de prueba SAS")
        ]
        assert con.execute("SELECT version FROM schema_version").fetchone() == (VERSION_ESQUEMA,)


@pytest.mark.parametrize(
    "escrito",
    ["900000009", "900000009-0", "NIT 900.000.009-0", " 900 000 009 ", "9000000090", "900,000,009"],
)
def test_id_cliente_se_escribe_como_sea(escrito):
    crear_cliente(escrito, "X")
    with abrir("900000009") as con:
        assert con.execute("SELECT id FROM cliente").fetchone() == ("900000009",)


def test_digito_de_verificacion_de_la_dian():
    assert digito_verificacion("800197268") == 4  # NIT de la DIAN
    assert digito_verificacion("890903938") == 8  # Bancolombia
    assert digito_verificacion("900000009") == 0


@pytest.mark.parametrize(
    ("escrito", "interpretado"),
    [
        ("1032456789", "1032456789"),  # cédula de 10 dígitos: no se toca
        ("1032456789" + str(digito_verificacion("1032456789")), "1032456789"),  # 11 con DV
        ("9000000091", "9000000091"),  # 10 dígitos pero DV incorrecto: no se adivina
        ("C.C. 79.123.456", "79123456"),
    ],
)
def test_la_cantidad_de_digitos_dice_si_trae_dv(escrito, interpretado):
    assert normalizar_id(escrito) == interpretado


def test_con_duda_se_usa_el_cliente_registrado():
    cedula = "79123456"
    crear_cliente(cedula, "Persona")
    con_dv = cedula + str(digito_verificacion(cedula))
    assert normalizar_id(con_dv) == cedula  # 9 dígitos: podría ser otra cédula, pero existe esta


@pytest.mark.parametrize("id_cliente", ["", "abc", "９０", "NIT"])
def test_id_cliente_sin_digitos_se_rechaza(id_cliente):
    with pytest.raises(ErrorCliente, match="identificación inválida"):
        crear_cliente(id_cliente, "X")


def test_cliente_repetido_o_sin_nombre_se_rechaza():
    crear_cliente("900000009", "Cliente")

    with pytest.raises(ErrorCliente, match="ya existe"):
        crear_cliente("900000009", "Otro")
    with pytest.raises(ErrorCliente, match="vacío"):
        crear_cliente("900000010", "  ")


def test_abrir_cliente_inexistente():
    with pytest.raises(ErrorCliente, match="no existe"):
        abrir("900000009")


def test_abrir_base_de_otra_version():
    ruta = crear_cliente("900000009", "Cliente")
    with duckdb.connect(str(ruta)) as con:
        con.execute("UPDATE schema_version SET version = 99")

    with pytest.raises(ErrorCliente, match="versión 99"):
        abrir("900000009")


def test_creacion_fallida_no_deja_base_a_medio_crear(tmp_path, monkeypatch):
    malo = tmp_path / "malo.sql"
    malo.write_text("CREATE TABLE schema_version (;")
    monkeypatch.setattr("auditor_dian.base.ESQUEMA", malo)

    with pytest.raises(duckdb.Error):
        crear_cliente("900000009", "Cliente")

    with pytest.raises(ErrorCliente, match="no existe"):
        abrir("900000009")


def test_base_copiada_en_la_carpeta_de_otro_cliente_se_rechaza():
    import shutil

    from auditor_dian.base import ruta_base

    crear_cliente("900000009", "Cliente A")
    destino = ruta_base("800000008")
    destino.parent.mkdir(parents=True)
    shutil.copy(ruta_base("900000009"), destino)  # alguien copió la base de A en la carpeta de B
    with pytest.raises(ErrorCliente, match="pertenece al cliente 900000009"):
        abrir("800000008")
    with pytest.raises(ErrorCliente, match="pertenece al cliente 900000009"):
        abrir("800000008", solo_lectura=True)


def test_cualquier_nit_o_cedula_en_cualquier_formato():
    """La regla no depende de valores puntuales: miles de identificaciones al azar, escritas de
    todas las formas que usa un contador, se interpretan igual."""
    import random

    azar = random.Random(2026)

    def puntos(n: str) -> str:
        return f"{int(n):,}".replace(",", ".")

    formas = [
        lambda n, dv: n,
        lambda n, dv: puntos(n),
        lambda n, dv: f"{n}-{dv}",
        lambda n, dv: f"NIT {puntos(n)}-{dv}",
        lambda n, dv: f"  {n} - {dv} ",
        lambda n, dv: f"C.C. {' '.join([n[:3], n[3:6], n[6:]])}",
        lambda n, dv: f"{puntos(n)}, DV {dv}".replace(", DV ", "-"),
    ]
    for _ in range(1000):
        empresa = azar.choice("89") + "".join(azar.choices("0123456789", k=8))
        cedula = "1" + "".join(azar.choices("0123456789", k=9))  # cédulas de 10 dígitos
        for numero in (empresa, cedula):
            dv = digito_verificacion(numero)
            for forma in formas:
                assert normalizar_id(forma(numero, dv)) == numero, forma(numero, dv)
            assert normalizar_id(numero + str(dv)) == numero  # DV pegado sin guion
    for basura in ("", "abc", "N.I.T.", "--", "９００"):
        with pytest.raises(ErrorCliente):
            normalizar_id(basura)
