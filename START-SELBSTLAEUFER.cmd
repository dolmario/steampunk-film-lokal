@echo off
rem Startet den ganzen Ablauf: Figuren, Standbilder, Clips (je Clip frisches ComfyUI) und Rohschnitt.
rem Vorher COMFYUI_DIR auf den ComfyUI-Ordner setzen (Ordner mit main.py) und COMFYUI_PYTHON auf dessen python.exe.
rem Beispiel:  set COMFYUI_DIR=C:\ComfyUI  &  set COMFYUI_PYTHON=C:\ComfyUI\venv\Scripts\python.exe
rem Optional:  set GERAET=meinpc  (Name der Messdatei, Standard: Rechnername)
rem Optional:  set MODELL=dev     (klein4 Standard, klein9 oder dev)
setlocal
if "%COMFYUI_DIR%"=="" (echo COMFYUI_DIR nicht gesetzt & exit /b 1)
if "%COMFYUI_PYTHON%"=="" (echo COMFYUI_PYTHON nicht gesetzt & exit /b 1)
if "%GERAET%"=="" set GERAET=%COMPUTERNAME%
if "%MODELL%"=="" set MODELL=klein4
cd /d "%~dp0runner"
"%COMFYUI_PYTHON%" selbstlaeufer.py --geraet "%GERAET%" --comfyui "%COMFYUI_DIR%" --modell %MODELL%
set FEHLER=%ERRORLEVEL%
if not "%FEHLER%"=="0" echo Abbruch mit Fehlercode %FEHLER%
pause
exit /b %FEHLER%
