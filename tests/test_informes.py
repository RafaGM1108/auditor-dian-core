import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest
from fabrica import CLIENTE, CUFE_FV1001, contenedor, crear_base_comun, fixture, respuesta_dian
from openpyxl import load_workbook
from typer.testing import CliRunner

from auditor_dian.base import abrir, crear_cliente
from auditor_dian.cli import app
from auditor_dian.excel import exportar
from auditor_dian.informes import InformeDesconocido, ejecutar
from auditor_dian.ingesta import ingerir


@pytest.fixture
def con(tmp_path):
    crear_base_comun(tmp_path)
    with abrir(CLIENTE, solo_lectura=True) as lectura:
        yield lectura


def test_compras_por_proveedor_resta_notas_credito_y_de_ajuste(con):
    r = ejecutar(con, "compras_por_proveedor", date(2026, 1, 1), date(2026, 2, 28))

    assert r.columnas_resumen == [
        "emisor_identificacion",
        "emisor_nombre",
        "moneda",
        "documentos",
        "subtotal",
        "total",
    ]
    # Valores escritos a mano: 500.000 - 100.000 y 130.000 + 130.000 - 10.000 + 4.500.
    assert r.filas_resumen == [
        ("1000000001", "VENDEDOR PERSONA NATURAL", "COP", 2, Decimal("400000"), Decimal("400000")),
        ("900000001", "PROVEEDOR UNO SAS", "COP", 4, Decimal("254500"), Decimal("300000")),
    ]
    assert len(r.filas) == 6  # la exportación a otro adquirente no aparece
    nc = next(f for f in r.filas if f[2] == "NC55")
    assert nc[-1] == Decimal("-10500")
    assert all(f[3] for f in r.filas)


def test_el_rango_es_por_fecha_de_emision_e_inclusive(con):
    r = ejecutar(con, "compras_por_proveedor", date(2026, 1, 15), date(2026, 1, 20))

    assert [(f[0], f[3], f[5]) for f in r.filas_resumen] == [
        ("900000001", 3, Decimal("295500"))  # FV1001 + FV1002 - NC55
    ]


def test_rango_sin_documentos_da_resumen_vacio(con):
    r = ejecutar(con, "compras_por_proveedor", date(2025, 1, 1), date(2025, 12, 31))

    assert r.filas == [] and r.filas_resumen == []


def test_informe_desconocido(con):
    with pytest.raises(InformeDesconocido, match="compras_por_proveedor"):
        ejecutar(con, "no_existe", date(2026, 1, 1), date(2026, 1, 31))


def test_la_base_de_los_informes_es_de_solo_lectura(con):
    with pytest.raises(duckdb.Error):
        con.execute("DELETE FROM documentos")


def test_cli_informe_presenta_a_dos_decimales(con):
    con.close()  # la CLI abre su propia conexión
    resultado = CliRunner().invoke(
        app,
        [
            "informe",
            CLIENTE,
            "compras_por_proveedor",
            "--desde",
            "2026-01-01",
            "--hasta",
            "2026-02-28",
        ],
    )

    assert resultado.exit_code == 0, resultado.output
    fila = "VENDEDOR PERSONA NATURAL  COP     2           400.000,00  400.000,00"
    assert fila in resultado.stdout
    assert "restan" in resultado.stdout
    assert "Detalle: 6 filas." in resultado.stdout


@pytest.mark.parametrize(
    ("argumentos", "mensaje"),
    [
        ([CLIENTE, "no_existe", "--desde", "2026-01-01", "--hasta", "2026-01-31"], "desconocido"),
        (
            [CLIENTE, "compras_por_proveedor", "--desde", "2026-02-01", "--hasta", "2026-01-01"],
            "posterior",
        ),
        (
            ["123", "compras_por_proveedor", "--desde", "2026-01-01", "--hasta", "2026-01-31"],
            "no existe el cliente",
        ),
    ],
)
def test_cli_informe_errores(con, argumentos, mensaje):
    con.close()
    resultado = CliRunner().invoke(app, ["informe", *argumentos])

    assert resultado.exit_code == 1
    assert mensaje in resultado.stderr


