"""Punto de entrada: analizar un paciente de punta a punta.

    resultado = analizar("carpeta_con_4_resonancias", edad=62)
    resultado = analizar(rutas={"t1": ..., "t1ce": ..., "t2": ..., "flair": ...},
                         segmentacion="seg.nii.gz", progreso=lambda etapa, fraccion: ...)
    resultado = analizar("carpeta", edad=62, referencia="seg_radiologo.nii.gz")   # + validacion

Es lo que llamaran el backend y la linea de comandos. Lanza ErrorEntrada si la entrada
no se puede procesar (mensaje pensado para el usuario) y escribe en `salida`:
segmentacion.nii.gz, caracteristicas.csv, resultado.json y vista.png; con referencia,
ademas referencia.nii.gz, diferencias.nii.gz y comparacion.png.
"""

import json
import shutil
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import nibabel as nib
import numpy as np

from . import __version__
from .config import AVISO, MODALIDADES
from .entrada import ErrorEntrada, buscar_modalidades, validar_formato
from .evaluacion import caso_del_estudio, comparar, mapa_diferencias, ubicar_en_estudio
from .pronostico import pronosticar
from .radiomica import extraer_caracteristicas, tabla_caracteristicas, volumenes
from .segmentacion import nnunet_disponible, posprocesar_et, segmentar_nnunet, validar_segmentacion
from .vista import figura, figura_comparacion

ETAPAS = ("entrada", "segmentacion", "radiomica", "pronostico", "validacion", "salida")


@dataclass
class Resultado:
    aviso: str
    volumen_cm3: dict
    estado_regiones: dict
    pronostico: dict
    segmentacion: str
    avisos_formato: list
    edad: float | None
    archivos: dict = field(default_factory=dict)
    evaluacion: dict | None = None     # solo con segmentacion de referencia (radiologo)
    version_nucleo: str = __version__
    fecha: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def a_dict(self):
        return asdict(self)


def _avisar(progreso, etapa, fraccion=1.0):
    if progreso:
        progreso(etapa, float(fraccion))


def _guardar_mascara(datos, img_ref, destino):
    nueva = nib.Nifti1Image(np.asarray(datos).astype(np.uint8), img_ref.affine, img_ref.header)
    nueva.set_data_dtype(np.uint8)
    nib.save(nueva, destino)


def _leer_mascara(ruta, rutas, que):
    """Mascara BraTS (0/1/2/4) con la forma de las resonancias; devuelve (datos int16, imagen)."""
    if not Path(ruta).is_file():
        raise ErrorEntrada(f"no existe la {que}: {ruta}")
    img = nib.load(ruta)
    datos = np.asanyarray(img.dataobj).astype(np.int16)
    try:
        validar_segmentacion(datos)
    except ValueError as e:
        raise ErrorEntrada(f"{que}: {e}") from e
    if datos.shape != nib.load(rutas["t1"]).shape:
        raise ErrorEntrada(f"la {que} {datos.shape} no tiene la forma de las resonancias")
    return datos, img


def _nombres_del_caso(carpeta, rutas, id_caso):
    """Posibles identificadores del paciente: id explicito, carpeta y prefijo de los archivos."""
    nombres = [id_caso]
    if carpeta is not None:
        nombres.append(Path(carpeta).name)
    for m, p in rutas.items():
        base = Path(p).name.split(".")[0]
        if base.endswith(f"_{m}"):
            nombres.append(base[: -len(m) - 1])
    return nombres


