@echo off
chcp 65001 >nul
title Compilador TidyDesk AI v2.1 (.exe)
echo ========================================================
echo   Compilando TidyDesk AI v2.1 a Ejecutable Nativo (.exe)
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] Verificando PyInstaller y dependencias...
python -m pip install --break-system-packages pyinstaller -q

echo [2/3] Generando icono nativo (.ico)...
python -c "import sys; sys.path.insert(0, 'backend'); from tray_app import create_tray_icon_image; img = create_tray_icon_image(True); img.save('tidydesk.ico', format='ICO', sizes=[(64,64), (32,32), (16,16)])"

echo [3/3] Empaquetando TidyDesk_AI.exe (Ventana Nativa + System Tray)...
python -m PyInstaller --noconfirm --onefile --noconsole ^
    --name "TidyDesk_AI" ^
    --icon "tidydesk.ico" ^
    --paths "backend" ^
    --add-data "frontend;frontend" ^
    --hidden-import "tkinter" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "uvicorn.logging" ^
    --hidden-import "uvicorn.loops" ^
    --hidden-import "uvicorn.loops.auto" ^
    --hidden-import "uvicorn.protocols" ^
    --hidden-import "uvicorn.protocols.http" ^
    --hidden-import "uvicorn.protocols.http.auto" ^
    --hidden-import "uvicorn.protocols.websockets" ^
    --hidden-import "uvicorn.protocols.websockets.auto" ^
    --hidden-import "uvicorn.lifespan" ^
    --hidden-import "uvicorn.lifespan.on" ^
    backend\tray_app.py

echo.
echo ========================================================
echo   COMPILACION FINALIZADA CON EXITO!
echo   Tu ejecutable portable se encuentra en: dist\TidyDesk_AI.exe
echo ========================================================
pause
