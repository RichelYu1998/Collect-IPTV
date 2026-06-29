@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul 2>&1
set PYTHONIOENCODING=utf-8
title IPTV Live Stream Collection Tool

for /f "delims=" %%i in ('py -c "import re; m=re.search(r'###\s+v([\d.]+)', open('README.md', encoding='utf-8').read()); print(m.group(1) if m else '0.0.0')" 2^>nul') do set VERSION=%%i
if not defined VERSION set VERSION=0.0.0

echo ========================================
echo IPTV Live Stream Collection Tool - v%VERSION%
echo ========================================

set "VENV_PATH=.venv"
set "FASTEST_PIP_MIRROR="

call :detect_python_env
if errorlevel 1 (
    pause
    exit /b 1
)

call :test_pip_mirrors
call :detect_venv
call :setup_venv

if "%1"=="--collect" set "COLLECT_ONLY=1" & goto run_collection_only
set "COLLECT_ONLY=0"
goto run_collection_and_web

:detect_python_env
echo.
echo ========================================
echo Environment Detection and Configuration
echo ========================================

echo [1/5] Detecting Python environment...

where py >nul 2>&1
if errorlevel 1 (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Python not in PATH, searching system...

        if exist "C:\Python3*\python.exe" (
            for /d %%p in ("C:\Python3*") do set "PYTHON_PATH=%%~dp0python.exe"
        ) else if exist "C:\Program Files\Python3*\python.exe" (
            for /d %%p in ("C:\Program Files\Python3*") do set "PYTHON_PATH=%%~dp0python.exe"
        ) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python3*\python.exe" (
            for /d %%p in ("C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python3*") do set "PYTHON_PATH=%%~dp0python.exe"
        )

        if defined PYTHON_PATH (
            echo [*] Found Python: %PYTHON_PATH%
            for %%P in ("%PYTHON_PATH%") do set "PYTHON_DIR=%%~dpP"
            set "PATH=%PATH%;%PYTHON_DIR%"
            set "PYTHON_CMD=%PYTHON_PATH%"
        ) else (
            echo [WARNING] Python not found, auto-installing...

            where winget >nul 2>&1
            if not errorlevel 1 (
                echo     Installing Python via Winget...
                winget install Python.Python.3 --accept-package-agreements --accept-source-agreements --silent
                if not errorlevel 1 goto :python_verify_install
            )

            where choco >nul 2>&1
            if not errorlevel 1 (
                echo     Installing Python via Chocolatey...
                choco install python -y
                if not errorlevel 1 goto :python_verify_install
            )

            where scoop >nul 2>&1
            if not errorlevel 1 (
                echo     Installing Python via Scoop...
                scoop install python
                if not errorlevel 1 goto :python_verify_install
            )

            echo     Querying latest Python version...
            for /f "delims=" %%v in ('curl -s https://www.python.org/ftp/python/ ^| findstr /r "^3\.[0-9]*\.[0-9]*/$" ^| sort /r ^| findstr /n "^" ^| findstr "^[1]:"') do (
                for /f "tokens=1 delims=/" %%a in ("%%v") do set "PYTHON_LATEST_VERSION=%%a"
            )
            if not defined PYTHON_LATEST_VERSION set "PYTHON_LATEST_VERSION=3.11.9"
            echo     Latest Python version: %PYTHON_LATEST_VERSION%

            echo     Downloading Python %PYTHON_LATEST_VERSION% installer...
            if not exist "%TEMP%\python_installer.exe" (
                curl -L -o "%TEMP%\python_installer.exe" https://www.python.org/ftp/python/%PYTHON_LATEST_VERSION%/python-%PYTHON_LATEST_VERSION%-amd64.exe
            )

            if exist "%TEMP%\python_installer.exe" (
                echo     Silently installing Python to %CD%\_python...
                "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=0 Include_pip=1 TargetDir="%CD%\_python"
                if exist "%CD%\_python\python.exe" (
                    set "PYTHON_CMD=%CD%\_python\python.exe"
                    set "PATH=%CD%\_python;%PATH%"
                    echo [*] Python installed to: %CD%\_python
                    del "%TEMP%\python_installer.exe" 2>nul
                ) else (
                    echo [ERROR] Python installation failed
                    exit /b 1
                )
            ) else (
                echo [ERROR] Python download failed
                exit /b 1
            )
        )
    ) else (
        set PYTHON_CMD=python
    )
) else (
    set PYTHON_CMD=py
)

