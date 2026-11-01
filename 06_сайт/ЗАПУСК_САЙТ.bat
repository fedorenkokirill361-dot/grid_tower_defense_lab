@echo off
cd /d "%~dp0.."
echo.
echo Поле:    http://localhost:8765/06_сайт/
echo Виджет:  http://localhost:8765/04_виджет/
echo Каталог: http://localhost:8765/05_каталог/
echo.
echo Это окно должно оставаться открытым. Закроете его — страницы перестанут открываться.
echo.
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -m http.server 8765
