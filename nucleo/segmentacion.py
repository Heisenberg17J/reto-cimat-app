"""Segmentacion con nnU-Net (opcional) y posprocesado de ET.

nnU-Net y PyTorch solo se importan si se usan: sin ellos el nucleo funciona igual
cuando la segmentacion llega ya hecha (por ejemplo, desde Colab).
"""

import json
from pathlib import Path

import nibabel as nib
import numpy as np

from .config import MODALIDADES, MODELO_NNUNET, POSPROCESO

BRATS_A_NNUNET = {0: 0, 2: 1, 1: 2, 4: 3}     # edema 2->1, necrosis 1->2, realce 4->3
NNUNET_A_BRATS = {v: k for k, v in BRATS_A_NNUNET.items()}


def reasignar(seg, mapa):
    """Cambia etiquetas segun mapa; falla con cualquier etiqueta no prevista."""
    inesperadas = set(np.unique(seg).tolist()) - set(mapa)
    if inesperadas:
        raise ValueError(f"etiquetas inesperadas: {sorted(inesperadas)}")
    nueva = np.zeros_like(seg, dtype=np.uint8)
    for origen, destino in mapa.items():
        nueva[seg == origen] = destino
    return nueva


def umbral_et():
    return json.loads(Path(POSPROCESO).read_text())["umbral_casos_nuevos"]


def posprocesar_et(seg_nnunet, umbral=None):
    """ET predicho por debajo del umbral -> necrosis/no realzado; devuelve (etiquetas BraTS, info)."""
    umbral = umbral_et() if umbral is None else umbral
    seg = np.asarray(seg_nnunet).astype(np.int16)
    n_et = int((seg == 3).sum())
    descartado = 0 < n_et < umbral
    if descartado:
        seg = seg.copy()
        seg[seg == 3] = 2
    return reasignar(seg, NNUNET_A_BRATS), {"voxeles_et_predichos": n_et, "et_descartado": descartado,
                                            "umbral": umbral}


def validar_segmentacion(seg):
    etiquetas = set(np.unique(seg).tolist())
    if not etiquetas <= {0, 1, 2, 4}:
        raise ValueError(f"la segmentacion debe tener etiquetas BraTS 0/1/2/4; tiene {sorted(etiquetas)}")


def registrar_entrenador():
    """nnU-Net necesita encontrar la clase del entrenador con la que se guardaron los pesos."""
    import nnunetv2
    destino = Path(nnunetv2.__path__[0]) / "training" / "nnUNetTrainer" / "variants" / \
        "nnUNetTrainer_100epochs_ckpt5.py"
    if not destino.exists():
        destino.write_text(
            "from nnunetv2.training.nnUNetTrainer.variants.training_length.nnUNetTrainer_Xepochs "
            "import nnUNetTrainer_100epochs\n\n\n"
            "class nnUNetTrainer_100epochs_ckpt5(nnUNetTrainer_100epochs):\n"
            "    def on_train_start(self):\n"
            "        super().on_train_start()\n"
            "        self.save_every = 5\n")


def nnunet_disponible():
    try:
        import nnunetv2  # noqa: F401
        import torch     # noqa: F401
    except ImportError:
        return False
    return (Path(MODELO_NNUNET) / "plans.json").exists()


def segmentar_nnunet(rutas, trabajo, folds=(0, 1, 2, 3, 4), tta=None):
    """Devuelve (segmentacion en etiquetas nnU-Net, imagen de referencia, dispositivo)."""
    import torch
    from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor

    if not (Path(MODELO_NNUNET) / "plans.json").exists():
        raise FileNotFoundError(f"no estan los pesos de nnU-Net en {MODELO_NNUNET}")
    registrar_entrenador()
    disp = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if tta is None:                       # en GPU vale la pena; en CPU lo hace ~8x mas lento
        tta = disp.type == "cuda"
    pred = nnUNetPredictor(tile_step_size=0.5, use_gaussian=True, use_mirroring=tta,
                           device=disp, verbose=False, allow_tqdm=False)
    pred.initialize_from_trained_model_folder(str(MODELO_NNUNET), use_folds=tuple(folds),
                                              checkpoint_name="checkpoint_final.pth")
    pred.predict_from_files([[str(rutas[m]) for m in MODALIDADES]], [str(Path(trabajo) / "nnunet")],
                            save_probabilities=False, overwrite=True,
                            num_processes_preprocessing=1, num_processes_segmentation_export=1)
    img = nib.load(Path(trabajo) / "nnunet.nii.gz")
    return np.asanyarray(img.dataobj).astype(np.int16), img, f"{disp.type}, folds {list(folds)}, TTA {tta}"
