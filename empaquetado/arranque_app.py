"""Punto de entrada de la app portable (Fase 5).

Arranca el servidor local y abre el navegador (igual que `reto-cimat-servidor`). Se congela
con PyInstaller. `freeze_support()` es imprescindible: nnU-Net usa multiprocessing con
'spawn' y, sin él, cada proceso hijo relanzaría la app (bucle de procesos en Windows).
"""

import multiprocessing

from backend.servidor import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
