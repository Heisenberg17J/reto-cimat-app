"""Punto de entrada del binario empaquetado (Fase 0).

Equivale al script de consola `reto-cimat-analizar`, pero como archivo real para que
PyInstaller lo congele. No añade logica: solo llama a `nucleo.cli.main`.
"""

import sys

from nucleo.cli import main

if __name__ == "__main__":
    sys.exit(main())
