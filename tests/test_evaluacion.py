"""Pruebas de la validacion contra una segmentacion de referencia (nucleo/evaluacion.py).

Las sinteticas no necesitan datos. La de fidelidad al estudio usa datos_prueba/ (no
versionado): la prediccion cruda de nnU-Net, posprocesada y comparada con la mascara
manual, debe dar exactamente la fila de metricas_segmentacion_oof.csv del estudio.

    pytest tests/test_evaluacion.py
"""

from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import pytest

from nucleo import analizar
from nucleo.config import METRICAS_OOF
from nucleo.evaluacion import HD_VACIO, caso_del_estudio, comparar, mapa_diferencias, ubicar_en_estudio
from nucleo.segmentacion import posprocesar_et

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "datos_prueba"
requiere_datos = pytest.mark.skipif(not (DATOS / "Brats18_CBICA_AAP_1" / "referencia.nii.gz").exists(),
                                    reason="faltan datos_prueba/ con referencia.nii.gz (ver docs/INICIO_SESION.md)")


def _cubo(desde, lado=10, forma=(40, 40, 40), etiqueta=4):
    m = np.zeros(forma, np.uint8)
    x, y, z = desde
    m[x:x + lado, y:y + lado, z:z + lado] = etiqueta
    return m


def test_identicas():
    m = _cubo((10, 10, 10))
    for v in comparar(m, m).values():
        assert v["dice"] == 1.0 and v["hd95_mm"] == 0.0 and v["sensibilidad"] == 1.0


def test_vacias_las_dos_y_una_sola():
    vacia, m = np.zeros((40, 40, 40), np.uint8), _cubo((10, 10, 10), etiqueta=2)   # solo edema: TC y ET vacios
    r = comparar(m, m)
    assert r["ET"]["dice"] == 1.0 and r["ET"]["hd95_mm"] == 0.0 and r["ET"]["sensibilidad"] is None
    r = comparar(vacia, m)
    assert r["WT"]["dice"] == 0.0 and r["WT"]["hd95_mm"] == HD_VACIO


def test_desplazado():
    a, b = _cubo((10, 10, 10)), _cubo((12, 10, 10))
    r = comparar(a, b)["ET"]
    assert r["dice"] == pytest.approx(2 * 800 / 2000)
    assert r["hd95_mm"] == pytest.approx(2.0)
    assert comparar(a, b, voxel=(2, 1, 1))["ET"]["hd95_mm"] == pytest.approx(4.0)   # respeta el voxel


def test_mapa_diferencias():
    d = mapa_diferencias(_cubo((10, 10, 10)), _cubo((12, 10, 10)))
    assert (d == 1).sum() == 800 and (d == 2).sum() == 200 and (d == 3).sum() == 200


def test_ubicar_en_estudio():
    perfecto = {r: {"dice": 1.0, "hd95_mm": 0.0} for r in ("WT", "TC", "ET")}
    u = ubicar_en_estudio(perfecto, "Brats18_CBICA_AAP_1")
    assert u["n_pacientes"] == 285
    for v in u["regiones"].values():
        assert v["percentil_dice"] == 100.0 and v["percentil_hd95"] == 100.0
        assert sum(v["histograma_dice"]) == 285
    assert u["fila_del_paciente"]["WT"]["dice"] == pytest.approx(0.9548144897859685)


def test_caso_del_estudio():
    assert caso_del_estudio([None, "Brats18_CBICA_AAP_1"]) == {"paciente_id": "Brats18_CBICA_AAP_1", "fold": 0,
                                                              "grupo": "HGG_superv"}
    assert caso_del_estudio(["UPENN-GBM-00001_11"]) is None


@requiere_datos
@pytest.mark.parametrize("pid", ["Brats18_CBICA_AAP_1", "Brats18_2013_25_1"])
def test_metricas_identicas_al_estudio(pid):
    crudo = DATOS / "nnunet_crudo" / f"{pid}.nii.gz"
    if crudo.exists():
        pred, _ = posprocesar_et(np.asanyarray(nib.load(crudo).dataobj))
    else:                                   # la mascara del ejemplo ya es la final fuera de fold
        pred = np.asanyarray(nib.load(DATOS / pid / "segmentacion.nii.gz").dataobj)
    ref = np.asanyarray(nib.load(DATOS / pid / "referencia.nii.gz").dataobj)
    esperado = pd.read_csv(METRICAS_OOF).set_index(["paciente_id", "region"])
    for region, v in comparar(pred, ref).items():
        e = esperado.loc[(pid, region)]
        assert v["dice"] == pytest.approx(e["dice"], abs=1e-9), region
        assert v["hd95_mm"] == pytest.approx(e["hd95_mm"], abs=1e-9), region
        assert v["especificidad"] == pytest.approx(e["especificidad"], abs=1e-9), region
        assert (v["voxeles_pred"], v["voxeles_ref"]) == (e["voxeles_pred"], e["voxeles_real"]), region


@requiere_datos
def test_analizar_con_referencia(tmp_path):
    pid = "Brats18_CBICA_AAP_1"
    r = analizar(DATOS / pid, edad=39.068, segmentacion=DATOS / pid / "segmentacion.nii.gz",
                 referencia=DATOS / pid / "referencia.nii.gz", salida=tmp_path)
    ev = r.evaluacion
    assert ev["metricas"]["WT"]["dice"] == pytest.approx(0.9548144897859685, abs=1e-9)
    assert ev["caso_del_estudio"]["fold"] == 0
    assert ev["estudio"]["fila_del_paciente"]["ET"]["dice"] == pytest.approx(ev["metricas"]["ET"]["dice"])
    assert ev["pronostico_ref"]["aplica"]
    assert ev["volumen_ref_cm3"]["WT"] == pytest.approx(103.5, abs=0.01)
    for n in ("referencia.nii.gz", "diferencias.nii.gz", "comparacion.png"):
        assert Path(r.archivos[n]).is_file(), n
