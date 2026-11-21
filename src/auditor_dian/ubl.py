"""Lee Invoice, CreditNote y DebitNote (UBL 2.1, perfil DIAN) y los convierte en Documento.

Referencia: Anexo Técnico de Factura Electrónica de Venta v1.9 (Resolución DIAN 000165 de 2023).
Documento soporte y nota de ajuste: Anexo Técnico Documento Soporte v1.1 (Res. 000167 de 2021).
Los IDs de campo citados (FAD12, FAJ21, ...) son los del anexo; el cotejo completo está en
docs/investigacion/anexo-tecnico.md. Los valores de las tablas de códigos (tipos de documento,
identificación, tributos, formas y medios de pago) están en la "Caja de Herramientas" FE 1.9 de
la DIAN, fuera del anexo; se cotejaron el 2026-11-20.
"""

from collections.abc import Callable
from dataclasses import replace
from datetime import date, time
from decimal import Decimal, InvalidOperation

from lxml import etree

from auditor_dian.modelos import Advertencia, Documento, Linea, Parte, Referencia, Tributo

NS = {
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
    "sts": "dian:gov:co:facturaelectronica:Structures-2-1",  # anexo FE v1.9, sección 5.3.1
}

_UBL = "urn:oasis:names:specification:ubl:schema:xsd:"

# raíz -> (elemento de tipo, elemento de línea, elemento de cantidad, elemento de totales)
RAICES = {
    f"{{{_UBL}Invoice-2}}Invoice": (
        "cbc:InvoiceTypeCode",
        "cac:InvoiceLine",
        "cbc:InvoicedQuantity",
        "cac:LegalMonetaryTotal",
    ),
    f"{{{_UBL}CreditNote-2}}CreditNote": (
        "cbc:CreditNoteTypeCode",
        "cac:CreditNoteLine",
        "cbc:CreditedQuantity",
        "cac:LegalMonetaryTotal",
    ),
    # UBL 2.1 DebitNote no tiene elemento de tipo y usa RequestedMonetaryTotal.
    f"{{{_UBL}DebitNote-2}}DebitNote": (
        None,
        "cac:DebitNoteLine",
        "cbc:DebitedQuantity",
        "cac:RequestedMonetaryTotal",
    ),
}

# Sin entidades externas ni red: el XML viene de terceros (protección contra XXE).
PARSER = etree.XMLParser(resolve_entities=False, no_network=True, remove_blank_text=True)


class DocumentoNoSoportado(ValueError):
    pass


def leer_documento(xml: bytes) -> Documento:
    return desde_raiz(etree.fromstring(xml, PARSER))


# Lectores de plugins para raíces que core no conoce (SPEC §8): raíz -> leer(raiz) -> Documento.
LECTORES: dict[str, Callable[..., Documento]] = {}


def registrar_lector(raiz: str, leer: Callable[..., Documento]) -> None:
    if raiz in RAICES or raiz in LECTORES:
        raise ValueError(f"la raíz {raiz} ya tiene lector")
    LECTORES[raiz] = leer


def desde_raiz(raiz) -> Documento:
    if raiz.tag in LECTORES:
        try:
            return LECTORES[raiz.tag](raiz)
        except Exception as error:  # el fallo de un plugin queda como error de lectura del archivo
            raise DocumentoNoSoportado(
                f"falló el lector del plugin para {raiz.tag}: {error}"
            ) from error
    if raiz.tag not in RAICES:
        raise DocumentoNoSoportado(f"raíz no soportada: {raiz.tag}")
    return _Lectura(raiz).documento()


