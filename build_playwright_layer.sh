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
# 1) Instala playwright en la layer (site-packages)
pip install --no-cache-dir --target /opt/layer/python/lib/python${PYVER}/site-packages playwright==1.48.0
# 2) Asegura que Python vea ese site-packages
export PYTHONPATH=/opt/layer/python/lib/python${PYVER}/site-packages:\$PYTHONPATH
# 3) Instala Chromium de Playwright en la carpeta de la layer
export PLAYWRIGHT_BROWSERS_PATH=/opt/layer/playwright/ms-playwright
python -m playwright install chromium
# 4) Limpieza opcional
find /opt/layer/python/lib/python${PYVER}/site-packages -name 'tests' -type d -prune -exec rm -rf {} +
"

echo ">> Empaquetando ZIP de la layer…"
pushd "$LAYER_ROOT" >/dev/null
zip -r ../playwright-layer.zip .
popd >/dev/null

echo ">> Verificando contenido del ZIP:"
unzip -l .layers/playwright-layer.zip | sed -n '1,120p'
echo ">> Listo: .layers/playwright-layer.zip"
