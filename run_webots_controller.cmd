@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

if "%WEBOTS_HOME%"=="" (
  if exist "C:\Program Files\Webots" (
    set "WEBOTS_HOME=C:\Program Files\Webots"
  ) else if exist "C:\Program Files (x86)\Webots" (
    set "WEBOTS_HOME=C:\Program Files (x86)\Webots"
  )
)

if "%WEBOTS_HOME%"=="" (
  echo No se pudo detectar WEBOTS_HOME. Define la variable WEBOTS_HOME antes de ejecutar este script.
  exit /b 1
)

set "PYTHONPATH=%WEBOTS_HOME%\lib\controller\python"

if "%WEBOTS_PYTHON_EXECUTABLE%"=="" (
  if exist "%SCRIPT_DIR%.venv-webots\Scripts\python.exe" (
    set "WEBOTS_PYTHON_EXECUTABLE=%SCRIPT_DIR%.venv-webots\Scripts\python.exe"
  ) else (
    set "WEBOTS_PYTHON_EXECUTABLE=python"
  )
)

"%WEBOTS_PYTHON_EXECUTABLE%" "%SCRIPT_DIR%symple_controller_act_2_1.py"
endlocal
