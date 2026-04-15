# 🚀 IPTV直播源自动采集工具 - 完整使用指南

欢迎使用IPTV直播源自动采集工具！这是一个功能完整的跨平台IPTV采集系统，支持Windows、Linux和macOS。

## 📦 项目特性

### ✨ 核心功能

- **🤖 智能分类**：自动识别CCTV、各省市频道、主题频道等
- **⚡ 质量筛选**：测试延迟和可用性，优选最佳源
- **🌐 用户友好**：提供网页界面，支持搜索和筛选
- **🔄 持续更新**：每4小时自动更新，确保数据新鲜度
- **🐍 虚拟环境**：自动检测和管理Python虚拟环境
- **📱 跨平台**：支持Windows、Linux、macOS

### 🎯 智能分类系统

- **央视频道**：CCTV-1到CCTV-16、CGTN、CHC等
- **省市频道**：全国31个省市自治区频道
- **主题频道**：新闻、体育、影视、少儿、音乐、戏曲等
- **港澳台频道**：翡翠台、明珠台、东森、中天等
- **文旅频道**：景区、风景、观光等特色频道

### 🔍 质量筛选机制

- **可用性测试**：实时检测直播源是否可访问
- **延迟测量**：测试响应时间，优选低延迟源
- **智能去重**：自动识别和合并重复频道
- **并发测试**：支持30个并发连接，提高测试效率

## 📋 文件说明

### 核心脚本

| 文件名 | 平台 | 说明 |
|--------|------|------|
| [iptv_tool.bat](iptv_tool.bat) | Windows | 完整版Windows工具（推荐） |
| [iptv_tool.sh](iptv_tool.sh) | Linux/macOS | 完整版Linux/macOS工具（推荐） |

### 核心文件

| 文件名 | 说明 |
|--------|------|
| [.github/workflows/iptv.py](.github/workflows/iptv.py) | IPTV采集核心脚本 |
| [.github/workflows/index.html](.github/workflows/index.html) | 网页界面 |
| [.github/workflows/IPTV/](.github/workflows/IPTV/) | 频道配置目录 |

### 生成文件

| 文件名 | 说明 |
|--------|------|
| best_sorted.m3u | M3U格式播放列表 |
| best_sorted.m3u8 | M3U8格式播放列表 |

## 🚀 快速开始

### Windows用户

#### 方法1：使用完整版工具（推荐）

```cmd
# 双击运行或在命令行执行
iptv_tool.bat
```

#### 方法2：首次使用流程

1. **环境检测**
   ```
   选择 [1] 环境检测与配置
   ```

2. **创建虚拟环境**
   ```
   选择 [2] 虚拟环境管理 → [1] 创建虚拟环境
   ```

3. **运行采集**
   ```
   选择 [3] 运行IPTV采集
   ```

4. **启动网页服务**
   ```
   选择 [4] 启动本地网页服务
   ```

### Linux/macOS用户

#### 方法1：使用完整版工具（推荐）

```bash
# 添加执行权限
chmod +x iptv_tool.sh

# 运行工具
./iptv_tool.sh
```

#### 方法2：首次使用流程

1. **环境检测**
   ```
   选择 [1] 环境检测与配置
   ```

2. **创建虚拟环境**
   ```
   选择 [2] 虚拟环境管理 → [1] 创建虚拟环境
   ```

3. **运行采集**
   ```
   选择 [3] 运行IPTV采集
   ```

4. **启动网页服务**
   ```
   选择 [4] 启动本地网页服务
   ```

## 📖 功能详解

### 1. 环境检测与配置

**功能说明**：
- 检测Python环境（python/python3/py）
- 检测虚拟环境（venv/.venv）
- 检测依赖包（aiohttp）
- 检测脚本文件
- 检测IPTV配置目录
- 检测网络连接

**使用场景**：
- 首次使用前检查环境
- 排查运行问题时诊断
- 验证配置是否正确

### 2. 虚拟环境管理

**功能说明**：
- 创建Python虚拟环境
- 激活虚拟环境并安装依赖
- 删除虚拟环境

**优势**：
- 隔离项目依赖
- 避免版本冲突
- 便于环境管理

**使用建议**：
- 强烈建议使用虚拟环境
- 每个项目使用独立的虚拟环境
- 定期更新依赖包

### 3. 运行IPTV采集

**功能说明**：
- 自动检测并使用虚拟环境
- 采集IPTV直播源
- 智能分类和质量筛选
- 生成M3U播放列表

**采集流程**：
```
1. 读取IPTV源列表
   ↓
2. 并发测试所有直播源
   ↓
3. 智能分类和去重
   ↓
4. 优选最佳源（低延迟、高可用）
   ↓
5. 生成排序后的M3U文件
```

