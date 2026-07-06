@echo off
REM Build Windows .exe
REM Execute este script no Windows com Python e PyInstaller instalados

cd /d "%~dp0"

rmdir /s /q build dist 2>nul

pyinstaller --onefile --windowed --noconfirm ^
  --name "scale-generator" ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  --hidden-import "flask" ^
  --hidden-import "sqlite3" ^
  --hidden-import "datetime" ^
  --hidden-import "random" ^
  --hidden-import "json" ^
  --hidden-import "webbrowser" ^
  --hidden-import "threading" ^
  --hidden-import "socket" ^
  --hidden-import "jinja2" ^
  --hidden-import "markupsafe" ^
  --hidden-import "werkzeug" ^
  --hidden-import "click" ^
  --hidden-import "itsdangerous" ^
  --collect-submodules "flask" ^
  app.py

echo.
echo === Build concluido! ===
echo Executavel: dist\scale-generator.exe
echo.
pause