def analizar(carpeta=None, *, rutas=None, edad=None, segmentacion=None, referencia=None, id_caso=None,
             salida=None, folds=(0, 1, 2, 3, 4), tta=None, progreso=None):
    """Analiza un paciente. Ver el docstring del modulo.

    carpeta / rutas   las 4 resonancias en formato BraTS (una de las dos)
    edad              en anos; sin ella no hay pronostico
    segmentacion      mascara ya hecha (etiquetas BraTS 0/1/2/4); sin ella se usa nnU-Net
    referencia        mascara del radiologo (BraTS 0/1/2/4): NO reemplaza a la del modelo, se compara con
                      ella (metricas de BraTS, ubicacion en el estudio y pronostico con las dos mascaras)
    id_caso           nombre del paciente; si es uno de BraTS 2018 del estudio, nnU-Net usa solo el fold
                      que no lo vio en el entrenamiento (se deduce tambien de la carpeta o los archivos)
    salida            carpeta de resultados (por defecto, una temporal que devuelve en archivos)
    progreso          funcion(etapa, fraccion) para informar el avance
    """
    _avisar(progreso, "entrada", 0)
    if rutas is None:
        if carpeta is None:
            raise ErrorEntrada("hay que indicar la carpeta del paciente o las rutas de las 4 resonancias")
        rutas = buscar_modalidades(carpeta)
    else:
        rutas = {m: Path(rutas[m]) for m in MODALIDADES} if set(MODALIDADES) <= set(rutas) else None
        if rutas is None:
            raise ErrorEntrada(f"faltan resonancias: se necesitan {MODALIDADES}")
        for m, p in rutas.items():
            if not p.is_file():
                raise ErrorEntrada(f"no existe la resonancia {m}: {p}")
    if edad is not None and not (0 < float(edad) < 120):
        raise ErrorEntrada(f"edad fuera de rango: {edad}")
    avisos = validar_formato(rutas)
    caso = caso_del_estudio(_nombres_del_caso(carpeta, rutas, id_caso))
    ref = _leer_mascara(referencia, rutas, "segmentacion de referencia") if referencia is not None else None
    _avisar(progreso, "entrada")

    salida = Path(salida) if salida else Path(tempfile.mkdtemp(prefix="analisis_"))
    salida.mkdir(parents=True, exist_ok=True)
    trabajo = Path(tempfile.mkdtemp(prefix="trabajo_"))
    try:
        _avisar(progreso, "segmentacion", 0)
        if segmentacion is not None:
            seg, img_ref = _leer_mascara(segmentacion, rutas, "segmentacion")
            fuente = f"externa: {Path(segmentacion).name}"
        else:
            if not nnunet_disponible():
                raise ErrorEntrada("no hay segmentacion y nnU-Net no esta disponible (faltan PyTorch, "
                                   "nnunetv2 o los pesos). Sube una segmentacion hecha en Colab.")
            nota_fold = ""
            if caso is not None:          # paciente del estudio: solo el modelo que no lo vio (D22)
                folds = (caso["fold"],)
                nota_fold = f"; {caso['paciente_id']} es del estudio: solo el fold que no lo vio"
            seg_nn, img_ref, info = segmentar_nnunet(rutas, trabajo, folds, tta)
            seg, post = posprocesar_et(seg_nn)
            fuente = f"nnU-Net ({info})" + nota_fold + (
                f"; ET de {post['voxeles_et_predichos']} voxeles descartado" if post["et_descartado"] else "")
        _guardar_mascara(seg, img_ref, salida / "segmentacion.nii.gz")
        _avisar(progreso, "segmentacion")

        caract, estados = extraer_caracteristicas(rutas, seg, img_ref, trabajo, progreso)
        tabla_caracteristicas(caract).to_csv(salida / "caracteristicas.csv", index=False)

        _avisar(progreso, "pronostico", 0)
        pron = pronosticar(caract, edad, estados)
        _avisar(progreso, "pronostico")

        evaluacion = None
        if ref is not None:
            evaluacion = _validar(rutas, seg, ref, img_ref, edad, caso, referencia, trabajo, salida, progreso)
    finally:
        shutil.rmtree(trabajo, ignore_errors=True)

    vols = {k: round(v, 2) for k, v in volumenes(seg).items()}
    res = Resultado(aviso=AVISO, volumen_cm3=vols, estado_regiones=estados, pronostico=pron,
                    segmentacion=fuente, avisos_formato=avisos, edad=edad, evaluacion=evaluacion)
    titulo = (f"WT {vols['WT']:.1f} cm³ · TC {vols['TC']:.1f} cm³ · ET {vols['ET']:.1f} cm³ | "
              + (f"supervivencia {pron['clase']}, ~{pron['dias_mediana_estimada']:.0f} días"
                 if pron["aplica"] else "pronóstico: no aplica") + " | prototipo de investigación")
    figura(rutas["flair"], seg, salida / "vista.png", titulo)
    nombres = ["segmentacion.nii.gz", "caracteristicas.csv", "resultado.json", "vista.png"]
    if evaluacion is not None:
        nombres += ["referencia.nii.gz", "diferencias.nii.gz", "comparacion.png"]
    res.archivos = {n: str(salida / n) for n in nombres}
    (salida / "resultado.json").write_text(json.dumps(res.a_dict(), indent=2, ensure_ascii=False))
    _avisar(progreso, "salida")
    return res


def _validar(rutas, seg, ref, img_ref, edad, caso, ruta_ref, trabajo, salida, progreso):
    """Compara la mascara del modelo con la de referencia y recalcula el pronostico con la de referencia."""
    datos_ref, _ = ref
    _avisar(progreso, "validacion", 0)
    voxel = img_ref.header.get_zooms()[:3]
    metricas = comparar(seg, datos_ref, voxel)
    _guardar_mascara(datos_ref, img_ref, salida / "referencia.nii.gz")
    _guardar_mascara(mapa_diferencias(seg, datos_ref), img_ref, salida / "diferencias.nii.gz")

    # Segunda pasada de radiomica con la mascara del radiologo: cuanto cambia el pronostico (D26)
    trabajo_ref = Path(trabajo) / "referencia"
    trabajo_ref.mkdir(exist_ok=True)
    caract_ref, estados_ref = extraer_caracteristicas(
        rutas, datos_ref, img_ref, trabajo_ref,
        lambda _etapa, f: _avisar(progreso, "validacion", 0.1 + 0.85 * f))
    pron_ref = pronosticar(caract_ref, edad, estados_ref)

    figura_comparacion(rutas["flair"], seg, datos_ref, salida / "comparacion.png",
                       "Modelo frente a radiólogo · Dice " +
                       " · ".join(f"{r} {m['dice']:.3f}" for r, m in metricas.items()))
    _avisar(progreso, "validacion")
    return {"fuente_ref": Path(ruta_ref).name,
            "metricas": metricas,
            "estudio": ubicar_en_estudio(metricas, caso["paciente_id"] if caso else None),
            "caso_del_estudio": caso,
            "volumen_ref_cm3": {k: round(v, 2) for k, v in volumenes(datos_ref).items()},
            "estado_regiones_ref": estados_ref,
            "pronostico_ref": pron_ref}
