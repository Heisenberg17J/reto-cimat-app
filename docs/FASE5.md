# Fase 5 · Ejecutable portable y publicación

**Objetivo:** que una persona común descargue **un solo archivo**, lo descomprima y haga doble clic para abrir la app en
el navegador, **sin instalar Python, Node ni nada**. Sin instalador (se evita el aviso extra de SmartScreen de un `.exe`
de instalación).

## Qué produce

El workflow `.github/workflows/empaquetar.yml` construye en `windows-latest` y `ubuntu-latest` una **carpeta portable**
con PyInstaller y la comprime:

- `reto-cimat-app-windows.zip` → al descomprimir, `reto-cimat-app/reto-cimat-app.exe` (doble clic → abre el navegador).
- `reto-cimat-app-linux.zip` → `reto-cimat-app/reto-cimat-app`.

Incluye: servidor FastAPI + frontend compilado (`frontend/dist`) + núcleo + PyRadiomics + scikit-survival + PyTorch (CPU)
+ nnU-Net + los artefactos pequeños. **No** incluye los pesos de nnU-Net (~1 GB): se **descargan en el primer arranque**
(Fase 4) y se verifican con sha256. Tamaño esperado del zip: ~0.5–1 GB (por PyTorch CPU).

## Cómo construir y publicar

- **A mano:** pestaña *Actions → "Fase 5 - empaquetar app portable" → Run workflow*. Deja los `.zip` como artefactos.
- **Publicar en un Release:** crear y empujar una etiqueta `app-v*`:
  ```bash
  git tag app-v1 && git push origin app-v1
  ```
  El workflow adjunta los dos `.zip` al Release de esa etiqueta.

## Piezas (en `empaquetado/`)

| Archivo | Qué es |
|---|---|
| `arranque_app.py` | Punto de entrada congelado: `multiprocessing.freeze_support()` + arranca el servidor |
| `reto-cimat-app.spec` | Receta de PyInstaller de la app completa (incluye torch + nnU-Net; excluye los pesos) |
| `hook_runtime_artefactos.py` | Apunta `NUCLEO_ARTEFACTOS` a los artefactos empaquetados (compartido con la Fase 0) |

## Puntos delicados (validación en CI)

- **nnU-Net congelado.** nnU-Net descubre las clases de entrenador recorriendo su paquete (`pkgutil`), lo que suele
  fallar en apps congeladas porque los `.py` quedan en un zip. El spec fuerza a dejar sus fuentes en disco
  (`module_collection_mode = {"nnunetv2": "pyz+py", ...}`). La prueba definitiva es **descargar el artefacto de la CI y
  correr una segmentación real** (no cubierta por el smoke test, que solo arranca el servidor y comprueba `/api/salud`).
  Es probable que los primeros builds necesiten añadir algún *hidden import* que PyInstaller no detecte; se afina ahí.
- **El build es pesado** (~1–2 GB por PyTorch). Se hace en la CI (RAM de sobra) y no en cada push. **No se construye en
  local** en equipos con poca RAM (p. ej. WSL de 8 GB) para no provocar un OOM.
- **SmartScreen.** Al ser un portable sin firmar, Windows puede avisar la primera vez ("Más información → Ejecutar de
  todas formas"). Documentar esto para el usuario, o conseguir un certificado de firma de código.

## Estado

Configuración lista (spec + workflow + lanzador), validada en sintaxis. **Pendiente:** el primer build real en la CI y
confirmar la segmentación con nnU-Net desde el artefacto empaquetado (afinando *hidden imports* si hace falta).
