#!/bin/bash

# ========================================
# IPTV直播源自动采集工具 - Linux/macOS完整版
# 功能：环境检测、虚拟环境、数据采集、网页服务
# ========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 工作目录
WORK_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$WORK_DIR"

# 日志函数
log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_section() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
}

# 检测Python环境
detect_python() {
    log_section "🔍 环境检测与配置"
    
    echo "[1/6] 检测Python环境..."
    PYTHON_CMD=""
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        log_info "Python版本：$(python3 --version 2>&1 | awk '{print $2}') (命令: python3)"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        log_info "Python版本：$(python --version 2>&1 | awk '{print $2}') (命令: python)"
    else
        log_error "Python环境检测失败"
        echo ""
        echo "请先安装Python 3.10或更高版本："
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
            echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
            echo "  Arch Linux: sudo pacman -S python python-pip"
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            echo "  macOS: brew install python3"
        fi
        return 1
    fi
    
    return 0
}

# 检测虚拟环境
detect_venv() {
    echo "[2/6] 检测虚拟环境..."
    
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        log_info "检测到虚拟环境：venv"
        VENV_EXISTS=1
        VENV_PATH="venv"
    elif [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
        log_info "检测到虚拟环境：.venv"
        VENV_EXISTS=1
        VENV_PATH=".venv"
    else
        log_warn "未检测到虚拟环境"
        VENV_EXISTS=0
        VENV_PATH=""
    fi
    
    return 0
}

# 检测依赖包
check_dependencies() {
    echo "[3/6] 检测依赖包..."
    
    if [ -n "$VENV_PATH" ]; then
        source "$VENV_PATH/bin/activate"
        if $PYTHON_CMD -c "import aiohttp" &> /dev/null; then
            log_info "aiohttp依赖正常"
        else
            log_warn "aiohttp未安装"
        fi
        deactivate
    else
        if $PYTHON_CMD -c "import aiohttp" &> /dev/null; then
            log_info "aiohttp依赖正常"
        else
            log_warn "aiohttp未安装"
        fi
    fi
    
    return 0
}

# 检测脚本文件
check_scripts() {
    echo "[4/6] 检测脚本文件..."
    
    if [ -f ".github/workflows/iptv.py" ]; then
        log_info "iptv.py脚本文件存在"
    else
        log_error "iptv.py脚本文件不存在"
    fi
    
    if [ -f ".github/workflows/index.html" ]; then
        log_info "index.html网页文件存在"
    else
        log_error "index.html网页文件不存在"
    fi
    
    return 0
}

# 检测IPTV配置目录
check_iptv_config() {
    echo "[5/6] 检测IPTV配置目录..."
    
    if [ -d ".github/workflows/IPTV" ]; then
        log_info "IPTV配置目录存在"
        
        if [ -f ".github/workflows/IPTV/CCTV.txt" ]; then
            log_info "CCTV频道配置文件存在"
        else
            log_warn "CCTV频道配置文件不存在"
        fi
        
        province_count=$(find .github/workflows/IPTV -name "*.txt" | wc -l)
        log_info "省市频道配置文件数量：$province_count 个"
    else
        log_error "IPTV配置目录不存在"
    fi
    
    return 0
}

# 检测网络连接
check_network() {
    echo "[6/6] 检测网络连接..."
    
    if ping -c 1 8.8.8.8 &> /dev/null; then
        log_info "网络连接正常"
    else
        log_warn "网络连接测试失败"
    fi
    
    return 0
}

# 完整环境检测
check_environment() {
    detect_python || return 1
    detect_venv
    check_dependencies
    check_scripts
    check_iptv_config
    check_network
    
    log_section "环境检测完成"
    return 0
}

# 创建虚拟环境
create_venv() {
    log_section "创建虚拟环境"
    
    if [ -d "venv" ]; then
        log_warn "venv目录已存在"
        read -p "是否删除并重新创建？ (y/n): " overwrite
        if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
            echo "已取消创建"
            return 0
        fi
        rm -rf venv
    fi
    
    echo "正在创建虚拟环境..."
    $PYTHON_CMD -m venv venv
    
    if [ $? -ne 0 ]; then
        log_error "虚拟环境创建失败"
        return 1
    fi
    
    log_info "虚拟环境创建成功"
    
    echo "正在安装依赖包..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install aiohttp
    deactivate
    
    log_info "依赖包安装完成"
    return 0
}

# 激活虚拟环境并安装依赖
activate_venv() {
    log_section "激活虚拟环境并安装依赖"
    
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        log_info "虚拟环境已激活：venv"
    elif [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        log_info "虚拟环境已激活：.venv"
    else
        log_error "未找到虚拟环境"
        echo "请先创建虚拟环境"
        return 1
    fi
    
    echo ""
    echo "正在检查并安装依赖..."
    pip install --upgrade pip
    pip install aiohttp
    
    log_info "依赖包安装完成"
    echo ""
    echo "提示：虚拟环境已在此会话中激活"
    echo "如需在新的终端窗口中使用，请运行："
    echo "  source venv/bin/activate"
    echo ""
    
    deactivate
    return 0
}

# 删除虚拟环境
delete_venv() {
    log_section "删除虚拟环境"
    
    if [ -d "venv" ]; then
        log_warn "即将删除venv目录"
        read -p "确认删除？ (y/n): " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            rm -rf venv
            log_info "虚拟环境已删除"
        else
            echo "已取消删除"
        fi
    elif [ -d ".venv" ]; then
        log_warn "即将删除.venv目录"
        read -p "确认删除？ (y/n): " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            rm -rf .venv
            log_info "虚拟环境已删除"
        else
            echo "已取消删除"
        fi
    else
        echo "未找到虚拟环境"
    fi
    
    return 0
}

# 虚拟环境管理菜单
venv_management() {
    while true; do
        clear
        echo ""
        echo "═══════════════════════════════════════════════════════════"
        echo "  🐍 虚拟环境管理"
        echo "═══════════════════════════════════════════════════════════"
        echo ""
        
        if [ -d "venv" ] || [ -d ".venv" ]; then
            log_info "检测到虚拟环境"
        else
            log_warn "未检测到虚拟环境"
        fi
        echo ""
        
        echo "请选择操作："
        echo "  [1] 创建虚拟环境"
        echo "  [2] 激活虚拟环境并安装依赖"
        echo "  [3] 删除虚拟环境"
        echo "  [0] 返回主菜单"
        echo ""
        read -p "请选择操作 (0-3): " venv_choice
        
        case $venv_choice in
            1)
                create_venv
                ;;
            2)
                activate_venv
                ;;
            3)
                delete_venv
                ;;
            0)
                return 0
                ;;
            *)
                echo ""
                log_error "无效选项"
                ;;
        esac
        
        echo ""
        read -p "按Enter键继续..."
    done
}

