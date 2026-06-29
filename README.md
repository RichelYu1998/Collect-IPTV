## 📡Collect-IPTV
初始版本基于 DeepSeek 与 ChatGPT 生成，最新版本使用 Gemini 与 GPT-5.3-Codex 持续优化；依托 GitHub 服务器进行源地址可用性与延迟测试，网页已更新台标展示，并支持去重与优选低延迟最佳 URL，M3U 播放列表每 4 小时自动更新。

> ⚠️ 特别说明：因使用 GitHub 服务器，**不保证国内网络环境下的链接速度与可用性**。  
> ⚠️ 所有频道的完整性与有效性高度依赖上游网络资源；若上游频道源大面积失效，自动更新时可能会被可用性检测过滤。

---

## 🚀 本地运行工具

本项目现已提供功能完整的跨平台IPTV采集工具，支持Windows、Linux和macOS！

### ✨ 核心特性

- **🤖 智能分类**：自动识别CCTV、各省市频道、主题频道等
- **⚡ 质量筛选**：测试延迟和可用性，优选最佳源
- **🌐 用户友好**：提供网页界面，支持搜索、筛选和在线播放
- **🎬 在线播放**：网页内置 HLS 播放器，点击频道即可观看直播
- **🔊 音量控制**：自定义音量调节、静音切换，支持所有音频编码自动转码
- **🔄 持续更新**：每4小时自动更新，确保数据新鲜度
- **🐍 虚拟环境**：自动检测和管理Python虚拟环境
- **📱 跨平台**：支持Windows、Linux、macOS
- **🔊 CORS代理**：内置代理服务器，解决浏览器跨域限制
- **🎯 CDN轮询**：IPTV源、Geo数据、PIP镜像、FFmpeg下载均自动测速选最快CDN
- **🔧 零硬编码**：所有配置项均可通过环境变量自定义，无任何硬编码值
- **📦 统一管理**：所有安装依赖（Python、FFmpeg、PIP配置）统一存放于.venv目录

### 📦 快速开始

#### Windows用户
```cmd
# 双击运行或在命令行执行
iptv_tool.bat
```

#### Linux/macOS用户
```bash
# 添加执行权限
chmod +x iptv_tool.sh

# 运行工具
./iptv_tool.sh
```

### 🔄 自动运行流程

双击脚本即可，无需手动操作：

```
[1/5] 检测Python环境（未安装则自动安装到.venv）
[1/3] 测试FFmpeg CDN源速度（未安装则自动安装到.venv）
[2/5] 测试PIP镜像源速度（自动选择最快镜像）
[3/5] 检测Python虚拟环境
[4/5] 设置虚拟环境并安装依赖
[5/5] 运行IPTV采集（自动测速选最快CDN） → 注册定时任务 → 启动本地网页服务
```

**启动后自动**：
- ✅ 运行IPTV采集，生成最新的播放列表
- ✅ 注册系统定时任务（Windows: 任务计划程序 / Linux: crontab），每4小时自动运行采集
- ✅ 启动本地网页服务 http://localhost:8000（含CORS代理和在线播放）
- ✅ 显示局域网访问地址（手机/其他设备可直接访问）
- ✅ 自动安装FFmpeg，支持AC3/EAC3等音频编码实时转码

### 📋 命令行参数

| 参数 | 说明 |
|------|------|
| 无参数 | 采集IPTV + 注册定时任务 + 启动Web服务器（默认） |
| `--collect` | 仅运行IPTV采集（定时任务内部调用，自动退出不暂停） |

---

## 🎯 智能分类系统

- **央视频道**：CCTV-1到CCTV-16、CGTN、CHC等
- **省市频道**：全国31个省市自治区频道
- **主题频道**：新闻、体育、影视、少儿、音乐、戏曲等
- **港澳台频道**：翡翠台、明珠台、东森、中天等
- **文旅频道**：景区、风景、观光等特色频道

## 🔍 质量筛选机制

- **可用性测试**：实时检测直播源是否可访问
- **延迟测量**：测试响应时间，优选低延迟源
- **智能去重**：自动识别和合并重复频道
- **并发测试**：支持30个并发连接，提高测试效率

## 📁 生成的文件

运行成功后，会在项目根目录生成：
- **best_sorted.m3u** - M3U格式播放列表
- **best_sorted.m3u8** - M3U8格式播放列表

