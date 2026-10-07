# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller: app portable COMPLETA (Fase 5).

Empaqueta el servidor FastAPI + el frontend compilado + el núcleo + PyRadiomics +
scikit-survival + PyTorch (CPU) + nnU-Net, en una carpeta portable. NO incluye los pesos
de nnU-Net (~1 GB): se descargan en el primer arranque (Fase 4) y se verifican con sha256.

Requisitos de build (los cumple la CI, ver .github/workflows/empaquetar.yml):
  - frontend compilado en frontend/dist (npm run build)
  - entorno con torch (CPU) y nnunetv2 instalados, además del backend
  - PyRadiomics compilado (rueda de la Fase 0)

    pyinstaller empaquetado/reto-cimat-app.spec --noconfirm

Nota: congelar nnU-Net es delicado porque descubre clases de entrenador de forma dinámica
(recorre el paquete con pkgutil). Por eso se fuerza a dejar sus .py en disco
(module_collection_mode) y se incluye la variante del entrenador como hidden import.
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

AQUI = Path(SPECPATH).resolve()
RAIZ = AQUI.parent

datas, binaries, hiddenimports = [], [], []


def arbol(origen, destino):
    origen = Path(origen)
    salida = []
    for f in origen.rglob("*"):
        if f.is_file():
            salida.append((str(f), str((Path(destino) / f.relative_to(origen)).parent)))
    return salida


# --- Paquetes con datos/binarios/extensiones C o imports dinámicos ---
PAQUETES = [
    "radiomics", "pykwalify", "ruamel", "pywt",       # radiómica
    "sksurv", "sklearn",                               # pronóstico
    "SimpleITK", "nibabel", "skimage", "scipy", "pandas", "matplotlib",
    "torch", "torchvision", "timm", "nnunetv2",        # segmentación (torchvision: ops nativas como nms)
    "batchgenerators", "batchgeneratorsv2", "acvl_utils", "dynamic_network_architectures",
    "fastapi", "starlette", "uvicorn", "anyio", "multipart",  # backend
    "einops", "tqdm", "yaml", "seaborn", "blosc2", "threadpoolctl",  # deps que nnU-Net suele arrastrar
]
for paquete in PAQUETES:
    try:
        d, b, h = collect_all(paquete)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass  # opcional/ausente: el build en CI delataría lo que falte

# uvicorn carga sus protocolos/loops por nombre: hay que declararlos.
hiddenimports += [
    "uvicorn.lifespan.on", "uvicorn.lifespan.off",
    "uvicorn.loops.auto", "uvicorn.loops.asyncio",
    "uvicorn.protocols.http.auto", "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets.auto", "uvicorn.protocols.websockets.websockets_impl",
    "pywt._extensions._pywt",
]

# --- Datos de la app (lo que se lee en ejecución) ---
# Artefactos PEQUEÑOS (nunca los pesos: artefactos/nnunet queda fuera a propósito).
for nombre in ("params_brats2018_v0.yaml", "pronostico_coxnet.joblib", "pronostico_coxnet.json",
               "postproceso_et.json", "SHA256SUMS", "PROCEDENCIA.md"):
    datas += [(str(RAIZ / "artefactos" / nombre), "artefactos")]
# Frontend compilado y datos del backend.
datas += arbol(RAIZ / "frontend" / "dist", "frontend/dist")
datas += arbol(RAIZ / "backend" / "estatico", "backend/estatico")
datas += [(str(RAIZ / "backend" / "pesos_manifiesto.json"), "backend")]

excludes = ["pytest", "IPython", "notebook", "tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6"]

a = Analysis(
    [str(AQUI / "arranque_app.py")],
    pathex=[str(RAIZ)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(AQUI / "hook_runtime_artefactos.py")],
    excludes=excludes,
    noarchive=False,
    optimize=0,
    # nnU-Net descubre clases recorriendo el paquete: deja sus .py en disco, no solo en el zip.
    module_collection_mode={
        "nnunetv2": "pyz+py",
        "dynamic_network_architectures": "pyz+py",
    },
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="reto-cimat-app",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="reto-cimat-app")
