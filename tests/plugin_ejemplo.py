"""Plugin de ejemplo (SPEC §8, M5): usa los cuatro puntos de extensión de `App`.

Un plugin real se instala como paquete con, en su pyproject.toml:

    [project.entry-points."auditor_dian.plugins"]
    ejemplo = "plugin_ejemplo:register"
"""

from datetime import date
from decimal import Decimal

from auditor_dian.modelos import Documento, Parte
from auditor_dian.servidor import AVISO

TIQUETE = "{urn:ejemplo:tiquete}Tiquete"  # raíz inventada para el ejemplo, no es un tipo DIAN

DETALLE = """
    SELECT tipo, numero, cufe, moneda, signo * total_pagar AS total
    FROM docs
    ORDER BY tipo, numero
"""
RESUMEN = """
    SELECT tipo, moneda, count(*) AS documentos, sum(total) AS total
    FROM detalle
    GROUP BY ALL
    ORDER BY tipo, moneda
"""


def register(app) -> None:
    app.informe("compras_por_tipo", "Totales por tipo de documento.", DETALLE, RESUMEN)
    app.lector(TIQUETE, leer_tiquete)

    @app.herramienta
    def contar_documentos(cliente: str) -> dict:
        """Cuántos documentos tiene guardados el cliente."""
        with app.abrir(cliente) as con:
            total = con.execute("SELECT count(*) FROM documentos").fetchone()[0]
        return {"aviso": AVISO, "documentos": total}


def roto(app) -> None:
    raise RuntimeError("falta configuración")


def leer_tiquete(raiz) -> Documento:
    def texto(nombre: str) -> str:
        return raiz.findtext(f"{{urn:ejemplo:tiquete}}{nombre}")

    def parte(nombre: str) -> Parte:
        return Parte("31", texto(nombre), None, None)

    total = Decimal(texto("Total"))  # un Total no numérico hace fallar el lector a propósito
    return Documento(
        tipo="ejemplo",
        prefijo=None,
        numero=texto("ID"),
        cufe=texto("UUID"),
        esquema_cufe=None,
        fecha_emision=date.fromisoformat(texto("Fecha")),
        hora_emision=None,
        fecha_vencimiento=None,
        forma_pago="1",
        medios_pago=("10",),
        moneda="COP",
        trm=None,
        emisor=parte("Emisor"),
        adquirente=parte("Adquirente"),
        subtotal=total,
        base_gravable=None,
        total_impuestos_incluidos=total,
        descuentos=None,
        cargos=None,
        anticipos=None,
        redondeo=None,
        total_pagar=total,
        referencias=(),
        impuestos=(),
        retenciones=(),
        lineas=(),
        advertencias=(),
    )
