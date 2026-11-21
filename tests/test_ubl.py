from datetime import date, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from auditor_dian.modelos import Advertencia, Parte, Referencia, Tributo
from auditor_dian.ubl import DocumentoNoSoportado, leer_documento

FIXTURES = Path(__file__).parent / "fixtures"
BOGOTA = timezone(timedelta(hours=-5))
EMISOR = Parte("31", "900000001", "1", "PROVEEDOR UNO SAS")
ADQUIRENTE = Parte("31", "900000009", "9", "CLIENTE DE PRUEBA SAS")
REF_FV1001 = Referencia("FV1001", "cufe" + "0" * 90 + "1", date(2026, 1, 15))


def leer(nombre: str):
    return leer_documento((FIXTURES / nombre).read_bytes())


def test_varios_medios_de_pago():
    # PaymentMeans es 1..N (FAN01); en facturas reales llegan "ZZZ" y "48" juntos.
    xml = (FIXTURES / "factura_01.xml").read_bytes()
    otro = b"<cac:PaymentMeans><cbc:ID>2</cbc:ID><cbc:PaymentMeansCode>48</cbc:PaymentMeansCode>"
    doc = leer_documento(
        xml.replace(b"<cac:PaymentMeans>", otro + b"</cac:PaymentMeans><cac:PaymentMeans>", 1)
    )

    assert (doc.forma_pago, doc.medios_pago) == ("2", ("48", "42"))
    assert leer("nota_credito_91.xml").medios_pago == ()


def test_factura_de_venta():
    doc = leer("factura_01.xml")

    assert (doc.tipo, doc.prefijo, doc.numero) == ("01", "FV", "FV1001")
    assert doc.cufe == REF_FV1001.cufe
    assert doc.esquema_cufe == "CUFE-SHA384"
    assert doc.fecha_emision == date(2026, 1, 15)
    assert doc.hora_emision == time(10, 30, tzinfo=BOGOTA)
    assert doc.fecha_vencimiento == date(2026, 2, 14)
    assert (doc.forma_pago, doc.medios_pago, doc.moneda, doc.trm) == ("2", ("42",), "COP", None)
    assert (doc.emisor, doc.adquirente) == (EMISOR, ADQUIRENTE)
    assert doc.subtotal == Decimal("130000.00")
    assert doc.base_gravable == Decimal("130000.00")
    assert doc.total_pagar == Decimal("150500.00")
    assert doc.total_impuestos_incluidos == Decimal("150500.00")
    assert (doc.descuentos, doc.cargos, doc.anticipos, doc.redondeo) == (None,) * 4
    assert doc.referencias == ()
    assert doc.impuestos == (
        Tributo("01", Decimal("19.00"), Decimal("100000.00"), Decimal("19000.00")),
        Tributo("01", Decimal("5.00"), Decimal("30000.00"), Decimal("1500.00")),
    )
    assert doc.retenciones == (
        Tributo("06", Decimal("2.50"), Decimal("130000.00"), Decimal("3250.00")),
    )
    assert doc.validado_dian is None
    assert doc.advertencias == ()


def test_lineas_de_factura_traen_sus_impuestos():
    lineas = leer("factura_01.xml").lineas

    assert [(li.numero, li.descripcion, li.cantidad, li.unidad) for li in lineas] == [
        ("1", "Resma de papel carta", Decimal("2"), "94"),
        ("2", "Cuaderno argollado", Decimal("1"), "94"),
    ]
    assert lineas[0].valor_unitario == Decimal("50000.00")
    assert lineas[0].valor_total == Decimal("100000.00")
    assert lineas[0].impuestos == (
        Tributo("01", Decimal("19.00"), Decimal("100000.00"), Decimal("19000.00")),
    )


def test_nota_credito_referencia_la_factura():
    doc = leer("nota_credito_91.xml")

    assert (doc.tipo, doc.prefijo, doc.numero) == ("91", None, "NC55")
    assert doc.esquema_cufe == "CUDE-SHA384"
    assert doc.referencias == (REF_FV1001,)
    assert doc.total_pagar == Decimal("10500.00")
    assert doc.lineas[0].cantidad == Decimal("0.5")
    assert doc.fecha_vencimiento is None
    assert doc.advertencias == ()


def test_nota_debito_usa_requested_monetary_total_y_vencimiento_en_payment_means():
    doc = leer("nota_debito_92.xml")

    assert (doc.tipo, doc.numero) == ("92", "ND7")
    assert doc.referencias == (REF_FV1001,)
    assert doc.subtotal == Decimal("4500.00")
    assert doc.total_pagar == Decimal("4500.00")
    assert doc.fecha_vencimiento == date(2026, 3, 20)
    assert doc.lineas[0].cantidad == Decimal("1")
    assert doc.advertencias == ()


def test_campo_obligatorio_faltante_queda_en_none_con_advertencia():
    xml = (FIXTURES / "factura_01.xml").read_bytes()
    inicio = xml.index(b"<cbc:UUID")
    xml = xml[:inicio] + xml[xml.index(b"</cbc:UUID>") + len(b"</cbc:UUID>") :]

    doc = leer_documento(xml)

    assert doc.cufe is None
    assert doc.advertencias == (Advertencia("campo_faltante", "cufe"),)


