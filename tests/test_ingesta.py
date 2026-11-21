import zipfile
from datetime import time, timedelta, timezone
from decimal import Decimal

import pytest
from fabrica import CUFE_FV1001, contenedor, fixture, respuesta_dian

from auditor_dian.base import abrir, crear_cliente
from auditor_dian.ingesta import ingerir

CLIENTE = "900000009"  # adquirente de los fixtures
TABLAS = (
    "archivos_ingeridos",
    "documentos",
    "referencias",
    "impuestos",
    "retenciones",
    "lineas",
    "impuestos_linea",
    "advertencias",
)


@pytest.fixture
def con():
    crear_cliente(CLIENTE, "Cliente de prueba SAS")
    with abrir(CLIENTE) as con:
        yield con


@pytest.fixture
def carpeta(tmp_path):
    d = tmp_path / "correo"
    (d / "enero").mkdir(parents=True)
    with zipfile.ZipFile(d / "enero" / "FV1001.zip", "w") as zf:
        zf.writestr("FV1001.xml", contenedor(fixture("factura_01.xml"), respuesta_dian()))
        zf.writestr("FV1001.pdf", b"%PDF")
    (d / "enero" / "NC55.xml").write_text(fixture("nota_credito_91.xml"), encoding="utf-8")
    (d / "ND7.xml").write_text(fixture("nota_debito_92.xml"), encoding="utf-8")
    (d / "DS20.xml").write_text(fixture("documento_soporte_05.xml"), encoding="utf-8")
    (d / "roto.xml").write_bytes(b"<Invoice>")
    return d


def _conteos(con) -> dict:
    return {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in TABLAS}


def test_ingerir_carpeta(con, carpeta):
    r = ingerir(con, CLIENTE, carpeta)

    assert (r.archivos_nuevos, r.documentos, r.errores, r.fallidos) == (5, 4, 1, [])
    assert con.execute("SELECT tipo, numero FROM documentos ORDER BY numero").fetchall() == [
        ("05", "DS20"),
        ("01", "FV1001"),
        ("91", "NC55"),
        ("92", "ND7"),
    ]
    assert con.execute(
        "SELECT validado_dian, miembro FROM documentos WHERE cufe = ?", [CUFE_FV1001]
    ).fetchone() == (True, "FV1001.xml")
    assert con.execute(
        "SELECT codigo, detalle LIKE 'XML mal formado%' FROM advertencias WHERE cufe IS NULL"
    ).fetchall() == [("error_lectura", True)]


def test_reingerir_no_duplica_nada(con, carpeta):
    ingerir(con, CLIENTE, carpeta)
    antes = _conteos(con)

    r = ingerir(con, CLIENTE, carpeta)

    assert (r.archivos_nuevos, r.archivos_repetidos, r.documentos) == (0, 5, 0)
    assert _conteos(con) == antes


def test_valores_vuelven_exactos_de_la_base(con, carpeta):
    ingerir(con, CLIENTE, carpeta)

    assert con.execute(
        "SELECT total_pagar, hora_emision FROM documentos WHERE cufe = ?", [CUFE_FV1001]
    ).fetchone() == (Decimal("150500.00"), time(10, 30, tzinfo=timezone(timedelta(hours=-5))))
    assert con.execute(
        "SELECT codigo, tarifa, valor FROM retenciones r JOIN documentos d USING (cufe)"
        " WHERE d.numero = 'DS20' ORDER BY orden"
    ).fetchall() == [
        ("06", Decimal("3.50"), Decimal("17500.00")),
        ("07", Decimal("0.966"), Decimal("4830.00")),
    ]
    assert con.execute(
        "SELECT l.cantidad, r.cufe_referenciado FROM lineas l JOIN referencias r USING (cufe)"
        " JOIN documentos d USING (cufe) WHERE d.numero = 'NC55'"
    ).fetchone() == (Decimal("0.5"), CUFE_FV1001)
    assert con.execute(
        "SELECT count(*) FROM impuestos_linea i JOIN documentos d USING (cufe)"
        " WHERE d.numero = 'FV1001'"
    ).fetchone() == (2,)


