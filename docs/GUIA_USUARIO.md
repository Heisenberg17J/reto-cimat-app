# Guía de usuario — Análisis de glioma (reto-cimat-app)

> **Prototipo de investigación. No es una herramienta clínica** ni sustituye el criterio médico. El pronóstico
> depende casi solo de la edad. No tome decisiones clínicas con esta app.

Esta guía explica, paso a paso y sin tecnicismos, cómo instalar y usar la aplicación en **Windows**.

---

## 1. Qué hace

A partir de las **4 resonancias** de un paciente con glioma (y, si se conoce, su **edad**), la app:

1. **Segmenta** el tumor (edema, necrosis y realce).
2. Calcula sus **volúmenes** (cm³).
3. Estima la **supervivencia**: corta (< 10 meses), media (10–15) o larga (> 15), con los días aproximados.

Todo ocurre **en su propio equipo**: las imágenes **no se suben a internet**.

## 2. Qué necesita

- Un PC con **Windows** (10 u 11), unos **4 GB de RAM** libres y ~2 GB de disco.
- Las **4 resonancias en formato BraTS** (archivos `.nii` o `.nii.gz`): `t1`, `t1ce`, `t2` y `flair`.
  - Deben estar **sin cráneo, co-registradas y de 240×240×155** (formato BraTS). Una resonancia clínica normal
    (DICOM del hospital) **no** viene así y, por ahora, la app no la convierte.
- **Internet solo la primera vez**, para descargar los modelos (~550 MB). Después funciona sin conexión.

## 3. Instalar (no hace falta instalador)

1. Descargue el archivo **`reto-cimat-app-windows.zip`** (de la sección *Releases* del proyecto).
2. **Descomprímalo** en una carpeta, por ejemplo en el Escritorio. Quedará una carpeta `reto-cimat-app`.
3. Entre a esa carpeta y haga **doble clic en `reto-cimat-app.exe`**.

### Aviso de Windows (SmartScreen)

Como la app no está firmada, Windows puede mostrar un aviso azul *"Windows protegió su PC"*. Es normal para un
programa nuevo:

- Haga clic en **"Más información"** y luego en **"Ejecutar de todas formas"**.

Se abrirá una ventana negra (el servidor) y, en unos segundos, **su navegador** con la aplicación. **No cierre la
ventana negra** mientras use la app; para salir, ciérrela o pulse `Ctrl + C`.

## 4. Primer arranque: descarga de modelos

La primera vez, la app detecta que faltan los **modelos de segmentación** y ofrece **"Descargar modelos (~550 MB)"**.
Pulse el botón y espere a que la barra llegue al final (una sola vez). Si prefiere no descargarlos, puede subir una
segmentación ya hecha en cada análisis (ver el paso 5, opción avanzada).

## 5. Analizar un paciente

1. En la pantalla de inicio, pulse **"Analizar un paciente"**.
2. **Cargue las resonancias**: arrastre los 4 archivos (o una carpeta, o un `.zip`) a la zona indicada. La app
   reconoce cada una por su nombre; si no puede, podrá asignarlas a mano.
3. **Edad** (opcional): escríbala si la conoce. **Sin edad no hay pronóstico** (la app no la inventa); aun así verá la
   segmentación y los volúmenes.
4. **Modo de segmentación automática**:
   - **Rápido** (recomendado): ~2 minutos.
   - **Completo**: ~12 minutos, algo más preciso.
   - *(Este paso solo aplica si no sube una segmentación propia.)*
5. *(Opcional, avanzado)* Puede **subir una segmentación ya hecha**; entonces se omite la segmentación automática.
6. Pulse **"Analizar paciente"** y espere. La barra muestra las etapas (leer, segmentar, radiómica, pronóstico).

## 6. Leer los resultados

- **Visor 3D**: los tres planos del cerebro con la máscara en colores — **rojo** necrosis/no realzado, **verde** edema,
  **amarillo** realce. Puede cambiar la modalidad y la opacidad de la máscara.
- **Volúmenes** (cm³): tumor completo (WT), núcleo (TC) y realce (ET).
- **Pronóstico**: la clase de supervivencia y los días estimados, con el **desempeño esperado** del modelo. Si dice
  **"No aplica"**, el motivo será que **falta la edad** o que **no hay realce (ET)** — el modelo se entrenó solo con
  tumores con realce, y no inventa un resultado.
- **Vista de control**: una imagen (FLAIR + segmentación) que sirve para el informe.
- Botones para **guardar un informe en PDF** y **descargar** la segmentación y los datos.

> El **informe PDF** incluye volúmenes, pronóstico y la vista de control (no el visor 3D, que no se ve bien impreso).

## 7. Privacidad

- Las imágenes **nunca salen de su equipo**: el servidor solo escucha localmente (`127.0.0.1`).
- Solo se aceptan **NIfTI** (no DICOM), que no suele traer datos personales del paciente.
- Los archivos temporales de cada análisis se **borran al cerrar** la app.

## 8. Si algo falla

- **No abre el navegador:** abra uno manualmente y vaya a la dirección que muestra la ventana negra
  (por ejemplo `http://localhost:8000`).
- **"Formato no válido" / avisos:** revise que sean las 4 resonancias en formato BraTS.
- **Va muy lento o se queda sin memoria:** use el modo **Rápido** y cierre otros programas pesados.
- **Registro para soporte:** la app guarda un registro en `C:\Users\<usted>\.reto-cimat\reto-cimat.log`.
  Adjúntelo si pide ayuda.

---

## Créditos

**Universidad Antonio José Camacho (UNIAJC)** — **Team Camacho**, semilleros **Appliscience** y **SEMOSIMA**.

Autores: **Hejembert Jaramillo, Daniel León, Karen Arroyave, Dylan Cuervo, Nikol López.**

Modelos del proyecto de investigación *reto-CIMAT* (BraTS 2018). Prototipo de investigación, no clínico.
