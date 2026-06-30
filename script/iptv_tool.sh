#!/bin/bash

# ========================================
# IPTV 直播源采集工具 - Linux/macOS
# 自动: 环境检测 -> 镜像测试 -> 虚拟环境 -> 定时任务 -> Web服务
# ========================================

VERSION=$(python3 -c "import re; m=re.search(r'###\s+v(\d+\.\d+\.\d+)', open('README.md', encoding='utf-8').read()); print(m.group(1) if m else '0.0.0')" 2>/dev/null || python -c "import re; m=re.search(r'###\s+v(\d+\.\d+\.\d+)', open('README.md', encoding='utf-8').read()); print(m.group(1) if m else '0.0.0')" 2>/dev/null || echo "0.0.0")

echo "========================================"
echo "IPTV 直播源采集工具 - v${VERSION}"
echo "========================================"

SCRIPT_START_TIME=$(date +%s)

VENV_PATH=".venv"
FASTEST_PIP_MIRROR=""

SERVER_PORT="${IPTV_SERVER_PORT:-8000}"
LAN_IP_DETECT_HOST="${IPTV_LAN_IP_DETECT_HOST:-8.8.8.8}"
LAN_IP_DETECT_PORT="${IPTV_LAN_IP_DETECT_PORT:-80}"
export IPTV_TIMEOUT="${IPTV_TIMEOUT:-3}"
export IPTV_MAX_PARALLEL="${IPTV_MAX_PARALLEL:-30}"
export IPTV_PROXY_TIMEOUT="${IPTV_PROXY_TIMEOUT:-15}"
export IPTV_TRANSCODE_SESSION_TIMEOUT="${IPTV_TRANSCODE_SESSION_TIMEOUT:-600}"

show_step_time() {
    local step_name="$1"
    local step_start="$2"
    local now=$(date +%s)
    local diff=$((now - step_start))
    if [ "$diff" -ge 60 ]; then
        local mins=$((diff / 60))
        local secs=$((diff % 60))
        echo "[*] $step_name 耗时: ${mins}分 ${secs}秒"
    else
        echo "[*] $step_name 耗时: ${diff}秒"
    fi
}

init_homebrew() {
    if [ "$(uname -s)" != "Darwin" ]; then
        return 0
    fi

    if command -v brew &> /dev/null; then
        echo "[*] Homebrew 已在 PATH 中: $(command -v brew)"
        return 0
    fi

    local brew_candidate=""
    for brew_path in \
        "/opt/homebrew/bin/brew" \
        "/usr/local/bin/brew" \
        "$HOME/.linuxbrew/bin/brew" \
        "/home/linuxbrew/.linuxbrew/bin/brew"; do
        if [ -x "$brew_path" ]; then
            brew_candidate="$brew_path"
            break
        fi
    done

    if [ -n "$brew_candidate" ]; then
        echo "[*] 检测到 Homebrew: $brew_candidate，正在加载本地环境..."
        eval "$($brew_candidate shellenv)"
        if command -v brew &> /dev/null; then
            echo "[*] Homebrew 环境加载成功，前缀: ${HOMEBREW_PREFIX:-未知}"
        else
            echo "[警告] Homebrew 环境加载失败"
        fi
    else
        echo "[警告] 未找到 Homebrew，部分功能可能受限"
    fi
}

