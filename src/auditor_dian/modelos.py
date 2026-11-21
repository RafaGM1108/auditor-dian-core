from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal


@dataclass(frozen=True)
class Advertencia:
    codigo: str  # p. ej. "campo_faltante", "valor_invalido"
    detalle: str


@dataclass(frozen=True)
class Tributo:
    """Un subtotal de impuesto (cac:TaxTotal) o de retención (cac:WithholdingTaxTotal)."""

    codigo: str | None  # 01 IVA, 04 INC, 03 ICA; 05 ReteIVA, 06 ReteRenta, 07 ReteICA
    tarifa: Decimal | None  # porcentaje; None en tributos por unidad (p. ej. bolsas)
    base: Decimal | None
    valor: Decimal | None


@dataclass(frozen=True)
class Parte:
    tipo_identificacion: str | None  # 31 NIT, 13 cédula, ...
    identificacion: str | None
    dv: str | None
    nombre: str | None


@dataclass(frozen=True)
class Referencia:
    """Documento que una nota corrige (cac:BillingReference)."""

    numero: str | None
    cufe: str | None
    fecha: date | None


@dataclass(frozen=True)
class Linea:
    numero: str | None
    descripcion: str | None
    cantidad: Decimal | None
    unidad: str | None
    valor_unitario: Decimal | None
    valor_total: Decimal | None
    impuestos: tuple[Tributo, ...]


@dataclass(frozen=True)
class Documento:
    tipo: str | None  # código DIAN: 01, 02, 03, 04, 91, 92 (FE 1.9 tabla 13.1.3); 05, 95 (DS 1.1)
    prefijo: str | None
    numero: str | None  # cbc:ID completo, con el prefijo incluido como lo emite el facturador
    cufe: str | None  # CUFE, CUDE o CUDS según el tipo
    esquema_cufe: str | None  # atributo schemeName de cbc:UUID, p. ej. "CUFE-SHA384"
    fecha_emision: date | None
    hora_emision: time | None  # conserva la zona horaria del XML
    fecha_vencimiento: date | None
    forma_pago: str | None  # cac:PaymentMeans/cbc:ID (FAN02): 1 contado, 2 crédito
    # cbc:PaymentMeansCode (FAN03) de cada cac:PaymentMeans, que es 1..N (FAN01): 10 efectivo,
    # 48 tarjeta crédito, 49 tarjeta débito... (FE 1.9 tabla 13.3.4.2)
    medios_pago: tuple[str, ...]
    moneda: str | None
    trm: Decimal | None
    emisor: Parte
    adquirente: Parte
    subtotal: Decimal | None  # LineExtensionAmount
    base_gravable: Decimal | None  # TaxExclusiveAmount
    total_impuestos_incluidos: Decimal | None  # TaxInclusiveAmount: subtotal + impuestos
    descuentos: Decimal | None  # AllowanceTotalAmount: descuentos globales
    cargos: Decimal | None  # ChargeTotalAmount: cargos globales
    anticipos: Decimal | None  # PrepaidAmount
    redondeo: Decimal | None  # PayableRoundingAmount: único monto que puede ser negativo
    total_pagar: Decimal | None  # PayableAmount
    referencias: tuple[Referencia, ...]  # una nota puede corregir varias facturas
    impuestos: tuple[Tributo, ...]
    retenciones: tuple[Tributo, ...]
    lineas: tuple[Linea, ...]
    advertencias: tuple[Advertencia, ...]
    validado_dian: bool | None = None  # None = desconocido; lo fija el AttachedDocument


@dataclass(frozen=True)
class Lectura:
    ruta: str  # archivo tal como llegó (el .zip o el .xml)
    sha256: str  # del archivo tal como llegó: es la llave de idempotencia de la ingesta
    miembro: str | None  # nombre del XML dentro del ZIP; None si es un XML suelto
    documento: Documento | None
    error: str | None  # por qué no hay documento
