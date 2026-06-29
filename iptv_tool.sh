#!/bin/bash

# ========================================
# IPTV Live Stream Collection Tool - Linux/macOS
# Auto: env detect -> mirror test -> venv -> scheduled task -> web server
# ========================================

VERSION=$(python3 -c "import re; m=re.search(r'###\s+v(\d+\.\d+\.\d+)', open('README.md', encoding='utf-8').read()); print(m.group(1) if m else '0.0.0')" 2>/dev/null || python -c "import re; m=re.search(r'###\s+v(\d+\.\d+\.\d+)', open('README.md', encoding='utf-8').read()); print(m.group(1) if m else '0.0.0')" 2>/dev/null || echo "0.0.0")

echo "========================================"
echo "IPTV Live Stream Collection Tool - v${VERSION}"
echo "========================================"

VENV_PATH=".venv"
FASTEST_PIP_MIRROR=""

detect_python_env() {
    echo ""
    echo "========================================"
    echo "Environment Detection and Configuration"
    echo "========================================"

    echo "[1/5] Detecting Python environment..."

    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        echo "Python: $(python3 --version 2>&1)"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        echo "Python: $(python --version 2>&1)"
    else
        echo "Python not in PATH, searching system..."

        COMMON_PYTHON_PATHS=(
            "/usr/bin/python3"
            "/usr/local/bin/python3"
            "/opt/homebrew/bin/python3"
            "$HOME/.pyenv/shims/python3"
            "/usr/bin/python"
            "/usr/local/bin/python"
        )

        for py_path in "${COMMON_PYTHON_PATHS[@]}"; do
            if [ -x "$py_path" ]; then
                echo "[*] Found Python: $py_path"
                export PATH="$(dirname $py_path):$PATH"
                PYTHON_CMD="$py_path"
                break
            fi
        done

        if [ -z "$PYTHON_CMD" ]; then
            echo "[WARNING] Python not found, auto-installing..."

            case "$(uname -s)" in
                Darwin)
                    if command -v brew &> /dev/null; then
                        echo "    Installing Python via Homebrew..."
                        brew install python
                    elif [ -f "/opt/homebrew/bin/brew" ]; then
                        echo "    Installing Python via Homebrew (Apple Silicon)..."
                        /opt/homebrew/bin/brew install python
                    else
                        echo "[ERROR] Homebrew not found, cannot auto-install Python"
                        echo "Install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                        return 1
                    fi
                    ;;
                Linux)
                    if command -v apt-get &> /dev/null; then
                        echo "    Installing Python via apt..."
                        sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip
                    elif command -v yum &> /dev/null; then
                        echo "    Installing Python via yum..."
                        sudo yum install -y python3 python3-pip
                    elif command -v dnf &> /dev/null; then
                        echo "    Installing Python via dnf..."
                        sudo dnf install -y python3 python3-pip
                    elif command -v pacman &> /dev/null; then
                        echo "    Installing Python via pacman..."
                        sudo pacman -Syu --noconfirm python python-pip
                    else
                        echo "[ERROR] Package manager not recognized, please install Python manually"
                        return 1
                    fi
                    ;;
                *)
                    echo "[ERROR] Unsupported OS"
                    return 1
                    ;;
            esac

            if command -v python3 &> /dev/null; then
                PYTHON_CMD="python3"
                echo "[*] Python installed: $(python3 --version 2>&1)"
            elif command -v python &> /dev/null; then
                PYTHON_CMD="python"
                echo "[*] Python installed: $(python --version 2>&1)"
            else
                echo "[ERROR] Python installation failed"
                return 1
            fi
        fi
    fi

    echo ""
    echo "[*] Checking virtual environment status..."
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "Already in virtual environment: $VIRTUAL_ENV"
        IN_VENV=1
    else
        echo "Not in virtual environment"
        IN_VENV=0
    fi

    return 0
}