---

## 🎬 使用生成的播放列表

### 推荐播放器

**Windows**：
- **PotPlayer** - 功能强大，支持多种格式
- **VLC Media Player** - 经典跨平台播放器
- **Kodi** - 媒体中心，支持插件扩展

**Linux**：
- **VLC Media Player** - 稳定可靠
- **mpv** - 轻量级，性能优秀
- **Kodi** - 功能丰富的媒体中心

**macOS**：
- **VLC Media Player** - 经典选择
- **IINA** - 现代化，界面美观
- **mpv** - 轻量级，键盘友好

### 导入播放列表

1. 打开播放器
2. 找到"打开文件"或"导入播放列表"选项
3. 选择生成的 `best_sorted.m3u` 或 `best_sorted.m3u8` 文件
4. 开始观看直播

---

## 📂 项目文件说明

### 核心脚本

| 文件名 | 平台 | 说明 |
|--------|------|------|
| [iptv_tool.bat](iptv_tool.bat) | Windows | 一键启动工具 |
| [iptv_tool.sh](iptv_tool.sh) | Linux/macOS | 一键启动工具 |

### 核心文件

| 文件名 | 说明 |
|--------|------|
| [.github/workflows/iptv.py](.github/workflows/iptv.py) | IPTV采集核心脚本 |
| [.github/workflows/index.html](.github/workflows/index.html) | 网页界面（含HLS在线播放） |
| [.github/workflows/IPTV/](.github/workflows/IPTV/) | 频道配置目录 |
| [server.py](server.py) | 本地Web服务器（含CORS代理） |

### 生成文件

| 文件名 | 说明 |
|--------|------|
| best_sorted.m3u | M3U格式播放列表 |
| best_sorted.m3u8 | M3U8格式播放列表 |

---

## 🔧 高级配置

### 环境变量配置

所有配置项均可通过环境变量自定义，无任何硬编码值：

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| `IPTV_SERVER_PORT` | 8000 | Web 服务器端口 |
| `IPTV_TIMEOUT` | 3 | IPTV 流检测超时(秒) |
| `IPTV_MAX_PARALLEL` | 30 | 最大并发请求数 |
| `IPTV_OUTPUT_FILE` | best_sorted.m3u | 输出文件名 |
| `IPTV_CONNECT_TIMEOUT` | 3 | 连接超时(秒) |
| `IPTV_DNS_CACHE_TTL` | 300 | DNS 缓存时间(秒) |
| `IPTV_SOURCE_CDN_TIMEOUT` | 5 | CDN 测速超时(秒) |
| `IPTV_PROXY_TIMEOUT` | 15 | 代理请求超时(秒) |
| `IPTV_TRANSCODE_SESSION_TIMEOUT` | 600 | 转码会话超时(秒) |
| `IPTV_TRANSCODE_AUDIO_BITRATE` | 128k | 转码音频比特率 |
| `IPTV_TRANSCODE_AUDIO_CHANNELS` | 2 | 转码音频声道数 |
| `IPTV_TRANSCODE_HLS_TIME` | 4 | HLS 分片时长(秒) |
| `IPTV_TRANSCODE_HLS_LIST_SIZE` | 6 | HLS 播放列表长度 |
| `IPTV_LAN_IP_DETECT_HOST` | 8.8.8.8 | 局域网 IP 检测目标 |
| `IPTV_LAN_IP_DETECT_PORT` | 80 | 局域网 IP 检测端口 |
| `IPTV_MAX_CONTENT_LENGTH` | 52428800 | 代理最大内容长度(字节) |
| `PYTHON_LATEST_VERSION` | 3.11.9 | 自动安装 Python 版本 |

使用示例：
```cmd
:: Windows - 自定义端口
set IPTV_SERVER_PORT=9000
iptv_tool.bat
```
```bash
# Linux/macOS - 自定义端口
IPTV_SERVER_PORT=9000 ./iptv_tool.sh
```

### CDN 轮询测速

本项目对所有外部资源均实现 CDN 轮询测速，自动选择最快源：

