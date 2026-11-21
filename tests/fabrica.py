from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
CUFE_FV1001 = "cufe" + "0" * 90 + "1"

_CABECERA = (
    'xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" '
    'xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"'
)


def respuesta_dian(cufe: str = CUFE_FV1001, codigo: str = "02") -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ApplicationResponse xmlns="urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2"
  {_CABECERA}>
  <cbc:UBLVersionID>UBL 2.1</cbc:UBLVersionID>
  <cbc:ID>9000000001</cbc:ID>
  <cbc:IssueDate>2026-01-15</cbc:IssueDate>
  <cac:DocumentResponse>
    <cac:Response>
      <cbc:ResponseCode>{codigo}</cbc:ResponseCode>
      <cbc:Description>Documento validado por la DIAN</cbc:Description>
    </cac:Response>
    <cac:DocumentReference>
      <cbc:ID>FV1001</cbc:ID>
      <cbc:UUID schemeName="CUFE-SHA384">{cufe}</cbc:UUID>
    </cac:DocumentReference>
  </cac:DocumentResponse>
</ApplicationResponse>"""


def contenedor(documento: str, *respuestas: str) -> bytes:
    """AttachedDocument con el documento y cero o más respuestas DIAN, todo en CDATA."""
    linea = ""
    for i, respuesta in enumerate(respuestas, start=1):
        linea += f"""
  <cac:ParentDocumentLineReference>
    <cbc:LineID>{i}</cbc:LineID>
    <cac:DocumentReference>
      <cbc:ID>FV1001</cbc:ID>
      <cbc:DocumentType>ApplicationResponse</cbc:DocumentType>
      <cac:Attachment>
        <cac:ExternalReference>
          <cbc:MimeCode>text/xml</cbc:MimeCode>
          <cbc:Description><![CDATA[{respuesta}]]></cbc:Description>
        </cac:ExternalReference>
      </cac:Attachment>
    </cac:DocumentReference>
  </cac:ParentDocumentLineReference>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<AttachedDocument xmlns="urn:oasis:names:specification:ubl:schema:xsd:AttachedDocument-2"
  {_CABECERA}>
  <cbc:UBLVersionID>UBL 2.1</cbc:UBLVersionID>
  <cbc:CustomizationID>Documentos adjuntos</cbc:CustomizationID>
  <cbc:DocumentType>Contenedor de Factura Electrónica</cbc:DocumentType>
  <cbc:ParentDocumentID>FV1001</cbc:ParentDocumentID>
  <cac:Attachment>
    <cac:ExternalReference>
      <cbc:MimeCode>text/xml</cbc:MimeCode>
      <cbc:Description><![CDATA[{documento}]]></cbc:Description>
    </cac:ExternalReference>
  </cac:Attachment>{linea}
</AttachedDocument>""".encode()


def fixture(nombre: str) -> str:
    return (FIXTURES / nombre).read_text(encoding="utf-8")


CLIENTE = "900000009"  # adquirente de todos los fixtures salvo la exportación
FIXTURES_COMUNES = [
    "factura_01.xml",  # 01 FV1001 2026-01-15 PROVEEDOR UNO: subtotal 130.000, total 150.500
    "factura_cargo_01.xml",  # 01 FV1002 2026-01-15 PROVEEDOR UNO: 130.000 / 155.500
    "nota_credito_91.xml",  # 91 NC55 2026-01-20 PROVEEDOR UNO: 10.000 / 10.500, resta
    "nota_debito_92.xml",  # 92 ND7 2026-02-20 PROVEEDOR UNO: 4.500 / 4.500, suma
    "documento_soporte_05.xml",  # 05 DS20 2026-01-28 VENDEDOR: 500.000 / 500.000
    "nota_ajuste_95.xml",  # 95 NA3 2026-02-02 VENDEDOR: 100.000 / 100.000, resta
    "factura_exportacion_02.xml",  # adquirente EXT-000123: no es compra del cliente
]


def crear_base_comun(carpeta: Path) -> None:
    """Cliente CLIENTE con los fixtures comunes y FV1003 (FV1001 emitida en marzo) ingeridos."""
    from auditor_dian.base import abrir, crear_cliente
    from auditor_dian.ingesta import ingerir

    for nombre in FIXTURES_COMUNES:
        (carpeta / nombre).write_text(fixture(nombre), encoding="utf-8")
    marzo = (
        fixture("factura_01.xml")
        .replace("FV1001", "FV1003")
        .replace("2026-01-15", "2026-03-10")
        .replace("2026-02-14", "2026-04-09")
        .replace(">42</cbc:PaymentMeansCode>", ">48</cbc:PaymentMeansCode>")  # tarjeta crédito
    )
    (carpeta / "FV1003.xml").write_text(marzo.replace(CUFE_FV1001, CUFE_FV1001[:-1] + "3"))
    crear_cliente(CLIENTE, "Cliente de prueba SAS")
    with abrir(CLIENTE) as con:
        ingerir(con, CLIENTE, carpeta)
