"""La aplicacion FastAPI: endpoints que envuelven `nucleo.analizar()`.

    POST   /api/analisis               sube resonancias (sueltas o .zip) + edad + segmentacion -> {id}
    GET    /api/analisis/{id}          estado, etapa, avance, error o resultado
    GET    /api/analisis/{id}/archivo/{nombre}   segmentacion, resonancias, vista.png, resultado.json
    DELETE /api/analisis/{id}          borra los archivos del analisis
    GET    /api/salud                  comprobacion y aviso "no clinico"

El frontend compilado (Fase 3) o la pagina minima de `estatico/` se sirven en /.
"""

import json
import os
import shutil
import sys
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from nucleo import ErrorEntrada, __version__
from nucleo.config import AVISO, MODALIDADES
from nucleo.entrada import buscar_modalidades

from .pesos import GestorPesos
from .registro import configurar_registro
from .tareas import ARCHIVOS_SALIDA, GestorTareas

AQUI = Path(__file__).resolve().parent
MODALIDADES_NII = {f"{m}.nii.gz": m for m in MODALIDADES}   # para el visor
TROZO = 1024 * 1024


async def _guardar_subida(subida: UploadFile, destino: Path):
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "wb") as f:
        while trozo := await subida.read(TROZO):
            f.write(trozo)


async def _recibir(subida: UploadFile, entrada: Path):
    """Guarda una subida en `entrada`. Si es un .zip, extrae solo los .nii(.gz), aplanados."""
    nombre = Path(subida.filename or "archivo").name
    if nombre.lower().endswith(".zip"):
        tmp = entrada.parent / nombre
        await _guardar_subida(subida, tmp)
        try:
            with zipfile.ZipFile(tmp) as z:
                for miembro in z.namelist():
                    base = Path(miembro).name
                    if base and (base.lower().endswith(".nii") or base.lower().endswith(".nii.gz")):
                        (entrada / base).write_bytes(z.read(miembro))   # aplanado: evita zip-slip
        finally:
            tmp.unlink(missing_ok=True)
    else:
        await _guardar_subida(subida, entrada / nombre)


def carpeta_ejemplos() -> Path | None:
    """Carpeta con casos de ejemplo (imágenes BraTS); NO se distribuye (licencia).

    Orden: NUCLEO_EJEMPLOS, 'ejemplos/' junto al .exe (app congelada), o datos_prueba/ (desarrollo).
    """
    candidatos = []
    if os.environ.get("NUCLEO_EJEMPLOS"):
        candidatos.append(Path(os.environ["NUCLEO_EJEMPLOS"]))
    if getattr(sys, "frozen", False):
        candidatos.append(Path(sys.executable).resolve().parent / "ejemplos")
    candidatos.append(AQUI.parent / "datos_prueba")
    for c in candidatos:
        if c.is_dir():
            return c
    return None


def listar_ejemplos() -> list[dict]:
    """Casos disponibles (carpetas con las 4 resonancias). Metadatos opcionales en ejemplos.json."""
    base = carpeta_ejemplos()
    if base is None:
        return []
    meta = {}
    if (base / "ejemplos.json").is_file():
        try:
            meta = json.loads((base / "ejemplos.json").read_text())
        except (ValueError, OSError):
            meta = {}
    salida = []
    for sub in sorted(p for p in base.iterdir() if p.is_dir()):
        try:
            buscar_modalidades(sub)
        except ErrorEntrada:
            continue
        m = meta.get(sub.name, {})
        salida.append({"id": sub.name, "nombre": m.get("nombre", sub.name), "edad": m.get("edad"),
                       "tiene_segmentacion": (sub / "segmentacion.nii.gz").is_file()})
    return salida


