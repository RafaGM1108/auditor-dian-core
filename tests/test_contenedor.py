import pytest
from fabrica import CUFE_FV1001, contenedor, fixture, respuesta_dian

from auditor_dian.contenedor import leer_xml
from auditor_dian.modelos import Advertencia
from auditor_dian.ubl import DocumentoNoSoportado, leer_documento


def test_xml_directo_se_lee_igual_que_con_ubl():
    xml = fixture("factura_01.xml").encode()

    assert leer_xml(xml) == leer_documento(xml)


def test_contenedor_validado_por_dian():
    doc = leer_xml(contenedor(fixture("factura_01.xml"), respuesta_dian()))

    assert doc.cufe == CUFE_FV1001
    assert doc.numero == "FV1001"
    assert doc.validado_dian is True
    assert doc.advertencias == ()


def test_contenedor_con_documento_rechazado():
    doc = leer_xml(contenedor(fixture("factura_01.xml"), respuesta_dian(codigo="04")))

    assert doc.validado_dian is False


def test_contenedor_sin_respuesta_queda_desconocido():
    doc = leer_xml(contenedor(fixture("nota_credito_91.xml")))

    assert doc.tipo == "91"
    assert doc.validado_dian is None
    assert doc.advertencias == ()


def test_respuesta_de_otro_documento_no_cuenta_como_validacion():
    doc = leer_xml(contenedor(fixture("factura_01.xml"), respuesta_dian(cufe="otro")))

    assert doc.validado_dian is None
    assert doc.advertencias == (
        Advertencia("validacion_de_otro_documento", "CUFE en la respuesta: 'otro'"),
    )


def test_respuesta_ilegible_da_advertencia():
    doc = leer_xml(contenedor(fixture("factura_01.xml"), "<ApplicationResponse>"))

    assert doc.validado_dian is None
    assert [a.codigo for a in doc.advertencias] == ["validacion_ilegible"]


def test_documento_embebido_con_otra_codificacion_conserva_tildes():
    documento = (
        fixture("factura_01.xml")
        .replace('encoding="UTF-8"', 'encoding="ISO-8859-1"')
        .replace("Cuaderno argollado", "Café molido")
    )

    doc = leer_xml(contenedor(documento, respuesta_dian()))

    assert doc.lineas[1].descripcion == "Café molido"


def test_contenedor_vacio_se_rechaza():
    xml = contenedor("").replace(b"<![CDATA[]]>", b"")

    with pytest.raises(DocumentoNoSoportado):
        leer_xml(xml)


def test_respuesta_sin_codigo_da_advertencia():
    respuesta = respuesta_dian().replace("<cbc:ResponseCode>02</cbc:ResponseCode>", "")

    doc = leer_xml(contenedor(fixture("factura_01.xml"), respuesta))

    assert doc.validado_dian is None
    assert doc.advertencias == (Advertencia("campo_faltante", "validacion.ResponseCode"),)


def test_varias_respuestas_usa_la_del_documento():
    xml = contenedor(fixture("factura_01.xml"), respuesta_dian(cufe="otro"), respuesta_dian())

    doc = leer_xml(xml)

    assert doc.validado_dian is True
    assert doc.advertencias == ()


def test_codigo_de_evento_no_se_confunde_con_rechazo():
    doc = leer_xml(contenedor(fixture("factura_01.xml"), respuesta_dian(codigo="030")))

    assert doc.validado_dian is None
    assert doc.advertencias == (
        Advertencia("validacion_codigo_desconocido", "ResponseCode = '030'"),
    )
