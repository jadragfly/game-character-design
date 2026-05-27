@echo off
chcp 65001 >nul
echo ========================================
echo AI Background Removal for pig-contra-game
echo ========================================
echo.

set "PYTHON=C:\Users\HP\.trae-cn\skills\背景移除技能\.bg_env\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo Virtual env not found, trying system Python
    set "PYTHON=python"
)

echo Using: %PYTHON%
echo.

"%PYTHON%" "D:\impotent\skills\make_game\game-character-design\scripts\ai_bg_remove_game.py"

echo.
pause
