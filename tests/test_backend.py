"""Pruebas del backend FastAPI (Fase 2).

El contrato clave: el resultado que devuelve la API debe ser el mismo que el de
`nucleo.analizar()`, es decir, los numeros que protegen las pruebas de regresion. Las
que necesitan imagenes usan datos_prueba/ (no versionado); si falta, se saltan.

    pytest tests/test_backend.py
"""

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import crear_app

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "datos_prueba"
ESPERADO = json.loads((Path(__file__).parent / "esperado" / "esperado.json").read_text())
requiere_datos = pytest.mark.skipif(not DATOS.exists(), reason="faltan datos_prueba/ (ver docs/INICIO_SESION.md)")

PID = "Brats18_CBICA_AAP_1"
MODALIDADES = ("t1", "t1ce", "t2", "flair")


@pytest.fixture
def cliente(tmp_path):
    with TestClient(crear_app(raiz_datos=tmp_path / "datos")) as c:
        yield c


def _archivos_paciente():
    """Las 4 resonancias como subidas multipart (campo 'archivos')."""
    return [("archivos", (f"{m}.nii.gz", (DATOS / PID / f"{m}.nii.gz").read_bytes(), "application/gzip"))
            for m in MODALIDADES]


def _esperar(cliente, id, limite=300):
    """Sondea hasta que la tarea termina o falla; devuelve el estado final."""
    fin = time.time() + limite
    while time.time() < fin:
        e = cliente.get(f"/api/analisis/{id}").json()
        if e["estado"] in ("terminado", "error"):
            return e
        time.sleep(0.5)
    pytest.fail("la tarea no termino a tiempo")


def test_salud(cliente):
    r = cliente.get("/api/salud")
    assert r.status_code == 200
    assert "PROTOTIPO" in r.json()["aviso"]


def test_estado_desconocido(cliente):
    assert cliente.get("/api/analisis/noexiste").status_code == 404


def test_borrar_desconocido(cliente):
    assert cliente.delete("/api/analisis/noexiste").status_code == 404


def test_estado_pesos(cliente):
    r = cliente.get("/api/pesos")
    assert r.status_code == 200
    info = r.json()
    assert "instalados" in info and "descarga" in info and "carpeta" in info


def test_edad_fuera_de_rango(cliente):
    # Se valida antes de mirar los archivos: basta una subida cualquiera.
    r = cliente.post("/api/analisis",
                     files=[("archivos", ("t1.nii.gz", b"x", "application/gzip"))],
                     data={"edad": "200"})
    assert r.status_code == 400
    assert "edad" in r.json()["detail"]


def test_faltan_resonancias(cliente):
    r = cliente.post("/api/analisis",
                     files=[("archivos", ("cualquier.txt", b"x", "text/plain"))])
    assert r.status_code == 400
    assert "t1" in r.json()["detail"]


@requiere_datos
def test_analisis_igual_que_el_nucleo(cliente):
    esp = ESPERADO[PID]
    seg = [("segmentacion", ("segmentacion.nii.gz",
                             (DATOS / PID / "segmentacion.nii.gz").read_bytes(), "application/gzip"))]
    r = cliente.post("/api/analisis", files=_archivos_paciente() + seg,
                     data={"edad": str(esp["edad"])})
    assert r.status_code == 202
    id = r.json()["id"]

    e = _esperar(cliente, id)
    assert e["estado"] == "terminado", e.get("error")
    res = e["resultado"]

    # Mismos numeros que protege la regresion del nucleo.
    assert res["volumen_cm3"] == esp["volumen_cm3"]
    assert res["pronostico"]["aplica"]
    assert res["pronostico"]["riesgo"] == pytest.approx(esp["riesgo"], abs=1e-6)
    assert res["pronostico"]["dias_mediana_estimada"] == pytest.approx(esp["dias"], abs=1)
    assert "larga" in res["pronostico"]["clase"]

    # Los archivos se pueden descargar, incluida una resonancia para el visor.
    for nombre in ("resultado.json", "segmentacion.nii.gz", "vista.png", "caracteristicas.csv"):
        assert cliente.get(f"/api/analisis/{id}/archivo/{nombre}").status_code == 200, nombre
    assert cliente.get(f"/api/analisis/{id}/archivo/flair.nii.gz").status_code == 200
    assert cliente.get(f"/api/analisis/{id}/archivo/no_permitido.exe").status_code == 404

    # Borrar deja de encontrarlo.
    assert cliente.delete(f"/api/analisis/{id}").status_code == 204
    assert cliente.get(f"/api/analisis/{id}").status_code == 404


