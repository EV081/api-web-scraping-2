set -euo pipefail

PYVER="3.12"
LAYER_ROOT=".layers/playwright"

echo ">> Limpiando carpeta de layer…"
rm -rf "$LAYER_ROOT"
mkdir -p "$LAYER_ROOT/python/lib/python${PYVER}/site-packages"

echo ">> Construyendo layer dentro de Amazon Linux (Lambda Python ${PYVER})…"
docker run --rm \
  --entrypoint /bin/bash \
  -v "$(pwd)/$LAYER_ROOT":/opt/layer \
  public.ecr.aws/lambda/python:${PYVER} \
  -lc "
set -e
python -m pip install --upgrade pip
# 1) Instala playwright (incluye greenlet compilado) en site-packages de la layer
pip install --no-cache-dir --target /opt/layer/python/lib/python${PYVER}/site-packages playwright==1.48.0
# 2) Instala Chromium de Playwright y copia la cache a la layer
python -m playwright install chromium
mkdir -p /opt/layer/playwright
cp -r /root/.cache/ms-playwright /opt/layer/playwright/
# 3) Limpieza opcional para reducir tamaño
find /opt/layer/python/lib/python${PYVER}/site-packages -name 'tests' -type d -prune -exec rm -rf {} +
"

echo ">> Empaquetando ZIP de la layer…"
pushd "$LAYER_ROOT" >/dev/null
zip -r ../playwright-layer.zip .
popd >/dev/null

echo ">> Comprobando contenido del ZIP:"
unzip -l .layers/playwright-layer.zip | sed -n '1,80p'

echo ">> Listo: .layers/playwright-layer.zip"
