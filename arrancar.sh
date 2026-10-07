#!/usr/bin/env bash
# Arranca el backend del reto CIMAT: activa el entorno conda y levanta el servidor web local.
#
#   ./arrancar.sh                        # puerto libre, abre el navegador
#   ./arrancar.sh --puerto 8000          # puerto fijo
#   ./arrancar.sh --sin-navegador        # no abrir el navegador
#
# Déjalo corriendo en esta terminal mientras pruebas; para salir, Ctrl+C.
set -euo pipefail

ENTORNO="inferencia"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activar conda (busca su base; si no, usa la ruta por defecto de esta máquina)
CONDA_BASE="$(conda info --base 2>/dev/null || echo "$HOME/anaconda3")"
# shellcheck source=/dev/null
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate "$ENTORNO"

cd "$REPO"
echo "Entorno: $ENTORNO | Carpeta: $REPO"
echo "Arrancando el servidor… (Ctrl+C para salir)"
exec reto-cimat-servidor "$@"
