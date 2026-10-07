"""Punto de entrada: analizar un paciente de punta a punta.

    resultado = analizar("carpeta_con_4_resonancias", edad=62)
    resultado = analizar(rutas={"t1": ..., "t1ce": ..., "t2": ..., "flair": ...},
                         segmentacion="seg.nii.gz", progreso=lambda etapa, fraccion: ...)

Es lo que llamaran el backend y la linea de comandos. Lanza ErrorEntrada si la entrada
no se puede procesar (mensaje pensado para el usuario) y escribe en `salida`:
segmentacion.nii.gz, caracteristicas.csv, resultado.json y vista.png.
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
from .pronostico import pronosticar
from .radiomica import extraer_caracteristicas, tabla_caracteristicas, volumenes
from .segmentacion import nnunet_disponible, posprocesar_et, segmentar_nnunet, validar_segmentacion
from .vista import figura

ETAPAS = ("entrada", "segmentacion", "radiomica", "pronostico", "salida")


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
    version_nucleo: str = __version__
    fecha: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def a_dict(self):
        return asdict(self)


def _avisar(progreso, etapa, fraccion=1.0):
    if progreso:
        progreso(etapa, float(fraccion))


def analizar(carpeta=None, *, rutas=None, edad=None, segmentacion=None, salida=None,
             folds=(0, 1, 2, 3, 4), tta=None, progreso=None):
    """Analiza un paciente. Ver el docstring del modulo.

    carpeta / rutas   las 4 resonancias en formato BraTS (una de las dos)
    edad              en anos; sin ella no hay pronostico
    segmentacion      mascara ya hecha (etiquetas BraTS 0/1/2/4); sin ella se usa nnU-Net
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
    _avisar(progreso, "entrada")

    salida = Path(salida) if salida else Path(tempfile.mkdtemp(prefix="analisis_"))
    salida.mkdir(parents=True, exist_ok=True)
    trabajo = Path(tempfile.mkdtemp(prefix="trabajo_"))
    try:
        _avisar(progreso, "segmentacion", 0)
        if segmentacion is not None:
            if not Path(segmentacion).is_file():
                raise ErrorEntrada(f"no existe la segmentacion: {segmentacion}")
            img_ref = nib.load(segmentacion)
            seg = np.asanyarray(img_ref.dataobj).astype(np.int16)
            try:
                validar_segmentacion(seg)
            except ValueError as e:
                raise ErrorEntrada(str(e)) from e
            if seg.shape != nib.load(rutas["t1"]).shape:
                raise ErrorEntrada(f"la segmentacion {seg.shape} no tiene la forma de las resonancias")
            fuente = f"externa: {Path(segmentacion).name}"
        else:
            if not nnunet_disponible():
                raise ErrorEntrada("no hay segmentacion y nnU-Net no esta disponible (faltan PyTorch, "
                                   "nnunetv2 o los pesos). Sube una segmentacion hecha en Colab.")
            seg_nn, img_ref, info = segmentar_nnunet(rutas, trabajo, folds, tta)
            seg, post = posprocesar_et(seg_nn)
            fuente = f"nnU-Net ({info})" + (f"; ET de {post['voxeles_et_predichos']} voxeles descartado"
                                             if post["et_descartado"] else "")
        nueva = nib.Nifti1Image(seg.astype(np.uint8), img_ref.affine, img_ref.header)
        nueva.set_data_dtype(np.uint8)
        nib.save(nueva, salida / "segmentacion.nii.gz")
        _avisar(progreso, "segmentacion")

        caract, estados = extraer_caracteristicas(rutas, seg, img_ref, trabajo, progreso)
        tabla_caracteristicas(caract).to_csv(salida / "caracteristicas.csv", index=False)
    finally:
        shutil.rmtree(trabajo, ignore_errors=True)

    _avisar(progreso, "pronostico", 0)
    pron = pronosticar(caract, edad, estados)
    _avisar(progreso, "pronostico")

    vols = {k: round(v, 2) for k, v in volumenes(seg).items()}
    res = Resultado(aviso=AVISO, volumen_cm3=vols, estado_regiones=estados, pronostico=pron,
                    segmentacion=fuente, avisos_formato=avisos, edad=edad)
    titulo = (f"WT {vols['WT']:.1f} cm³ · TC {vols['TC']:.1f} cm³ · ET {vols['ET']:.1f} cm³ | "
              + (f"supervivencia {pron['clase']}, ~{pron['dias_mediana_estimada']:.0f} días"
                 if pron["aplica"] else "pronóstico: no aplica") + " | prototipo de investigación")
    figura(rutas["flair"], seg, salida / "vista.png", titulo)
    res.archivos = {n: str(salida / n) for n in
                    ("segmentacion.nii.gz", "caracteristicas.csv", "resultado.json", "vista.png")}
    (salida / "resultado.json").write_text(json.dumps(res.a_dict(), indent=2, ensure_ascii=False))
    _avisar(progreso, "salida")
    return res