**输出结果**：
- best_sorted.m3u - M3U格式播放列表
- best_sorted.m3u8 - M3U8格式播放列表

### 4. 启动本地网页服务

**功能说明**：
- 提供本地网页界面
- 支持搜索和筛选
- 实时查看频道信息
- 一键复制频道链接

**访问地址**：
- http://localhost:8000

**网页功能**：
- 格式筛选（M3U/M3U8）
- 分类筛选
- 频道搜索
- 台标显示
- 复制链接

### 5. 配置定时任务

**Windows定时任务**：
```cmd
# 1. 选择 [5] 配置定时任务
# 2. 按照提示配置Windows任务计划程序
# 3. 设置触发器（每4小时）
# 4. 指定脚本路径
```

**Linux/macOS定时任务**：
```bash
# 1. 选择 [5] 配置定时任务
# 2. 编辑crontab
crontab -e

# 3. 添加定时任务（每4小时运行一次）
0 */4 * * * /path/to/iptv_scheduled_task.sh >> /path/to/iptv_cron.log 2>&1
```

### 6. 查看生成的文件

**功能说明**：
- 查看M3U/M3U8文件内容
- 查看文件大小和修改时间
- 打开文件所在目录

### 7. 清理临时文件

**功能说明**：
- 清理Python缓存（__pycache__）
- 清理临时文件（*.pyc）
- 清理虚拟环境（venv/.venv）
- 清理生成的文件（best_sorted.m3u/m3u8）

**使用场景**：
- 释放磁盘空间
- 重置环境
- 清理测试文件

## 🎬 使用生成的播放列表

### 推荐播放器

#### Windows
- **PotPlayer** - 功能强大，支持多种格式
- **VLC Media Player** - 经典跨平台播放器
- **Kodi** - 媒体中心，支持插件扩展

#### Linux
- **VLC Media Player** - 稳定可靠
- **mpv** - 轻量级，性能优秀
- **Kodi** - 功能丰富的媒体中心

#### macOS
- **VLC Media Player** - 经典选择
- **IINA** - 现代化，界面美观
- **mpv** - 轻量级，键盘友好

### 导入播放列表

1. 打开播放器
2. 找到"打开文件"或"导入播放列表"选项
3. 选择生成的 `best_sorted.m3u` 或 `best_sorted.m3u8` 文件
4. 开始观看直播

## 🔧 高级配置

### 修改IPTV源列表

编辑 [.github/workflows/iptv.py](.github/workflows/iptv.py) 文件中的 `file_urls` 列表：

```python
file_urls = [
    "https://tzdr.com/iptv.txt",
    "https://live.kilvn.com/iptv.m3u",
    # 添加更多源...
]
```

### 调整采集参数

编辑 [.github/workflows/iptv.py](.github/workflows/iptv.py) 中的配置：

```python
CONFIG = {
    "timeout": 10,           # 超时时间（秒）
    "max_parallel": 30,      # 最大并发请求数
    "output_file": "best_sorted.m3u",  # 输出文件名
}
```

### 自定义频道分类

编辑 [.github/workflows/IPTV/](.github/workflows/IPTV/) 目录下的频道配置文件：

```
# 每行一个频道名称
CCTV-1
CCTV-2
北京卫视
上海卫视
```

## 🐛 故障排除

### 1. Python环境问题

**问题**：提示"未检测到Python环境"

**解决方法**：

**Windows**：
```cmd
# 1. 下载Python：https://www.python.org/downloads/
# 2. 安装时勾选"Add Python to PATH"
# 3. 重启命令行窗口
```

**Linux**：
```bash
# Ubuntu/Debian
sudo apt-get install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip

# Arch Linux
sudo pacman -S python python-pip
```

**macOS**：
```bash
brew install python3
```

### 2. 虚拟环境问题

**问题**：虚拟环境创建失败

**解决方法**：
```bash
# 确保已安装venv模块
python3 -m ensurepip --upgrade

# 手动创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. 依赖安装失败

**问题**：aiohttp安装失败

**解决方法**：

**Windows**：
```cmd
# 使用虚拟环境
venv\Scripts\activate
pip install aiohttp

# 或使用--user选项
pip install aiohttp --user
```

**Linux/macOS**：
```bash
# 使用虚拟环境
source venv/bin/activate
pip install aiohttp

# 或使用--user选项
pip3 install aiohttp --user

