"""Nucleo de analisis del reto CIMAT / BraTS 2018: segmentacion + radiomica + pronostico.

PROTOTIPO DE INVESTIGACION, NO ES UNA HERRAMIENTA CLINICA.

    from nucleo import analizar
    resultado = analizar("carpeta_con_4_resonancias", edad=62, segmentacion="seg.nii.gz")
"""

__version__ = "0.1.0"

from .analisis import ETAPAS, Resultado, analizar  # noqa: E402,F401
from .entrada import ErrorEntrada  # noqa: E402,F401
