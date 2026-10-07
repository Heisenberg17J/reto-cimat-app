"""Gestor de analisis en segundo plano.

Una tarea a la vez: la CPU no da para mas (segmentar tarda minutos), asi que las demas
esperan en una cola. Cada analisis vive en su carpeta (entrada/ + salida/); al cerrar el
gestor se borran todas. El avance (etapa, fraccion) lo reporta `nucleo.analizar` por su
callback `progreso`.
"""

import logging
import queue
import shutil
import tempfile
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from nucleo import ErrorEntrada, analizar

log = logging.getLogger("reto_cimat")


@dataclass
class Tarea:
    """Estado de un analisis. Los campos que lee la API se exponen con `estado_publico`."""

    id: str
    carpeta: Path
    estado: str = "en_cola"          # en_cola -> procesando -> terminado | error
    etapa: str | None = None         # entrada, segmentacion, radiomica, pronostico, salida
    fraccion: float = 0.0
    error: str | None = None
    es_error_entrada: bool = False   # True: culpa de la entrada (mensaje para el usuario)
    resultado: dict | None = None    # resultado.json (res.a_dict()), sin rutas absolutas
    edad: float | None = None
    segmentacion: Path | None = None
    folds: tuple = (0, 1, 2, 3, 4)   # qué modelos de nnU-Net usar (modo rápido: solo uno)

    @property
    def entrada(self) -> Path:
        return self.carpeta / "entrada"

    @property
    def salida(self) -> Path:
        return self.carpeta / "salida"

    def estado_publico(self) -> dict:
        d = {"id": self.id, "estado": self.estado, "etapa": self.etapa,
             "fraccion": round(self.fraccion, 3)}
        if self.estado == "error":
            d["error"] = self.error
            d["es_error_entrada"] = self.es_error_entrada
        elif self.estado == "terminado":
            d["resultado"] = self.resultado
            d["archivos"] = {n: f"/api/analisis/{self.id}/archivo/{n}"
                             for n in sorted(ARCHIVOS_SALIDA) if (self.salida / n).is_file()}
        return d


ARCHIVOS_SALIDA = ("caracteristicas.csv", "resultado.json", "segmentacion.nii.gz", "vista.png")


class GestorTareas:
    """Cola de analisis con un unico trabajador en segundo plano."""

    def __init__(self, raiz=None):
        self.raiz = Path(raiz) if raiz else Path(tempfile.mkdtemp(prefix="reto_backend_"))
        self.raiz.mkdir(parents=True, exist_ok=True)
        self._tareas: dict[str, Tarea] = {}
        self._cola: queue.Queue[str] = queue.Queue()
        self._lock = threading.Lock()
        self._hilo = threading.Thread(target=self._trabajar, name="analisis", daemon=True)
        self._hilo.start()

    def crear(self) -> Tarea:
        """Reserva una tarea y su carpeta; aun no la encola."""
        tid = uuid.uuid4().hex[:12]
        carpeta = self.raiz / tid
        (carpeta / "entrada").mkdir(parents=True)
        (carpeta / "salida").mkdir(parents=True)
        tarea = Tarea(id=tid, carpeta=carpeta)
        with self._lock:
            self._tareas[tid] = tarea
        return tarea

    def encolar(self, tarea: Tarea, edad=None, segmentacion=None, folds=(0, 1, 2, 3, 4)):
        tarea.edad = edad
        tarea.segmentacion = segmentacion
        tarea.folds = tuple(folds)
        self._cola.put(tarea.id)

    def obtener(self, tid) -> Tarea | None:
        with self._lock:
            return self._tareas.get(tid)

    def borrar(self, tid) -> bool:
        with self._lock:
            tarea = self._tareas.pop(tid, None)
        if tarea is None:
            return False
        shutil.rmtree(tarea.carpeta, ignore_errors=True)
        return True

    def cerrar(self):
        """Borra todos los temporales. Se llama al apagar el servidor."""
        with self._lock:
            self._tareas.clear()
        shutil.rmtree(self.raiz, ignore_errors=True)

    def _trabajar(self):
        while True:
            tid = self._cola.get()
            try:
                tarea = self.obtener(tid)
                if tarea is None:          # borrada antes de empezar
                    continue
                self._procesar(tarea)
            finally:
                self._cola.task_done()

    def _procesar(self, tarea: Tarea):
        tarea.estado = "procesando"
        log.info("analisis %s: inicio (edad=%s, folds=%s, segmentacion_externa=%s)",
                 tarea.id, tarea.edad, list(tarea.folds), tarea.segmentacion is not None)

        def progreso(etapa, fraccion):
            tarea.etapa = etapa
            tarea.fraccion = float(fraccion)

        try:
            r = analizar(tarea.entrada, edad=tarea.edad, segmentacion=tarea.segmentacion,
                         folds=tarea.folds, salida=tarea.salida, progreso=progreso)
            tarea.resultado = _sin_rutas(r.a_dict(), tarea.id)
            tarea.fraccion = 1.0
            tarea.estado = "terminado"
            log.info("analisis %s: terminado", tarea.id)
        except ErrorEntrada as e:
            tarea.estado, tarea.error, tarea.es_error_entrada = "error", str(e), True
            log.warning("analisis %s: error de entrada: %s", tarea.id, e)
        except Exception as e:  # noqa: BLE001  (cualquier fallo del nucleo se informa, no tumba el hilo)
            tarea.estado, tarea.error, tarea.es_error_entrada = "error", f"error inesperado: {e}", False
            log.exception("analisis %s: error inesperado", tarea.id)


def _sin_rutas(resultado: dict, tid: str) -> dict:
    """Reemplaza las rutas absolutas de 'archivos' por URLs de descarga de la API."""
    resultado = dict(resultado)
    resultado["archivos"] = {n: f"/api/analisis/{tid}/archivo/{n}"
                             for n in resultado.get("archivos", {})}
    return resultado
