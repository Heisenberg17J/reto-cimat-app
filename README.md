# reto-cimat-app · Análisis de gliomas: segmentación + pronóstico

> **Prototipo de investigación. No es una herramienta clínica** ni sustituye el criterio médico. El pronóstico
> depende casi solo de la edad: en validación cruzada, el modelo (c-index 0.622) no supera a la edad sola (0.624).

Aplicación para analizar pacientes nuevos con los modelos del proyecto **reto-CIMAT / BraTS 2018**. A partir de las 4
resonancias de un paciente (y, si se conoce, su edad):

1. **Segmenta** el tumor con nnU-Net: edema, necrosis y realce.
2. Calcula sus **volúmenes** y su **radiómica**, igual que en el estudio.
3. Estima la **supervivencia**: corta (< 10 meses), media (10–15) o larga (> 15), y los días.

El estudio completo, con datos, entrenamiento y validación, está en el repositorio de investigación `reto-CIMAT`
(sus decisiones se citan aquí como D*n*).

## Estado

Objetivo: una **app de escritorio para personas comunes**, con instalador para Windows (y Linux), sin terminal ni
Docker. Arquitectura y fases en [docs/PLAN.md](docs/PLAN.md).

| Fase | Qué | Estado |
|---|---|---|
| 0 | Viabilidad del empaquetado en Windows: compilar PyRadiomics y obtener los mismos números ([docs/FASE0.md](docs/FASE0.md)) | **En progreso** |
| 1 | **Núcleo** (`nucleo/`): la lógica de análisis como funciones reutilizables, con pruebas de regresión | **Hecha** |
| 2 | **Backend FastAPI local** (`backend/`): API, cola de análisis y página web mínima | **Hecha** |
| 3 | **Interfaz React + NiiVue** (`frontend/`): visor, volúmenes, pronóstico | **v1 hecha** (falta probar en navegador) |
| 4 | **Arranque, modos rápido/completo, descarga de pesos (sha256) y registro** | **v1 hecha** (falta URL de Releases) |
| 5 | **Ejecutable portable** (Windows/Linux `.zip`), sin instalador | **Hecha** (probado en Windows real) |
| 6 | (Futuro) Preprocesamiento de resonancias clínicas (DICOM → formato BraTS) | Futuro |
| 7 | Validación con usuarios | Pendiente |

**Para el usuario final:** [docs/GUIA_USUARIO.md](docs/GUIA_USUARIO.md) (instalar y usar la app en Windows, sin tecnicismos).

**Para empezar a trabajar aquí:** [docs/INICIO_SESION.md](docs/INICIO_SESION.md) (entorno, archivos a copiar, primer
mensaje para Claude Code). Contexto científico: [docs/CONTEXTO.md](docs/CONTEXTO.md).

## Estructura

```
nucleo/            lógica de análisis (sin interfaz)
  analisis.py        analizar(): la función que llamarán el backend y la línea de comandos
  entrada.py         localizar y validar las 4 resonancias (ErrorEntrada)
  segmentacion.py    nnU-Net (opcional) y posprocesado de ET (D24)
  radiomica.py       z-score, regiones WT/TC/ET y PyRadiomics (D2–D13)
  pronostico.py      modelo final de Cox (D30); sin edad o sin ET, "no aplica"
  vista.py           figura de control
  cli.py             línea de comandos
artefactos/        YAML de PyRadiomics, modelo de pronóstico y umbral de ET (ver PROCEDENCIA.md)
tests/             pruebas de regresión y valores esperados (tests/esperado/)
docs/              PLAN, CONTEXTO e INICIO_SESION
datos_prueba/      (no versionado) 2 pacientes de BraTS para las pruebas
```

## Instalación

Se necesita **Python 3.11** con **numpy 1.26**, porque PyRadiomics 3.0.1 no funciona con numpy 2:

```
conda create -n reto-app python=3.11 -y && conda activate reto-app
pip install -c restricciones.txt -e ".[pruebas]"
pip install versioneer==0.29 && pip install --no-build-isolation pyradiomics==3.0.1
# Opcional, para segmentar con nnU-Net en esta máquina:
pip install -c restricciones.txt --extra-index-url https://download.pytorch.org/whl/cpu -e ".[segmentacion]"
```

**Pesos de nnU-Net** (opcionales; sin ellos hay que subir la segmentación ya hecha): copiar desde Drive
`nnUNet_results/Dataset501_BraTS2018/nnUNetTrainer_100epochs_ckpt5__nnUNetPlans__3d_fullres/` (los archivos
`plans.json`, `dataset.json` y `dataset_fingerprint.json`, y `fold_*/checkpoint_final.pth`) a `artefactos/nnunet/` con la
misma estructura, o indicar su ubicación con `NUCLEO_NNUNET`.

## Uso

**Desde Python** (así lo usará el backend):

```python
from nucleo import analizar, ErrorEntrada

r = analizar("carpeta_con_4_resonancias", edad=62,
             segmentacion="segmentacion.nii.gz",      # opcional: sin ella se usa nnU-Net
             salida="resultados/paciente_1",
             progreso=lambda etapa, fraccion: print(etapa, fraccion))
r.volumen_cm3        # {'WT': ..., 'TC': ..., 'ET': ...}
r.pronostico         # {'aplica': True, 'clase': ..., 'dias_mediana_estimada': ..., ...}
r.archivos           # segmentacion.nii.gz, caracteristicas.csv, resultado.json, vista.png
```

**Desde la terminal:**

```
reto-cimat-analizar --caso CARPETA --edad 62 --segmentacion segmentacion.nii.gz
```

- **Entrada:** `t1`, `t1ce`, `t2` y `flair` en NIfTI, con nombre simple (`t1.nii.gz`) o de BraTS (`<id>_t1.nii.gz`), en
  **formato BraTS**: sin cráneo, co-registradas, voxel de 1 mm y 240 × 240 × 155. Si no lo cumplen, se avisa.
- **Sin edad:** no hay pronóstico; la edad lleva casi toda la señal y no se imputa. Como referencia, se muestra cómo
  cambiaría el resultado con 40–80 años.
- **Sin realce (ET):** no hay pronóstico; el modelo se entrenó solo con HGG con realce.
- **Errores de entrada:** lanzan `ErrorEntrada`, con un mensaje pensado para mostrarse al usuario.

## Pruebas

```
pytest
```

Comparan el núcleo con valores sacados del estudio (`tests/esperado/`), usando `datos_prueba/`:
- 1146 características idénticas a las del estudio;
- el mismo riesgo (−0.778728, unos 522 días, para Brats18_CBICA_AAP_1);
- el mismo posprocesado de ET;
- "no aplica" sin edad y sin ET;
- errores de entrada claros;
- artefactos íntegros.

Si falta `datos_prueba/`, las pruebas que la necesitan se saltan.

## Privacidad

Solo se aceptan NIfTI, no DICOM, que suele traer datos del paciente. Los archivos temporales se borran al terminar.
Ninguna imagen médica debe subirse a este repositorio (`.gitignore` excluye `*.nii*`).