:python_verify_install
if not defined PYTHON_CMD (
    where py >nul 2>&1 && set "PYTHON_CMD=py"
    where python >nul 2>&1 && set "PYTHON_CMD=python"
)

echo.
echo Python version:
%PYTHON_CMD% --version

echo [*] Checking virtual environment status...
if defined VIRTUAL_ENV (
    echo Already in virtual environment: %VIRTUAL_ENV%
    set IN_VENV=1
) else (
    echo Not in virtual environment
    set IN_VENV=0
)
exit /b 0

:test_pip_mirrors
echo [2/5] Testing PIP mirror sources...

set "MIRRORS[0]=https://pypi.tuna.tsinghua.edu.cn/simple|Tsinghua"
set "MIRRORS[1]=https://mirrors.aliyun.com/pypi/simple/|Aliyun"
set "MIRRORS[2]=https://pypi.douban.com/simple/|Douban"
set "MIRRORS[3]=https://pypi.mirrors.ustc.edu.cn/simple/|USTC"

set "MIN_TIME=9999"
set "BEST_MIRROR="
set "BEST_NAME="

for /L %%i in (0,1,3) do (
    for /f "tokens=1,2 delims=|" %%a in ("!MIRRORS[%%i]!") do (
        set "MIRROR_URL=%%a"
        set "MIRROR_NAME=%%b"
        echo     Testing !MIRROR_NAME!...

        curl -s -o nul -w "%%{time_connect}" --connect-timeout 1.5 --max-time 2 "!MIRROR_URL!" > temp_pip_time.txt 2>&1
        set /p TEST_TIME=<temp_pip_time.txt
        del temp_pip_time.txt 2>nul

        if not defined TEST_TIME set "TEST_TIME=9999"

        if "!TEST_TIME!"=="0" (
            echo         !MIRROR_NAME!: timeout/failed
            set "TEST_TIME=9999"
        ) else (
            for /f "tokens=* delims=" %%t in ('%PYTHON_CMD% -c "print(int(float('!TEST_TIME!')*1000))"') do set "PIP_INT_TIME=%%t"
            echo         !MIRROR_NAME!: !TEST_TIME!s (!PIP_INT_TIME!ms)
            if !PIP_INT_TIME! LSS !MIN_TIME! (
                set "MIN_TIME=!PIP_INT_TIME!"
                set "BEST_MIRROR=!MIRROR_URL!"
                set "BEST_NAME=!MIRROR_NAME!"
            )
        )
    )
)

if "!BEST_MIRROR!"=="" (
    echo [WARNING] All mirrors failed, using default PyPI
    set "FASTEST_PIP_MIRROR=https://pypi.org/simple/"
) else (
    set "FASTEST_PIP_MIRROR=!BEST_MIRROR!"
    echo.
    echo [*] Fastest PIP mirror: !BEST_NAME! (!MIN_TIME!ms)
)
exit /b 0

:detect_venv
echo [3/5] Detecting Python virtual environment...

if exist venv\Scripts\activate.bat (
    echo Found virtual environment: venv
    set VENV_EXISTS=1
    set VENV_PATH=venv
) else if exist .venv\Scripts\activate.bat (
    echo Found virtual environment: .venv
    set VENV_EXISTS=1
    set VENV_PATH=.venv
) else (
    echo No virtual environment found
    set VENV_EXISTS=0
)
exit /b 0

:setup_venv
echo [4/5] Setting up Python virtual environment and installing dependencies...

if %VENV_EXISTS%==0 (
    echo Creating virtual environment at %VENV_PATH%...
    %PYTHON_CMD% -m venv %VENV_PATH%
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    set VENV_EXISTS=1
)

if not exist %VENV_PATH% (
    echo ERROR: Virtual environment path not found: %VENV_PATH%
    pause
    exit /b 1
)

call %VENV_PATH%\Scripts\activate.bat

if defined FASTEST_PIP_MIRROR (
    echo [*] Configuring PIP mirror: %FASTEST_PIP_MIRROR%

    if not exist "%VENV_PATH%\pip_config" mkdir "%VENV_PATH%\pip_config"

    set "TRUSTED_HOST=!FASTEST_PIP_MIRROR!"
    set "TRUSTED_HOST=!TRUSTED_HOST:https://=!"
    set "TRUSTED_HOST=!TRUSTED_HOST:http://=!"
    for /f "delims=/" %%h in ("!TRUSTED_HOST!") do set "TRUSTED_HOST=%%h"

    echo [global]> "%VENV_PATH%\pip_config\pip.ini"
    echo index-url=%FASTEST_PIP_MIRROR%>> "%VENV_PATH%\pip_config\pip.ini"
    echo trusted-host=%TRUSTED_HOST%>> "%VENV_PATH%\pip_config\pip.ini"
    echo [install]>> "%VENV_PATH%\pip_config\pip.ini"
    echo trusted-host=%TRUSTED_HOST%>> "%VENV_PATH%\pip_config\pip.ini"

    set PIP_CONFIG_FILE=%VENV_PATH%\pip_config\pip.ini
)

