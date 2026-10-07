"""Figura de control: FLAIR con la segmentacion, en los tres planos por el centro del nucleo."""

import nibabel as nib
import numpy as np

COLORES_RGBA = [(0, 0, 0, 0), (0.9, 0.1, 0.1, 1), (0.1, 0.8, 0.2, 1), (1.0, 0.85, 0.0, 1)]


def figura(ruta_flair, seg, destino, titulo):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    colores = ListedColormap(COLORES_RGBA)
    s = np.select([seg == 1, seg == 2, seg == 4], [1, 2, 3], 0)     # 1 necrosis, 2 edema, 3 realce
    flair = np.asanyarray(nib.load(ruta_flair).dataobj)
    nucleo = np.isin(s, (1, 3)) if np.isin(s, (1, 3)).any() else s > 0
    cx, cy, cz = (np.round(np.argwhere(nucleo).mean(axis=0)).astype(int) if nucleo.any()
                  else np.array(s.shape) // 2)
    cortes = [("axial", lambda a: np.rot90(a[:, :, cz])), ("coronal", lambda a: np.rot90(a[:, cy, :])),
              ("sagital", lambda a: np.rot90(a[cx, :, :]))]
    fig, ejes = plt.subplots(1, 3, figsize=(13, 4.8))
    for eje, (nombre, corte) in zip(ejes, cortes):
        eje.imshow(corte(flair), cmap="gray")
        eje.imshow(corte(s), cmap=colores, vmin=0, vmax=3, alpha=0.45, interpolation="nearest")
        eje.set_title(f"FLAIR, {nombre}")
        eje.axis("off")
    fig.legend(handles=[Patch(color=colores(1), label="necrosis / no realzado"),
                        Patch(color=colores(2), label="edema"), Patch(color=colores(3), label="realce (ET)")],
               loc="lower center", ncol=3, frameon=False)
    fig.suptitle(titulo, fontsize=10)
    fig.tight_layout(rect=(0, 0.07, 1, 0.94))
    fig.savefig(destino, dpi=110)
    plt.close(fig)
