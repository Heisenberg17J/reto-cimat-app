# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller: CLI minimo del nucleo, para la Fase 0 (viabilidad del empaquetado).

Empaqueta SOLO la linea de comandos y la pila cientifica (PyRadiomics, scikit-survival,
SimpleITK, nibabel, matplotlib...). NO incluye PyTorch ni nnU-Net: este binario analiza a
partir de una segmentacion ya hecha (--segmentacion). Su unico fin es demostrar que, en un
Windows (o Linux) sin Python instalado, el nucleo arranca y da los mismos numeros (paso 5).

    pyinstaller empaquetado/reto-cimat-cli.spec --noconfirm
    dist/reto-cimat-analizar/reto-cimat-analizar --caso CARPETA --edad 62 \
        --segmentacion segmentacion.nii.gz
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

AQUI = Path(SPECPATH).resolve()          # empaquetado/
RAIZ = AQUI.parent                        # raiz del repo

datas, binaries, hiddenimports = [], [], []

# Paquetes con datos (esquemas YAML) o extensiones C que PyInstaller no detecta solo.
for paquete in ("radiomics", "pykwalify", "sksurv", "SimpleITK", "nibabel", "ruamel", "pywt"):
    try:
        d, b, h = collect_all(paquete)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass  # paquete opcional no instalado: el smoke test lo delataria

# sklearn: el modelo .joblib (StandardScaler + Coxnet) carga clases por nombre.
hiddenimports += collect_submodules("sklearn")
hiddenimports += ["pywt._extensions._pywt"]

# Artefactos (YAML de PyRadiomics, modelo de pronostico, umbral de ET): se leen en
# ejecucion; el runtime hook apunta NUCLEO_ARTEFACTOS aqui.
datas += [(str(RAIZ / "artefactos"), "artefactos")]

# Fuera lo pesado que el CLI minimo NO usa (reduce el binario varios GB).
excludes = [
    "torch", "torchvision", "torchaudio", "nnunetv2", "nnunetv1",
    "pytest", "IPython", "notebook", "tkinter",
    "PyQt5", "PyQt6", "PySide2", "PySide6",
]

a = Analysis(
    [str(AQUI / "arranque_cli.py")],
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
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="reto-cimat-analizar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="reto-cimat-analizar",
)
