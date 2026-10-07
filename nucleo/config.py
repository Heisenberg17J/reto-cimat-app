"""Constantes y rutas de los artefactos.

Los artefactos (YAML de PyRadiomics, modelo de pronostico y umbral de ET) son copias
fijas del repositorio de investigacion; ver artefactos/PROCEDENCIA.md. Sus rutas se
pueden cambiar con variables de entorno, util para el backend o un contenedor.
"""

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARTEFACTOS = Path(os.environ.get("NUCLEO_ARTEFACTOS", RAIZ / "artefactos"))

PARAMS = ARTEFACTOS / "params_brats2018_v0.yaml"
MODELO_PRONOSTICO = ARTEFACTOS / "pronostico_coxnet.joblib"
POSPROCESO = ARTEFACTOS / "postproceso_et.json"
# Pesos de nnU-Net: no van en git (pesan ~1 GB); ver README
MODELO_NNUNET = Path(os.environ.get(
    "NUCLEO_NNUNET",
    ARTEFACTOS / "nnunet" / "Dataset501_BraTS2018" / "nnUNetTrainer_100epochs_ckpt5__nnUNetPlans__3d_fullres"))

MODALIDADES = ["t1", "t1ce", "t2", "flair"]           # orden de canales de nnU-Net (0000..0003)
REGIONES = {"WT": (1, 2, 4), "TC": (1, 4), "ET": (4,)}  # etiquetas BraTS de cada region
MODALIDAD_FORMA = "t1"                                  # imagen que se pasa a PyRadiomics para shape

CLASES = {0: "corta (< 300 dias, < 10 meses)",
          1: "media (300-450 dias, 10-15 meses)",
          2: "larga (> 450 dias, > 15 meses)"}

AVISO = ("PROTOTIPO DE INVESTIGACION. No es una herramienta clinica ni sustituye el criterio "
         "medico. El pronostico depende casi solo de la edad.")
