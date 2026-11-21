import os
import re
from pathlib import Path

import duckdb

VERSION_ESQUEMA = 3
ESQUEMA = Path(__file__).with_name("schema.sql")


class ErrorCliente(Exception):
    pass


def inicio() -> Path:
    return Path(os.environ.get("AUDITOR_DIAN_HOME") or Path.home() / ".auditor-dian")


def ruta_base(id_cliente: str) -> Path:
    return ruta_exacta(normalizar_id(id_cliente))


# Pesos del dígito de verificación del NIT (DIAN, módulo 11), del dígito de la derecha hacia la
# izquierda.
PESOS_DV = (3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71)


def digito_verificacion(nit: str) -> int:
    resto = sum(int(d) * p for d, p in zip(reversed(nit), PESOS_DV, strict=False)) % 11
    return resto if resto < 2 else 11 - resto


def normalizar_id(id_cliente: str) -> str:
    """NIT o cédula como lo escriba el usuario ("NIT 900.000.009-0", "9000000090", "C.C. 1.032
    456 789") a solo dígitos y sin dígito de verificación, que es como viene la identificación
    del adquirente en el XML. El DV se quita si va tras un guion, o si sobra por la cantidad de
    dígitos y es el correcto: un NIT de empresa tiene 9 dígitos y empieza por 8 o 9, y una
    cédula tiene a lo sumo 10. Si aun así queda en duda, se usa el cliente ya registrado."""
    texto = re.sub(r"[^0-9-]", "", id_cliente)
    if m := re.fullmatch(r"(.*[0-9])-([0-9])", texto):
        return m[1].replace("-", "")
    digitos = texto.replace("-", "")
    if not digitos:
        raise ErrorCliente(
            f"identificación inválida {id_cliente!r}: escriba el NIT o la cédula con sus números "
            "(por ejemplo 900.000.009-0 o 1032456789)"
        )
    con_dv = len(digitos) > 1 and int(digitos[-1]) == digito_verificacion(digitos[:-1])
    if con_dv and (len(digitos) == 11 or (len(digitos) == 10 and digitos[0] in "89")):
        return digitos[:-1]
    if con_dv and not ruta_exacta(digitos).exists() and ruta_exacta(digitos[:-1]).exists():
        return digitos[:-1]
    return digitos


def ruta_exacta(id_cliente: str) -> Path:
    """Base de una identificación ya limpia, como la del adquirente en el XML: sin interpretar."""
    return inicio() / "clientes" / id_cliente / "auditor.duckdb"


def crear_cliente(id_cliente: str, nombre: str) -> Path:
    id_cliente = normalizar_id(id_cliente)
    ruta = ruta_base(id_cliente)
    if not nombre.strip():
        raise ErrorCliente("el nombre del cliente no puede estar vacío")
    if ruta.exists():
        raise ErrorCliente(f"el cliente {id_cliente} ya existe en {ruta}")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    try:
        with duckdb.connect(str(ruta)) as con:
            con.execute(ESQUEMA.read_text(encoding="utf-8"))
            con.execute("INSERT INTO schema_version (version) VALUES (?)", [VERSION_ESQUEMA])
            con.execute("INSERT INTO cliente (id, nombre) VALUES (?, ?)", [id_cliente, nombre])
    except Exception:
        ruta.unlink(missing_ok=True)  # sin base a medio crear que bloquee el siguiente intento
        raise
    return ruta


def abrir(id_cliente: str, solo_lectura: bool = False) -> duckdb.DuckDBPyConnection:
    ruta = ruta_base(id_cliente)
    if not ruta.exists():
        raise ErrorCliente(
            f"no existe el cliente {id_cliente}; créelo con la herramienta crear_cliente o con "
            "`auditor clientes crear`"
        )
    con = duckdb.connect(str(ruta), read_only=solo_lectura)
    version = con.execute("SELECT max(version) FROM schema_version").fetchone()[0]
    if version != VERSION_ESQUEMA:
        con.close()
        raise ErrorCliente(
            f"la base de {id_cliente} tiene esquema versión {version}; "
            f"esta versión de auditor usa la {VERSION_ESQUEMA}. Cree el cliente de nuevo "
            "y vuelva a ingerir las facturas"
        )
    registrado = con.execute("SELECT id FROM cliente").fetchone()[0]
    if registrado != ruta.parent.name:  # base copiada o renombrada en la carpeta de otro cliente
        con.close()
        raise ErrorCliente(
            f"la base de la carpeta {ruta.parent.name} pertenece al cliente {registrado}: no se "
            "usa para no mezclar la información de dos clientes"
        )
    return con
