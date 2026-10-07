"""Localizar y validar las 4 resonancias de un paciente."""

from pathlib import Path

import nibabel as nib
import numpy as np

from .config import MODALIDADES


class ErrorEntrada(ValueError):
    """La entrada no se puede procesar; el mensaje explica por que (pensado para mostrarse al usuario)."""


def buscar_modalidades(carpeta):
    """Devuelve {modalidad: ruta}. Acepta t1.nii.gz o <id>_t1.nii.gz, sin confundir t1 con t1ce,
    y busca tambien un nivel mas abajo (carpeta de BraTS subida tal cual)."""
    carpeta = Path(carpeta)
    if not carpeta.is_dir():
        raise ErrorEntrada(f"{carpeta} no existe o no es una carpeta. Debe contener las 4 resonancias "
                           f"del paciente (t1, t1ce, t2 y flair).")
    archivos = list(carpeta.glob("*.nii*")) + list(carpeta.glob("*/*.nii*"))
    rutas = {}
    for mod in MODALIDADES:
        candidatos = [f for f in archivos
                      if f.name.split(".")[0] == mod or f.name.split(".")[0].endswith(f"_{mod}")]
        if len(candidatos) != 1:
            vistos = [str(f.relative_to(carpeta)) for f in archivos] or "ninguno"
            raise ErrorEntrada(f"hay {len(candidatos)} archivos para '{mod}' (se espera 1). "
                               f"Archivos .nii encontrados: {vistos}. Deben llamarse {mod}.nii.gz "
                               f"o <id>_{mod}.nii.gz")
        rutas[mod] = candidatos[0]
    return rutas


def validar_formato(rutas):
    """Lista de avisos si las imagenes no parecen formato BraTS. No detiene el analisis."""
    imgs = {m: nib.load(p) for m, p in rutas.items()}
    ref, avisos = imgs["t1"], []
    for m, im in imgs.items():
        if im.shape != ref.shape or not np.allclose(im.affine, ref.affine, atol=1e-3):
            avisos.append(f"{m}: forma o geometria distinta de t1 (no co-registradas)")
    if ref.shape != (240, 240, 155):
        avisos.append(f"tamano {ref.shape}; BraTS usa (240, 240, 155)")
    if not np.allclose(ref.header.get_zooms()[:3], 1, atol=1e-2):
        avisos.append(f"voxel {tuple(round(float(z), 2) for z in ref.header.get_zooms()[:3])} mm; BraTS usa 1 mm")
    fondo = float((np.asanyarray(ref.dataobj) == 0).mean())
    if fondo < 0.5:
        avisos.append(f"solo {fondo:.0%} de fondo en 0: probablemente conserva el craneo")
    return avisos
