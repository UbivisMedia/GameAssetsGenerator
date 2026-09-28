@echo off
title GameAssetGenerator Studio
echo ========================================================
echo   Starting GameAssetGenerator Studio
echo ========================================================
echo.

where py >nul 2>&1
if not errorlevel 1 goto use_py

where python >nul 2>&1
if not errorlevel 1 goto use_python

echo ERROR: Neither 'py' nor 'python' was found in PATH!
pause
exit /b 1

:use_py
echo Starting with Python Launcher py -3.10...
py -3.10 main.py
goto end

:use_python
echo Starting with Python...
python main.py
goto end

:end
pause
