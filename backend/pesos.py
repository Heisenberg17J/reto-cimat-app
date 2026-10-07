"""Gestión de los pesos de nnU-Net: estado y descarga en el primer arranque.

Los pesos (~550 MB) no viajan en la app; se descargan una vez (GitHub Releases, Fase 5),
se verifican con sha256 y se extraen en la carpeta que lee el núcleo (`MODELO_NNUNET`).
Mientras no haya publicación, `url` del manifiesto está vacía y se copian a mano; se puede
probar la descarga definiendo la variable de entorno NUCLEO_PESOS_URL.
"""

import hashlib
import json
import logging
import os
import shutil
import tempfile
import threading
import urllib.request
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path

from nucleo.config import MODELO_NNUNET

log = logging.getLogger("reto_cimat")
AQUI = Path(__file__).resolve().parent
MANIFIESTO = json.loads((AQUI / "pesos_manifiesto.json").read_text())

# Archivos que deben existir bajo MODELO_NNUNET para considerar los pesos instalados.
ARCHIVOS = ["plans.json", "dataset.json", "dataset_fingerprint.json"] + \
           [f"fold_{i}/checkpoint_final.pth" for i in range(5)]


def _url():
    return os.environ.get("NUCLEO_PESOS_URL") or MANIFIESTO.get("url") or ""


def faltantes():
    return [a for a in ARCHIVOS if not (MODELO_NNUNET / a).exists()]


def _sha256(ruta, trozo=1024 * 1024):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while bloque := f.read(trozo):
            h.update(bloque)
    return h.hexdigest()


@dataclass
class EstadoDescarga:
    estado: str = "inactivo"      # inactivo|descargando|verificando|extrayendo|terminado|error
    fraccion: float = 0.0
    mensaje: str = ""
    error: str | None = None


class GestorPesos:
    """Descarga los pesos una vez, en segundo plano, con progreso. Un solo trabajo a la vez."""

    def __init__(self):
        self.estado = EstadoDescarga(estado="terminado" if not faltantes() else "inactivo")
        self._hilo = None
        self._lock = threading.Lock()

    def en_curso(self):
        return self._hilo is not None and self._hilo.is_alive()

    def info(self):
        return {
            "instalados": not faltantes(),
            "faltan": faltantes(),
            "carpeta": str(MODELO_NNUNET),
            "descarga_disponible": bool(_url()),
            "tamano_mb": round(MANIFIESTO.get("tamano_bytes", 0) / 1e6),
            "descarga": asdict(self.estado),
        }

    def iniciar(self):
        with self._lock:
            if self.en_curso():
                return
            if not faltantes():
                self.estado = EstadoDescarga(estado="terminado", fraccion=1.0, mensaje="ya instalados")
                return
            url = _url()
            if not url:
                self.estado = EstadoDescarga(
                    estado="error",
                    error="no hay URL de descarga configurada todavía; copia los pesos a mano "
                          "(ver docs/INICIO_SESION.md) o define NUCLEO_PESOS_URL.")
                return
            self.estado = EstadoDescarga(estado="descargando", mensaje="descargando…")
            self._hilo = threading.Thread(target=self._trabajo, args=(url,), name="pesos", daemon=True)
            self._hilo.start()

    def _trabajo(self, url):
        destino = MODELO_NNUNET.parent.parent     # p. ej. artefactos/nnunet/
        tmp = Path(tempfile.mkdtemp(prefix="pesos_"))
        zip_path = tmp / MANIFIESTO["nombre"]
        try:
            log.info("pesos: descargando de %s", url)
            self._descargar(url, zip_path)

            self.estado.estado, self.estado.mensaje = "verificando", "verificando integridad…"
            esperado = MANIFIESTO.get("sha256")
            obtenido = _sha256(zip_path)
            if esperado and obtenido != esperado:
                raise ValueError(f"sha256 no coincide (esperado {esperado[:12]}…, obtenido {obtenido[:12]}…)")

            self.estado.estado, self.estado.mensaje = "extrayendo", "extrayendo…"
            destino.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path) as z:     # zip propio, ya verificado por sha256
                z.extractall(destino)
            falt = faltantes()
            if falt:
                raise ValueError(f"tras extraer siguen faltando archivos: {falt}")

            self.estado.estado, self.estado.fraccion, self.estado.mensaje = "terminado", 1.0, "listo"
            log.info("pesos: instalados en %s", destino)
        except Exception as e:  # noqa: BLE001
            self.estado.estado, self.estado.error = "error", str(e)
            log.exception("pesos: fallo la descarga/instalacion")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _descargar(self, url, destino):
        pet = urllib.request.Request(url, headers={"User-Agent": "reto-cimat-app"})
        with urllib.request.urlopen(pet) as r:  # noqa: S310 (url nuestra/configurada)
            total = int(r.headers.get("Content-Length") or MANIFIESTO.get("tamano_bytes") or 0)
            leido = 0
            with open(destino, "wb") as f:
                while trozo := r.read(256 * 1024):
                    f.write(trozo)
                    leido += len(trozo)
                    if total:
                        self.estado.fraccion = round(leido / total, 4)
