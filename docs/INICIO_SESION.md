# Cómo iniciar una sesión de trabajo en este repositorio

Esta guía es para quien abra este proyecto por primera vez, o en una máquina nueva. El proyecto de investigación
(`reto-CIMAT`) **no se toca**: de allá solo se **copian** archivos, una vez.

## 1. Qué ya está en el repositorio (versionado)

| Ruta | Qué es |
|---|---|
| `nucleo/` | La lógica de análisis |
| `backend/`, `frontend/` | Servidor FastAPI local y la interfaz web (React + NiiVue) |
| `artefactos/` | YAML de PyRadiomics, modelo de pronóstico y umbral de ET, con `SHA256SUMS` y `PROCEDENCIA.md` |
| `tests/` | Pruebas de regresión y sus valores esperados (`tests/esperado/`) |
| `docs/` | `CONTEXTO.md` (de dónde viene todo), `GUIA_USUARIO.md` y esta guía |
| `CLAUDE.md` | Reglas para Claude Code (las lee solo al abrir una sesión aquí) |
| `pyproject.toml`, `restricciones.txt` | Dependencias con versiones fijas |

## 2. Lo que hay que copiar a mano (NO va en git)

| Qué | De dónde | A dónde | Para qué |
|---|---|---|---|
| **Datos de prueba**: 2 pacientes de BraTS 2018 + 3 predicciones crudas de nnU-Net (~17 MB) | La carpeta `datos_prueba/` ya preparada en `/home/hejembert/investigaciones/reto_cimat_app/` (o generarla de nuevo desde `reto_CIMAT`, ver abajo) | `datos_prueba/` | Las pruebas de regresión |
| **Pesos de nnU-Net**: `plans.json`, `dataset.json`, `dataset_fingerprint.json` y `fold_0…4/checkpoint_final.pth` | Google Drive: `MyDrive/reto_cimat/nnUNet_results/Dataset501_BraTS2018/nnUNetTrainer_100epochs_ckpt5__nnUNetPlans__3d_fullres/` | `artefactos/nnunet/Dataset501_BraTS2018/nnUNetTrainer_100epochs_ckpt5__nnUNetPlans__3d_fullres/`, con la misma estructura | Segmentar dentro de la app. Sin ellos, la app pide la segmentación hecha en Colab |

Para bajar solo los pesos necesarios desde Colab, ver la celda de `inferencia/README.md` en el repo de investigación:
genera `pesos_nnunet.zip` en Drive.

Para **regenerar** `datos_prueba/` desde `reto_CIMAT` (solo lectura allá):

```
R=../reto_CIMAT; A=.
for P in Brats18_CBICA_AAP_1 Brats18_2013_25_1; do
  D=$(dirname $(grep "^$P," $R/datos/brats2018/manifest.csv | cut -d, -f3)); mkdir -p $A/datos_prueba/$P
  for m in t1 t1ce t2 flair; do cp $R/$D/${P}_$m.nii.gz $A/datos_prueba/$P/$m.nii.gz; done
  cp $R/datos/segmentaciones_pred/${P}_seg.nii.gz $A/datos_prueba/$P/segmentacion.nii.gz
done
mkdir -p $A/datos_prueba/nnunet_crudo
for P in Brats18_2013_16_1 Brats18_2013_24_1 Brats18_CBICA_AAP_1; do
  cp $R/datos/predicciones_oof/fold_*/validation/$P.nii.gz $A/datos_prueba/nnunet_crudo/ 2>/dev/null
done
```

## 3. Crear el repositorio en GitHub (una sola vez)

1. En GitHub, crear un repositorio vacío, por ejemplo `reto-cimat-app`. **Privado** mientras no se revise la licencia de
   uso de los datos de BraTS para los pesos y los artefactos.
2. En esta carpeta:
   ```
   git init -b main
   git add .
   git commit -m "Fase 1: nucleo de analisis con pruebas de regresion"
   git remote add origin https://github.com/<usuario>/reto-cimat-app.git
   git push -u origin main
   ```
   Antes del commit, comprobar con `git status` que **no** aparezcan `datos_prueba/`, `*.nii.gz` ni `artefactos/nnunet/`;
   el `.gitignore` ya los excluye.

## 4. Entorno de Python

**Opción rápida** (en esta máquina): usar el entorno `inferencia` del proyecto, que ya tiene todo, incluido el núcleo
instalado en modo editable:

```
conda activate inferencia
```

**Opción limpia** (otra máquina, Linux):

```
conda create -n reto-app python=3.11 -y && conda activate reto-app
pip install -c restricciones.txt -e ".[pruebas]"
pip install versioneer==0.29 && pip install --no-build-isolation pyradiomics==3.0.1
pip install -c restricciones.txt --extra-index-url https://download.pytorch.org/whl/cpu -e ".[segmentacion]"
```

En **Windows**, `pyradiomics` no se instala así (no hay versión compilada publicada): se compila en la CI de GitHub
Actions (ver `.github/workflows/`) o con Visual Studio Build Tools.

## 5. Comprobar que todo está bien

```
pytest                    # pruebas de regresión del núcleo + del backend
reto-cimat-analizar --caso datos_prueba/Brats18_CBICA_AAP_1 --edad 39.068 \
    --segmentacion datos_prueba/Brats18_CBICA_AAP_1/segmentacion.nii.gz
```

La segunda línea debe mostrar: volúmenes WT 101.61 / TC 24.61 / ET 16.47 cm³, supervivencia larga y ~522 días.

## 6. Abrir la sesión con Claude Code

```
cd /home/hejembert/investigaciones/reto_cimat_app
claude
```

Claude leerá `CLAUDE.md` automáticamente. Un buen primer mensaje:

> Lee docs/CONTEXTO.md y revisa el estado del repo; dime en qué puedo ayudar a continuar.

Recordatorio: esa sesión trabaja **solo** en `reto_cimat_app`; el proyecto de investigación no se modifica.
