@echo off
setlocal EnableDelayedExpansion
title SYSTEM ORCHESTRATOR
color 0B
chcp 65001 >nul

echo Initializing SYSTEM...
if exist "C:\ufo\ufo\desktop_launchers\BankFidelity_Matrix.ps1" (
    powershell -ExecutionPolicy Bypass -File "C:\ufo\ufo\desktop_launchers\BankFidelity_Matrix.ps1"
)

:menu
cls
echo ==============================================================================================================
echo                                         SYSTEM ORCHESTRATOR
echo ==============================================================================================================
echo.
echo   [1] PROTOCOL: OMNI-PARSE    (PDF Extraction, Cryptographic Ledger Math, Multi-AI Fallback, Statement Auditing)
echo   [2] INTERFACE: SYNAPSE      (Interactive REPL, Natural Language UI Control, Desktop Automation, Semantic Mapping)
echo   [3] DIAGNOSTIC: PHANTOM     (Visual E2E Test, Unattended Notepad Automation, Screenshot Verification, Sanity Check)
echo   [4] INTERFACE: OVERSEER     (Legacy UFO Control Panel, Manual Agent Dispatch, Raw Task Input)
echo   [5] DIRECTIVE: BLACKOUT     (Offline Mode, Local 12GB Vision Models, Llama-Server, Qwen-VL, Port Proxy)
echo   [6] SYSTEM: NEURAL-LINK     (Master API Keys, Agent Model Routing, Execution Timeouts, Global Settings Editor)
echo   [7] AUDIT: PANOPTICON       (5-Layer Architecture Scan, Dependency Check, MCP Server Verification, Routing Check)
echo.
echo   [X] EXIT: TERMINATE
echo ==============================================================================================================
set /p choice="Command > "

if /i "!choice!"=="1" start "" "C:\ufo\ufo\desktop_launchers\01_BankFidelity_Terminal.bat"
if /i "!choice!"=="2" start "" "C:\ufo\ufo\desktop_launchers\05_UFO_Admin_Terminal.bat"
if /i "!choice!"=="3" start "" "C:\ufo\ufo\desktop_launchers\06_Run_UFO_E2E_Test.bat"
if /i "!choice!"=="4" start "" "C:\ufo\ufo\desktop_launchers\02_UFO_Control_Panel.bat"
if /i "!choice!"=="5" start "" "C:\ufo\ufo\desktop_launchers\03_AI_Dream_Team_Launcher.bat"
if /i "!choice!"=="6" start "" "C:\ufo\ufo\desktop_launchers\07_Configuration_Dashboard.bat"
if /i "!choice!"=="7" start "" "C:\ufo\ufo\desktop_launchers\04_E2E_Diagnostics.bat"
if /i "!choice!"=="X" exit

goto menu
