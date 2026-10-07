"""Runtime hook: apunta el nucleo a los artefactos empaquetados.

Se ejecuta ANTES de importar el nucleo, asi que `nucleo.config` toma esta ruta. Los
artefactos (YAML, modelo .joblib, umbral) viajan dentro del paquete (ver el .spec) y en
tiempo de ejecucion viven en sys._MEIPASS. Si el usuario fija NUCLEO_ARTEFACTOS a mano,
se respeta (setdefault).
"""

import os
import sys

_base = getattr(sys, "_MEIPASS", None)
if _base:
    os.environ.setdefault("NUCLEO_ARTEFACTOS", os.path.join(_base, "artefactos"))
