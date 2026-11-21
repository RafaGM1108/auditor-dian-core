# Anexo Técnico de factura electrónica: versión vigente y rutas usadas

Consultado: 2026-11-20. Cotejo hecho sobre los PDF oficiales (los PDF no se guardan en el repositorio por su tamaño; se citan sus URL).

## Fuentes

- **Anexo Técnico de Factura Electrónica de Venta, versión 1.9** — Resolución DIAN 000165 del 1 de noviembre de 2023, 753 páginas. [PDF en dian.gov.co](https://www.dian.gov.co/impuestos/factura-electronica/Documents/Anexo-Tecnico-Factura-Electronica-de-Venta-vr-1-9.pdf).
- **Anexo Técnico Documento Soporte en adquisiciones a sujetos no obligados a facturar, versión 1.1** — Resolución DIAN 000167 de 2021, 290 páginas. [PDF en dian.gov.co](https://www.dian.gov.co/impuestos/factura-electronica/Documents/Anexo-Tecnico-Documento-Soporte-No-Obligados.pdf).
- Vigencia de la 1.9: la Resolución 000008 de 2024 fijó la adopción obligatoria desde el 1 de mayo de 2024 ([normograma Invima](https://normograma.invima.gov.co/normograma/docs/pdf/resolucion_dian_0165_2023.pdf)); antes aplicaba la 1.8 (Concepto DIAN 1531 de 2024, [normograma DIAN](https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_1531_2024.htm)). No se encontró una versión posterior.

**Hallazgo clave:** en la versión 1.9 las tablas de códigos (13.1.3 tipos de documento, 13.2.1 tipos de identificación, 13.2.3 tributos, formas y medios de pago) **ya no están en el anexo**: se movieron a la "Caja de Herramientas" de la DIAN (`Caja_de_herramientas_Factura_Electronica_Validacion_Previa.zip\Anexo Tecnico\Tablas Referenciadas`, en Excel). Las rutas se pudieron cotejar; varios valores de códigos no.

## Resultado del cotejo

Estados: **confirmado** (coincide con el anexo), **sin cotejar** (el valor está en la Caja de Herramientas), **ambiguo** (el anexo se contradice).

| Campo | Ruta / valor que usa el parser | Referencia en el anexo | Estado |
| --- | --- | --- | --- |
| Número | `cbc:ID` | UBL 2.1 | confirmado |
| CUFE / CUDE | `cbc:UUID`, `@schemeName` `CUFE-SHA384` (factura) o `CUDE-SHA384` (notas) | FE 1.9: FAD06/FAD08, CAD08, DAD08; texto de AE43: "CUFE-SHA384 para la FE, CUDE-SHA384 para otro DFE" | confirmado |
| Tipo de factura | `cbc:InvoiceTypeCode` | FAD12 | ruta confirmada |
| Código `02` exportación, `03` contingencia | — | Reglas que citan `InvoiceTypeCode = "02"` (exportación) y FAI01 (`"03"` contingencia) | confirmado |
| Códigos `01` venta, `02` exportación, `03` instrumento de transmisión (talonario), `04` factura tipo 04, `91` nota crédito, `92` nota débito | — | Tabla 13.1.3 de la Caja de Herramientas FE 1.9 (`Caja-de-herramientas-FE-V1-9.zip`, descargada de dian.gov.co el 2026-11-20); ruta de nota crédito CAD12 `cbc:CreditNoteTypeCode` | confirmado; **`04` faltaba** en el informe de anulaciones, ya corregido |
| Tipo de nota débito | No hay elemento; el parser asigna `92` por la raíz | La lista de campos de `DebitNote` (grupo DAD) no tiene elemento de tipo | confirmado (que no existe); `92` confirmado en la tabla 13.1.3 |
| Prefijo | `ext:UBLExtensions//sts:AuthorizedInvoices/sts:Prefix`, namespace `dian:gov:co:facturaelectronica:Structures-2-1` | FAB10 (0..1); namespaces en 5.3.1 | confirmado |
| NIT, DV, tipo de identificación | `cac:PartyTaxScheme/cbc:CompanyID` (sin DV), `@schemeID` = DV, `@schemeName` = tipo | Emisor FAJ21/FAJ24/FAJ25; adquiriente FAK21/FAK24/FAK25; `@schemeAgencyID` = "195" (FAJ22) | confirmado |
| Códigos de tipo de identificación (31 NIT, 13 cédula, 50, 42) | — | Tabla 13.2.1 de la Caja de Herramientas FE 1.9 | confirmado |
| Nombre | `cac:PartyTaxScheme/cbc:RegistrationName`, alterno `cac:PartyLegalEntity/cbc:RegistrationName` | FAJ20 y FAJ43 | confirmado |
| Forma de pago | `cac:PaymentMeans/cbc:ID` | FAN02 "Formas de pago" | ruta confirmada |
| Valores 1 contado, 2 crédito | — | Tabla 13.3.4.1 de la Caja de Herramientas FE 1.9; también DS 1.1, tabla 16.3.4.1 | confirmado |
| Medios de pago | `cac:PaymentMeans/cbc:PaymentMeansCode`, uno por cada `cac:PaymentMeans` (el grupo es 1..N) | FAN01 (1..N), FAN03; valores en la tabla 13.3.4.2 de la Caja de Herramientas FE 1.9 (10 efectivo, 42 consignación, 46/47 transferencias, 48 tarjeta crédito, 49 tarjeta débito, ZZZ otro, entre 80 códigos) | confirmado; 10 de 57 facturas reales traen dos medios (por ejemplo `ZZZ` y `48`) |
| Vencimiento | `cbc:DueDate` o `cac:PaymentMeans/cbc:PaymentDueDate` | FAD11 (0..1); FAN04: "Obligatorio si es venta a crédito" | confirmado |
| Moneda y TRM | `cbc:DocumentCurrencyCode`; `cac:PaymentExchangeRate/cbc:CalculationRate` | FAD15, FAR01–FAR07 | **ambiguo** (ver abajo) |
| Totales: impuestos incluidos, descuentos, cargos, anticipos | `cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount`, `AllowanceTotalAmount`, `ChargeTotalAmount`, `PrepaidAmount` | FAU06, FAU08, FAU10, FAU12 (la tabla escribe "PrePaidAmount"; el XPath y UBL 2.1, `PrepaidAmount`) | confirmado; agregado el 2026-11-20 tras un caso real |
| Redondeo del total | `cac:LegalMonetaryTotal/cbc:PayableRoundingAmount` | Numeral 5.2.1; 5.2.3.1: único monto que puede ser negativo | confirmado |
| Regla del total a pagar | `PayableAmount = TaxInclusiveAmount − AllowanceTotalAmount + ChargeTotalAmount` | FAU14; tolerancia ±2,00 en valores monetarios (5.2.1.1) | se cumple exacto en los 12 documentos reales |
| Totales y líneas de nota débito | `cac:RequestedMonetaryTotal`, `cac:DebitNoteLine/cbc:DebitedQuantity` | `/DebitNote/cac:RequestedMonetaryTotal/...`; DAV05 | confirmado |
| Impuestos | `cac:TaxTotal/cac:TaxSubtotal` | UBL 2.1; grupo FAS | ruta confirmada |
| Retenciones | `cac:WithholdingTaxTotal/cac:TaxSubtotal` | FAT01: son **autorretenciones del emisor**; un bloque por código de tributo | ruta confirmada; ver hallazgo |
| Códigos de tributo (01 IVA, 03 ICA, 04 INC, 05 ReteIVA, 06 ReteRenta, 07 ReteICA, 22 INC Bolsas; 30–36 nuevos) | — | Tabla 13.2.2 Tributos de la Caja de Herramientas FE 1.9 (el anexo la citaba como 13.2.3) | confirmado |
| Documento embebido | `cac:Attachment/cac:ExternalReference/cbc:Description` del `AttachedDocument` | Sección 6.4, AE33–AE37 (CDATA, UTF-8) | confirmado |
| Respuesta DIAN | `cac:ParentDocumentLineReference/cac:DocumentReference/cac:Attachment/cac:ExternalReference/cbc:Description` | AE38–AE50; `ParentDocumentLineReference` es **1..N** | confirmado |
| Código de validación | `cac:DocumentResponse/cac:Response/cbc:ResponseCode`: `02` validado, `04` rechazado | AAH03 en 6.5.5.1 ("Documento Validado por la DIAN") y 6.5.5.2 ("Documento Rechazado por la DIAN"); los códigos 030–034 son eventos | confirmado |
| CUFE validado | `cac:DocumentResponse/cac:DocumentReference/cbc:UUID` | AAH07 | confirmado |
| Tipos de documento soporte | `05` (Invoice) y `95` (CreditNote) | DS 1.1, tabla 16.1.3 | confirmado |
| CUDS | `cbc:UUID`, `@schemeName` `CUDS-SHA384` | DS 1.1, DSAD06/DSAD08 | confirmado |
| Vendedor y comprador en documento soporte | Vendedor en `AccountingSupplierParty`, adquiriente en `AccountingCustomerParty` | DS 1.1, DSAJ21 "NIT del vendedor", DSAK21 "Id del adquiriente"; en 1.1 se eliminó `PartyLegalEntity` del vendedor | confirmado |
| Referencia de la nota de ajuste | `cac:BillingReference/cac:InvoiceDocumentReference` (`cbc:ID`, `cbc:UUID`, `cbc:IssueDate`) | DS 1.1, NSBG01–NSBG06 (1..1) | confirmado |
| Retenciones en documento soporte | `cac:WithholdingTaxTotal` | DS 1.1, DSAT01: autorretenciones (p. ej. ReteIVA a no residentes, ReteRenta) | confirmado |

## Hallazgos que cambian el diseño

1. **Las retenciones del XML son autorretenciones.** En la factura (FAT01) y en el documento soporte (DSAT01), `WithholdingTaxTotal` es para que el emisor autorretenedor declare lo que se autorretiene. No es la retención que practica el comprador. El informe `retenciones` (SPEC §7) debe presentarlas así.
2. **Moneda: el anexo se contradice.** La tabla de campos dice que FAD15 rechaza si `DocumentCurrencyCode` no es "COP", pero la regla de validación FAD15a solo exige un código ISO 4217 válido, y FAR04 contempla que el documento esté en COP y se informe otra divisa. FAR02 exige `SourceCurrencyCode` = COP. El fixture `factura_exportacion_02.xml` usa `Source=USD`, `Target=COP` (práctica de la versión 1.8). **Lo aclaran los XML de ejemplo de la Caja de Herramientas FE 1.9** (carpeta "Ejemplificaciones"): `SourceCurrencyCode` es siempre la moneda del documento. Un documento en USD trae `Source=USD`, `Target=COP` y `CalculationRate` = pesos por dólar (`Servicios.xml`, `DebitNote.xml`, `Exportacion.xml`). Un documento en COP puede informar otra divisa con `Source=COP`, `Target=USD` y la tasa (`Ejemplificacion cambio otra Moneda.xml`, FAR04). Como los informes no convierten (decisión 0006, regla 2) y agrupan por `moneda`, ninguno de los dos casos cambia una cifra; para convertir habría que mirar `Target`, no solo la tasa.
4. **Anticipos.** La regla FAU14 de la 1.9 calcula `PrepaidAmount` pero no lo resta: `PayableAmount = TaxInclusive − Allowance + Charge`, y el numeral 11.9.2 dice que desde la 1.8 los anticipos son informativos. Ocho ejemplos de la Caja de Herramientas, emitidos en 2019 con reglas anteriores, sí lo restan (`PayableAmount` = 1.000 menos). En un documento así, `total_pagar` sale neto del anticipo y los informes de compras lo suman neto. Ninguna factura real cargada trae anticipos.
3. **Un contenedor puede traer varias respuestas** (AE38 1..N). El parser ahora usa la respuesta cuyo CUFE coincide con el documento, e ignora (con advertencia) las demás.

## Pendiente

- ~~Conseguir la Caja de Herramientas y cotejar las tablas de códigos~~: *hecho el 2026-11-20*. Todo coincide salvo que faltaba el tipo `04`. Las listas `.gc` de la carpeta "Listas de valores" del mismo ZIP son de una versión anterior (por ejemplo, `06` aparece como "ReteFuente" y no están los tributos 30–36): se usaron las tablas `.xlsx` de "Anexo Tecnico/Tablas Referenciadas", que son las de la 1.9.
- ~~Confirmar la dirección de `PaymentExchangeRate`~~: *aclarado el 2026-11-20* con los ejemplos oficiales (hallazgo 2). Siguen sin aparecer facturas reales en otra moneda.
- Documento soporte (05/95): la Caja de Herramientas FE no trae ejemplos y no se encontró una caja de herramientas pública del anexo DS 1.1. Las pruebas usan los fixtures sintéticos.