@requiere_datos
def test_sin_edad_no_hay_pronostico(cliente):
    seg = [("segmentacion", ("segmentacion.nii.gz",
                             (DATOS / PID / "segmentacion.nii.gz").read_bytes(), "application/gzip"))]
    r = cliente.post("/api/analisis", files=_archivos_paciente() + seg)
    id = r.json()["id"]
    e = _esperar(cliente, id)
    assert e["estado"] == "terminado", e.get("error")
    assert not e["resultado"]["pronostico"]["aplica"]
    assert "edad" in e["resultado"]["pronostico"]["motivo"]


def _zip_brats_con_seg():
    """Carpeta BraTS tal cual en un .zip: <id>_<modalidad>.nii.gz + <id>_seg.nii.gz (la del radiólogo)."""
    import io
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for m in MODALIDADES:
            z.write(DATOS / PID / f"{m}.nii.gz", f"{PID}/{PID}_{m}.nii.gz")
        z.write(DATOS / PID / "referencia.nii.gz", f"{PID}/{PID}_seg.nii.gz")
    return buf.getvalue()


requiere_referencia = pytest.mark.skipif(not (DATOS / PID / "referencia.nii.gz").exists(),
                                         reason="falta datos_prueba/<caso>/referencia.nii.gz")


@requiere_referencia
def test_zip_con_seg_se_usa_como_referencia(cliente):
    # La _seg del zip NO reemplaza al modelo: aqui el modelo es la segmentacion subida aparte.
    seg = [("segmentacion", ("segmentacion.nii.gz",
                             (DATOS / PID / "segmentacion.nii.gz").read_bytes(), "application/gzip"))]
    r = cliente.post("/api/analisis", files=[("archivos", ("caso.zip", _zip_brats_con_seg(), "application/zip"))]
                     + seg, data={"edad": "39.068"})
    assert r.status_code == 202, r.text
    e = _esperar(cliente, r.json()["id"])
    assert e["estado"] == "terminado", e.get("error")
    res = e["resultado"]
    assert res["volumen_cm3"] == ESPERADO[PID]["volumen_cm3"]           # el modelo sigue siendo el modelo
    ev = res["evaluacion"]
    assert ev["metricas"]["WT"]["dice"] == pytest.approx(0.9548144897859685, abs=1e-9)
    assert ev["caso_del_estudio"]["paciente_id"] == PID                  # reconocido por el nombre del zip
    for n in ("referencia.nii.gz", "diferencias.nii.gz", "comparacion.png"):
        assert n in e["archivos"], n
        assert cliente.get(e["archivos"][n]).status_code == 200, n


@requiere_referencia
def test_ejemplo_con_referencia(cliente, monkeypatch):
    monkeypatch.setenv("NUCLEO_EJEMPLOS", str(DATOS))
    ej = {x["id"]: x for x in cliente.get("/api/ejemplos").json()}
    assert ej[PID]["tiene_referencia"]
    e = _esperar(cliente, cliente.post(f"/api/ejemplos/{PID}").json()["id"])
    assert e["estado"] == "terminado", e.get("error")
    assert e["resultado"]["evaluacion"]["estudio"]["fila_del_paciente"] is not None


@requiere_datos
def test_sin_referencia_no_hay_evaluacion(cliente):
    seg = [("segmentacion", ("segmentacion.nii.gz",
                             (DATOS / PID / "segmentacion.nii.gz").read_bytes(), "application/gzip"))]
    e = _esperar(cliente, cliente.post("/api/analisis", files=_archivos_paciente() + seg).json()["id"])
    assert e["estado"] == "terminado", e.get("error")
    assert e["resultado"]["evaluacion"] is None
    assert "comparacion.png" not in e["archivos"]
