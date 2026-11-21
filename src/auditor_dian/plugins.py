"""Extensiones (SPEC §8): plugins instalados con entry points del grupo `auditor_dian.plugins`.

Un plugin declara en su `pyproject.toml`:

    [project.entry-points."auditor_dian.plugins"]
    mi_plugin = "mi_paquete:register"

y `register(app)` recibe un `App`, que es todo lo que un plugin puede tocar. `core` funciona
completo sin plugins; un plugin que falla al cargar se reporta y se salta. La interfaz es mínima
a propósito: ampliarla solo cuando `pro` lo necesite de verdad.
"""

import sys
from collections.abc import Callable
from importlib.metadata import entry_points

import anyio
import duckdb

from auditor_dian import base, informes, ubl
from auditor_dian.modelos import Documento

GRUPO = "auditor_dian.plugins"


class App:
    """Puntos de extensión que `core` ofrece a un plugin."""

    def herramienta(self, funcion: Callable, titulo: str | None = None) -> Callable:
        """Registra `funcion` como herramienta MCP de solo lectura, con su nombre y docstring.
        `titulo` es el nombre legible que muestra Claude Desktop. El docstring dice qué hace y
        cuándo usarla con frases del usuario, y cada parámetro lleva su descripción (los tipos
        de `auditor_dian.parametros` ya la traen). Debe abrir la base con `app.abrir` y devolver
        el aviso de `auditor_dian.servidor.AVISO`."""
        from auditor_dian.servidor import (  # el SDK de MCP, solo si hace falta
            LECTURA,
            descripcion,
            nombres_invalidos,
            servidor,
        )

        existentes = {h.name for h in anyio.run(servidor.list_tools)}
        if funcion.__name__ in existentes:
            raise ValueError(f"ya existe la herramienta MCP {funcion.__name__!r}")
        texto = descripcion(funcion.__doc__ or "")
        servidor.tool(title=titulo, description=texto, annotations=LECTURA)(funcion)
        (registrada,) = [h for h in anyio.run(servidor.list_tools) if h.name == funcion.__name__]
        if malos := nombres_invalidos(registrada.name, registrada.input_schema):
            servidor.remove_tool(funcion.__name__)
            raise ValueError(
                f"herramienta {funcion.__name__!r}: la API de Claude no acepta los nombres {malos}"
                " (solo letras ASCII, dígitos, '_', '-' y '.'; p. ej. 'anio', no 'año')"
            )
        return funcion

    def informe(self, nombre: str, nota: str, detalle_sql: str, resumen_sql: str) -> None:
        """Registra un informe: el detalle lee de `docs` y el resumen de `detalle`."""
        informes.registrar(nombre, nota, detalle_sql, resumen_sql)

    def lector(self, raiz: str, leer: Callable[..., Documento]) -> None:
        """Registra `leer(elemento_raiz) -> Documento` para una raíz XML que core no conoce,
        en notación `{espacio de nombres}Nombre`."""
        ubl.registrar_lector(raiz, leer)

    def abrir(self, id_cliente: str, escritura: bool = False) -> duckdb.DuckDBPyConnection:
        """Base del cliente (úsela con `with`). Por defecto en solo lectura, para las herramientas
        MCP del plugin: si el cliente no existe, el agente recibe el motivo y no un error genérico.
        `escritura=True` es solo para comandos de carga del plugin, nunca para una herramienta MCP
        (el servidor es de solo lectura). El plugin escribe solo en sus tablas, con prefijo propio,
        y nunca en las de core."""
        if escritura:
            return base.abrir(id_cliente)
        from auditor_dian.servidor import abrir_cliente

        return abrir_cliente(id_cliente)


_cargados: list[str] | None = None


def cargar() -> list[str]:
    """Carga una sola vez los plugins instalados; devuelve los nombres de los que cargaron.
    Se llama antes de arrancar el servidor MCP, fuera de un bucle asíncrono."""
    global _cargados
    if _cargados is None:
        _cargados = []
        for entrada in entry_points(group=GRUPO):
            try:
                entrada.load()(App())
            except Exception as error:  # un plugin roto no debe dejar a core inservible
                print(f"Aviso: no se cargó el plugin {entrada.name!r}: {error}", file=sys.stderr)
            else:
                _cargados.append(entrada.name)
    return _cargados
