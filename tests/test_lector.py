import hashlib
import zipfile

from fabrica import contenedor, fixture, respuesta_dian

from auditor_dian.lector import LIMITE_XML, leer_ruta


def _zip(ruta, miembros: dict[str, bytes]):
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as zf:
        for nombre, datos in miembros.items():
            zf.writestr(nombre, datos)
    return ruta


def _sha(ruta) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def test_zip_con_varios_xml_ignora_pdf_y_metadatos_de_macos(tmp_path):
    zip_ = _zip(
        tmp_path / "correo.zip",
        {
            "FV1001.xml": contenedor(fixture("factura_01.xml"), respuesta_dian()),
            "NC55.XML": fixture("nota_credito_91.xml").encode(),
            "FV1001.pdf": b"%PDF-1.4 no es XML",
            "__MACOSX/._FV1001.xml": b"\x00\x05\x16\x07",
        },
    )

    lecturas = list(leer_ruta(zip_))

    assert [(lec.miembro, lec.documento.numero, lec.error) for lec in lecturas] == [
        ("FV1001.xml", "FV1001", None),
        ("NC55.XML", "NC55", None),
    ]
    assert {lec.sha256 for lec in lecturas} == {_sha(zip_)}
    assert lecturas[0].documento.validado_dian is True


def test_carpeta_recursiva_ordenada_y_errores_no_detienen_el_recorrido(tmp_path):
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "nd.xml").write_text(fixture("nota_debito_92.xml"), encoding="utf-8")
    (tmp_path / "a_mal.xml").write_bytes(b"<Invoice><sin cerrar>")
    (tmp_path / "c_otro.xml").write_bytes(b"<Catalogo/>")
    (tmp_path / "d_roto.zip").write_bytes(b"no es un zip")
    _zip(tmp_path / "e_solo_pdf.zip", {"FV.pdf": b"%PDF"})
    (tmp_path / "notas.txt").write_text("se ignora")

    lecturas = list(leer_ruta(tmp_path))

    nombres = [lec.ruta.removeprefix(str(tmp_path) + "/") for lec in lecturas]
    assert nombres == ["a_mal.xml", "b/nd.xml", "c_otro.xml", "d_roto.zip", "e_solo_pdf.zip"]
    assert lecturas[0].error.startswith("XML mal formado")
    assert lecturas[1].documento.tipo == "92"
    assert lecturas[1].miembro is None
    assert lecturas[1].sha256 == _sha(tmp_path / "b" / "nd.xml")
    assert lecturas[2].error.startswith("raíz no soportada")
    assert lecturas[3].error == "ZIP inválido"
    assert lecturas[4].error == "ZIP sin XML"


def test_xml_descomprimido_demasiado_grande_se_rechaza_sin_leerlo_completo(tmp_path):
    zip_ = _zip(tmp_path / "bomba.zip", {"grande.xml": b" " * (LIMITE_XML + 1)})

    [lectura] = leer_ruta(zip_)

    assert lectura.documento is None
    assert lectura.error == "XML demasiado grande"


def test_archivo_demasiado_grande_conserva_su_sha256(tmp_path, monkeypatch):
    monkeypatch.setattr("auditor_dian.lector.LIMITE_XML", 10)
    grande = tmp_path / "grande.xml"
    grande.write_bytes(b"<Invoice>" + b" " * 10 + b"</Invoice>")

    [lectura] = leer_ruta(grande)

    assert lectura.error == "archivo demasiado grande"
    assert lectura.sha256 == _sha(grande)


def test_miembro_corrupto_del_zip_da_error_y_sigue_con_los_demas(tmp_path):
    zip_ = tmp_path / "corrupto.zip"
    with zipfile.ZipFile(zip_, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("a.xml", fixture("nota_debito_92.xml"))
        zf.writestr("b.xml", fixture("nota_credito_91.xml"))
    datos = zip_.read_bytes()
    i = datos.index(b"ND7")  # daña un byte del primer XML: falla la verificación CRC
    zip_.write_bytes(datos[:i] + b"XX7" + datos[i + 3 :])

    lecturas = list(leer_ruta(zip_))

    assert lecturas[0].error.startswith("no se pudo descomprimir")
    assert lecturas[1].documento.numero == "NC55"
