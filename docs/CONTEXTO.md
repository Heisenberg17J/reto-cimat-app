# Contexto: qué hace el núcleo y de dónde viene

## El proyecto de investigación (resumen)

`reto-CIMAT` trabajó con los 285 pacientes de entrenamiento de BraTS 2018 (210 HGG, 75 LGG):

| Objetivo | Modelo | Resultado (fuera de fold) |
|---|---|---|
| Segmentación | nnU-Net v2 3D, 5 folds × 100 épocas, por regiones WT/TC/ET | Dice WT 0.907, TC 0.842, ET 0.769; HD95 mediano 3.6 / 3.5 / 2.2 mm |
| Pronóstico (163 HGG con supervivencia) | Cox Elastic Net con edad + radiómica (y un algoritmo genético como comparación) | c-index 0.622; la **edad sola da 0.624**. El genético quedó peor (0.605) |

**Conclusión que la app debe respetar: el pronóstico depende casi por completo de la edad.** En el modelo final, la edad
pesa 0.418 y la mayor de las 9 características radiómicas, 0.037 (en escala estandarizada). Con la misma resonancia, el
resultado va de "supervivencia larga" a los 40 años a "corta" a los 80.

## El flujo del núcleo (`nucleo.analizar`)

```
4 resonancias NIfTI (t1, t1ce, t2, flair) en formato BraTS  [+ edad]  [+ segmentación opcional]
 1. entrada.py       localizar los archivos y avisar si no parecen formato BraTS
 2. segmentacion.py  nnU-Net (5 folds) si no se da la máscara → posprocesado: ET < 500 voxeles se descarta
 3. radiomica.py     z-score sobre el cerebro → máscaras WT/TC/ET → PyRadiomics (1146 características)
 4. pronostico.py    Cox final → riesgo, clase (corta / media / larga) y días; o "no aplica"
 5. salida           segmentacion.nii.gz, caracteristicas.csv, resultado.json, vista.png
```

- **Etiquetas BraTS:** 1 necrosis / no realzado, 2 edema, 4 realce. Regiones: WT = {1,2,4}, TC = {1,4}, ET = {4}.
- **Clases de supervivencia** (Bakas et al. 2018, arXiv:1811.02629): corta < 10 meses (< 300 días), media 10–15, larga > 15.
- **"No aplica"** si falta la edad, o si no hay realce (ET). El modelo se entrenó solo con HGG con realce.
- `progreso(etapa, fraccion)` informa el avance por etapas: entrada, segmentacion, radiomica, pronostico y salida.

## Números que las pruebas protegen (`tests/esperado/`)

- Brats18_CBICA_AAP_1, edad 39.068: 1146 características idénticas al estudio (tolerancia 1e-9), riesgo −0.778728,
  ~522 días, clase larga, volúmenes WT 101.61 / TC 24.61 / ET 16.47 cm³.
- Brats18_2013_25_1: ET vacío tras el posprocesado → "no aplica".
- Posprocesado de ET: 3 predicciones crudas de nnU-Net dan máscaras idénticas, bit a bit, a las del estudio.

## Limitaciones que la app debe comunicar

1. **Formato de entrada.** Las resonancias deben estar **en formato BraTS**: sin cráneo, co-registradas al atlas SRI24,
   voxel de 1 mm y 240 × 240 × 155. **Una resonancia clínica normal (DICOM del hospital) no viene así.** Convertirla
   requiere un preprocesamiento (DICOM → NIfTI, registro, extracción de cráneo) que la versión 1 **no** incluye; ver
   PLAN, fase 6.
2. **No es clínico:** sin validación externa, la exactitud con pacientes nuevos no está medida.
3. **Segmentación en CPU:** varios minutos por paciente; con GPU NVIDIA, segundos.
4. **Pesos de nnU-Net:** los 5 checkpoints finales. Hay que distribuirlos aparte y revisar la licencia de uso de los datos
   de BraTS antes de publicarlos.