| 资源类型 | CDN 镜像 | 测速方式 |
|---------|---------|---------|
| IPTV 源 | jsdelivr / gh-proxy / raw.githubusercontent.com | HEAD 请求测延迟 |
| Geo 数据 | jsdelivr / fastly / raw.githubusercontent.com / gh-proxy | HEAD 请求测延迟 |
| PIP 镜像 | 清华 / 阿里云 / 豆瓣 / USTC | curl 测连接时间 |
| FFmpeg 下载 | Gyan.dev / BtbN / CodexFFmpeg | curl 测连接时间 |

### .venv 统一管理

所有安装依赖统一存放在 `.venv` 目录中：

```
.venv/
├── Scripts/              ← Python venv (Windows)
├── bin/                  ← Python venv (Linux/macOS)
├── Lib/                  ← Python venv 依赖包
├── pip_config/           ← PIP 镜像源配置
│   └── pip.ini / pip.conf
├── python/               ← 自动安装的 Python（仅当系统无 Python 时）
│   └── python.exe
└── ffmpeg/               ← 自动安装的 FFmpeg（仅当系统无 FFmpeg 时）
    └── bin/
        ├── ffmpeg.exe
        ├── ffplay.exe
        └── ffprobe.exe
```

删除 `.venv` 即可完全清理所有自动安装的依赖。

### 音频转码

当直播流使用浏览器不支持的音频编码（如 AC3/EAC3）时，自动启动 FFmpeg 实时转码为 AAC：

```
原始流 → FFmpeg: 视频copy + 音频AC3→AAC → 浏览器播放
```

- 转码仅在检测到不兼容音频时自动启动
- 关闭播放器后自动停止 FFmpeg 进程，释放资源
- 转码参数可通过环境变量自定义（比特率、声道数等）

### 修改IPTV源列表

编辑 [.github/workflows/iptv.py](.github/workflows/iptv.py) 文件中的 `IPTV_SOURCE_CDNS` 列表：

```python
IPTV_SOURCE_CDNS = [
    {
        "name": "源名称 (CDN)",
        "urls": [
            "https://cdn.jsdelivr.net/...",   # CDN 镜像（优先测速）
            "https://raw.githubusercontent.com/...",  # 原始地址（备用）
        ],
    },
    # 添加更多源...
]
```

### 自定义频道分类

在 [.github/workflows/IPTV/](.github/workflows/IPTV/) 目录下添加 `*频道.txt` 文件即可，脚本会自动扫描：

```
# 每行一个频道名称
CCTV-1
CCTV-2
北京卫视
上海卫视
```

---

## 🐛 常见问题

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
- 检查端口是否被占用（默认8000，可通过 `IPTV_SERVER_PORT` 环境变量修改）
- 局域网其他设备访问时使用启动时显示的局域网地址（如 `http://192.168.x.x:8000`）
- 检查防火墙设置

### 7. 网页播放无声音

**问题**：网页中播放直播有画面但没声音

**原因**：部分 IPTV 源使用 AC3/EAC3 (Dolby Digital) 音频编码，浏览器不支持解码

**解决方法**：
- 工具已内置 FFmpeg 自动安装和实时音频转码功能
- 启动脚本会自动检测并安装 FFmpeg 到 `.venv/ffmpeg/`
- 播放 AC3/EAC3 音频时自动转码为 AAC，确保有声音
- 如自动安装失败，可手动安装 FFmpeg：
  - Windows: `choco install ffmpeg` 或从 https://ffmpeg.org/download.html 下载
  - Linux: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
- 也可使用 PotPlayer/VLC 等本地播放器直接打开链接（原生支持所有音频编码）

### 8. 网页播放报网络错误

**问题**：点击播放后提示"网络错误，无法加载直播流"

**解决方法**：
- 确保使用 `server.py` 启动Web服务（而非 `python -m http.server`）
- `server.py` 内置CORS代理，可解决浏览器跨域限制
- 部分直播源可能已下线或不可用，尝试其他频道
- 如果所有频道都无法播放，检查本地网络连接

### 9. 定时任务问题

**Windows**：检查任务计划程序中 `IPTV_Collection` 任务是否存在
```cmd
schtasks /query /tn "IPTV_Collection"
```

**Linux/macOS**：检查crontab中是否有对应条目
```bash
crontab -l | grep iptv_tool
```

---

## 📊 测试结果