def test_mismo_cufe_en_otro_archivo_no_se_duplica(con, tmp_path):
    (tmp_path / "a.xml").write_text(fixture("factura_01.xml"), encoding="utf-8")
    (tmp_path / "b.xml").write_bytes(contenedor(fixture("factura_01.xml"), respuesta_dian()))

    r = ingerir(con, CLIENTE, tmp_path)

    assert (r.archivos_nuevos, r.documentos, r.cufes_repetidos) == (2, 1, 1)
    assert con.execute(
        "SELECT a.codigo, a.cufe FROM advertencias a JOIN archivos_ingeridos f USING (sha256)"
        " WHERE f.ruta LIKE '%b.xml'"
    ).fetchall() == [("cufe_repetido", CUFE_FV1001)]


def test_venta_del_cliente_se_guarda_con_advertencia(tmp_path):
    # factura_01 la emite 900000001 a 900000009: para el cliente 900000001 es una venta suya.
    crear_cliente("900000001", "Otro cliente")
    (tmp_path / "f.xml").write_text(fixture("factura_01.xml"), encoding="utf-8")

    with abrir("900000001") as con:
        r = ingerir(con, "900000001", tmp_path)
        assert r.documentos == 1
        assert con.execute("SELECT codigo, detalle FROM advertencias").fetchall() == [
            ("adquirente_distinto", "adquirente '900000009', cliente '900000001'")
        ]


def test_decimales_de_mas_se_redondean_con_advertencia(con, tmp_path):
    xml = fixture("documento_soporte_05.xml").replace(
        "<cbc:Percent>0.966</cbc:Percent>", "<cbc:Percent>0.9665</cbc:Percent>"
    )
    (tmp_path / "ds.xml").write_text(xml, encoding="utf-8")

    ingerir(con, CLIENTE, tmp_path)

    assert con.execute("SELECT tarifa FROM retenciones WHERE codigo = '07'").fetchone() == (
        Decimal("0.966"),
    )
    assert con.execute("SELECT codigo, detalle FROM advertencias").fetchall() == [
        ("valor_redondeado", "retenciones.tarifa: 0.9665 → 0.966")
    ]


def test_documento_sin_cufe_no_se_guarda(con, tmp_path):
    xml = fixture("nota_debito_92.xml")
    inicio, fin = xml.index("<cbc:UUID"), xml.index("</cbc:UUID>") + len("</cbc:UUID>")
    (tmp_path / "nd.xml").write_text(xml[:inicio] + xml[fin:], encoding="utf-8")

    r = ingerir(con, CLIENTE, tmp_path)

    assert (r.documentos, r.errores) == (0, 1)
    assert con.execute("SELECT count(*) FROM documentos").fetchone() == (0,)
    assert con.execute("SELECT codigo FROM advertencias ORDER BY codigo").fetchall() == [
        ("campo_faltante",),
        ("documento_sin_cufe",),
    ]


def test_archivo_que_no_cabe_en_la_base_no_queda_marcado_y_se_reintenta(con, tmp_path):
    xml = fixture("nota_debito_92.xml").replace(
        ">4500.00</cbc:PayableAmount>", ">1E+16</cbc:PayableAmount>"
    )
    (tmp_path / "nd.xml").write_text(xml, encoding="utf-8")

    r = ingerir(con, CLIENTE, tmp_path)

    assert r.archivos_nuevos == 0
    assert [ruta.endswith("nd.xml") for ruta, _ in r.fallidos] == [True]
    assert _conteos(con) == dict.fromkeys(TABLAS, 0)
    assert len(ingerir(con, CLIENTE, tmp_path).fallidos) == 1  # se reintenta, no se salta


