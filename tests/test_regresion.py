"""Pruebas de regresion: el nucleo debe dar EXACTAMENTE lo mismo que el estudio.

Los valores esperados (tests/esperado/) salieron del repositorio de investigacion
reto-CIMAT (commit 53dd56b). Las imagenes de prueba estan en datos_prueba/, que NO
se versiona (son datos de BraTS): ver docs/INICIO_SESION.md para conseguirlas. Si
faltan, las pruebas que las necesitan se saltan.

    pytest
"""

import hashlib
import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import pytest

from nucleo import ErrorEntrada, analizar
from nucleo.config import ARTEFACTOS
from nucleo.segmentacion import posprocesar_et

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "datos_prueba"
ESPERADO = json.loads((Path(__file__).parent / "esperado" / "esperado.json").read_text())
requiere_datos = pytest.mark.skipif(not DATOS.exists(), reason="faltan datos_prueba/ (ver docs/INICIO_SESION.md)")

PID = "Brats18_CBICA_AAP_1"            # HGG con supervivencia
SIN_ET = "Brats18_2013_25_1"           # HGG cuyo ET predicho descarto el posprocesado


def test_artefactos_integros():
    for linea in (ARTEFACTOS / "SHA256SUMS").read_text().splitlines():
        suma, nombre = linea.split()
        assert hashlib.sha256((ARTEFACTOS / nombre).read_bytes()).hexdigest() == suma, nombre


@requiere_datos
def test_mismas_caracteristicas_y_riesgo(tmp_path):
    e = ESPERADO[PID]
    r = analizar(DATOS / PID, edad=e["edad"], segmentacion=DATOS / PID / "segmentacion.nii.gz", salida=tmp_path)
    nuevo = pd.read_csv(r.archivos["caracteristicas.csv"]).iloc[0]
    ref = pd.read_csv(Path(__file__).parent / "esperado" / f"caracteristicas_{PID}.csv") \
        .set_index("paciente_id").loc[PID]
    assert list(nuevo.index) == list(ref.index)                      # mismas 1146 columnas, mismo orden
    np.testing.assert_allclose(nuevo.to_numpy(float), ref.to_numpy(float), rtol=1e-9, atol=1e-12)
    assert r.pronostico["aplica"]
    assert r.pronostico["riesgo"] == pytest.approx(e["riesgo"], abs=1e-6)
    assert r.pronostico["dias_mediana_estimada"] == pytest.approx(e["dias"], abs=1)
    assert r.volumen_cm3 == e["volumen_cm3"]


@requiere_datos
def test_sin_edad_no_hay_pronostico(tmp_path):
    r = analizar(DATOS / PID, segmentacion=DATOS / PID / "segmentacion.nii.gz", salida=tmp_path)
    assert not r.pronostico["aplica"] and "edad" in r.pronostico["motivo"]
    assert len(r.pronostico["solo_referencia_segun_edad (NO es una prediccion)"]) == 5


@requiere_datos
def test_sin_et_no_hay_pronostico(tmp_path):
    r = analizar(DATOS / SIN_ET, edad=60, segmentacion=DATOS / SIN_ET / "segmentacion.nii.gz", salida=tmp_path)
    assert r.estado_regiones["ET"] == ESPERADO[SIN_ET]["estado_ET"]
    assert not r.pronostico["aplica"] and "ET" in r.pronostico["motivo"]


@requiere_datos
def test_posprocesado_identico_al_estudio():
    for pid, e in ESPERADO["posprocesado"].items():
        s = np.asanyarray(nib.load(DATOS / "nnunet_crudo" / f"{pid}.nii.gz").dataobj)
        mascara, info = posprocesar_et(s)
        assert info["voxeles_et_predichos"] == e["voxeles_et"], pid
        assert info["et_descartado"] == e["descartado"], pid
        assert hashlib.sha256(np.ascontiguousarray(mascara).tobytes()).hexdigest() == e["sha256_mascara_brats"], pid


def test_errores_de_entrada(tmp_path):
    with pytest.raises(ErrorEntrada, match="no existe"):
        analizar(tmp_path / "no_existe")
    (tmp_path / "T1_axial.nii").write_bytes(b"")
    with pytest.raises(ErrorEntrada, match="Deben llamarse"):
        analizar(tmp_path)