# 运行IPTV采集
run_collection() {
    log_section "运行IPTV采集"
    
    # 检测Python环境
    if ! detect_python; then
        return 1
    fi
    
    # 检测虚拟环境
    detect_venv
    
    # 激活虚拟环境（如果存在）
    if [ -n "$VENV_PATH" ]; then
        echo "使用虚拟环境：$VENV_PATH"
        source "$VENV_PATH/bin/activate"
        USING_VENV=1
    else
        log_warn "未检测到虚拟环境，使用系统Python"
        echo "💡 建议创建虚拟环境以隔离依赖"
        USING_VENV=0
    fi
    
    echo ""
    echo "开始采集IPTV直播源..."
    echo "========================================"
    echo ""
    
    $PYTHON_CMD .github/workflows/iptv.py
    
    if [ $? -ne 0 ]; then
        echo ""
        log_error "脚本执行失败"
        if [ $USING_VENV -eq 1 ]; then
            deactivate
        fi
        return 1
    fi
    
    if [ $USING_VENV -eq 1 ]; then
        deactivate
    fi
    
    echo ""
    echo "========================================"
    log_info "IPTV直播源采集完成！"
    echo "========================================"
    echo ""
    
    # 检查生成的文件
    if [ -f "best_sorted.m3u" ]; then
        echo "📄 生成的M3U文件：best_sorted.m3u"
        echo "   文件大小：$(wc -c < best_sorted.m3u) 字节"
    fi
    
    if [ -f "best_sorted.m3u8" ]; then
        echo "📄 生成的M3U8文件：best_sorted.m3u8"
        echo "   文件大小：$(wc -c < best_sorted.m3u8) 字节"
    fi
    
    echo ""
    echo "💡 提示："
    echo "   - 可以使用支持M3U格式的播放器打开生成的文件"
    echo "   - 推荐播放器：VLC、mpv、Kodi、IINA等"
    echo "   - 定期运行此脚本以获取最新的直播源"
    echo ""
    
    return 0
}

