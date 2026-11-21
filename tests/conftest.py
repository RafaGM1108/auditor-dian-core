import pytest


@pytest.fixture(autouse=True)
def inicio_temporal(tmp_path, monkeypatch):
    """Ninguna prueba escribe en el ~/.auditor-dian real."""
    monkeypatch.setenv("AUDITOR_DIAN_HOME", str(tmp_path / "auditor-dian"))
    return tmp_path / "auditor-dian"
