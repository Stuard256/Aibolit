@echo off
SETLOCAL

:: Проверка наличия Git
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Git не установлен!
    echo Скачайте с https://git-scm.com/download/win
    pause
    exit /b 1
)

:: Путь к папке с репозиторием
set "REPO_PATH=%~dp0"

:: Переход в папку проекта
cd /d "%REPO_PATH%"

:: Основная логика обновления
git fetch origin
git reset --hard origin/main
git pull origin main

:: Дополнительные действия (если нужно)
:: Например, установка зависимостей:
call pip install -r requirements.txt

echo Обновление завершено!
timeout /t 3
exit