detect_python_env() {
    echo ""
    echo "========================================"
    echo "环境检测与配置"
    echo "========================================"

    echo "[1/5] 检测 Python 环境..."

    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        echo "Python: $(python3 --version 2>&1)"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        echo "Python: $(python --version 2>&1)"
    else
        echo "Python 不在 PATH 中，正在搜索系统..."

        COMMON_PYTHON_PATHS=(
            "$WORK_DIR/.venv/python/bin/python3"
            "$WORK_DIR/.venv/python/bin/python"
            "/usr/bin/python3"
            "/usr/local/bin/python3"
            "/opt/homebrew/bin/python3"
            "$HOME/.pyenv/shims/python3"
            "/usr/bin/python"
            "/usr/local/bin/python"
        )

        for py_path in "${COMMON_PYTHON_PATHS[@]}"; do
            if [ -x "$py_path" ]; then
                echo "[*] 找到 Python: $py_path"
                export PATH="$(dirname $py_path):$PATH"
                PYTHON_CMD="$py_path"
                break
            fi
        done

        if [ -z "$PYTHON_CMD" ]; then
            echo "[警告] 未找到 Python，正在自动安装..."

            case "$(uname -s)" in
                Darwin)
                    if command -v brew &> /dev/null; then
                        echo "    通过 Homebrew 安装 Python..."
                        brew install python
                    else
                        echo "[错误] 未找到 Homebrew，无法自动安装 Python"
                        echo "请先安装 Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                        return 1
                    fi
                    ;;
                Linux)
                    if command -v apt-get &> /dev/null; then
                        echo "    通过 apt 安装 Python..."
                        sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip
                    elif command -v yum &> /dev/null; then
                        echo "    通过 yum 安装 Python..."
                        sudo yum install -y python3 python3-pip
                    elif command -v dnf &> /dev/null; then
                        echo "    通过 dnf 安装 Python..."
                        sudo dnf install -y python3 python3-pip
                    elif command -v pacman &> /dev/null; then
                        echo "    通过 pacman 安装 Python..."
                        sudo pacman -Syu --noconfirm python python-pip
                    else
                        echo "[错误] 未识别的包管理器，请手动安装 Python"
                        return 1
                    fi
                    ;;
                *)
                    echo "[错误] 不支持的操作系统"
                    return 1
                    ;;
            esac

            if command -v python3 &> /dev/null; then
                PYTHON_CMD="python3"
                echo "[*] Python 安装完成: $(python3 --version 2>&1)"
            elif command -v python &> /dev/null; then
                PYTHON_CMD="python"
                echo "[*] Python 安装完成: $(python --version 2>&1)"
            else
                echo "[错误] Python 安装失败"
                return 1
            fi
        fi
    fi

    echo ""
    echo "[*] 检查虚拟环境状态..."
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "已在虚拟环境中: $VIRTUAL_ENV"
        IN_VENV=1
    else
        echo "未在虚拟环境中"
        IN_VENV=0
    fi

    return 0
}

detect_ffmpeg() {
    echo ""
    echo "========================================"
    echo "FFmpeg 检测与安装"
    echo "========================================"

    if command -v ffmpeg &> /dev/null; then
        echo "[*] FFmpeg 已安装:"
        ffmpeg -version 2>&1 | head -1
        return 0
    fi

    FFMPEG_DIR="$WORK_DIR/.venv/ffmpeg"
    if [ -x "$FFMPEG_DIR/bin/ffmpeg" ]; then
        echo "[*] 在虚拟环境中找到 FFmpeg: $FFMPEG_DIR"
        export PATH="$FFMPEG_DIR/bin:$PATH"
        ffmpeg -version 2>&1 | head -1
        return 0
    fi

    echo "未找到 FFmpeg，正在自动安装..."
    echo ""

    case "$(uname -s)" in
        Darwin)
            if command -v brew &> /dev/null; then
                echo "[1/1] 通过 Homebrew 安装 FFmpeg..."
                brew install ffmpeg
            else
                echo "[警告] 未找到 Homebrew，无法自动安装 FFmpeg"
                echo "   请先安装 Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                echo "   然后运行: brew install ffmpeg"
                return 0
            fi
            ;;
        Linux)
            if command -v apt-get &> /dev/null; then
                echo "[1/1] 通过 apt 安装 FFmpeg..."
                sudo apt-get update -qq && sudo apt-get install -y ffmpeg
            elif command -v yum &> /dev/null; then
                echo "[1/1] 通过 yum 安装 FFmpeg..."
                sudo yum install -y epel-release 2>/dev/null
                sudo yum install -y ffmpeg
            elif command -v dnf &> /dev/null; then
                echo "[1/1] 通过 dnf 安装 FFmpeg..."
                sudo dnf install -y ffmpeg
            elif command -v pacman &> /dev/null; then
                echo "[1/1] 通过 pacman 安装 FFmpeg..."
                sudo pacman -Syu --noconfirm ffmpeg
            elif command -v apk &> /dev/null; then
                echo "[1/1] 通过 apk 安装 FFmpeg..."
                sudo apk add ffmpeg
            else
                echo "[警告] 未识别的包管理器，请手动安装 FFmpeg"
                return 0
            fi
            ;;
        *)
            echo "[警告] 不支持的操作系统，无法自动安装 FFmpeg"
            return 0
            ;;
    esac

    if command -v ffmpeg &> /dev/null; then
        echo "[*] FFmpeg 安装成功:"
        ffmpeg -version 2>&1 | head -1
    else
        echo "[警告] FFmpeg 安装可能失败，浏览器中 AC3/EAC3 音频将无声音"
        echo "   可手动安装 FFmpeg: https://ffmpeg.org/download.html"
    fi
}