test_pip_mirrors() {
    echo "[2/5] Testing PIP mirror sources..."

    declare -a MIRRORS=(
        "https://pypi.tuna.tsinghua.edu.cn/simple|Tsinghua"
        "https://mirrors.aliyun.com/pypi/simple/|Aliyun"
        "https://pypi.douban.com/simple/|Douban"
        "https://pypi.mirrors.ustc.edu.cn/simple/|USTC"
    )

    MIN_TIME=9999
    BEST_MIRROR=""
    BEST_NAME=""

    for mirror_entry in "${MIRRORS[@]}"; do
        IFS='|' read -r MIRROR_URL MIRROR_NAME <<< "$mirror_entry"
        echo "    Testing $MIRROR_NAME..."

        TEST_TIME=$(curl -s -o /dev/null -w "%{time_connect}" --connect-timeout 1.5 --max-time 2 "$MIRROR_URL" 2>/dev/null)

        if [ -z "$TEST_TIME" ] || [ "$TEST_TIME" = "0.000" ]; then
            echo "        $MIRROR_NAME: timeout/failed"
        else
            INT_TIME=${TEST_TIME%%.*}
            INT_TIME=${INT_TIME#0}
            [ -z "$INT_TIME" ] && INT_TIME=0
            echo "        $MIRROR_NAME: ${TEST_TIME}s (${INT_TIME}ms)"
            if [ "$INT_TIME" -lt "$MIN_TIME" ]; then
                MIN_TIME=$INT_TIME
                BEST_MIRROR="$MIRROR_URL"
                BEST_NAME="$MIRROR_NAME"
            fi
        fi
    done

    if [ -n "$BEST_MIRROR" ]; then
        FASTEST_PIP_MIRROR="$BEST_MIRROR"
        echo "[*] Fastest PIP mirror: $BEST_NAME (${MIN_TIME}ms)"
    else
        echo "[WARNING] All mirrors failed, using default PyPI"
        FASTEST_PIP_MIRROR="https://pypi.org/simple/"
    fi
}

detect_venv() {
    echo "[3/5] Detecting Python virtual environment..."

    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        echo "Found virtual environment: venv"
        VENV_EXISTS=1
        VENV_PATH="venv"
    elif [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
        echo "Found virtual environment: .venv"
        VENV_EXISTS=1
        VENV_PATH=".venv"
    else
        echo "No virtual environment found"
        VENV_EXISTS=0
    fi
}

setup_venv() {
    echo "[4/5] Setting up Python virtual environment and installing dependencies..."

    if [ "$VENV_EXISTS" -eq 0 ]; then
        echo "Creating virtual environment at $VENV_PATH..."
        $PYTHON_CMD -m venv $VENV_PATH

        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to create virtual environment"
            exit 1
        fi
        VENV_EXISTS=1
    fi

    source "$VENV_PATH/bin/activate"

    if [ -n "$FASTEST_PIP_MIRROR" ]; then
        echo "[*] Configuring PIP mirror: $FASTEST_PIP_MIRROR"

        mkdir -p "$VENV_PATH/pip_config"

        TRUSTED_HOST=$(echo "$FASTEST_PIP_MIRROR" | sed -E 's|^https?://([^/]+).*|\1|')

        cat > "$VENV_PATH/pip_config/pip.conf" << EOF
[global]
index-url = $FASTEST_PIP_MIRROR
trusted-host = $TRUSTED_HOST
[install]
trusted-host = $TRUSTED_HOST
EOF

        export PIP_CONFIG_FILE="$VENV_PATH/pip_config/pip.conf"
    fi

    echo "Installing Python dependencies..."

    if [ -n "$FASTEST_PIP_MIRROR" ]; then
        pip install --upgrade pip -i "$FASTEST_PIP_MIRROR" --disable-pip-version-check
        pip install aiohttp -i "$FASTEST_PIP_MIRROR" --disable-pip-version-check

        if [ $? -ne 0 ]; then
            echo "WARNING: Mirror install failed, trying default source..."
            pip install --upgrade pip --disable-pip-version-check
            pip install aiohttp --disable-pip-version-check
        fi
    else
        pip install --upgrade pip --disable-pip-version-check
        pip install aiohttp --disable-pip-version-check
    fi

    if [ $? -ne 0 ]; then
        echo "ERROR: Dependency installation failed"
        exit 1
    fi

    echo "Python virtual environment setup complete"
}

run_collection() {
    echo ""
    echo "========================================"
    echo "Running IPTV Collection"
    echo "========================================"

    echo "[5/5] Checking script files and config..."

    if [ ! -f ".github/workflows/iptv.py" ]; then
        echo "ERROR: iptv.py script not found"
        exit 1
    fi
    echo "[*] iptv.py script found"

    if [ -d ".github/workflows/IPTV" ]; then
        echo "[*] IPTV config directory found"
    else
        echo "WARNING: IPTV config directory not found"
    fi

    echo ""
    echo "Starting IPTV stream collection..."
    echo "========================================"
    echo ""

    source "$VENV_PATH/bin/activate"
    $PYTHON_CMD .github/workflows/iptv.py

    if [ $? -ne 0 ]; then
        echo ""
        echo "ERROR: Script execution failed"
        exit 1
    fi

    echo ""
    echo "========================================"
    echo "IPTV Collection Complete!"
    echo "========================================"
    echo ""

    if [ -f "best_sorted.m3u" ]; then
        echo "Generated M3U file: best_sorted.m3u"
        echo "   File size: $(wc -c < best_sorted.m3u) bytes"
    fi

    if [ -f "best_sorted.m3u8" ]; then
        echo "Generated M3U8 file: best_sorted.m3u8"
        echo "   File size: $(wc -c < best_sorted.m3u8) bytes"
    fi

    echo ""
    echo "Tips:"
    echo "   - Use M3U-compatible players to open generated files"
    echo "   - Recommended: VLC, mpv, Kodi, IINA, etc."
    echo ""
}

setup_scheduled_task_and_web() {
    echo ""
    echo "========================================"
    echo "Setting Up Scheduled Task"
    echo "========================================"

    echo "[5/5] Registering scheduled task..."

    WORK_DIR="$(cd "$(dirname "$0")" && pwd)"
    SCRIPT_PATH="$WORK_DIR/$(basename "$0")"
    CRON_CMD="0 */4 * * * cd $WORK_DIR && $SCRIPT_PATH --collect >> $WORK_DIR/iptv_cron.log 2>&1"

    EXISTING_CRON=$(crontab -l 2>/dev/null | grep -F "iptv_tool.sh --collect")

    if [ -n "$EXISTING_CRON" ]; then
        echo "[*] Scheduled task already exists in crontab:"
        echo "    $EXISTING_CRON"
    else
        echo "Adding crontab entry: every 4 hours"
        echo "    $CRON_CMD"
        echo ""

        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

        if [ $? -eq 0 ]; then
            echo "[*] Scheduled task created successfully!"
        else
            echo "[WARNING] Failed to add crontab entry"
            echo "    You can manually add: crontab -e"
            echo "    Add this line:"
            echo "    $CRON_CMD"
        fi
    fi

    echo ""
    echo "========================================"
    echo "Starting Local Web Server"
    echo "========================================"

    if [ ! -f ".github/workflows/index.html" ]; then
        echo "ERROR: index.html not found"
        exit 1
    fi

    echo "Starting local web server..."
    echo ""
    echo "Server URL: http://localhost:8000"
    echo ""
    echo "Tips:"
    echo "   - Press Ctrl+C to stop the server"
    echo "   - Closing this terminal will also stop the server"
    echo "   - Scheduled task will auto-collect every 4 hours"
    echo ""
    echo "========================================"
    echo ""

    source "$VENV_PATH/bin/activate"
    $PYTHON_CMD "$WORK_DIR/server.py" 8000
    cd "$WORK_DIR"
}

cleanup_exit() {
    echo ""
    echo "Cleaning up processes..."
    pkill -f "server.py 8000" >/dev/null 2>&1
    echo "Done"
    exit 0
}

main() {
    WORK_DIR="$(cd "$(dirname "$0")" && pwd)"
    cd "$WORK_DIR"

    detect_python_env || exit 1
    test_pip_mirrors
    detect_venv
    setup_venv

    case "${1:-}" in
        --collect)
            run_collection
            ;;
        *)
            run_collection
            setup_scheduled_task_and_web
            ;;
    esac
}

trap cleanup_exit INT TERM

main "$@"