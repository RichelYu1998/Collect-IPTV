@echo off
chcp 65001 >nul
title IPTV Tool - Complete Version

setlocal enabledelayedexpansion

REM ========================================
REM IPTV Live Stream Collection Tool - Windows Complete Version
REM Functions: Environment Check, Virtual Environment, Data Collection, Web Service
REM ========================================

:main_menu
cls
echo.
echo ============================================================
echo        IPTV Live Stream Collection Tool - Complete Version
echo ============================================================
echo.
echo Menu:
echo.
echo   [1] Environment Check and Configuration
echo   [2] Virtual Environment Management
echo   [3] Run IPTV Collection
echo   [4] Start Local Web Server
echo   [5] Setup Scheduled Task
echo   [6] View Generated Files
echo   [7] Clean Temporary Files
echo   [8] View Help Documentation
echo   [0] Exit Program
echo.
set /p choice="Please select function (0-8): "

if "%choice%"=="1" goto check_environment
if "%choice%"=="2" goto venv_management
if "%choice%"=="3" goto run_collection
if "%choice%"=="4" goto start_web_server
if "%choice%"=="5" goto setup_scheduled_task
if "%choice%"=="6" goto view_files
if "%choice%"=="7" goto cleanup
if "%choice%"=="8" goto show_help
if "%choice%"=="0" goto exit_program

echo.
echo Invalid option, please try again
timeout /t 2 >nul
goto main_menu

:check_environment
cls
echo.
echo ============================================================
echo   Environment Check and Configuration
echo ============================================================
echo.

REM Check Python environment
echo [1/6] Checking Python environment...
set PYTHON_CMD=
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto :python_found
)
where python3 >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    goto :python_found
)
where py >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    goto :python_found
)

echo Error: Python environment not detected
echo.
echo Please install Python 3.10 or higher first:
echo   Download: https://www.python.org/downloads/
echo   Check "Add Python to PATH" during installation
echo.
pause
goto main_menu

:python_found
for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo OK: Python version %PYTHON_VERSION% (command: %PYTHON_CMD%)
echo.

REM Check virtual environment
echo [2/6] Checking virtual environment...
if exist "venv\Scripts\activate.bat" (
    echo OK: Virtual environment detected: venv
    set VENV_EXISTS=1
) else if exist ".venv\Scripts\activate.bat" (
    echo OK: Virtual environment detected: .venv
    set VENV_EXISTS=1
) else (
    echo Warning: No virtual environment detected
    set VENV_EXISTS=0
)
echo.

REM Check dependencies
echo [3/6] Checking dependencies...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    %PYTHON_CMD% -c "import aiohttp" >nul 2>&1
    if %errorlevel% equ 0 (
        echo OK: aiohttp dependency is installed
    ) else (
        echo Warning: aiohttp not installed
    )
    call deactivate
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    %PYTHON_CMD% -c "import aiohttp" >nul 2>&1
    if %errorlevel% equ 0 (
        echo OK: aiohttp dependency is installed
    ) else (
        echo Warning: aiohttp not installed
    )
    call deactivate
) else (
    %PYTHON_CMD% -c "import aiohttp" >nul 2>&1
    if %errorlevel% equ 0 (
        echo OK: aiohttp dependency is installed
    ) else (
        echo Warning: aiohttp not installed
    )
)
echo.

REM Check script files
echo [4/6] Checking script files...
if exist ".github\workflows\iptv.py" (
    echo OK: iptv.py script file exists
) else (
    echo Error: iptv.py script file not found
)

if exist ".github\workflows\index.html" (
    echo OK: index.html web file exists
) else (
    echo Error: index.html web file not found
)
echo.

REM Check IPTV configuration directory
echo [5/6] Checking IPTV configuration directory...
if exist ".github\workflows\IPTV" (
    echo OK: IPTV configuration directory exists
    
    if exist ".github\workflows\IPTV\CCTV.txt" (
        echo OK: CCTV channel configuration file exists
    ) else (
        echo Warning: CCTV channel configuration file not found
    )
    
    set /a province_count=0
    for %%f in (.github\workflows\IPTV\*.txt) do (
        set /a province_count+=1
    )
    echo OK: Provincial channel configuration files: !province_count!
) else (
    echo Error: IPTV configuration directory not found
)
echo.