def test_iva_por_bimestre_y_tarifa_neto_de_notas(con):
    r = ejecutar(con, "iva_compras_por_bimestre", date(2026, 1, 1), date(2026, 3, 31))

    # A mano: al 5 %, FV1001 + FV1002 - NC55 (30.000 + 30.000 - 10.000; 1.500 + 1.500 - 500).
    assert r.filas_resumen == [
        ("2026-01/02", "COP", Decimal("5"), 3, Decimal("50000"), Decimal("2500")),
        ("2026-01/02", "COP", Decimal("19"), 2, Decimal("200000"), Decimal("38000")),
        ("2026-03/04", "COP", Decimal("5"), 1, Decimal("30000"), Decimal("1500")),
        ("2026-03/04", "COP", Decimal("19"), 1, Decimal("100000"), Decimal("19000")),
    ]
    assert "no es una determinación" in r.nota.lower()


def base_aparte(tmp_path, archivos: dict[str, str | bytes]):
    """Base con solo estos archivos, para casos que no caben en los fixtures comunes."""
    for nombre, contenido in archivos.items():
        if isinstance(contenido, str):
            contenido = contenido.encode("utf-8")
        (tmp_path / nombre).write_bytes(contenido)
    crear_cliente(CLIENTE, "Cliente")
    with abrir(CLIENTE) as c:
        ingerir(c, CLIENTE, tmp_path)
    return abrir(CLIENTE, solo_lectura=True)


def copia(nombre: str, **cambios: str) -> str:
    xml = fixture(nombre)
    for viejo, nuevo in cambios.items():
        assert viejo in xml, viejo
        xml = xml.replace(viejo, nuevo)
    return xml


def cufe(final: str) -> str:
    return CUFE_FV1001[: -len(final)] + final


def test_iva_suma_por_tarifa_los_subtotales_repetidos(tmp_path):
    # Un emisor real repite IVA 19 % en varios TaxSubtotal: debe quedar una fila por tarifa.
    xml = fixture("factura_01.xml").replace(
        "<cbc:Percent>5.00</cbc:Percent>", "<cbc:Percent>19.00</cbc:Percent>"
    )
    with base_aparte(tmp_path, {"f.xml": xml}) as c:
        r = ejecutar(c, "iva_compras_por_bimestre", date(2026, 1, 1), date(2026, 1, 31))

    assert [(f[8], f[9], f[10]) for f in r.filas] == [
        (Decimal("19"), Decimal("130000"), Decimal("20500"))
    ]


def test_retenciones_por_mes_y_codigo(con):
    r = ejecutar(con, "retenciones", date(2026, 1, 1), date(2026, 3, 31))

    # A mano: código 06 en enero = 3.250 + 3.250 (FV1001, FV1002) + 17.500 (DS20).
    assert r.filas_resumen == [
        ("2026-01", "COP", "06", "ReteRenta", 3, Decimal("760000"), Decimal("24000")),
        ("2026-01", "COP", "07", "ReteICA", 1, Decimal("500000"), Decimal("4830")),
        ("2026-03", "COP", "06", "ReteRenta", 1, Decimal("130000"), Decimal("3250")),
    ]
    assert "autorretenciones" in r.nota


def test_duplicados_y_anulaciones(tmp_path):
    nc55 = "cude" + "0" * 88 + "091"
    sin_cufe = re.sub(
        r"(<cac:BillingReference>.*?)<cbc:UUID[^>]*>[^<]*</cbc:UUID>",
        r"\1",
        copia("nota_credito_91.xml", NC55="NC57", FV1001="FV2000", **{nc55: nc55[:-3] + "097"}),
        flags=re.S,
    )
    archivos = {
        "FV1001.xml": fixture("factura_01.xml"),
        # Mismo emisor y número, otro CUFE.
        "FV1001-bis.xml": copia("factura_01.xml", **{CUFE_FV1001: cufe("9")}),
        "NC55.xml": fixture("nota_credito_91.xml"),  # 10.500 sobre FV1001: parcial
        "FV1002.xml": fixture("factura_cargo_01.xml"),  # total 155.500
        # 155.499 sobre FV1002: total, dentro de ±2,00.
        "NC56.xml": copia(
            "nota_credito_91.xml",
            NC55="NC56",
            FV1001="FV1002",
            **{
                nc55: nc55[:-3] + "096",
                CUFE_FV1001: cufe("12"),
                '"COP">10500.00</cbc:PayableAmount>': '"COP">155499.00</cbc:PayableAmount>',
            },
        ),
        # Factura tipo 04 (tabla 13.1.3): también puede quedar anulada.
        "FV2000.xml": copia(
            "factura_01.xml",
            FV1001="FV2000",
            **{CUFE_FV1001: cufe("7"), ">01</cbc:InvoiceTypeCode>": ">04</cbc:InvoiceTypeCode>"},
        ),
        "NC57.xml": sin_cufe,  # cita FV2000 solo por número
    }
    with base_aparte(tmp_path, archivos) as c:
        r = ejecutar(c, "duplicados_y_anulaciones", date(2026, 1, 1), date(2026, 1, 31))

    assert [(f[0], f[3], f[9], f[10]) for f in r.filas] == [
        ("anulada_parcial", "FV1001", Decimal("10500"), "NC55"),
        ("anulada_parcial", "FV2000", Decimal("10500"), "NC57"),
        ("anulada_total", "FV1002", Decimal("155499"), "NC56"),
        ("duplicado", "FV1001", None, "2 documentos con este número"),
        ("duplicado", "FV1001", None, "2 documentos con este número"),
    ]
    assert r.filas_resumen == [
        ("anulada_parcial", "COP", 2, Decimal("301000"), Decimal("21000")),
        ("anulada_total", "COP", 1, Decimal("155500"), Decimal("155499")),
        ("duplicado", "COP", 2, Decimal("301000"), None),
    ]