# 启动本地网页服务
start_web_server() {
    log_section "启动本地网页服务"
    
    if [ ! -f ".github/workflows/index.html" ]; then
        log_error "未找到index.html文件"
        return 1
    fi
    
    echo "正在启动本地网页服务..."
    echo ""
    echo "📡 服务地址：http://localhost:8000"
    echo "📁 服务目录：$WORK_DIR"
    echo ""
    echo "💡 提示："
    echo "   - 按 Ctrl+C 停止服务"
    echo "   - 关闭此终端也会停止服务"
    echo ""
    echo "========================================"
    echo ""
    
    # 检测Python环境
    if ! detect_python; then
        return 1
    fi
    
    cd .github/workflows
    $PYTHON_CMD -m http.server 8000
    cd "$WORK_DIR"
    
    return 0
}

# 配置定时任务
setup_scheduled_task() {
    log_section "配置定时任务"
    
    echo "正在创建定时任务脚本..."
    echo ""
    
    # 创建定时任务脚本
    cat > iptv_scheduled_task.sh << 'EOF'
#!/bin/bash

# IPTV定时采集任务

LOG_FILE="iptv_scheduled.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "开始IPTV定时采集"

# 设置工作目录
cd "$(dirname "$0")" || exit 1

# 检测Python环境
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    log "错误：未检测到Python环境"
    exit 1
fi

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# 运行采集脚本
$PYTHON_CMD .github/workflows/iptv.py

log "IPTV定时采集完成"
EOF
    
    chmod +x iptv_scheduled_task.sh
    
    log_info "定时任务脚本已创建：iptv_scheduled_task.sh"
    echo ""
    echo "💡 配置crontab定时任务（每4小时运行一次）："
    echo "   crontab -e"
    echo ""
    echo "   添加以下行："
    echo "   0 */4 * * * $WORK_DIR/iptv_scheduled_task.sh >> $WORK_DIR/iptv_cron.log 2>&1"
    echo ""
    echo "💡 或者直接运行测试："
    echo "   ./iptv_scheduled_task.sh"
    echo ""
    
    return 0
}

# 查看生成的文件
view_files() {
    log_section "查看生成的文件"
    
    echo "生成的播放列表文件："
    echo ""
    
    if [ -f "best_sorted.m3u" ]; then
        echo "[1] best_sorted.m3u (M3U格式)"
        echo "    大小：$(wc -c < best_sorted.m3u) 字节"
        echo "    修改时间：$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" best_sorted.m3u 2>/dev/null || stat -c "%y" best_sorted.m3u)"
        echo ""
    fi
    
    if [ -f "best_sorted.m3u8" ]; then
        echo "[2] best_sorted.m3u8 (M3U8格式)"
        echo "    大小：$(wc -c < best_sorted.m3u8) 字节"
        echo "    修改时间：$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" best_sorted.m3u8 2>/dev/null || stat -c "%y" best_sorted.m3u8)"
        echo ""
    fi
    
    if [ ! -f "best_sorted.m3u" ] && [ ! -f "best_sorted.m3u8" ]; then
        echo "暂无生成的文件"
        echo ""
    fi
    
    echo "请选择操作："
    echo "  [1] 查看M3U文件"
    echo "  [2] 查看M3U8文件"
    echo "  [3] 打开文件所在目录"
    echo "  [0] 返回主菜单"
    echo ""
    read -p "请选择操作 (0-3): " view_choice
    
    case $view_choice in
        1)
            if [ -f "best_sorted.m3u" ]; then
                ${PAGER:-less} best_sorted.m3u
            fi
            ;;
        2)
            if [ -f "best_sorted.m3u8" ]; then
                ${PAGER:-less} best_sorted.m3u8
            fi
            ;;
        3)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                open .
            else
                xdg-open . 2>/dev/null || echo "无法打开文件管理器"
            fi
            ;;
        0)
            return 0
            ;;
    esac
    
    return 0
}