REM Check network connection
echo [6/6] Checking network connection...
ping -n 1 8.8.8.8 >nul 2>&1
if %errorlevel% equ 0 (
    echo OK: Network connection is normal
) else (
    echo Warning: Network connection test failed
)
echo.

echo ============================================================
echo   Environment Check Complete
echo ============================================================
echo.
pause
goto main_menu

:venv_management
cls
echo.
echo ============================================================
echo   Virtual Environment Management
echo ============================================================
echo.

if exist "venv\Scripts\activate.bat" (
    echo OK: Virtual environment detected: venv
) else if exist ".venv\Scripts\activate.bat" (
    echo OK: Virtual environment detected: .venv
) else (
    echo Warning: No virtual environment detected
)
echo.

echo Please select operation:
echo   [1] Create virtual environment
echo   [2] Activate virtual environment and install dependencies
echo   [3] Delete virtual environment
echo   [0] Return to main menu
echo.
set /p venv_choice="Please select operation (0-3): "

if "%venv_choice%"=="1" goto create_venv
if "%venv_choice%"=="2" goto activate_venv
if "%venv_choice%"=="3" goto delete_venv
if "%venv_choice%"=="0" goto main_menu

echo.
echo Invalid option
pause
goto main_menu

:create_venv
cls
echo.
echo ============================================================
echo   Create Virtual Environment
echo ============================================================
echo.

if exist "venv" (
    echo Warning: venv directory already exists
    set /p overwrite="Delete and recreate? (y/n): "
    if /i not "%overwrite%"=="y" (
        echo Creation cancelled
        pause
        goto main_menu
    )
    rmdir /s /q venv
)

echo Creating virtual environment...
%PYTHON_CMD% -m venv venv

if %errorlevel% neq 0 (
    echo Error: Virtual environment creation failed
    pause
    goto main_menu
)

echo OK: Virtual environment created successfully
echo.
echo Installing dependencies...
call venv\Scripts\activate.bat
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install aiohttp
call deactivate

echo OK: Dependencies installed successfully
echo.
pause
goto main_menu

:activate_venv
cls
echo.
echo ============================================================
echo   Activate Virtual Environment and Install Dependencies
echo ============================================================
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo OK: Virtual environment activated: venv
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo OK: Virtual environment activated: .venv
) else (
    echo Error: Virtual environment not found
    echo Please create virtual environment first
    pause
    goto main_menu
)

echo.
echo Checking and installing dependencies...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install aiohttp

echo OK: Dependencies installed successfully
echo.
echo Note: Virtual environment is activated in this session
echo To use in a new command window, run:
echo   venv\Scripts\activate.bat
echo.
pause
call deactivate
goto main_menu

:delete_venv
cls
echo.
echo ============================================================
echo   Delete Virtual Environment
echo ============================================================
echo.

if exist "venv" (
    echo Warning: About to delete venv directory
    set /p confirm="Confirm deletion? (y/n): "
    if /i "%confirm%"=="y" (
        rmdir /s /q venv
        echo OK: Virtual environment deleted
    ) else (
        echo Deletion cancelled
    )
) else if exist ".venv" (
    echo Warning: About to delete .venv directory
    set /p confirm="Confirm deletion? (y/n): "
    if /i "%confirm%"=="y" (
        rmdir /s /q .venv
        echo OK: Virtual environment deleted
    ) else (
        echo Deletion cancelled
    )
) else (
    echo Virtual environment not found
)

echo.
pause
goto main_menu

:run_collection
cls
echo.
echo ============================================================
echo   Run IPTV Collection
echo ============================================================
echo.

REM Detect Python environment
set PYTHON_CMD=
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto :python_found_run
)
where python3 >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    goto :python_found_run
)
where py >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    goto :python_found_run
)

echo Error: Python environment not detected
pause
goto main_menu

:python_found_run

REM Detect virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Using virtual environment: venv
    call venv\Scripts\activate.bat
    set USING_VENV=1
) else if exist ".venv\Scripts\activate.bat" (
    echo Using virtual environment: .venv
    call .venv\Scripts\activate.bat
    set USING_VENV=1
) else (
    echo Warning: No virtual environment detected, using system Python
    echo Suggestion: Create virtual environment to isolate dependencies
    set USING_VENV=0
)