test_pip_mirrors() {
    echo "[2/5] 测试 PIP 镜像源..."

    declare -a MIRRORS=(
        "https://pypi.tuna.tsinghua.edu.cn/simple|清华"
        "https://mirrors.aliyun.com/pypi/simple/|阿里云"
        "https://pypi.douban.com/simple/|豆瓣"
        "https://pypi.mirrors.ustc.edu.cn/simple/|中科大"
    )

    MIN_TIME=9999
    BEST_MIRROR=""
    BEST_NAME=""

    for mirror_entry in "${MIRRORS[@]}"; do
        IFS='|' read -r MIRROR_URL MIRROR_NAME <<< "$mirror_entry"
        echo "    测试 $MIRROR_NAME..."

        TEST_TIME=$(curl -s -o /dev/null -w "%{time_connect}" --connect-timeout 1.5 --max-time 2 "$MIRROR_URL" 2>/dev/null)

        if [ -z "$TEST_TIME" ] || [ "$TEST_TIME" = "0.000" ]; then
            echo "        $MIRROR_NAME: 超时/失败"
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
        echo "[*] 最快 PIP 镜像: $BEST_NAME (${MIN_TIME}ms)"
    else
        echo "[警告] 所有镜像均失败，使用默认 PyPI"
        FASTEST_PIP_MIRROR="https://pypi.org/simple/"
    fi
}

detect_venv() {
    echo "[3/5] 检测 Python 虚拟环境..."

    if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
        echo "已找到虚拟环境: .venv"
        VENV_EXISTS=1
    else
        echo "未找到虚拟环境"
        VENV_EXISTS=0
    fi
}

setup_venv() {
    echo "[4/5] 配置 Python 虚拟环境并安装依赖..."

    if [ "$VENV_EXISTS" -eq 0 ]; then
        echo "正在创建虚拟环境: $VENV_PATH..."
        $PYTHON_CMD -m venv $VENV_PATH

        if [ $? -ne 0 ]; then
            echo "错误: 创建虚拟环境失败"
            exit 1
        fi
        VENV_EXISTS=1
    fi

    source "$VENV_PATH/bin/activate"

    if [ -n "$FASTEST_PIP_MIRROR" ]; then
        echo "[*] 配置 PIP 镜像: $FASTEST_PIP_MIRROR"

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

    echo "正在安装 Python 依赖..."

    if [ -n "$FASTEST_PIP_MIRROR" ]; then
        pip install --upgrade pip -i "$FASTEST_PIP_MIRROR" --disable-pip-version-check
        pip install aiohttp -i "$FASTEST_PIP_MIRROR" --disable-pip-version-check

        if [ $? -ne 0 ]; then
            echo "警告: 镜像安装失败，尝试默认源..."
            pip install --upgrade pip --disable-pip-version-check
            pip install aiohttp --disable-pip-version-check
        fi
    else
        pip install --upgrade pip --disable-pip-version-check
        pip install aiohttp --disable-pip-version-check
    fi

    if [ $? -ne 0 ]; then
        echo "错误: 依赖安装失败"
        exit 1
    fi

    echo "Python 虚拟环境配置完成"
}