echo Installing Python dependencies...
%PYTHON_CMD% -m pip install --upgrade pip --disable-pip-version-check -i %FASTEST_PIP_MIRROR%
%PYTHON_CMD% -m pip install aiohttp --disable-pip-version-check -i %FASTEST_PIP_MIRROR%

if errorlevel 1 (
    echo WARNING: Mirror install failed, trying default source...
    %PYTHON_CMD% -m pip install --upgrade pip --disable-pip-version-check
    %PYTHON_CMD% -m pip install aiohttp --disable-pip-version-check

    if errorlevel 1 (
        echo ERROR: Dependency installation failed
        pause
        exit /b 1
    )
)

echo Python virtual environment setup complete
exit /b 0

:run_collection_only
echo.
echo ========================================
echo Running IPTV Collection
echo ========================================

call :do_collection

echo.
echo Tips:
echo    - Use M3U-compatible players to open generated files
echo    - Recommended: PotPlayer, VLC, Kodi, etc.
echo.
if "%COLLECT_ONLY%"=="1" exit /b 0
pause
exit /b 0

:run_collection_and_web
echo.
echo ========================================
echo Running IPTV Collection
echo ========================================

call :do_collection

goto setup_scheduled_task_and_web

:do_collection
echo [5/5] Checking script files and config...

if not exist ".github\workflows\iptv.py" (
    echo ERROR: iptv.py script not found
    pause
    exit /b 1
)
echo [*] iptv.py script found

if exist ".github\workflows\IPTV" (
    echo [*] IPTV config directory found
) else (
    echo WARNING: IPTV config directory not found
)

echo.
echo Starting IPTV stream collection...
echo ========================================
echo.

call %VENV_PATH%\Scripts\activate.bat
%PYTHON_CMD% .github\workflows\iptv.py

if errorlevel 1 (
    echo.
    echo ERROR: Script execution failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo IPTV Collection Complete!
echo ========================================
echo.

if exist "best_sorted.m3u" (
    echo Generated M3U file: best_sorted.m3u
    for %%F in (best_sorted.m3u) do echo    File size: %%~zF bytes
)

if exist "best_sorted.m3u8" (
    echo Generated M3U8 file: best_sorted.m3u8
    for %%F in (best_sorted.m3u8) do echo    File size: %%~zF bytes
)

echo.
exit /b 0

:setup_scheduled_task_and_web
echo.
echo ========================================
echo Setting Up Scheduled Task
echo ========================================

echo [5/5] Registering scheduled task...

set "TASK_NAME=IPTV_Collection"
set "SCRIPT_PATH=%~f0"
set "WORK_DIR=%CD%"

schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if not errorlevel 1 goto task_exists

echo Creating scheduled task: %TASK_NAME%
echo    Trigger: Every 4 hours
echo    Command: %SCRIPT_PATH% --collect
echo    Work dir: %WORK_DIR%
echo.

schtasks /create /tn "%TASK_NAME%" /tr "\"%SCRIPT_PATH%\" --collect" /sc hourly /mo 4 /f

if errorlevel 1 (
    echo [WARNING] Failed to create scheduled task via schtasks
    echo    You can manually create it in Task Scheduler (taskschd.msc)
) else (
    echo [*] Scheduled task created successfully!
)
goto task_done

:task_exists
echo [*] Scheduled task already exists: %TASK_NAME%
schtasks /query /tn "%TASK_NAME%" /fo list | findstr /i "Status Schedule Task"

:task_done

echo.
echo ========================================
echo Starting Local Web Server
echo ========================================

if not exist ".github\workflows\index.html" (
    echo ERROR: index.html not found
    pause
    exit /b 1
)

echo Starting local web server...
echo.
echo Server URL: http://localhost:8000
echo.
echo Tips:
echo    - Press Ctrl+C to stop the server
echo    - Closing this window will also stop the server
echo    - Scheduled task will auto-collect every 4 hours
echo.
echo ========================================
echo.

call %VENV_PATH%\Scripts\activate.bat
cd /d "%~dp0"
%PYTHON_CMD% "%~dp0server.py" 8000
pause
exit /b 0