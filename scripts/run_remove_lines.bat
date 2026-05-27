@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo Image Cleanup for pig-soldier
echo ========================================
echo.

set "SCRIPT_DIR=D:\impotent\skills\make_game\game-character-design\scripts"
set "RUN_DIR=D:\impotent\skills\make_game\pig-contra-game\run\pig-soldier"

echo Step 1: Removing black lines...
echo ----------------------------------------
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%\remove_lines.ps1"
echo.

echo Step 2: Removing white background...
echo ----------------------------------------
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%\remove_white_bg.ps1"
echo.

echo Done! Please check:
echo   %RUN_DIR%\final\spritesheet.png
echo.
pause
