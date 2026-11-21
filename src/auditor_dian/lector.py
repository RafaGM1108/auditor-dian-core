import hashlib
import io
import zipfile
from collections.abc import Iterator
from pathlib import Path

from lxml import etree

from auditor_dian.contenedor import leer_xml
from auditor_dian.modelos import Lectura
from auditor_dian.ubl import DocumentoNoSoportado

LIMITE_XML = 20 * 1024 * 1024  # una factura real pesa KB; más que esto es sospechoso (zip bomb)
LIMITE_ZIP = 10 * LIMITE_XML


def leer_ruta(ruta: Path) -> Iterator[Lectura]:
    if ruta.is_dir():
        archivos = sorted(
            p for p in ruta.rglob("*") if p.is_file() and p.suffix.lower() in (".xml", ".zip")
        )
        for archivo in archivos:
            yield from leer_archivo(archivo)
    else:
        yield from leer_archivo(ruta)


def leer_archivo(ruta: Path) -> Iterator[Lectura]:
    es_zip = ruta.suffix.lower() == ".zip"
    if ruta.stat().st_size > (LIMITE_ZIP if es_zip else LIMITE_XML):
        with ruta.open("rb") as f:  # hash por bloques: no se carga a memoria
            sha = hashlib.file_digest(f, "sha256").hexdigest()
        yield Lectura(str(ruta), sha, None, None, "archivo demasiado grande")
        return
    datos = ruta.read_bytes()
    sha = hashlib.sha256(datos).hexdigest()
    if not es_zip:
        yield _leer(str(ruta), sha, None, datos)
        return
    try:
        zf = zipfile.ZipFile(io.BytesIO(datos))
    except zipfile.BadZipFile:
        yield Lectura(str(ruta), sha, None, None, "ZIP inválido")
        return
    miembros = [
        info
        for info in zf.infolist()
        # __MACOSX/ son metadatos que agrega el compresor de macOS, no documentos.
        if not info.is_dir()
        and info.filename.lower().endswith(".xml")
        and not info.filename.startswith("__MACOSX/")
    ]
    if not miembros:
        yield Lectura(str(ruta), sha, None, None, "ZIP sin XML")
    for info in miembros:
        try:
            with zf.open(info) as f:
                # Se lee con tope: el tamaño que declara el encabezado del ZIP puede mentir.
                xml = f.read(LIMITE_XML + 1)
        except (zipfile.BadZipFile, RuntimeError, OSError) as error:
            yield Lectura(str(ruta), sha, info.filename, None, f"no se pudo descomprimir: {error}")
            continue
        if len(xml) > LIMITE_XML:
            yield Lectura(str(ruta), sha, info.filename, None, "XML demasiado grande")
            continue
        yield _leer(str(ruta), sha, info.filename, xml)


def _leer(ruta: str, sha: str, miembro: str | None, xml: bytes) -> Lectura:
    try:
        return Lectura(ruta, sha, miembro, leer_xml(xml), None)
    except etree.XMLSyntaxError as error:
        return Lectura(ruta, sha, miembro, None, f"XML mal formado: {error}")
    except DocumentoNoSoportado as error:
        return Lectura(ruta, sha, miembro, None, str(error))