class _Lectura:
    def __init__(self, raiz):
        self.raiz = raiz
        self.advertencias: list[Advertencia] = []

    def documento(self) -> Documento:
        r = self.raiz
        tipo_el, linea_el, cantidad_el, totales_el = RAICES[r.tag]
        # La nota débito no tiene elemento de tipo en el anexo FE v1.9 (grupo DAD), así que el
        # código sale de la raíz.
        tipo = _texto(r, tipo_el) if tipo_el else "92"
        totales = _primero(r, totales_el)
        doc = Documento(
            tipo=tipo,
            prefijo=_texto(r, "ext:UBLExtensions//sts:AuthorizedInvoices/sts:Prefix"),
            numero=_texto(r, "cbc:ID"),
            cufe=_texto(r, "cbc:UUID"),
            esquema_cufe=_texto(r, "cbc:UUID/@schemeName"),
            fecha_emision=self._fecha(r, "cbc:IssueDate"),
            hora_emision=self._hora(r, "cbc:IssueTime"),
            fecha_vencimiento=self._fecha(r, "cbc:DueDate")
            or self._fecha(r, "cac:PaymentMeans/cbc:PaymentDueDate"),
            forma_pago=_texto(r, "cac:PaymentMeans/cbc:ID"),
            medios_pago=tuple(
                m.text.strip()
                for m in r.xpath("cac:PaymentMeans/cbc:PaymentMeansCode", namespaces=NS)
                if m.text and m.text.strip()
            ),
            moneda=_texto(r, "cbc:DocumentCurrencyCode"),
            trm=self._decimal(r, "cac:PaymentExchangeRate/cbc:CalculationRate"),
            # En el documento soporte (05/95) el XML lo genera el comprador, pero el
            # vendedor sigue en AccountingSupplierParty (anexo DS v1.1, DSAJ21; adquiriente DSAK21).
            emisor=self._parte(_primero(r, "cac:AccountingSupplierParty/cac:Party")),
            adquirente=self._parte(_primero(r, "cac:AccountingCustomerParty/cac:Party")),
            subtotal=self._decimal(totales, "cbc:LineExtensionAmount"),
            base_gravable=self._decimal(totales, "cbc:TaxExclusiveAmount"),
            # Anexo FE 1.9 FAU06/FAU08/FAU10/FAU12 y numeral 5.2.1 (PayableRoundingAmount); el
            # anexo valida PayableAmount = TaxInclusive - Allowance + Charge (FAU14).
            total_impuestos_incluidos=self._decimal(totales, "cbc:TaxInclusiveAmount"),
            descuentos=self._decimal(totales, "cbc:AllowanceTotalAmount"),
            cargos=self._decimal(totales, "cbc:ChargeTotalAmount"),
            # La tabla del anexo dice "PrePaidAmount"; su XPath y UBL 2.1 usan PrepaidAmount.
            anticipos=self._decimal(totales, "cbc:PrepaidAmount"),
            redondeo=self._decimal(totales, "cbc:PayableRoundingAmount"),
            total_pagar=self._decimal(totales, "cbc:PayableAmount"),
            referencias=tuple(
                Referencia(
                    numero=_texto(ref, "cbc:ID"),
                    cufe=_texto(ref, "cbc:UUID"),
                    fecha=self._fecha(ref, "cbc:IssueDate"),
                )
                for ref in r.xpath(
                    "cac:BillingReference/cac:InvoiceDocumentReference", namespaces=NS
                )
            ),
            impuestos=self._tributos(r, "cac:TaxTotal"),
            retenciones=self._tributos(r, "cac:WithholdingTaxTotal"),
            lineas=tuple(
                self._linea(nodo, cantidad_el) for nodo in r.xpath(linea_el, namespaces=NS)
            ),
            advertencias=(),
        )
        obligatorios = {
            "tipo": doc.tipo,
            "numero": doc.numero,
            "cufe": doc.cufe,
            "fecha_emision": doc.fecha_emision,
            "emisor.identificacion": doc.emisor.identificacion,
            "adquirente.identificacion": doc.adquirente.identificacion,
            "total_pagar": doc.total_pagar,
        }
        for campo, valor in obligatorios.items():
            if valor is None:
                self._advertir("campo_faltante", campo)
        if doc.moneda not in (None, "COP") and doc.trm is None:
            self._advertir("campo_faltante", "trm")  # sin TRM no se puede llevar a pesos
        return replace(doc, advertencias=tuple(self.advertencias))

    def _parte(self, party) -> Parte:
        # CompanyID sin DV; @schemeID = DV, @schemeName = tipo de identificación
        # (anexo FE v1.9, FAJ21/FAJ24/FAJ25 emisor y FAK21/FAK24/FAK25 adquiriente).
        ruta = "cac:PartyTaxScheme/cbc:CompanyID"
        if party is not None and _primero(party, ruta) is None:
            ruta = "cac:PartyLegalEntity/cbc:CompanyID"
        return Parte(
            tipo_identificacion=_texto(party, f"{ruta}/@schemeName"),
            identificacion=_texto(party, ruta),
            dv=_texto(party, f"{ruta}/@schemeID"),
            nombre=_texto(party, "cac:PartyTaxScheme/cbc:RegistrationName")
            or _texto(party, "cac:PartyLegalEntity/cbc:RegistrationName"),
        )

    def _tributos(self, nodo, total_el: str) -> tuple[Tributo, ...]:
        return tuple(
            Tributo(
                codigo=_texto(sub, "cac:TaxCategory/cac:TaxScheme/cbc:ID"),
                tarifa=self._decimal(sub, "cac:TaxCategory/cbc:Percent"),
                base=self._decimal(sub, "cbc:TaxableAmount"),
                valor=self._decimal(sub, "cbc:TaxAmount"),
            )
            for sub in nodo.xpath(f"{total_el}/cac:TaxSubtotal", namespaces=NS)
        )

    def _linea(self, nodo, cantidad_el: str) -> Linea:
        return Linea(
            numero=_texto(nodo, "cbc:ID"),
            descripcion=_texto(nodo, "cac:Item/cbc:Description"),
            cantidad=self._decimal(nodo, cantidad_el),
            unidad=_texto(nodo, f"{cantidad_el}/@unitCode"),
            valor_unitario=self._decimal(nodo, "cac:Price/cbc:PriceAmount"),
            valor_total=self._decimal(nodo, "cbc:LineExtensionAmount"),
            impuestos=self._tributos(nodo, "cac:TaxTotal"),
        )

    def _decimal(self, nodo, ruta: str) -> Decimal | None:
        return self._convertir(nodo, ruta, _decimal_finito)

    def _fecha(self, nodo, ruta: str) -> date | None:
        return self._convertir(nodo, ruta, date.fromisoformat)

    def _hora(self, nodo, ruta: str) -> time | None:
        return self._convertir(nodo, ruta, time.fromisoformat)

    def _convertir(self, nodo, ruta, conversor):
        texto = _texto(nodo, ruta)
        if texto is None:
            return None
        try:
            return conversor(texto)
        except (InvalidOperation, ValueError):
            self._advertir("valor_invalido", f"{ruta} = {texto!r}")
            return None

    def _advertir(self, codigo: str, detalle: str) -> None:
        self.advertencias.append(Advertencia(codigo, detalle))


def _decimal_finito(texto: str) -> Decimal:
    valor = Decimal(texto)
    if not valor.is_finite():  # Decimal() acepta "NaN" e "Infinity"; ningún monto DIAN lo es
        raise ValueError(texto)
    return valor


def _primero(nodo, ruta: str):
    if nodo is None:
        return None
    encontrados = nodo.xpath(ruta, namespaces=NS)
    return encontrados[0] if encontrados else None


def _texto(nodo, ruta: str) -> str | None:
    valor = _primero(nodo, ruta)
    if valor is None:
        return None
    texto = (valor if isinstance(valor, str) else valor.text or "").strip()
    return texto or None