# 清理临时文件
cleanup() {
    log_section "清理临时文件"
    
    echo "警告：此操作将删除以下文件："
    echo "  - Python缓存文件 (__pycache__)"
    echo "  - 临时文件 (*.pyc)"
    echo "  - 虚拟环境 (venv/.venv)"
    echo "  - 生成的播放列表 (best_sorted.m3u/m3u8)"
    echo ""
    read -p "确认清理？ (y/n): " confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "已取消清理"
        return 0
    fi
    
    echo ""
    echo "正在清理..."
    
    # 清理Python缓存
    if [ -d "__pycache__" ]; then
        rm -rf __pycache__
        log_info "已清理：__pycache__"
    fi
    
    # 清理.pyc文件
    find . -name "*.pyc" -delete 2>/dev/null
    log_info "已清理：*.pyc文件"
    
    # 清理虚拟环境
    if [ -d "venv" ]; then
        rm -rf venv
        log_info "已清理：venv虚拟环境"
    fi
    
    if [ -d ".venv" ]; then
        rm -rf .venv
        log_info "已清理：.venv虚拟环境"
    fi
    
    # 清理生成的文件
    if [ -f "best_sorted.m3u" ]; then
        rm best_sorted.m3u
        log_info "已清理：best_sorted.m3u"
    fi
    
    if [ -f "best_sorted.m3u8" ]; then
        rm best_sorted.m3u8
        log_info "已清理：best_sorted.m3u8"
    fi
    
    echo ""
    log_info "清理完成！"
    echo ""
    
    return 0
}

# 显示帮助
show_help() {
    log_section "帮助文档"
    
    echo "🎯 功能说明："
    echo ""
    echo "  [1] 环境检测与配置"
    echo "     - 检测Python环境"
    echo "     - 检测虚拟环境"
    echo "     - 检测依赖包"
    echo "     - 检测脚本文件"
    echo "     - 检测网络连接"
    echo ""
    echo "  [2] 虚拟环境管理"
    echo "     - 创建虚拟环境"
    echo "     - 激活虚拟环境并安装依赖"
    echo "     - 删除虚拟环境"
    echo ""
    echo "  [3] 运行IPTV采集"
    echo "     - 自动检测并使用虚拟环境"
    echo "     - 采集IPTV直播源"
    echo "     - 智能分类和质量筛选"
    echo "     - 生成M3U播放列表"
    echo ""
    echo "  [4] 启动本地网页服务"
    echo "     - 提供网页界面"
    echo "     - 支持搜索和筛选"
    echo "     - 实时查看频道信息"
    echo ""
    echo "  [5] 配置定时任务"
    echo "     - 创建定时任务脚本"
    echo "     - 配置crontab定时任务"
    echo "     - 实现自动更新"
    echo ""
    echo "  [6] 查看生成的文件"
    echo "     - 查看M3U/M3U8文件"
    echo "     - 打开文件所在目录"
    echo ""
    echo "  [7] 清理临时文件"
    echo "     - 清理Python缓存"
    echo "     - 清理虚拟环境"
    echo "     - 清理生成的文件"
    echo ""
    echo "📖 详细文档："
    echo "   - 查看README.md了解更多信息"
    echo "   - 查看项目GitHub页面获取最新更新"
    echo ""
    
    return 0
}

# 主菜单
main_menu() {
    while true; do
        clear
        echo ""
        echo "╔════════════════════════════════════════════════════════════╗"
        echo "║     IPTV直播源自动采集工具 - Linux/macOS完整版          ║"
        echo "╚════════════════════════════════════════════════════════════╝"
        echo ""
        echo "📋 功能菜单："
        echo ""
        echo "  [1] 环境检测与配置"
        echo "  [2] 虚拟环境管理"
        echo "  [3] 运行IPTV采集"
        echo "  [4] 启动本地网页服务"
        echo "  [5] 配置定时任务"
        echo "  [6] 查看生成的文件"
        echo "  [7] 清理临时文件"
        echo "  [8] 查看帮助文档"
        echo "  [0] 退出程序"
        echo ""
        read -p "请选择功能 (0-8): " choice
        
        case $choice in
            1)
                check_environment
                ;;
            2)
                venv_management
                ;;
            3)
                run_collection
                ;;
            4)
                start_web_server
                ;;
            5)
                setup_scheduled_task
                ;;
            6)
                view_files
                ;;
            7)
                cleanup
                ;;
            8)
                show_help
                ;;
            0)
                echo ""
                echo "感谢使用IPTV直播源自动采集工具！"
                echo ""
                exit 0
                ;;
            *)
                echo ""
                log_error "无效选项，请重新选择"
                ;;
        esac
        
        echo ""
        read -p "按Enter键继续..."
    done
}

# 程序入口
main_menu