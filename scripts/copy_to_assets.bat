@echo off
chcp 65001 >nul
echo ========================================
echo Copy Spritesheet to assets folder
echo ========================================
echo.

set "PYTHON=C:\Users\HP\.trae-cn\skills\背景移除技能\.bg_env\Scripts\python.exe"

if not exist "%PYTHON%" (
    set "PYTHON=python"
)

"%PYTHON%" "D:\impotent\skills\make_game\game-character-design\scripts\copy_to_assets.py"

echo.
pause
