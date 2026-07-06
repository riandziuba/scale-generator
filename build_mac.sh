#!/bin/bash
# Build macOS .app
set -e

cd "$(dirname "$0")"

rm -rf build dist

python3 -m PyInstaller --onefile --windowed --noconfirm \
  --name "scale-generator" \
  --add-data "templates:templates" \
  --add-data "static:static" \
  --hidden-import "flask" \
  --hidden-import "sqlite3" \
  --hidden-import "datetime" \
  --hidden-import "random" \
  --hidden-import "json" \
  --hidden-import "webbrowser" \
  --hidden-import "threading" \
  --hidden-import "socket" \
  --hidden-import "jinja2" \
  --hidden-import "markupsafe" \
  --hidden-import "werkzeug" \
  --hidden-import "click" \
  --hidden-import "itsdangerous" \
  --collect-submodules "flask" \
  app.py

echo ""
echo "=== Build concluído! ==="
echo "Executável: dist/scale-generator"
echo ""
echo "Para criar um .app com ícone, execute o script build_app_mac.sh"
