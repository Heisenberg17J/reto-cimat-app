"""Validacion de la segmentacion del modelo contra una de referencia (radiologo).

Las metricas son las oficiales de BraTS 2018 (Bakas et al. 2018, arXiv:1811.02629) y se
calculan igual que en el estudio (segmentacion/metricas_segmentacion.py, D28): Dice,
Hausdorff 95 (mm), sensibilidad y especificidad para WT, TC y ET. Convencion para regiones
vacias, como la herramienta de BraTS: si no hay region ni real ni predicha, Dice = 1 y
HD95 = 0; si falta en una sola, Dice = 0 y HD95 = 373.13 mm (diagonal de 240 x 240 x 155).

`ubicar_en_estudio` compara el caso con las 285 predicciones fuera de fold del estudio.
"""

from functools import lru_cache

import numpy as np
import pandas as pd
from scipy import ndimage

from .config import FOLDS, METRICAS_OOF, REGIONES

HD_VACIO = 373.13
BORDES_DICE = np.round(np.linspace(0, 1, 21), 2)       # histograma de Dice en pasos de 0.05

DIF_ACUERDO, DIF_SOLO_MODELO, DIF_SOLO_REFERENCIA = 1, 2, 3


def superficie(m):
    return m & ~ndimage.binary_erosion(m)


def hd95(a, b, voxel=(1.0, 1.0, 1.0)):
    """Hausdorff 95 simetrico entre dos mascaras no vacias, en mm."""
    # Recorte a la caja que contiene a las dos, con margen, para acelerar
    idx = np.argwhere(a | b)
    lo, hi = np.maximum(idx.min(0) - 2, 0), idx.max(0) + 3
    caja = tuple(slice(l, h) for l, h in zip(lo, hi))
    a, b = a[caja], b[caja]
    sa, sb = superficie(a), superficie(b)
    d_a = ndimage.distance_transform_edt(~sb, sampling=voxel)[sa]     # superficie de a -> superficie de b
    d_b = ndimage.distance_transform_edt(~sa, sampling=voxel)[sb]
    return float(max(np.percentile(d_a, 95), np.percentile(d_b, 95)))


def comparar(pred, ref, voxel=(1.0, 1.0, 1.0)):
    """{region: {dice, hd95_mm, sensibilidad, especificidad, voxeles_pred, voxeles_ref}}.

    pred y ref en etiquetas BraTS (0/1/2/4) y con la misma forma.
    """
    pred, ref = np.asarray(pred), np.asarray(ref)
    if pred.shape != ref.shape:
        raise ValueError(f"formas distintas: {pred.shape} y {ref.shape}")
    voxel = tuple(float(v) for v in voxel)
    salida = {}
    for region, etiquetas in REGIONES.items():
        mp, mr = np.isin(pred, etiquetas), np.isin(ref, etiquetas)
        tp, n_p, n_r = int((mp & mr).sum()), int(mp.sum()), int(mr.sum())
        if n_p == 0 and n_r == 0:
            dice, hd = 1.0, 0.0
        elif n_p == 0 or n_r == 0:
            dice, hd = 0.0, HD_VACIO
        else:
            dice, hd = 2 * tp / (n_p + n_r), hd95(mp, mr, voxel)
        salida[region] = {"dice": dice, "hd95_mm": hd,
                          "sensibilidad": tp / n_r if n_r else None,
                          "especificidad": float(((~mp) & (~mr)).sum() / (~mr).sum()),
                          "voxeles_pred": n_p, "voxeles_ref": n_r}
    return salida


def mapa_diferencias(pred, ref):
    """Tumor completo (WT): 1 acuerdo, 2 solo el modelo, 3 solo la referencia; 0 fuera de los dos."""
    mp, mr = np.isin(pred, REGIONES["WT"]), np.isin(ref, REGIONES["WT"])
    return np.select([mp & mr, mp & ~mr, ~mp & mr],
                     [DIF_ACUERDO, DIF_SOLO_MODELO, DIF_SOLO_REFERENCIA], 0).astype(np.uint8)


@lru_cache(maxsize=1)
def tabla_estudio():
    return pd.read_csv(METRICAS_OOF)


@lru_cache(maxsize=1)
def tabla_folds():
    return pd.read_csv(FOLDS).set_index("paciente_id")


def caso_del_estudio(candidatos):
    """Si algun nombre es un paciente de BraTS 2018 del estudio: {paciente_id, fold, grupo}; si no, None."""
    folds = tabla_folds()
    for nombre in candidatos:
        if nombre and nombre in folds.index:
            fila = folds.loc[nombre]
            return {"paciente_id": nombre, "fold": int(fila["fold"]), "grupo": str(fila["grupo"])}
    return None


def ubicar_en_estudio(metricas, paciente_id=None):
    """Situa el caso entre las 285 predicciones fuera de fold del estudio, region por region.

    percentil_dice:  % del estudio con Dice <= el del caso (mas alto, mejor)
    percentil_hd95:  % del estudio con HD95 >= el del caso (mas alto, mejor)
    """
    t = tabla_estudio()
    salida = {"n_pacientes": int(t["paciente_id"].nunique()), "bordes_dice": BORDES_DICE.tolist(),
              "regiones": {}, "fila_del_paciente": None}
    for region, m in metricas.items():
        x = t[t["region"] == region]
        conteo, _ = np.histogram(x["dice"].clip(0, 1), bins=BORDES_DICE)
        salida["regiones"][region] = {
            "dice_mediana": float(x["dice"].median()), "dice_media": float(x["dice"].mean()),
            "hd95_mediana": float(x["hd95_mm"].median()),
            "percentil_dice": float(100 * (x["dice"] <= m["dice"]).mean()),
            "percentil_hd95": float(100 * (x["hd95_mm"] >= m["hd95_mm"]).mean()),
            "histograma_dice": conteo.tolist()}
    if paciente_id is not None:
        propia = t[t["paciente_id"] == paciente_id]
        if len(propia):
            salida["fila_del_paciente"] = {
                r["region"]: {"dice": float(r["dice"]), "hd95_mm": float(r["hd95_mm"])}
                for _, r in propia.iterrows()}
    return salida
