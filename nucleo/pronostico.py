"""Pronostico con el modelo final del estudio (Cox Elastic Net, D30).

El modelo se entreno con 163 HGG, todos con realce (ET). Depende casi solo de la edad:
c-index esperado 0.622 frente a 0.624 de la edad sola (validacion cruzada 5 x 10, D27).
"""

from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from .config import CLASES, MODELO_PRONOSTICO

EDADES_REFERENCIA = (40, 50, 60, 70, 80)


@lru_cache(maxsize=1)
def cargar_modelo(ruta=str(MODELO_PRONOSTICO)):
    return joblib.load(ruta)


def mediana_dias(funciones):
    """Mediana de supervivencia de cada S(t); si nunca baja de 0.5, el ultimo tiempo."""
    return np.array([f.x[np.argmax(f.y <= 0.5)] if (f.y <= 0.5).any() else f.x[-1] for f in funciones])


def predecir_coxnet(ajuste, clin, X):
    """Riesgo y mediana de supervivencia (dias); identico a pronostico/brazos.py del estudio."""
    A = ajuste["escalador"].transform(pd.concat([clin, X], axis=1)[ajuste["columnas"]])
    m, a = ajuste["modelo"], ajuste["alpha"]
    return m.predict(A, alpha=a), mediana_dias(m.predict_survival_function(A, alpha=a))


def clase_desde_riesgo(modelo, riesgo):
    c = modelo["cortes"]
    return 0 if riesgo >= c["corta_si_riesgo_>="] else (1 if riesgo >= c["media_si_riesgo_>="] else 2)


def _uno(modelo, X, edad):
    r, d = predecir_coxnet(modelo, pd.DataFrame([{"edad": float(edad)}]), X)
    k = clase_desde_riesgo(modelo, r[0])
    return float(r[0]), k, float(d[0])


def pronosticar(caract, edad, estados):
    """Dict con 'aplica' y, si aplica, riesgo, clase y dias. Sin edad o sin ET no hay pronostico."""
    modelo = cargar_modelo()
    faltan = [c for c in modelo["columnas_radiomicas"] if not np.isfinite(caract.get(c, np.nan))]
    if faltan:
        sin = sorted({c.split("_")[1] for c in faltan})
        return {"aplica": False,
                "motivo": f"faltan regiones {sin} (estado: {estados}). El modelo se entreno con HGG, todos "
                          f"con realce (ET), y no se puede aplicar sin el. Un ET vacio puede indicar un tumor "
                          f"de bajo grado, o un realce pequeno que el posprocesado descarto."}
    X = pd.DataFrame([{c: caract[c] for c in modelo["columnas_radiomicas"]}])
    referencia = {str(e): {"clase": CLASES[k], "dias_mediana_estimada": d}
                  for e in EDADES_REFERENCIA for _, k, d in [_uno(modelo, X, e)]}
    desempeno = modelo["meta"]["desempeno_esperado_cv_5x10 (D27)"]
    if edad is None:
        # La edad lleva casi toda la senal; imputarla daria solo el promedio de la cohorte
        return {"aplica": False,
                "motivo": "falta la edad. El modelo depende casi por completo de ella y no se imputa: "
                          "con la edad media, el resultado seria solo el promedio de la cohorte.",
                "solo_referencia_segun_edad (NO es una prediccion)": referencia,
                "desempeno_esperado": desempeno}
    riesgo, k, dias = _uno(modelo, X, edad)
    return {"aplica": True, "riesgo": riesgo, "clase": CLASES[k], "clase_id": k,
            "dias_mediana_estimada": dias, "segun_edad (referencia)": referencia,
            "desempeno_esperado": desempeno}
