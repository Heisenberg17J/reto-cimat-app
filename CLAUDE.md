# CLAUDE.md — reto-cimat-app

Este repositorio construye una **aplicación de escritorio para personas comunes (Windows primero, Linux después)**
que analiza resonancias de un paciente con glioma: segmentación del tumor, volúmenes y un pronóstico de
supervivencia orientativo. Es un **prototipo de investigación, no una herramienta clínica**.

## Reglas

1. **Solo se trabaja en este repositorio.** El proyecto de investigación (`../reto_CIMAT`, repo `reto-CIMAT`) **no se
   modifica nunca**. Si hace falta algo de allá, se copia aquí y se documenta su procedencia (ver `artefactos/PROCEDENCIA.md`).
2. **El núcleo científico (`nucleo/`) no cambia de comportamiento.** Cualquier cambio en `nucleo/` debe mantener verdes las
   pruebas de regresión (`pytest`): 1146 características idénticas a las del estudio y el mismo riesgo. Las fases nuevas
   (backend, frontend, empaquetado) **envuelven** el núcleo, no lo reescriben.
3. **Los artefactos son fijos:** `artefactos/*` (YAML, modelo, umbral) no se editan; `SHA256SUMS` lo comprueba.
4. **Ninguna imagen médica entra a git** (`*.nii*`, `datos_prueba/`, `salidas/`). Tampoco los pesos de nnU-Net.
5. **Honestidad en la interfaz:** el aviso "prototipo de investigación, no clínico" es siempre visible. Sin edad o sin
   realce (ET) **no hay pronóstico** (nunca imputar la edad). Mostrar siempre el desempeño esperado (c-index 0.62,
   prácticamente igual a la edad sola).
6. **Versiones fijas:** Python 3.11, numpy 1.26.4 (PyRadiomics 3.0.1 no funciona con numpy 2), scikit-survival 0.23.1 (el
   modelo `.joblib` se guardó con ella). Ver `restricciones.txt` y `pyproject.toml`.
7. Idioma: código, comentarios, interfaz y documentación **en español** (mensajes al usuario sin tecnicismos).

## Dónde está cada cosa

- `docs/CONTEXTO.md`: qué hace el núcleo, de dónde salen los modelos, números que hay que preservar y limitaciones.
- `docs/GUIA_USUARIO.md`: guía para el usuario final (instalar y usar la app en Windows).
- `docs/INICIO_SESION.md`: cómo preparar el entorno y los archivos que hay que copiar.
- `nucleo/analisis.py`: `analizar(...)`, la única función que deben llamar el backend o la línea de comandos.

## Comandos

```
conda activate reto-app          # o el entorno "inferencia" del proyecto de investigación
pytest                           # pruebas de regresión (~70 s; necesitan datos_prueba/)
reto-cimat-analizar --caso datos_prueba/Brats18_CBICA_AAP_1 --edad 39.068 \
    --segmentacion datos_prueba/Brats18_CBICA_AAP_1/segmentacion.nii.gz
```
