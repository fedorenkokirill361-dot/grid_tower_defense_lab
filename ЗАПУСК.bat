@echo off
cd /d "%~dp0"
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" main.py
echo.
echo Игра закрылась. Если вместо игры была ошибка, её текст написан выше.
pause
