set -euo pipefail

LAYER_ROOT=".layers/playwright"
PYVER="3.12"

echo ">> Limpiando carpeta de layer…"
rm -rf "$LAYER_ROOT"
mkdir -p "$LAYER_ROOT/python/lib/python${PYVER}/site-packages"

echo ">> Construyendo layer dentro de Amazon Linux (Lambda Python ${PYVER})…"
docker run --rm -v "$(pwd)/$LAYER_ROOT":/opt/layer \
  public.ecr.aws/lambda/python:${PYVER} \
  /bin/bash -lc "
set -e
python -m pip install --upgrade pip
# 1) Instala playwright y deps (incluye greenlet compilado) en la layer
pip install --no-cache-dir --target /opt/layer/python/lib/python${PYVER}/site-packages playwright==1.48.0
# 2) Instala Chromium de Playwright (+ libs) y copia la cache al layer
python -m playwright install chromium
mkdir -p /opt/layer/playwright
cp -r /root/.cache/ms-playwright /opt/layer/playwright/
# 3) Limpiezas opcionales para reducir tamaño:
find /opt/layer/python/lib/python${PYVER}/site-packages -name \"tests\" -type d -prune -exec rm -rf {} +
"

echo ">> Empaquetando ZIP de la layer…"
pushd "$LAYER_ROOT" >/dev/null
zip -r ../playwright-layer.zip .
popd >/dev/null

echo ">> Listo: .layers/playwright-layer.zip"
unzip -l .layers/playwright-layer.zip | head -n 50
