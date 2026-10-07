# Plan de la aplicación

**Objetivo:** que una **persona común** pueda, en **Windows** (Linux después), analizar un paciente **en el navegador**,
sin usar la terminal, sin Docker y sin internet (salvo una descarga inicial de los pesos). La app es un **servidor web
local**: corre en la propia máquina (`127.0.0.1`) y se abre en el navegador; **las imágenes nunca salen del equipo.**

> **Cambio de rumbo (2026-10-06):** en lugar de una app de escritorio con instalador (pywebview + Inno Setup), usamos un
> **frontend web servido por el backend local**. Se arranca con un ejecutable portable (o un `.bat`/`.sh`) que levanta el
> servidor y abre el navegador. Menos fricción (no hay instalación ni aviso de SmartScreen), mismo código.

## Arquitectura

```
┌──────────────── App web local (un solo proceso en la máquina del usuario) ─────────────┐
│  Navegador  ──abre──▶  http://127.0.0.1:PUERTO                                         │
│     │  Interfaz web (React + NiiVue; de momento, página mínima en backend/estatico)   │
│     ▼                                                                                  │
│  Backend FastAPI (sirve el frontend y la API; solo escucha en 127.0.0.1)              │
│     │  una tarea a la vez, en segundo plano, con progreso por etapas                   │
│     ▼                                                                                  │
│  nucleo.analizar()  →  nnU-Net (CPU/GPU) + PyRadiomics + Cox                           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

| Decisión | Elección | Por qué |
|---|---|---|
| Interfaz | **React + [NiiVue](https://github.com/niivue/niivue)** | NiiVue es un visor de resonancias para el navegador (WebGL): tres planos, máscara superpuesta, contraste. Se ve profesional y no hay que programar un visor |
| Backend | **FastAPI** local (solo `127.0.0.1`, puerto libre) | Envuelve `nucleo.analizar()` sin reescribirlo; las tareas largas (minutos) corren en segundo plano con progreso. Sirve también el frontend |
| Acceso | **Navegador del sistema** | No hace falta ventana nativa ni instalador: el servidor local abre el navegador en `127.0.0.1`. Las imágenes no salen del equipo |
| Empaquetado | **PyInstaller (carpeta/portable)** en Windows; **AppImage** en Linux | Lleva su propio Python: el usuario no instala nada. Un ejecutable que arranca el servidor y abre el navegador; **sin instalador** (sin aviso de SmartScreen de un `.exe` de instalación) |
| PyRadiomics | **Compilarlo nosotros** en GitHub Actions | **No hay versión compilada para Windows** (ni en pip ni en conda-forge, verificado el 2026-10-06). Compilarlo exige Visual Studio Build Tools, imposible de pedir a un usuario común |
| Pesos de nnU-Net | Descarga en el **primer arranque** (GitHub Releases), con barra de progreso y verificación sha256 | Mantiene pequeño el instalador; alternativa: un instalador "completo" que los incluya |
| PyTorch | Versión **CPU** por defecto | Funciona en cualquier PC. La GPU NVIDIA es una mejora opcional posterior (la versión CUDA pesa varios GB más) |
| Descartado: Docker | — | Pide instalar Docker Desktop, WSL2 y virtualización: demasiado para un usuario común |
| Descartado: Gradio | — | Bueno para demos, pero visualmente limitado y sin aspecto de app instalada |

## Fases

### Fase 0 · Viabilidad del empaquetado ⚠️ (hacer primero: es el mayor riesgo)
Antes de construir la interfaz, comprobar que el núcleo funciona **en Windows**, empaquetado:
1. Workflow de GitHub Actions (`windows-latest` y `ubuntu-latest`), con Python 3.11 y numpy 1.26.4: compilar la rueda de
   `pyradiomics==3.0.1` (MSVC en el runner de Windows) y guardarla como artefacto.
2. Instalar el núcleo con esa rueda y correr las pruebas que no necesitan imágenes (artefactos y errores de entrada).
3. **Regresión en un Windows real:** con `datos_prueba/` (que no va en git, por la licencia de BraTS), en un PC con
   Windows: `pytest` completo. **Criterio de éxito:** las 1146 características son iguales a las del estudio (tolerancia
   1e-9) y el riesgo da −0.778728.
4. Probar nnU-Net en CPU en Windows con un paciente: tiempo y RAM (objetivo: < 10 min con 1 fold y < 8 GB de RAM).
5. Un PyInstaller mínimo (solo `nucleo.cli`) que corra en un Windows **sin Python instalado**.

Si 3 o 5 fallan, se resuelve aquí. No avanzar a la interfaz con este riesgo abierto.

### Fase 1 · Núcleo ✅ (hecha)
`nucleo/` con `analizar()`, línea de comandos y 6 pruebas de regresión.

### Fase 2 · Backend FastAPI (`backend/`) ✅ (hecha)
- `POST /api/analisis`: recibe las 4 resonancias (sueltas o en un `.zip`), la edad opcional y la segmentación opcional.
  Valida y devuelve un `id`.
- `GET /api/analisis/{id}`: estado, etapa, fracción de avance, errores (`ErrorEntrada`, como mensaje para el usuario) y
  resultado.
- `GET /api/analisis/{id}/archivo/{nombre}`: segmentación, resonancias para el visor, `vista.png` y `resultado.json`.
- `DELETE /api/analisis/{id}`: borra los archivos del análisis.
- **Una tarea a la vez:** la CPU no da para más; las demás esperan en cola (un hilo trabajador). Los temporales se borran
  al cerrar la app.
- Lanzador `reto-cimat-servidor`: arranca uvicorn en un puerto libre de `127.0.0.1` y abre el navegador.
- Sirve el frontend: el compilado de `frontend/dist` (Fase 3) o, de momento, la página mínima de `backend/estatico/`.
- Pruebas con `TestClient` (`tests/test_backend.py`): el resultado del API es igual al de `nucleo.analizar()`
  (mismos volúmenes y riesgo que la regresión del núcleo).

### Fase 3 · Interfaz (`frontend/`, React + Vite + NiiVue) ✅ (v1 hecha)
Pantallas, en español y sin tecnicismos:
1. **Inicio:** qué hace la app, el aviso "no clínico" y el botón "Analizar un paciente".
2. **Carga:** arrastrar los 4 archivos, la carpeta o un `.zip`. Reconoce cada resonancia por su nombre y, si no puede, deja
   asignarla a mano. Edad opcional, explicando que sin ella no hay pronóstico. Opción avanzada: subir una segmentación.
3. **Progreso:** las etapas con barra y tiempo estimado (la segmentación en CPU tarda minutos).
4. **Resultados:**
   - visor NiiVue con los tres planos, la máscara en colores (rojo necrosis, verde edema, amarillo realce), opacidad y
     modalidad;
   - tarjeta de volúmenes (cm³);
   - tarjeta de pronóstico: clase y días, el desempeño esperado y la curva "cómo cambia con la edad"; o "no aplica" con
     el motivo;
   - botones para exportar un informe PDF y la segmentación.

La interfaz compilada (archivos estáticos de `frontend/dist`) la sirve el mismo FastAPI.

**Estado v1:** las 4 pantallas están hechas (`frontend/src/componentes/`): inicio, carga (arrastrar archivos/carpeta/`.zip`,
reconocer modalidades por nombre o asignarlas a mano, edad opcional, segmentación avanzada), progreso por etapas, y
resultados con **visor NiiVue** (modalidad, opacidad de la máscara, colores BraTS), volúmenes, pronóstico (o "no aplica")
y descargas. El informe PDF se genera con `window.print()` (estilos de impresión); la "curva según la edad" se muestra
como tabla de referencia (40–80 años). **Pendiente de probar en un navegador real** (el visor WebGL no se puede validar
sin pantalla). Desarrollo: `cd frontend && npm install && npm run build`; en dev, `npm run dev` + `reto-cimat-servidor
--puerto 8000 --sin-navegador` (Vite manda `/api` al backend).

### Fase 4 · Arranque y primer uso (en `backend/`) ✅ (v1 hecha)
- ✅ Lanzador que levanta el servidor y abre el navegador (`reto-cimat-servidor`; en WSL abre el navegador de Windows y
  admite `--host 0.0.0.0`).
- ✅ **Modo rápido (1 fold, por defecto) / completo (5 folds)**: `POST /api/analisis` acepta `modo`; selector en la carga.
- ✅ **Pesos de nnU-Net:** `backend/pesos.py` + `pesos_manifiesto.json`. `GET /api/pesos` informa si faltan; si hay URL
  (manifiesto o `NUCLEO_PESOS_URL`), `POST /api/pesos/descargar` los baja con barra, verifica sha256 y extrae. El
  frontend (`AvisoPesos`) lo ofrece en el inicio. **La URL real queda pendiente de la publicación en Releases (Fase 5);**
  mientras tanto se copian a mano o se usa `NUCLEO_PESOS_URL`.
- ✅ **Registro** de actividad y errores a `~/.reto-cimat/reto-cimat.log` (rota; `NUCLEO_DATOS` cambia la carpeta).
- Pendiente (menor): elegir **carpeta de resultados** persistente e **idioma** (la app es español-primero).

### Fase 5 · Ejecutable portable y publicación ⏳ (configurada; build en CI)
- ✅ GitHub Actions (`.github/workflows/empaquetar.yml`): PyInstaller (carpeta) en Windows y Linux, empaquetando servidor
  + frontend + núcleo + torch + nnU-Net; comprime en `.zip`. **Sin instalador.** No incluye los pesos (se descargan en el
  primer arranque, Fase 4). Base: Fase 0 (`empaquetado/`). Ver `docs/FASE5.md`.
- ✅ Publicación: al etiquetar `app-v*`, adjunta los `.zip` al Release.
- **Pendiente:** primer build real en CI y confirmar la segmentación con nnU-Net desde el artefacto (afinar *hidden
  imports*; nnU-Net congelado es lo delicado). **SmartScreen:** portable sin firmar → documentar "Ejecutar de todas
  formas" o firmar. Tamaño esperado ~1–2 GB (PyTorch CPU). (Linux: de momento `.zip`, no `.AppImage`).

### Fase 6 · (Futuro) Preprocesamiento de resonancias clínicas
Para aceptar resonancias reales del hospital (DICOM), habría que convertirlas a formato BraTS:
- DICOM → NIfTI (`dcm2niix`);
- co-registro de las 4 secuencias;
- extracción de cráneo (HD-BET);
- registro al atlas SRI24 y re-muestreo a 1 mm.

Es un proyecto en sí mismo, con su propia validación (BraTS Toolkit hace todo esto). Mientras no exista, la app acepta
**solo NIfTI en formato BraTS** y lo dice claramente.

### Fase 7 · Validación con usuarios
- Guía de usuario con capturas.
- Prueba con 2–3 personas no técnicas: ¿lo instalan?, ¿entienden los resultados y los avisos?
- Prueba de regresión final: la app instalada da los mismos números que el núcleo.