def crear_app(raiz_datos=None) -> FastAPI:
    configurar_registro()
    gestor = GestorTareas(raiz_datos)
    gestor_pesos = GestorPesos()

    @asynccontextmanager
    async def ciclo(app: FastAPI):
        yield
        gestor.cerrar()      # borra todos los temporales al apagar

    app = FastAPI(title="reto-cimat-app (backend)", version=__version__, lifespan=ciclo)
    app.state.gestor = gestor

    @app.get("/api/salud")
    def salud():
        return {"estado": "ok", "version_nucleo": __version__, "aviso": AVISO}

    @app.get("/api/pesos")
    def estado_pesos():
        """¿Están los pesos de nnU-Net? ¿Se pueden descargar? ¿Progreso de la descarga?"""
        return gestor_pesos.info()

    @app.post("/api/pesos/descargar", status_code=202)
    def descargar_pesos():
        gestor_pesos.iniciar()
        return gestor_pesos.info()

    @app.get("/api/ejemplos")
    def ejemplos():
        """Casos de ejemplo disponibles en el equipo (vacío si no hay ninguno)."""
        return listar_ejemplos()

    @app.post("/api/ejemplos/{id}", status_code=202)
    def analizar_ejemplo(id: str):
        base = carpeta_ejemplos()
        caso = base / Path(id).name if base else None   # Path(id).name: anti path traversal
        if caso is None or not caso.is_dir():
            raise HTTPException(404, "ejemplo no encontrado")
        try:
            rutas = buscar_modalidades(caso)
        except ErrorEntrada as e:
            raise HTTPException(400, str(e))

        info = next((e for e in listar_ejemplos() if e["id"] == caso.name), {})
        tarea = gestor.crear()
        for m, p in rutas.items():
            shutil.copy(p, tarea.entrada / f"{m}.nii.gz")
        seg_path = None
        seg = caso / "segmentacion.nii.gz"
        if seg.is_file():                      # usar la segmentación del ejemplo: demo rápida
            seg_path = tarea.carpeta / "segmentacion_entrada.nii.gz"
            shutil.copy(seg, seg_path)
        gestor.encolar(tarea, edad=info.get("edad"), segmentacion=seg_path, folds=(0,))
        return {"id": tarea.id}

    @app.post("/api/analisis", status_code=202)
    async def crear_analisis(
        archivos: list[UploadFile] = File(..., description="4 resonancias (sueltas o en un .zip)"),
        edad: float | None = Form(None),
        segmentacion: UploadFile | None = File(None),
        modo: str = Form("rapido", description="rapido (1 fold, ~2 min) o completo (5 folds, ~12 min)"),
    ):
        if edad is not None and not (0 < edad < 120):
            raise HTTPException(400, f"edad fuera de rango: {edad}")
        folds = (0,) if modo == "rapido" else (0, 1, 2, 3, 4)

        tarea = gestor.crear()
        for subida in archivos:
            await _recibir(subida, tarea.entrada)
        seg_path = None
        if segmentacion is not None and segmentacion.filename:
            seg_path = tarea.carpeta / "segmentacion_entrada.nii.gz"
            await _guardar_subida(segmentacion, seg_path)

        try:                              # validacion rapida: feedback inmediato si faltan resonancias
            buscar_modalidades(tarea.entrada)
        except ErrorEntrada as e:
            gestor.borrar(tarea.id)
            raise HTTPException(400, str(e))

        gestor.encolar(tarea, edad=edad, segmentacion=seg_path, folds=folds)
        return {"id": tarea.id}

    @app.get("/api/analisis/{id}")
    def estado_analisis(id: str):
        tarea = gestor.obtener(id)
        if tarea is None:
            raise HTTPException(404, "analisis no encontrado")
        return tarea.estado_publico()

    @app.get("/api/analisis/{id}/archivo/{nombre}")
    def descargar(id: str, nombre: str):
        tarea = gestor.obtener(id)
        if tarea is None:
            raise HTTPException(404, "analisis no encontrado")
        nombre = Path(nombre).name        # anti path traversal
        if nombre in ARCHIVOS_SALIDA:
            ruta = tarea.salida / nombre
        elif nombre in MODALIDADES_NII:
            try:
                ruta = buscar_modalidades(tarea.entrada)[MODALIDADES_NII[nombre]]
            except ErrorEntrada:
                raise HTTPException(404, "resonancia no disponible")
        else:
            raise HTTPException(404, "archivo no permitido")
        if not ruta.is_file():
            raise HTTPException(404, "archivo aun no disponible")
        return FileResponse(ruta)

    @app.delete("/api/analisis/{id}", status_code=204)
    def borrar_analisis(id: str):
        if not gestor.borrar(id):
            raise HTTPException(404, "analisis no encontrado")

    # Frontend: el compilado (Fase 3) tiene prioridad; si no, la pagina minima de estatico/.
    dist = AQUI.parent / "frontend" / "dist"
    web = dist if dist.is_dir() else AQUI / "estatico"
    if web.is_dir():
        app.mount("/", StaticFiles(directory=web, html=True), name="web")

    return app
