"""Carpeta de datos del usuario y registro de errores a un archivo (para soporte).

La carpeta de datos (por defecto ~/.reto-cimat, o NUCLEO_DATOS) guarda el registro y, más
adelante, resultados y pesos. El registro rota para no crecer sin límite.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

log = logging.getLogger("reto_cimat")


def carpeta_datos():
    d = Path(os.environ.get("NUCLEO_DATOS", Path.home() / ".reto-cimat"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def configurar_registro():
    """Escribe el registro en <carpeta_datos>/reto-cimat.log. Idempotente."""
    log.setLevel(logging.INFO)
    archivo = carpeta_datos() / "reto-cimat.log"
    if any(isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", "") == str(archivo)
           for h in log.handlers):
        return archivo  # ya configurado
    manejador = RotatingFileHandler(archivo, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    manejador.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(manejador)
    log.info("registro iniciado en %s", archivo)
    return archivo