def test_monto_invalido_queda_en_none_con_advertencia():
    xml = (
        (FIXTURES / "factura_01.xml")
        .read_bytes()
        .replace(b">150500.00</cbc:PayableAmount>", b">150.500,00</cbc:PayableAmount>")
    )

    doc = leer_documento(xml)

    assert doc.total_pagar is None
    assert doc.advertencias == (
        Advertencia("valor_invalido", "cbc:PayableAmount = '150.500,00'"),
        Advertencia("campo_faltante", "total_pagar"),
    )


def test_raiz_desconocida_se_rechaza():
    with pytest.raises(DocumentoNoSoportado):
        leer_documento(b"<Otra/>")


def test_no_resuelve_entidades_externas():
    xml = (
        b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]>'
        b'<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"'
        b' xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">'
        b"<cbc:ID>&e;</cbc:ID></Invoice>"
    )

    assert leer_documento(xml).numero is None


def test_factura_de_exportacion_en_moneda_extranjera_trae_trm():
    doc = leer("factura_exportacion_02.xml")

    assert (doc.tipo, doc.numero, doc.moneda, doc.trm) == ("02", "FE12", "USD", Decimal("4000.00"))
    assert doc.adquirente == Parte("50", "EXT-000123", None, "FOREIGN TEST CORP")
    assert doc.total_pagar == Decimal("1000.00")
    assert doc.impuestos == (Tributo("01", Decimal("0.00"), Decimal("1000.00"), Decimal("0.00")),)
    assert doc.lineas[0].unidad == "HUR"
    assert doc.advertencias == ()


def test_moneda_extranjera_sin_trm_da_advertencia():
    xml = (FIXTURES / "factura_exportacion_02.xml").read_bytes()
    inicio = xml.index(b"<cac:PaymentExchangeRate>")
    fin = xml.index(b"</cac:PaymentExchangeRate>") + len(b"</cac:PaymentExchangeRate>")

    doc = leer_documento(xml[:inicio] + xml[fin:])

    assert doc.trm is None
    assert doc.advertencias == (Advertencia("campo_faltante", "trm"),)


def test_factura_de_contingencia_se_lee_como_factura():
    xml = (
        (FIXTURES / "factura_01.xml")
        .read_bytes()
        .replace(b"<cbc:InvoiceTypeCode>01<", b"<cbc:InvoiceTypeCode>03<")
    )

    doc = leer_documento(xml)

    assert (doc.tipo, doc.numero, doc.total_pagar) == ("03", "FV1001", Decimal("150500.00"))
    assert doc.advertencias == ()


def test_documento_soporte_compra_a_persona_natural():
    doc = leer("documento_soporte_05.xml")

    assert (doc.tipo, doc.numero, doc.esquema_cufe) == ("05", "DS20", "CUDS-SHA384")
    assert doc.emisor == Parte("13", "1000000001", None, "VENDEDOR PERSONA NATURAL")
    assert doc.adquirente == ADQUIRENTE
    assert doc.impuestos == ()
    assert doc.retenciones == (
        Tributo("06", Decimal("3.50"), Decimal("500000.00"), Decimal("17500.00")),
        Tributo("07", Decimal("0.966"), Decimal("500000.00"), Decimal("4830.00")),
    )
    assert doc.base_gravable == Decimal("0.00")
    assert doc.total_pagar == Decimal("500000.00")
    assert doc.advertencias == ()


def test_nota_de_ajuste_referencia_el_documento_soporte():
    doc = leer("nota_ajuste_95.xml")

    assert (doc.tipo, doc.numero, doc.esquema_cufe) == ("95", "NA3", "CUDS-SHA384")
    assert doc.referencias == (Referencia("DS20", "cuds" + "0" * 90 + "5", date(2026, 1, 28)),)
    assert doc.total_pagar == Decimal("100000.00")
    assert doc.advertencias == ()


def test_identificacion_en_party_legal_entity_cuando_no_hay_party_tax_scheme():
    xml = (FIXTURES / "factura_01.xml").read_bytes()
    xml = xml.replace(b"cac:PartyTaxScheme>", b"cac:PartyLegalEntity>", 2)

    doc = leer_documento(xml)

    assert doc.emisor == EMISOR
    assert doc.adquirente == ADQUIRENTE


@pytest.mark.parametrize("texto", ["NaN", "Infinity", "-inf", "sNaN"])
def test_monto_no_finito_queda_en_none_con_advertencia(texto):
    xml = (FIXTURES / "factura_01.xml").read_bytes()
    xml = xml.replace(b">150500.00</cbc:PayableAmount>", f">{texto}</cbc:PayableAmount>".encode())

    doc = leer_documento(xml)

    assert doc.total_pagar is None
    assert Advertencia("valor_invalido", f"cbc:PayableAmount = {texto!r}") in doc.advertencias


def test_factura_con_cargo_global_lee_todos_los_totales():
    doc = leer("factura_cargo_01.xml")

    assert doc.total_impuestos_incluidos == Decimal("150500.00")
    assert (doc.descuentos, doc.cargos, doc.anticipos, doc.redondeo) == (
        Decimal("0.00"),
        Decimal("5000.00"),
        Decimal("0.00"),
        Decimal("0.00"),
    )
    assert doc.total_pagar == Decimal("155500.00")
    assert doc.total_impuestos_incluidos - doc.descuentos + doc.cargos == doc.total_pagar
    assert doc.advertencias == ()
