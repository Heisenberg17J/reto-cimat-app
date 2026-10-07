"""Linea de comandos.

    python -m nucleo.cli --caso CARPETA [--edad 62] [--segmentacion seg.nii.gz] [--salida DIR]
"""

import argparse
import sys
from pathlib import Path

from . import ErrorEntrada, analizar
from .config import AVISO


def main(argv=None):
    ap = argparse.ArgumentParser(description="Segmentacion + pronostico de un paciente (prototipo)")
    ap.add_argument("--caso", required=True, type=Path, help="carpeta con t1, t1ce, t2 y flair")
    ap.add_argument("--edad", type=float, help="edad en anos; sin ella no hay pronostico")
    ap.add_argument("--segmentacion", type=Path, help="mascara ya hecha (BraTS 0/1/2/4): omite nnU-Net")
    ap.add_argument("--folds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--tta", action="store_true", default=None, help="aumento en prueba con espejos")
    ap.add_argument("--salida", type=Path, help="carpeta de resultados (por defecto salidas/<caso>)")
    args = ap.parse_args(argv)

    print(AVISO + "\n")
    etapa_actual = [None]

    def progreso(etapa, fraccion):
        if etapa != etapa_actual[0]:
            etapa_actual[0] = etapa
            print(f"-> {etapa}")

    try:
        r = analizar(args.caso, edad=args.edad, segmentacion=args.segmentacion, folds=tuple(args.folds),
                     tta=args.tta, salida=args.salida or Path("salidas") / args.caso.resolve().name,
                     progreso=progreso)
    except ErrorEntrada as e:
        sys.stdout.flush()
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    for a in r.avisos_formato:
        print(f"AVISO de formato: {a}")
    print(f"\nsegmentacion: {r.segmentacion}")
    print(f"volumen (cm3): {r.volumen_cm3}")
    p = r.pronostico
    if p["aplica"]:
        print(f"pronostico: {p['clase']} | mediana estimada ~{p['dias_mediana_estimada']:.0f} dias "
              f"| riesgo {p['riesgo']:+.3f}")
    else:
        print(f"pronostico: no aplica. {p['motivo']}")
        for e, v in p.get("solo_referencia_segun_edad (NO es una prediccion)", {}).items():
            print(f"   referencia, si tuviera {e} anos: {v['clase']}, ~{v['dias_mediana_estimada']:.0f} dias")
    print(f"\nsalida: {Path(r.archivos['resultado.json']).parent}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
