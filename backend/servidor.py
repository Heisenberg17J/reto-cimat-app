"""Arranca el backend y abre el navegador. Es la 'app' para el usuario comun.

    reto-cimat-servidor                       # puerto libre, abre el navegador
    reto-cimat-servidor --puerto 8000
    reto-cimat-servidor --host 0.0.0.0        # accesible por la IP (util en WSL desde Windows)
    reto-cimat-servidor --sin-navegador

Por defecto solo escucha en 127.0.0.1 (las resonancias no salen del equipo). En WSL, si el
navegador de Windows no llega por localhost, usa --host 0.0.0.0 y entra por la IP de WSL.
"""

import argparse
import platform
import socket
import subprocess
import threading
import webbrowser

import uvicorn

from .app import crear_app


def _puerto_libre(preferido=0):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferido))
        except OSError:
            s.bind(("127.0.0.1", 0))       # el preferido esta ocupado: toma cualquiera
        return s.getsockname()[1]


def _es_wsl():
    return "microsoft" in platform.uname().release.lower()


def _ip_local():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
        except OSError:
            return None


def _abrir_navegador(url):
    """Abre el navegador. En WSL usa el de Windows (webbrowser/gio suele fallar)."""
    if _es_wsl():
        for cmd in (["wslview", url], ["explorer.exe", url], ["cmd.exe", "/c", "start", "", url]):
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except FileNotFoundError:
                continue
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main(argv=None):
    ap = argparse.ArgumentParser(description="Backend local del reto CIMAT (prototipo de investigacion)")
    ap.add_argument("--puerto", type=int, default=0, help="puerto (por defecto, uno libre)")
    ap.add_argument("--host", default="127.0.0.1",
                    help="interfaz donde escuchar (127.0.0.1 por defecto; 0.0.0.0 para acceder por IP)")
    ap.add_argument("--sin-navegador", action="store_true", help="no abrir el navegador")
    ap.add_argument("--autocomprobar", action="store_true",
                    help="importa la pila pesada (torch, nnU-Net, PyRadiomics, sksurv) y sale; "
                         "sirve para validar el empaquetado sin pesos ni datos")
    args = ap.parse_args(argv)

    if args.autocomprobar:
        import sys
        try:
            import torch
            import nnunetv2  # noqa: F401
            from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor  # noqa: F401
            from radiomics import featureextractor  # noqa: F401
            import sksurv  # noqa: F401
            from nucleo import analizar  # noqa: F401
            # torchvision debe registrar sus ops nativas (si no, "operator torchvision::nms does not exist")
            import torchvision  # noqa: F401
            torch.ops.torchvision.nms(torch.zeros((1, 4)), torch.zeros((1,)), 0.5)
            print(f"autocomprobacion OK: torch {torch.__version__}, torchvision {torchvision.__version__} "
                  f"(nms ok), nnU-Net + PyRadiomics + sksurv importados")
            sys.exit(0)
        except Exception as e:  # noqa: BLE001
            print(f"autocomprobacion FALLO: {type(e).__name__}: {e}")
            sys.exit(1)

    puerto = _puerto_libre(args.puerto)
    url_local = f"http://localhost:{puerto}"
    print(f"reto-cimat-app en {url_local}  (Ctrl+C para salir)")
    if args.host == "0.0.0.0":
        ip = _ip_local()
        if ip:
            print(f"   accesible tambien en http://{ip}:{puerto}  (p. ej. desde Windows si WSL)")

    if not args.sin_navegador:
        threading.Timer(1.0, lambda: _abrir_navegador(url_local)).start()

    uvicorn.run(crear_app(), host=args.host, port=puerto, log_level="info")


if __name__ == "__main__":
    main()
