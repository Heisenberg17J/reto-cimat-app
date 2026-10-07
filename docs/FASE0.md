# Fase 0 · Viabilidad del empaquetado

**Objetivo:** antes de construir la interfaz, comprobar que el núcleo se puede **empaquetar y ejecutar en Windows** (y
Linux) en un equipo **sin Python**, y que sigue dando **exactamente los mismos números** que el estudio. Es el mayor
riesgo del proyecto, porque **PyRadiomics no tiene versión compilada publicada** (ni en pip ni en conda-forge) y hay que
compilarlo nosotros. Ver `docs/PLAN.md`.

## Qué se automatiza (GitHub Actions)

`.github/workflows/viabilidad-empaquetado.yml` corre en `windows-latest` y `ubuntu-latest`, con Python 3.11, **sin nada
preinstalado por el usuario**:

1. **Compila la rueda de `pyradiomics==3.0.1`** con la receta fija (numpy 1.26.4 + versioneer 0.29,
   `--no-build-isolation`). En Windows usa el MSVC que el runner ya trae. La rueda se guarda como artefacto.
2. **Instala el núcleo con esa rueda** (bajo `restricciones.txt`) y corre las pruebas que **no** necesitan imágenes:
   `test_artefactos_integros` y `test_errores_de_entrada`.
3. **Empaqueta con PyInstaller** un CLI mínimo (`empaquetado/reto-cimat-cli.spec`) y comprueba que **arranca sin Python**
   (un caso inexistente debe dar `ErrorEntrada`, código 2). El CLI empaquetado se guarda como artefacto.

El CLI empaquetado **no incluye PyTorch ni nnU-Net** (que se importan de forma perezosa): analiza a partir de una
**segmentación ya hecha** (`--segmentacion`). Eso mantiene el binario en cientos de MB, no varios GB, y aísla el riesgo
real de la Fase 0 —compilar y congelar la pila de radiómica y pronóstico— del de la segmentación.

### Cómo dispararlo

El repositorio debe estar en GitHub (ver `docs/INICIO_SESION.md` §3). Luego: pestaña **Actions → "Fase 0 - viabilidad
del empaquetado" → Run workflow**, o con un `push` a `main` que toque `nucleo/`, `artefactos/`, `empaquetado/`,
`pyproject.toml` o `restricciones.txt`.

## Qué NO puede cubrir el CI (pasos manuales en un PC con Windows)

Las imágenes de BraTS y los pesos de nnU-Net **no van en git** (licencia de los datos, tamaño). Por eso dos pasos de la
Fase 0 se hacen a mano, una vez, en un Windows real con `datos_prueba/` copiado (ver `docs/INICIO_SESION.md` §2):

- **Paso 3 · Regresión completa.** Instalar el CLI empaquetado (o el núcleo con la rueda del CI) y correr `pytest`
  completo. **Criterio de éxito:** las 1146 características iguales a las del estudio (tolerancia 1e-9) y el riesgo
  **−0.778728** (≈522 días, clase larga; volúmenes WT 101.61 / TC 24.61 / ET 16.47 cm³).
- **Paso 4 · nnU-Net en CPU.** Con los pesos copiados, segmentar un paciente y medir **tiempo y RAM**
  (objetivo: < 10 min con 1 fold y < 8 GB de RAM).

## Validación local ya hecha (Linux, 2026-10-06)

Como el repositorio todavía no está en GitHub, el workflow aún no se ha ejecutado. Pero su lógica se validó a mano en
Linux (WSL2, Python 3.11) en un venv limpio, con resultados verdes:

- La rueda de `pyradiomics==3.0.1` **compila desde el sdist** con la receta documentada (sin usar caché).
- Las dos pruebas sin imágenes pasan con esa rueda.
- El CLI empaquetado con PyInstaller **arranca sin ningún Python en el entorno** (`env -i`), sin `torch` incluido
  (~650 MB en formato carpeta).
- **Números idénticos** con el binario congelado y un caso real + segmentación: 1146 características con diferencia
  máxima 3.6e-12 (< 1e-9), riesgo −0.7787280915 (= −0.778728), volúmenes WT 101.61 / TC 24.61 / ET 16.47 cm³,
  clase larga, ~522 días.

- **Paso 4 (nnU-Net en CPU) cumplido en Linux (2026-10-06):** con los pesos reales y 1 fold, segmentar
  Brats18_CBICA_AAP_1 tardó **2 min 21 s** y usó **2.7 GB de RAM** (objetivo: < 10 min, < 8 GB). El flujo completo
  (nnU-Net → radiómica → pronóstico) corrió sin pasar `--segmentacion`. Los volúmenes salen algo distintos del número de
  referencia porque es 1 fold, no el ensamble de 5 ni la predicción *out-of-fold*; es lo esperado.

Queda pendiente lo que solo prueba Windows: la compilación con **MSVC** y la regresión/segmentación en un PC real
(pasos 3 y 4). El workflow cubre la compilación MSVC y el arranque; los números en Windows son el paso manual 3.

## Criterio para cerrar la Fase 0

Verde el workflow en Windows **y** verdes a mano los pasos 3 y 4 en un Windows real. Si algo falla, se resuelve aquí: no
se avanza a la interfaz (Fase 2) con este riesgo abierto.

## Archivos de esta fase

| Archivo | Qué es |
|---|---|
| `.github/workflows/viabilidad-empaquetado.yml` | El workflow (pasos 1, 2 y 5) |
| `empaquetado/reto-cimat-cli.spec` | Receta de PyInstaller del CLI mínimo |
| `empaquetado/arranque_cli.py` | Punto de entrada que congela PyInstaller (llama a `nucleo.cli.main`) |
| `empaquetado/hook_runtime_artefactos.py` | Runtime hook: apunta `NUCLEO_ARTEFACTOS` a los artefactos empaquetados |
