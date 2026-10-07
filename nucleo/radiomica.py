"""Radiomica: el mismo procesamiento que los bloques 3-5 del estudio.

z-score sobre el cerebro (D2) -> mascaras WT/TC/ET (D3, D4) -> PyRadiomics con el
YAML del estudio, forma una vez por region (D6) y nombres <mod>_<region>_<clase>_<nombre> (D13).
"""

import logging
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import yaml

from .config import MODALIDAD_FORMA, MODALIDADES, PARAMS, REGIONES

for _ruidoso in ("radiomics", "pykwalify"):
    logging.getLogger(_ruidoso).setLevel(logging.ERROR)


def zscore(data):
    """Z-score con media y desviacion de los voxeles > 0 (cerebro); el fondo queda en 0."""
    mascara = data > 0
    valores = data[mascara]
    if valores.size == 0:
        raise ValueError("la imagen no tiene voxeles > 0")
    mu, sigma = float(valores.mean()), float(valores.std())
    if sigma == 0:
        raise ValueError("sigma = 0 dentro del cerebro")
    normalizado = np.zeros_like(data, dtype=np.float32)
    normalizado[mascara] = (valores - mu) / sigma
    return normalizado


def leer_umbrales(params=PARAMS):
    with open(params) as f:
        setting = yaml.safe_load(f).get("setting", {})
    return int(setting.get("minimumROISize", 1)), int(setting.get("minimumROIDimensions", 2))


def estado_region(mascara, min_voxeles, min_dims):
    """Clasifica la mascara igual que PyRadiomics, pero sin excepcion: (voxeles, dims, estado)."""
    n = int(mascara.sum())
    if n == 0:
        return n, 0, "vacia"
    idx = np.argwhere(mascara)
    dims = int(((idx.max(axis=0) - idx.min(axis=0) + 1) > 1).sum())
    if n < min_voxeles or dims < min_dims:
        return n, dims, "pequena"
    return n, dims, "ok"


def crear_extractores(params=PARAMS):
    """(extractor de forma, extractor de intensidad) a partir del mismo YAML."""
    import radiomics
    from radiomics import featureextractor
    radiomics.setVerbosity(logging.ERROR)

    forma = featureextractor.RadiomicsFeatureExtractor(str(params))
    forma.disableAllFeatures()
    forma.enableFeatureClassByName("shape")
    intensidad = featureextractor.RadiomicsFeatureExtractor(str(params))
    intensidad.enabledFeatures.pop("shape", None)
    return forma, intensidad


def nombre_columna(clave, modalidad, region):
    """'original_glcm_Contrast' -> 't1ce_ET_glcm_Contrast' (forma: 'mask_WT_shape_...')."""
    filtro, clase, nombre = clave.split("_", 2)
    if filtro != "original":
        clase = f"{filtro}-{clase}"
    return f"{modalidad or 'mask'}_{region}_{clase}_{nombre}"


def volumenes(seg):
    """cm3 de cada region (voxel de 1 mm3)."""
    return {r: int(np.isin(seg, e).sum()) / 1000 for r, e in REGIONES.items()}


def extraer_caracteristicas(rutas, seg, img_ref, trabajo, progreso=None):
    """Devuelve (caracteristicas, estado de cada region). trabajo: carpeta temporal."""
    trabajo = Path(trabajo)
    norm = {}
    for mod in MODALIDADES:
        img = nib.load(rutas[mod])
        nueva = nib.Nifti1Image(zscore(img.get_fdata()), img.affine, img.header)
        nueva.set_data_dtype(np.float32)
        norm[mod] = trabajo / f"norm_{mod}.nii.gz"
        nib.save(nueva, norm[mod])

    umbrales = leer_umbrales()
    tareas, estados = [], {}
    for region, etiquetas in REGIONES.items():
        mascara = np.isin(seg, etiquetas)
        estados[region] = estado_region(mascara, *umbrales)[2]
        if estados[region] != "ok":
            continue
        ruta = trabajo / f"mask_{region}.nii.gz"
        m_img = nib.Nifti1Image(mascara.astype(np.uint8), img_ref.affine, img_ref.header)
        m_img.set_data_dtype(np.uint8)
        nib.save(m_img, ruta)
        tareas.append(("forma", None, region, norm[MODALIDAD_FORMA], ruta))
        tareas += [("intensidad", mod, region, norm[mod], ruta) for mod in MODALIDADES]

    forma, intensidad = crear_extractores()
    extractores = {"forma": forma, "intensidad": intensidad}
    caract = {}
    for i, (tipo, mod, region, imagen, mascara) in enumerate(tareas, 1):
        res = extractores[tipo].execute(str(imagen), str(mascara))
        for clave, valor in res.items():
            if not clave.startswith("diagnostics_"):
                caract[nombre_columna(clave, mod, region)] = float(valor)
        if progreso:
            progreso("radiomica", i / len(tareas))
    return caract, estados


def tabla_caracteristicas(caract):
    return pd.DataFrame([caract])