### ✅ 环境检测测试
```
[1/5] Detecting Python environment...
Python: Python 3.14.3

FFmpeg Detection and Installation
[*] FFmpeg already installed:
ffmpeg version 7.0 ...

Testing FFmpeg CDN sources...
    Testing Gyan.dev...        0.152s (152ms)
    Testing BtbN...            0.341s (341ms)
    Testing CodexFFmpeg...     0.287s (287ms)
[*] Fastest FFmpeg CDN: Gyan.dev (152ms)

[2/5] Testing PIP mirror sources...
    Testing Tsinghua...        0.045s (45ms)
    Testing Aliyun...          0.032s (32ms)
    Testing Douban...          0.051s (51ms)
    Testing USTC...            0.038s (38ms)
[*] Fastest PIP mirror: Aliyun (32ms)

[3/5] Detecting Python virtual environment...
Found virtual environment: .venv

[4/5] Setting up Python virtual environment and installing dependencies...
Python virtual environment setup complete

[5/5] Registering scheduled task...
[*] Scheduled task created successfully!
```

### ✅ IPTV采集测试
```
Testing IPTV source CDN mirrors...
  Guovin/iptv-api (jsdelivr) | https://cdn.jsdelivr.net/...: 0.152s
  Guovin/iptv-api (jsdelivr) | https://raw.githubusercontent.com/...: 1.234s
  -> Selected: https://cdn.jsdelivr.net/... (0.152s)
  ...
Selected 5 source URLs via CDN speed test.

Testing geo data CDN sources...
  https://cdn.jsdelivr.net/...: 0.089s
  https://fastly.jsdelivr.net/...: 0.124s
  ...
  Fastest: https://cdn.jsdelivr.net/... (0.089s)
Loaded 6443 online geo tokens from: https://cdn.jsdelivr.net/...
Online geo classification tokens merged.
Valid streams: 1780, deduplicated: 1137, best-per-channel: 662
Generated sorted M3U file: best_sorted.m3u
```

### ✅ 网页服务测试
```
  访问地址: http://127.0.0.1:8000
  局域网地址: http://192.168.31.36:8000
  CORS proxy: /proxy/<encoded_url>
  音频转码: 已启用 (FFmpeg: .venv/ffmpeg/bin/ffmpeg.exe)
```

---

## 📢 免责声明（个人学习测试专用）

本项目仅用于**网络协议、爬虫技术、自动化脚本开发等个人学习与测试用途**，不用于任何商业、盈利及违规用途。

- 所有节目源均来自互联网公开可访问链接，项目本身不生产、不存储、不篡改任何媒体内容。  
- 严禁将本项目及生成的播放列表用于商业传播、二次分发、公开分享等行为。  
- 所有频道版权均归原版权方所有，使用前请确保符合当地法律法规。  
- 因违规使用本项目产生的任何法律责任、版权纠纷，均由使用者自行承担。

### Restrictions

Users **must not**:
- Redistribute the project or generated playlists for commercial purposes
- Share or publicly distribute the playlists
- Use the project for any activity that violates applicable laws

### Copyright

All channels and media resources remain the property of their respective copyright holders. The project author **assumes no responsibility** for any legal issues or copyright disputes arising from improper use.

### Liability

By using this project, users agree that they **bear all risk** for any misuse. The author or repository owner **is not liable** for any damages or legal consequences.

---

## 📺️TV station list

https://zilong7728.github.io/Collect-IPTV/

## ⏱️Last Run Time

<!-- Last Run Time --> 2026-04-15 09:31:45 CST

## 🔗Generated File Link