def nota_sobre_fv1001_y_fv1002(total: str) -> str:
    """NC60 que cita FV1001 y FV1002 (dos BillingReference), con el total dado."""
    segunda = (
        "<cac:BillingReference><cac:InvoiceDocumentReference><cbc:ID>FV1002</cbc:ID>"
        f'<cbc:UUID schemeName="CUFE-SHA384">{cufe("12")}</cbc:UUID>'
        "<cbc:IssueDate>2026-01-15</cbc:IssueDate></cac:InvoiceDocumentReference>"
        "</cac:BillingReference>\n  <cac:AccountingSupplierParty>"
    )
    nc55 = "cude" + "0" * 88 + "091"
    return copia(
        "nota_credito_91.xml",
        NC55="NC60",
        **{
            nc55: nc55[:-3] + "060",
            "<cac:AccountingSupplierParty>": segunda,
            '"COP">10500.00</cbc:PayableAmount>': f'"COP">{total}</cbc:PayableAmount>',
        },
    )


@pytest.mark.parametrize(
    ("total_nota", "esperado"),
    [
        # 150.500 + 155.500: anula las dos, cada una por su propio total.
        (
            "306000.00",
            [
                ("anulada_total", "FV1001", Decimal("150500"), "NC60"),
                ("anulada_total", "FV1002", Decimal("155500"), "NC60"),
            ],
        ),
        # No suma lo que las dos facturas: no se sabe cuánto le toca a cada una.
        (
            "100000.00",
            [
                ("anulada_sin_repartir", "FV1001", None, "NC60"),
                ("anulada_sin_repartir", "FV1002", None, "NC60"),
            ],
        ),
    ],
)
def test_nota_que_cita_varias_facturas_no_descuenta_su_total_de_cada_una(
    tmp_path, total_nota, esperado
):
    archivos = {
        "FV1001.xml": fixture("factura_01.xml"),  # total 150.500
        "FV1002.xml": fixture("factura_cargo_01.xml"),  # total 155.500
        "NC60.xml": nota_sobre_fv1001_y_fv1002(total_nota),
    }
    with base_aparte(tmp_path, archivos) as c:
        r = ejecutar(c, "duplicados_y_anulaciones", date(2026, 1, 1), date(2026, 1, 31))

    assert [(f[0], f[3], f[9], f[10]) for f in r.filas] == esperado


def test_nota_que_cita_una_factura_sin_cargar_no_se_reparte(tmp_path):
    # Cita FV1001 y FV1002, pero solo FV1001 está cargada: su total no es todo de FV1001.
    archivos = {
        "FV1001.xml": fixture("factura_01.xml"),
        "NC60.xml": nota_sobre_fv1001_y_fv1002("150500.00"),
    }
    with base_aparte(tmp_path, archivos) as c:
        r = ejecutar(c, "duplicados_y_anulaciones", date(2026, 1, 1), date(2026, 1, 31))

    assert [(f[0], f[3], f[9]) for f in r.filas] == [("anulada_sin_repartir", "FV1001", None)]


def test_facturas_credito_por_forma_de_pago(con):
    r = ejecutar(con, "facturas_credito", date(2026, 1, 1), date(2026, 3, 31))

    # Forma de pago 2: FV1001, FV1002, FV1003 y ND7; a mano:
    # 150.500 + 155.500 + 150.500 + 4.500.
    assert r.filas_resumen == [("900000001", "PROVEEDOR UNO SAS", "COP", 4, Decimal("461000"))]
    assert [(f[5], f[2], f[3], f[-1]) for f in r.filas] == [
        ("FV1001", 30, "2", "por verificar"),
        ("FV1002", 30, "2", "por verificar"),
        ("ND7", 28, "2", "por verificar"),
        ("FV1003", 30, "2", "por verificar"),
    ]


