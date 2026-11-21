"""Parámetros comunes de las herramientas MCP con la descripción que lee el agente. Sin el SDK
de MCP: los plugins los usan al declarar sus herramientas."""

from datetime import date
from typing import Annotated

from pydantic import Field

Cliente = Annotated[
    str,
    Field(
        description="NIT o cédula del cliente, tal como lo escriba el usuario: con puntos, "
        "espacios, guion, 'NIT' o 'C.C.', con o sin dígito de verificación. Si lo nombra por su "
        "razón social, búsquelo antes con listar_clientes."
    ),
]
Desde = Annotated[
    date,
    Field(
        description="Primer día del periodo, AAAA-MM-DD, incluido. Se filtra por fecha de "
        "emisión. Bimestre 1 = enero y febrero; 'el año pasado' = 1 de enero a 31 de diciembre."
    ),
]
Hasta = Annotated[date, Field(description="Último día del periodo, AAAA-MM-DD, incluido.")]
Anio = Annotated[
    int,
    Field(
        description="Año gravable, p. ej. 2025. La declaración que se presenta en 2026 es la "
        "del año gravable 2025."
    ),
]