echo.
echo Starting IPTV live stream collection...
echo ========================================
echo.

%PYTHON_CMD% .github\workflows\iptv.py

if %errorlevel% neq 0 (
    echo.
    echo Error: Script execution failed
    if %USING_VENV% equ 1 (
        call deactivate
    )
    pause
    goto main_menu
)

if %USING_VENV% equ 1 (
    call deactivate
)

echo.
echo ========================================
echo OK: IPTV live stream collection complete!
echo ========================================
echo.

REM Check generated files
if exist "best_sorted.m3u" (
    echo Generated M3U file: best_sorted.m3u
    for %%F in (best_sorted.m3u) do echo    File size: %%~zF bytes
)

if exist "best_sorted.m3u8" (
    echo Generated M3U8 file: best_sorted.m3u8
    for %%F in (best_sorted.m3u8) do echo    File size: %%~zF bytes
)

echo.
echo Tips:
echo    - Use M3U-compatible players to open generated files
echo    - Recommended players: PotPlayer, VLC, Kodi, etc.
echo    - Run this script regularly to get latest live streams
echo.
pause
goto main_menu

:start_web_server
cls
echo.
echo ============================================================
echo   Start Local Web Server
echo ============================================================
echo.

if not exist ".github\workflows\index.html" (
    echo Error: index.html file not found
    pause
    goto main_menu
)

echo Starting local web server...
echo.
echo Service address: http://localhost:8000
echo Service directory: %CD%
echo.
echo Tips:
echo    - Press Ctrl+C to stop service
echo    - Closing this window will also stop service
echo.
echo ========================================
echo.

REM Detect Python environment
set PYTHON_CMD=
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto :python_found_web
)
where python3 >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    goto :python_found_web
)
where py >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    goto :python_found_web
)

echo Error: Python environment not detected
pause
goto main_menu

:python_found_web

cd .github\workflows
%PYTHON_CMD% -m http.server 8000
cd ..\..

pause
goto main_menu

:setup_scheduled_task
cls
echo.
echo ============================================================
echo   Setup Scheduled Task
echo ============================================================
echo.

echo Creating scheduled task script...
echo.

REM Create scheduled task script
(
echo @echo off
echo chcp 65001 ^>nul
echo title IPTV Scheduled Collection Task
echo.
echo cd /d "%CD%"
echo.
echo echo [%%date%% %%time%%] Starting IPTV scheduled collection
echo.
echo REM Detect Python environment
echo set PYTHON_CMD=
echo where python ^>nul 2^>^&1
echo if %%errorlevel%% equ 0 ^(
echo     set PYTHON_CMD=python
echo ^) else ^(
echo     where python3 ^>nul 2^>^&1
echo     if %%errorlevel%% equ 0 ^(
echo         set PYTHON_CMD=python3
echo     ^) else ^(
echo         where py ^>nul 2^>^&1
echo         if %%errorlevel%% equ 0 ^(
echo             set PYTHON_CMD=py
echo         ^)
echo     ^)
echo ^)
echo.
echo REM Activate virtual environment
echo if exist "venv\Scripts\activate.bat" ^(
echo     call venv\Scripts\activate.bat
echo ^) else if exist ".venv\Scripts\activate.bat" ^(
echo     call .venv\Scripts\activate.bat
echo ^)
echo.
echo REM Run collection script
echo %%PYTHON_CMD%% .github\workflows\iptv.py
echo.
echo echo [%%date%% %%time%%] IPTV scheduled collection complete
echo.
) > iptv_scheduled_task.bat

echo OK: Scheduled task script created: iptv_scheduled_task.bat
echo.
echo Configure Windows Task Scheduler:
echo    1. Open "Task Scheduler" (Win+R, type taskschd.msc)
echo    2. Click "Create Basic Task"
echo    3. Set task name: IPTV Scheduled Collection
echo    4. Set trigger (e.g., every 4 hours)
echo    5. Action: Start program
echo    6. Program or script: %CD%\iptv_scheduled_task.bat
echo    7. Start in: %CD%
echo.
echo Or test directly:
echo    iptv_scheduled_task.bat
echo.
pause
goto main_menu

:view_files
cls
echo.
echo ============================================================
echo   View Generated Files
echo ============================================================
echo.