def test_totales_con_cargo_y_redondeo_negativo_vuelven_exactos(con, tmp_path):
    xml = fixture("factura_cargo_01.xml").replace(
        ">0.00</cbc:PayableRoundingAmount>", ">-0.40</cbc:PayableRoundingAmount>"
    )
    (tmp_path / "f.xml").write_text(xml, encoding="utf-8")

    ingerir(con, CLIENTE, tmp_path)

    assert con.execute(
        "SELECT total_impuestos_incluidos, descuentos, cargos, anticipos, redondeo, total_pagar"
        " FROM documentos"
    ).fetchone() == (
        Decimal("150500.00"),
        Decimal("0.00"),
        Decimal("5000.00"),
        Decimal("0.00"),
        Decimal("-0.40"),
        Decimal("155500.00"),
    )


def test_separar_no_parte_un_zip_con_varios_compradores_ni_adivina_sin_identificacion(tmp_path):
    from auditor_dian.ingesta import separar

    otro = fixture("factura_01.xml").replace(">900000009<", ">800000008<")
    with zipfile.ZipFile(tmp_path / "mezclado.zip", "w") as z:
        z.writestr("a.xml", fixture("factura_01.xml"))
        z.writestr("b.xml", otro.replace(CUFE_FV1001, CUFE_FV1001[:-1] + "9"))
    etiqueta = '<cbc:CompanyID schemeAgencyID="195" schemeID="9" schemeName="31">'
    sin_id = fixture("factura_01.xml").replace(f"{etiqueta}900000009</cbc:CompanyID>", "")
    (tmp_path / "sin_id.xml").write_text(sin_id, encoding="utf-8")
    (tmp_path / "bien.xml").write_text(fixture("factura_01.xml"), encoding="utf-8")

    s = separar(tmp_path)

    assert list(s.por_comprador) == [CLIENTE] and s.nombres[CLIENTE] == "CLIENTE DE PRUEBA SAS"
    assert sorted((a.rsplit("/", 1)[-1], m.split(":")[0]) for a, m in s.sin_asignar) == [
        ("mezclado.zip", "trae documentos de varios compradores (800000008, 900000009)"),
        ("sin_id.xml", "el comprador no tiene identificación"),
    ]
    # El motivo le dice al agente cómo cargarlo sin pedirle al usuario que separe a mano.
    assert "ingerir_facturas" in dict(s.sin_asignar)[str(tmp_path / "mezclado.zip")]


def test_cliente_escrito_con_puntos_y_dv_no_marca_adquirente_distinto(con, carpeta):
    ingerir(con, "900.000.009-9", carpeta)
    distintos = "SELECT count(*) FROM advertencias WHERE codigo = 'adquirente_distinto'"
    de_otro = "SELECT count(*) FROM documentos WHERE adquirente_identificacion <> '900000009'"
    assert con.execute(distintos).fetchone() == con.execute(de_otro).fetchone()


def test_documento_ajeno_no_se_guarda(tmp_path):
    crear_cliente("800000008", "Cliente que no es parte")
    (tmp_path / "f.xml").write_text(fixture("factura_01.xml"), encoding="utf-8")

    with abrir("800000008") as con:
        r = ingerir(con, "800.000.008", tmp_path)
        assert (r.documentos, r.ajenos) == (0, {"900000009": 1})
        assert con.execute("SELECT count(*) FROM documentos").fetchone() == (0,)
        (codigo,) = con.execute("SELECT codigo FROM advertencias").fetchone()
        assert codigo == "documento_ajeno"


def test_documentos_ajenos_de_versiones_anteriores_se_cuentan(con, carpeta):
    from auditor_dian.servidor import AJENOS_SQL

    ingerir(con, CLIENTE, carpeta)
    assert con.execute(AJENOS_SQL).fetchone() == (0,)
    con.execute("UPDATE documentos SET adquirente_identificacion = '1' WHERE numero = 'FV1001'")
    assert con.execute(AJENOS_SQL).fetchone() == (1,)  # como quedaba antes de la decisión 0011