run_collection() {
    echo ""
    echo "========================================"
    echo "运行 IPTV 采集"
    echo "========================================"

    echo "[5/5] 检查脚本文件和配置..."

    if [ ! -f ".github/workflows/iptv.py" ]; then
        echo "错误: 未找到 iptv.py 脚本"
        exit 1
    fi
    echo "[*] 已找到 iptv.py 脚本"

    if [ -d ".github/workflows/IPTV" ]; then
        echo "[*] 已找到 IPTV 配置目录"
    else
        echo "警告: 未找到 IPTV 配置目录"
    fi

    echo ""
    echo "开始采集 IPTV 直播源..."
    echo "========================================"
    echo ""

    COLLECT_START=$(date +%s)
    source "$VENV_PATH/bin/activate"
    $PYTHON_CMD .github/workflows/iptv.py

    if [ $? -ne 0 ]; then
        echo ""
        echo "错误: 脚本执行失败"
        exit 1
    fi

    show_step_time "IPTV 采集" "$COLLECT_START"

    echo ""
    echo "========================================"
    echo "IPTV 采集完成！"
    echo "========================================"
    echo ""

    if [ -f "best_sorted.m3u" ]; then
        echo "已生成 M3U 文件: best_sorted.m3u"
        echo "   文件大小: $(wc -c < best_sorted.m3u) 字节"
    fi

    if [ -f "best_sorted.m3u8" ]; then
        echo "已生成 M3U8 文件: best_sorted.m3u8"
        echo "   文件大小: $(wc -c < best_sorted.m3u8) 字节"
    fi

    if [ -f "$WORK_DIR/script/notify.py" ]; then
        echo "[*] 检测文件变更并发送通知..."
        $PYTHON_CMD "$WORK_DIR/script/notify.py"
    fi

    echo ""
    echo "提示:"
    echo "   - 使用支持 M3U 的播放器打开生成的文件"
    echo "   - 推荐: VLC、mpv、Kodi、IINA 等"

    show_step_time "总计" "$SCRIPT_START_TIME"
    echo ""
}

setup_scheduled_task_and_web() {
    echo ""
    echo "========================================"
    echo "配置定时任务"
    echo "========================================"

    echo "[5/5] 注册定时任务..."

    WORK_DIR="$(cd "$(dirname "$0")" && pwd)"
    SCRIPT_PATH="$WORK_DIR/$(basename "$0")"
    CRON_CMD="0 */4 * * * cd $WORK_DIR && $SCRIPT_PATH --collect >> $WORK_DIR/iptv_cron.log 2>&1"

    EXISTING_CRON=$(crontab -l 2>/dev/null | grep -F "iptv_tool.sh --collect")

    if [ -n "$EXISTING_CRON" ]; then
        echo "[*] 定时任务已存在于 crontab:"
        echo "    $EXISTING_CRON"
    else
        echo "正在添加 crontab 条目: 每4小时执行一次"
        echo "    $CRON_CMD"
        echo ""

        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

        if [ $? -eq 0 ]; then
            echo "[*] 定时任务创建成功！"
        else
            echo "[警告] 添加 crontab 条目失败"
            echo "    可手动添加: crontab -e"
            echo "    添加以下内容:"
            echo "    $CRON_CMD"
        fi
    fi

    echo ""
    echo "========================================"
    echo "启动本地 Web 服务"
    echo "========================================"

    if [ ! -f ".github/workflows/index.html" ]; then
        echo "错误: 未找到 index.html"
        exit 1
    fi

    echo "正在启动本地 Web 服务..."

    LAN_IP=$(python3 -c "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('$LAN_IP_DETECT_HOST',$LAN_IP_DETECT_PORT)); ip=s.getsockname()[0]; s.close(); print(ip)" 2>/dev/null || python -c "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('$LAN_IP_DETECT_HOST',$LAN_IP_DETECT_PORT)); ip=s.getsockname()[0]; s.close(); print(ip)" 2>/dev/null)

    echo ""
    echo "  访问地址: http://localhost:${SERVER_PORT}"
    if [ -n "$LAN_IP" ]; then
        echo "  局域网地址: http://${LAN_IP}:${SERVER_PORT}"
    fi
    echo ""
    echo "提示:"
    echo "   - 按 Ctrl+C 停止服务"
    echo "   - 关闭终端也会停止服务"
    echo "   - 定时任务将每4小时自动采集"
    echo ""
    echo "========================================"
    echo ""

    source "$VENV_PATH/bin/activate"
    $PYTHON_CMD "$WORK_DIR/server.py" $SERVER_PORT
    cd "$WORK_DIR"
}

cleanup_exit() {
    echo ""
    echo "正在清理进程..."
    pkill -f "server.py $SERVER_PORT" >/dev/null 2>&1
    echo "完成"
    exit 0
}

main() {
    WORK_DIR="$(cd "$(dirname "$0")" && pwd)"
    cd "$WORK_DIR"

    init_homebrew

    detect_python_env || exit 1

    STEP_START=$(date +%s)
    detect_ffmpeg
    show_step_time "FFmpeg 检测" "$STEP_START"

    STEP_START=$(date +%s)
    test_pip_mirrors
    show_step_time "PIP 镜像测试" "$STEP_START"

    STEP_START=$(date +%s)
    detect_venv
    setup_venv
    show_step_time "虚拟环境配置" "$STEP_START"

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