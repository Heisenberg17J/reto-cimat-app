# Procedencia de los artefactos

Copias fijas del repositorio de investigación `reto-CIMAT`, en el commit `53dd56b` (2026-10-06).
`SHA256SUMS` permite comprobar que no cambiaron; lo verifica `tests/test_regresion.py`.

| Archivo | Origen en el repo de investigación | Qué es |
|---|---|---|
| `params_brats2018_v0.yaml` | `config/params_brats2018_v0.yaml` | Parámetros de PyRadiomics (binWidth 0.1, solo imagen original; D7–D10) |
| `pronostico_coxnet.joblib` / `.json` | `modelos/` | Cox Elastic Net final con 163 HGG (D30). c-index esperado 0.622 (CV 5 × 10, D27) |
| `postproceso_et.json` | `resultados/segmentacion/postproceso_et.json` | Umbral para descartar ET pequeño en casos nuevos: 500 voxeles (D24) |
| `folds.csv` | `particiones/folds.csv` (paquete de metodología del 2026-10-10, commit `b476ee8`) | 5 × 57 pacientes (D22). Si el caso es un paciente del estudio, nnU-Net usa solo el fold que no lo vio |
| `metricas_segmentacion_oof.csv` | `resultados/segmentacion/metricas_oof.csv` (mismo paquete) | Dice, HD95, sensibilidad y especificidad fuera de fold de los 285 pacientes (D28): la app ubica cada caso validado entre ellos |
| `metricas_segmentacion_resumen.csv` | `resultados/segmentacion/metricas_resumen.csv` (mismo paquete) | Resumen de lo anterior: todos (285) y HGG con supervivencia (163) |
| `nnunet/` (no versionado) | Drive: `nnUNet_results/Dataset501_BraTS2018/...` | Pesos de nnU-Net, 5 folds (D23); ver el README |

Si se vuelve a entrenar algún modelo en el repo de investigación, hay que copiar los artefactos de nuevo,
regenerar `SHA256SUMS` (`sha256sum *.yaml *.joblib *.json *.csv > SHA256SUMS`) y pasar las pruebas.