# 或使用sudo
sudo pip3 install aiohttp
```

### 4. 网络连接问题

**问题**：无法访问IPTV源

**解决方法**：
- 检查网络连接是否正常
- 某些IPTV源可能需要代理访问
- 尝试更换其他IPTV源
- 检查防火墙设置

### 5. 权限问题（Linux/macOS）

**问题**：提示权限不足

**解决方法**：
```bash
# 添加执行权限
chmod +x iptv_tool.sh

# 创建虚拟环境时可能需要sudo
sudo python3 -m venv venv
```

### 6. 网页服务无法访问

**问题**：无法访问http://localhost:8000

**解决方法**：
- 确保网页服务已启动
- 检查端口8000是否被占用
- 尝试使用其他端口：`python -m http.server 8080`
- 检查防火墙设置

## 📊 运行示例

### Windows运行示例

```
╔════════════════════════════════════════════════════════════╗
║     IPTV直播源自动采集工具 - Windows完整版              ║
╚════════════════════════════════════════════════════════════╝

📋 功能菜单：

  [1] 环境检测与配置
  [2] 虚拟环境管理
  [3] 运行IPTV采集
  [4] 启动本地网页服务
  [5] 配置定时任务
  [6] 查看生成的文件
  [7] 清理临时文件
  [8] 查看帮助文档
  [0] 退出程序

请选择功能 (0-8): 3

═══════════════════════════════════════════════════════════
  📡 运行IPTV采集
═══════════════════════════════════════════════════════════

使用虚拟环境：venv

开始采集IPTV直播源...
========================================

Valid streams: 1234, deduplicated: 856, best-per-channel: 423
Generated sorted M3U file: best_sorted.m3u

========================================
✅ IPTV直播源采集完成！
========================================

📄 生成的M3U文件：best_sorted.m3u
   文件大小：123456 字节

💡 提示：
   - 可以使用支持M3U格式的播放器打开生成的文件
   - 推荐播放器：PotPlayer、VLC、Kodi等
   - 定期运行此脚本以获取最新的直播源
```

### Linux/macOS运行示例

```bash
╔════════════════════════════════════════════════════════════╗
║     IPTV直播源自动采集工具 - Linux/macOS完整版          ║
╚════════════════════════════════════════════════════════════╝

📋 功能菜单：

  [1] 环境检测与配置
  [2] 虚拟环境管理
  [3] 运行IPTV采集
  [4] 启动本地网页服务
  [5] 配置定时任务
  [6] 查看生成的文件
  [7] 清理临时文件
  [8] 查看帮助文档
  [0] 退出程序

请选择功能 (0-8): 3

═══════════════════════════════════════════════════════════
  📡 运行IPTV采集
═══════════════════════════════════════════════════════════

使用虚拟环境：venv

开始采集IPTV直播源...
========================================

Valid streams: 1234, deduplicated: 856, best-per-channel: 423
Generated sorted M3U file: best_sorted.m3u

========================================
✅ IPTV直播源采集完成！
========================================

📄 生成的M3U文件：best_sorted.m3u
   文件大小：123456 字节

💡 提示：
   - 可以使用支持M3U格式的播放器打开生成的文件
   - 推荐播放器：VLC、mpv、Kodi、IINA等
   - 定期运行此脚本以获取最新的直播源
```

## 📞 技术支持

- 📖 详细文档：查看本README.md
- 🌐 项目主页：https://zilong7728.github.io/Collect-IPTV/
- 💻 GitHub仓库：https://github.com/zilong7728/Collect-IPTV
- 📧 问题反馈：通过GitHub Issues提交

## ⚠️ 免责声明

本项目仅供学习测试使用，请勿用于商业用途。所有频道版权归原版权方所有。使用本工具产生的任何法律责任由使用者自行承担。

详细免责声明请参阅 [DISCLAIMER.md](DISCLAIMER.md)。

## 📝 更新日志

### v2.0.0 (2026-04-15)
- ✅ 整合所有功能到单一脚本文件
- ✅ 新增虚拟环境检测和管理
- ✅ 新增本地网页服务
- ✅ 新增定时任务配置
- ✅ 优化用户界面和交互体验
- ✅ 完善错误处理和日志输出
- ✅ 支持跨平台运行

### v1.0.0 (2026-04-15)
- ✅ 初始版本发布
- ✅ 支持IPTV采集和分类
- ✅ 支持质量筛选和去重
- ✅ 生成M3U播放列表

## 🎉 开始使用

现在您已经了解了所有功能，可以开始使用IPTV直播源自动采集工具了！

**推荐流程**：
1. 运行环境检测
2. 创建虚拟环境
3. 运行IPTV采集
4. 启动本地网页服务
5. 配置定时任务（可选）
6. 享受观看IPTV直播！

**需要帮助？** 查看详细文档或通过GitHub Issues提交问题。

---

**祝您使用愉快！** 🎬✨