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

setlocal enabledelayedexpansion
:: Определяем команду Python (сначала проверяем python3, потом python с проверкой версии)
python3 --version >nul 2>&1
if !errorlevel! == 0 (
    set PYTHON_CMD=python3
) else (
    python --version >nul 2>&1
    if !errorlevel! == 0 (
        for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
        for /f "tokens=1 delims=." %%j in ("!PYTHON_VERSION!") do set PYTHON_MAJOR=%%j
        if "!PYTHON_MAJOR!" LSS "3" (
            echo [ОШИБКА] Найден Python 2.x. Требуется Python 3.10+
            pause
            exit /b 1
        )
        set PYTHON_CMD=python
    ) else (
        echo [ОШИБКА] Python не найден! Установите Python 3.10+
        pause
        exit /b 1
    )
)

:: Дополнительные действия (если нужно)
:: Например, установка зависимостей:
call %PYTHON_CMD% -m pip install -r requirements.txt

echo Обновление завершено!
timeout /t 3
exit