<!-- Generated File Link --> [View Generated File](https://raw.githubusercontent.com/zilong7728/Collect-IPTV/refs/heads/main/best_sorted.m3u)

<!-- Generated File Link m3u8 --> [View Generated File](https://raw.githubusercontent.com/zilong7728/Collect-IPTV/refs/heads/main/best_sorted.m3u8)

## 💡 使用说明

### 在线使用
1. 点击上方「下载 M3U/M3U8 文件」获取最新节目源
2. 将文件导入支持 IPTV 的播放器（如 Kodi、PotPlayer、Perfect Player 等）
3. 节目源每 4 小时自动更新，建议定期重新下载

### 本地使用
1. 运行本地工具：`iptv_tool.bat` (Windows) 或 `./iptv_tool.sh` (Linux/macOS)
2. 脚本自动完成：环境检测 → 注册定时任务 → 启动网页服务
3. 访问 http://localhost:8000 查看网页界面
4. 使用生成的播放列表观看直播

## 📞 技术支持

- 🌐 项目主页：https://zilong7728.github.io/Collect-IPTV/
- 💻 GitHub仓库：https://github.com/zilong7728/Collect-IPTV
- 📧 问题反馈：通过GitHub Issues提交

## 📝 更新日志

### v2.2.0 (2026-06-29)
- ✅ 新增音量自定义调节（静音按钮、音量滑块、百分比显示）
- ✅ 新增 FFmpeg 自动安装（Windows 下载到 .venv/ffmpeg，Linux/macOS 通过包管理器安装）
- ✅ 新增 FFmpeg CDN 轮询测速（Gyan.dev / BtbN / CodexFFmpeg，自动选最快源下载）
- ✅ 新增 AC3/EAC3 音频实时转码为 AAC，解决浏览器不支持 Dolby Digital 无声音问题
- ✅ 新增 IPTV 源 CDN 轮询测速（jsdelivr / gh-proxy / raw.githubusercontent.com）
- ✅ 新增 Geo 数据 CDN 轮询测速（jsdelivr / fastly / gh-proxy / raw.githubusercontent.com）
- ✅ 新增局域网访问地址显示（手机/其他设备可直接访问）
- ✅ 新增代理服务器动态 Host 头，局域网设备也能正常播放直播流
- ✅ 所有配置项零硬编码，均可通过环境变量自定义（17 个环境变量）
- ✅ 所有安装依赖统一存放在 .venv 目录（Python / FFmpeg / PIP 配置）
- ✅ 省份频道文件自动扫描，新增省份无需改代码
- ✅ 添加"点击播放"覆盖层，确保浏览器用户手势触发播放
- ✅ 音频编码兼容性检测，不兼容时显示警告提示

### v2.1.0 (2026-06-29)
- ✅ 新增网页在线播放功能（基于 hls.js）
- ✅ 新增 CORS 代理服务器（server.py），解决浏览器跨域限制
- ✅ 新增 m3u8 内容重写，自动将流地址转换为代理地址
- ✅ 频道名称可点击直接播放
- ✅ 台标显示优化：名称规范化、CDN 回退域名修正、损坏 M3U 数据容错
- ✅ 启动脚本默认先采集再启动 Web 服务
- ✅ 计划任务（--collect）自动退出，不再 pause 阻塞
- ✅ 代理服务器改用多线程（ThreadingHTTPServer），错误处理更健壮
- ✅ 修复 batch 脚本嵌套 if/else 导致的解析错误
- ✅ 修复播放器 DOM 元素缺失导致的 JS 崩溃

### v2.0.0 (2026-04-15)
- ✅ 新增跨平台本地运行工具
- ✅ 新增虚拟环境检测和管理
- ✅ 新增本地网页服务
- ✅ 新增定时任务自动注册
- ✅ 整合所有功能到单一脚本文件
- ✅ 优化用户界面和交互体验
- ✅ 完善错误处理和日志输出
- ✅ 支持跨平台运行
- ✅ 完整测试通过

### v1.0.0 (2026-04-15)
- ✅ 初始版本发布
- ✅ 支持IPTV采集和分类
- ✅ 支持质量筛选和去重
- ✅ 生成M3U播放列表

## ⭐️Star History

[![Star History Chart](https://api.star-history.com/svg?repos=zilong7728/Collect-IPTV&type=Date)](https://star-history.com/#zilong7728/Collect-IPTV&Date)

## 🎉 开始使用

**推荐流程**：
1. 双击 `iptv_tool.bat` (Windows) 或运行 `./iptv_tool.sh` (Linux/macOS)
2. 脚本自动完成所有配置
3. 访问 http://localhost:8000 查看频道
4. 享受观看IPTV直播！

**需要帮助？** 通过GitHub Issues提交问题。

---

**祝您使用愉快！** 🎬✨

## 📊 项目状态

- ✅ **功能完整**：所有功能已实现并测试通过
- ✅ **跨平台支持**：Windows、Linux、macOS全部支持
- ✅ **文档完善**：提供详细的使用指南和故障排除
- ✅ **性能优化**：支持并发采集和智能筛选
- ✅ **用户友好**：一键启动，全自动运行

---

**项目版本：v2.2.0 | 最后更新：2026-06-29**