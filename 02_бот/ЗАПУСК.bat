@echo off
cd /d "%~dp0"
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" bot.py
echo.
echo Бот остановился. Если вместо бота была ошибка, её текст написан выше.
pause
