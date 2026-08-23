@echo off
setlocal EnableDelayedExpansion
title UNIVERSAL MATRIX STRESS TEST
color 0B
chcp 65001 >nul

echo ==============================================================================
echo                         E2E MATRIX STRESS TEST
echo ==============================================================================
echo.
echo This terminal will execute the massive matrix stress test across UFO and 
echo BankFidelity engines. It will consume real API tokens (Reducto, Gemini) 
echo and generate hundreds of screenshots to your Desktop.
echo.
echo Press ANY KEY to authenticate screenshots and begin the execution, or 
echo close this window to abort.
echo ==============================================================================
pause

cd /d "C:\ufo\ufo"
python scripts\e2e_matrix_stress_test.py

echo.
echo ==============================================================================
echo Matrix execution complete. Review the report on your Desktop.
echo ==============================================================================
pause