def test_facturas_credito_ignora_el_vencimiento_en_ventas_de_contado(tmp_path):
    # Caso real: venta de contado (forma de pago 1) con vencimiento a 30 días.
    credito = "<cbc:ID>2</cbc:ID>\n    <cbc:PaymentMeansCode>"
    contado = copia("factura_01.xml", **{credito: credito.replace("2", "1", 1)})
    with base_aparte(tmp_path, {"f.xml": contado}) as c:
        r = ejecutar(c, "facturas_credito", date(2026, 1, 1), date(2026, 1, 31))

    assert r.filas == []


def test_no_validadas_distingue_sin_respuesta_y_rechazadas(tmp_path):
    archivos = {
        "validada.xml": contenedor(fixture("factura_01.xml"), respuesta_dian()),
        "rechazada.xml": contenedor(
            fixture("factura_cargo_01.xml"), respuesta_dian(cufe("12"), codigo="04")
        ),
        "sin_respuesta.xml": fixture("nota_credito_91.xml"),
    }
    with base_aparte(tmp_path, archivos) as c:
        r = ejecutar(c, "no_validadas", date(2026, 1, 1), date(2026, 1, 31))

    assert [(f[0], f[3], f[8], Path(f[9]).name) for f in r.filas] == [
        ("rechazada", "FV1002", Decimal("155500"), "rechazada.xml"),
        ("sin_respuesta", "NC55", Decimal("-10500"), "sin_respuesta.xml"),
    ]
    assert r.filas_resumen == [
        ("rechazada", "COP", 1, Decimal("155500")),
        ("sin_respuesta", "COP", 1, Decimal("-10500")),
    ]


def test_exportar_excel_con_valores_exactos(con, tmp_path):
    r = ejecutar(con, "compras_por_proveedor", date(2026, 1, 1), date(2026, 2, 28))
    ruta = exportar(r, date(2026, 1, 1), date(2026, 2, 28), tmp_path / "compras.xlsx")

    libro = load_workbook(ruta)
    assert libro.sheetnames == ["resumen", "detalle"]
    resumen, detalle = libro["resumen"], libro["detalle"]
    assert resumen["A1"].value == "compras_por_proveedor"
    assert "restan" in resumen["A3"].value
    assert [c.value for c in resumen[5]] == r.columnas_resumen
    assert resumen["F6"].value == 400000 and resumen["F6"].number_format == "#,##0.00"
    assert [c.value for c in detalle[1]] == r.columnas
    assert detalle.max_row == 1 + len(r.filas)
    assert detalle["A2"].number_format == "yyyy-mm-dd"


def test_exportar_excel_conserva_los_seis_decimales(tmp_path):
    xml = copia(
        "factura_01.xml",
        **{'"COP">150500.00</cbc:PayableAmount>': '"COP">150500.123456</cbc:PayableAmount>'},
    )
    with base_aparte(tmp_path, {"f.xml": xml}) as c:
        r = ejecutar(c, "compras_por_proveedor", date(2026, 1, 1), date(2026, 1, 31))
    ruta = exportar(r, date(2026, 1, 1), date(2026, 1, 31), tmp_path / "f.xlsx")

    assert load_workbook(ruta)["detalle"]["I2"].value == 150500.123456


def test_cli_informe_con_xlsx(con, tmp_path):
    con.close()
    ruta = tmp_path / "iva.xlsx"
    argumentos = ["informe", CLIENTE, "iva_compras_por_bimestre", "--desde", "2026-01-01"]
    resultado = CliRunner().invoke(app, [*argumentos, "--hasta", "2026-03-31", "--xlsx", str(ruta)])

    assert resultado.exit_code == 0, resultado.output
    assert load_workbook(ruta)["resumen"]["A1"].value == "iva_compras_por_bimestre"

    sin_carpeta = str(tmp_path / "no" / "existe.xlsx")
    resultado = CliRunner().invoke(
        app, [*argumentos, "--hasta", "2026-03-31", "--xlsx", sin_carpeta]
    )
    assert resultado.exit_code == 1
    assert "existe.xlsx" in resultado.stderr
