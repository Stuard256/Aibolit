@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ═══════════════════════════════════════════════════════════
echo             ЗАПУСК ПРОГРАММЫ AIBOLIT
echo ═══════════════════════════════════════════════════════════
echo.

:: Определяем команду Python (сначала проверяем python3, потом python с проверкой версии)
python3 --version >nul 2>&1
if !errorlevel! == 0 (
    set PYTHON_CMD=python3
) else (
    python --version >nul 2>&1
    if !errorlevel! == 0 (
        :: Проверяем, что это Python 3, а не Python 2
        for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
        for /f "tokens=1 delims=." %%j in ("!PYTHON_VERSION!") do set PYTHON_MAJOR=%%j
        if "!PYTHON_MAJOR!" LSS "3" (
            echo [ОШИБКА] Найден Python 2.x. Требуется Python 3.10+
            echo.
            echo Установите Python 3.10+ с официального сайта:
            echo https://www.python.org/downloads/
            echo.
            echo Или из Microsoft Store:
            echo https://www.microsoft.com/store/productId/9PJPW5LDXLZ5
            echo.
            pause
            exit /b 1
        )
        set PYTHON_CMD=python
    ) else (
        echo [ОШИБКА] Python не найден!
        echo.
        echo Установите Python 3.10+ с официального сайта:
        echo https://www.python.org/downloads/
        echo.
        echo Или из Microsoft Store:
        echo https://www.microsoft.com/store/productId/9PJPW5LDXLZ5
        echo.
        pause
        exit /b 1
    )
)

:: Проверяем версию Python
echo [OK] Python найден
for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Версия: %PYTHON_VERSION%
echo.

:: Проверяем наличие зависимостей
echo Проверка зависимостей...
%PYTHON_CMD% -c "import flask" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ВНИМАНИЕ] Не все зависимости установлены!
    echo.
    echo Устанавливаю зависимости...
    %PYTHON_CMD% -m pip install -r requirements.txt
    %PYTHON_CMD% -m pip install joblib scikit-learn numpy pandas
    echo.
)

echo [OK] Все зависимости установлены
echo.

:: Запуск программы
echo ═══════════════════════════════════════════════════════════
echo Запускаю сервер...
echo Откройте в браузере: http://localhost:5000
echo.
echo Для остановки сервера нажмите Ctrl+C
echo ═══════════════════════════════════════════════════════════
echo.

:: Ждем немного и открываем браузер
start /B %PYTHON_CMD% app.py
timeout /t 3 /nobreak >nul
start http://localhost:5000

:: Ждем завершения
wait

