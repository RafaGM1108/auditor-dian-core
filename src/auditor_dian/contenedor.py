"""Lee un XML recibido: AttachedDocument (contenedor DIAN) o documento UBL directo.

El AttachedDocument trae el documento original como texto (CDATA) en
cac:Attachment/cac:ExternalReference/cbc:Description (campos AE33–AE37), y las respuestas
DIAN (ApplicationResponse) también como texto, una por cada cac:ParentDocumentLineReference
(AE38–AE50, 1..N). Referencia: Anexo Técnico FE v1.9, sección 6.4.
"""

import re
from dataclasses import replace

from lxml import etree

from auditor_dian.modelos import Advertencia, Documento
from auditor_dian.ubl import NS, PARSER, DocumentoNoSoportado, _texto, desde_raiz

ATTACHED = "{urn:oasis:names:specification:ubl:schema:xsd:AttachedDocument-2}AttachedDocument"
RUTA_DOCUMENTO = "cac:Attachment/cac:ExternalReference/cbc:Description"
RUTA_RESPUESTA = (
    "cac:ParentDocumentLineReference/cac:DocumentReference"
    "/cac:Attachment/cac:ExternalReference/cbc:Description"
)
# ResponseCode: "02" Documento Validado / "04" Documento Rechazado por la DIAN
# (Anexo FE v1.9, secciones 6.5.5.1 y 6.5.5.2, campo AAH03). Otros códigos son eventos (030–034).
RESULTADOS = {"02": True, "04": False}
_DECLARACION = re.compile(r"^\s*<\?xml[^>]*\?>")


def leer_xml(xml: bytes) -> Documento:
    raiz = etree.fromstring(xml, PARSER)
    if raiz.tag != ATTACHED:
        return desde_raiz(raiz)

    embebido = _texto(raiz, RUTA_DOCUMENTO)
    if embebido is None:
        raise DocumentoNoSoportado("AttachedDocument sin documento embebido")
    doc = desde_raiz(_parsear(embebido))

    otros = []
    for nodo in raiz.xpath(RUTA_RESPUESTA, namespaces=NS):
        try:
            ar = _parsear((nodo.text or "").strip())
        except etree.XMLSyntaxError as error:
            doc = _advertir(doc, "validacion_ilegible", str(error))
            continue
        cufe = _texto(ar, "cac:DocumentResponse/cac:DocumentReference/cbc:UUID")
        if cufe != doc.cufe:
            otros.append(cufe)
            continue
        codigo = _texto(ar, "cac:DocumentResponse/cac:Response/cbc:ResponseCode")
        if codigo is None:
            return _advertir(doc, "campo_faltante", "validacion.ResponseCode")
        if codigo not in RESULTADOS:
            return _advertir(doc, "validacion_codigo_desconocido", f"ResponseCode = {codigo!r}")
        return replace(doc, validado_dian=RESULTADOS[codigo])
    for cufe in otros:
        doc = _advertir(doc, "validacion_de_otro_documento", f"CUFE en la respuesta: {cufe!r}")
    return doc


def _parsear(texto: str):
    # El texto ya está decodificado: se quita la declaración para que lxml no
    # reinterprete su "encoding" (falla con str y daña tildes si declara ISO-8859-1).
    return etree.fromstring(_DECLARACION.sub("", texto, count=1), PARSER)


def _advertir(doc: Documento, codigo: str, detalle: str) -> Documento:
    return replace(doc, advertencias=(*doc.advertencias, Advertencia(codigo, detalle)))
