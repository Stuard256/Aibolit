@echo off
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

echo Normalizing phones
%PYTHON_CMD% -m flask normalize-phones
echo Normalizing phones finished
pause