echo Generated playlist files:
echo.

if exist "best_sorted.m3u" (
    echo [1] best_sorted.m3u (M3U format)
    for %%F in (best_sorted.m3u) do echo    Size: %%~zF bytes, Modified: %%~tF
    echo.
)

if exist "best_sorted.m3u8" (
    echo [2] best_sorted.m3u8 (M3U8 format)
    for %%F in (best_sorted.m3u8) do echo    Size: %%~zF bytes, Modified: %%~tF
    echo.
)

if not exist "best_sorted.m3u" if not exist "best_sorted.m3u8" (
    echo No generated files found
    echo.
)

echo Please select operation:
echo   [1] Open M3U file
echo   [2] Open M3U8 file
echo   [3] Open file directory
echo   [0] Return to main menu
echo.
set /p view_choice="Please select operation (0-3): "

if "%view_choice%"=="1" (
    if exist "best_sorted.m3u" notepad best_sorted.m3u
)
if "%view_choice%"=="2" (
    if exist "best_sorted.m3u8" notepad best_sorted.m3u8
)
if "%view_choice%"=="3" (
    explorer .
)
if "%view_choice%"=="0" goto main_menu

pause
goto main_menu

:cleanup
cls
echo.
echo ============================================================
echo   Clean Temporary Files
echo ============================================================
echo.

echo Warning: This operation will delete the following files:
echo   - Python cache files (__pycache__)
echo   - Temporary files (*.pyc)
echo   - Virtual environment (venv/.venv)
echo   - Generated playlists (best_sorted.m3u/m3u8)
echo.
set /p confirm="Confirm cleanup? (y/n): "

if /i not "%confirm%"=="y" (
    echo Cleanup cancelled
    pause
    goto main_menu
)

echo.
echo Cleaning up...

REM Clean Python cache
if exist "__pycache__" (
    rmdir /s /q __pycache__
    echo OK: Cleaned __pycache__
)

REM Clean .pyc files
del /s /q *.pyc >nul 2>&1
if %errorlevel% equ 0 (
    echo OK: Cleaned *.pyc files
)

REM Clean virtual environment
if exist "venv" (
    rmdir /s /q venv
    echo OK: Cleaned venv virtual environment
)

if exist ".venv" (
    rmdir /s /q .venv
    echo OK: Cleaned .venv virtual environment
)

REM Clean generated files
if exist "best_sorted.m3u" (
    del best_sorted.m3u
    echo OK: Cleaned best_sorted.m3u
)

if exist "best_sorted.m3u8" (
    del best_sorted.m3u8
    echo OK: Cleaned best_sorted.m3u8
)

echo.
echo OK: Cleanup complete!
echo.
pause
goto main_menu

:show_help
cls
echo.
echo ============================================================
echo   Help Documentation
echo ============================================================
echo.

echo Function Description:
echo.
echo   [1] Environment Check and Configuration
echo      - Check Python environment
echo      - Check virtual environment
echo      - Check dependencies
echo      - Check script files
echo      - Check network connection
echo.
echo   [2] Virtual Environment Management
echo      - Create virtual environment
echo      - Activate virtual environment and install dependencies
echo      - Delete virtual environment
echo.
echo   [3] Run IPTV Collection
echo      - Automatically detect and use virtual environment
echo      - Collect IPTV live streams
echo      - Smart classification and quality filtering
echo      - Generate M3U playlist
echo.
echo   [4] Start Local Web Server
echo      - Provide web interface
echo      - Support search and filtering
echo      - Real-time channel information viewing
echo.
echo   [5] Setup Scheduled Task
echo      - Create scheduled task script
echo      - Configure Windows Task Scheduler
echo      - Implement automatic updates
echo.
echo   [6] View Generated Files
echo      - View M3U/M3U8 files
echo      - Open file directory
echo.
echo   [7] Clean Temporary Files
echo      - Clean Python cache
echo      - Clean virtual environment
echo      - Clean generated files
echo.
echo For more information:
echo    - View README.md for more details
echo    - Visit project GitHub page for latest updates
echo.
pause
goto main_menu

:exit_program
cls
echo.
echo Thank you for using IPTV Live Stream Collection Tool!
echo.
timeout /t 2 >nul
exit /b 0