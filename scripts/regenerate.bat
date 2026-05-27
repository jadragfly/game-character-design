@echo off
chcp 65001 >nul
echo ========================================
echo Regenerate Spritesheet from decoded
echo ========================================
echo.

set "PYTHON=C:\Users\HP\.trae-cn\skills\背景移除技能\.bg_env\Scripts\python.exe"

if not exist "%PYTHON%" (
    set "PYTHON=python"
)

echo Using: %PYTHON%
echo.

"%PYTHON%" "D:\impotent\skills\make_game\game-character-design\scripts\regenerate_spritesheet.py"

echo.
pause
