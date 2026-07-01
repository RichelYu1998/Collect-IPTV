# 项目代码规范与范式 (Skill)

> 本文档基于 Collect-IPTV 项目提炼，可作为同类 Python + Shell + GitHub Actions IPTV 采集项目的二开模版。

---

## 一、项目结构规范

```
项目根目录/
├── .github/
│   └── workflows/
│       ├── iptv.py              # 采集脚本（核心逻辑）
│       ├── iptv.yml             # GitHub Actions 工作流
│       ├── index.html           # Web 前端页面
│       └── IPTV/                # 频道源配置（txt 文件）
├── script/
│   ├── iptv_tool.sh             # 本地启动脚本（环境检测→采集→Web服务）
│   └── notify.py                # 变更通知脚本（M3U/M3U8 变更→邮件通知）
├── config/
│   ├── notify.json              # 通知配置（运行时生成）
│   └── notify.json.example      # 通知配置模板
├── server.py                    # 本地 Web 服务（代理/转码/HLS）
├── file/                        # 运行时数据目录
│   ├── best_sorted.m3u          # 采集输出
│   ├── best_sorted.m3u8         # 采集输出
│   └── .cdn_cache.json          # CDN 缓存
├── ffmpeg/                      # FFmpeg 二进制（自动下载，含 ffmpeg + ffprobe）
├── .venv/                       # Python 虚拟环境（自动创建）
├── README.md                    # 项目文档（含版本号）
├── skill.md                     # 代码规范文档（本文件）
└── .gitignore
```

### 核心原则

1. **采集与展示分离**：`iptv.py` 负责采集，`server.py` 负责本地 Web 服务
2. **本地与云端双轨**：GitHub Actions 定时采集 + 本地脚本手动/定时采集
3. **配置与代码分离**：`config/` 存放配置，`file/` 存放运行时数据
4. **模板机制**：`.example` 文件作为配置模板，首次运行自动复制为正式配置
5. **零侵入通知**：`notify.py` 独立运行，通过文件 MD5 检测变更，不影响主流程

---

## 二、Shell 脚本规范（iptv_tool.sh）

### 2.1 启动流程

```
init_homebrew → detect_python_env → detect_ffmpeg → test_pip_mirrors → setup_venv → run_collection → notify → setup_scheduled_task_and_web
```

### 2.2 Homebrew 环境加载

macOS 上脚本可能在没有加载 `.zshrc` 的环境中运行（如 Finder 双击），需要通过 `brew shellenv` 初始化：

```bash
init_homebrew() {
    if [ "$(uname -s)" != "Darwin" ]; then
        return 0
    fi
    if command -v brew &> /dev/null; then
        return 0
    fi
    # 搜索常见 brew 路径，通过 shellenv 加载完整环境
    for brew_path in "/opt/homebrew/bin/brew" "/usr/local/bin/brew"; do
        if [ -x "$brew_path" ]; then
            eval "$($brew_path shellenv)"
            break
        fi
    done
}
```

**关键**：`brew shellenv` 会设置 `HOMEBREW_PREFIX`、`HOMEBREW_CELLAR`、`HOMEBREW_REPOSITORY`、`PATH` 等，确保用户本地自定义的 `HOMEBREW_BOTTLE_DOMAIN` 等变量也被继承。

### 2.3 编码规范

| 项目 | 规范 |
|------|------|
| 解释器 | `#!/bin/bash` |
| 输出语言 | 中文 |
| 错误前缀 | `[错误]` |
| 警告前缀 | `[警告]` |
| 信息前缀 | `[*]` |
| 步骤编号 | `[1/5]` `[2/5]` ... |
| 耗时显示 | `show_step_time "步骤名" "$START_TIME"` |
| 进程清理 | `trap cleanup_exit INT TERM` |

---

## 三、Python 采集脚本规范（iptv.py）

### 3.1 配置系统

所有可调参数通过环境变量 + `CONFIG` 字典管理：

```python
CONFIG = {
    "timeout": int(os.environ.get("IPTV_TIMEOUT", "3")),
    "max_parallel": int(os.environ.get("IPTV_MAX_PARALLEL", "200")),
    "output_file": os.environ.get("IPTV_OUTPUT_FILE", "file/best_sorted.m3u"),
}
```

### 3.2 FFmpeg + FFprobe 管理

- 优先检测系统 PATH 中的 ffmpeg
- 其次检测项目目录 `ffmpeg/bin/`
- macOS 优先通过 Homebrew 安装
- Linux 通过各包管理器安装
- Windows 通过下载静态二进制
- **FFprobe 必须与 FFmpeg 一起安装**，否则无法探测 AC3/EAC3 等音频编码
- macOS evermeet.cx 源需单独下载 ffprobe：`https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip`
- npm `ffmpeg-static` 包不含 ffprobe，需额外安装 `@ffprobe-installer/ffprobe`
- 如果检测到 FFmpeg 已安装但 FFprobe 缺失，自动触发补充安装（`_install_ffprobe_only`）

### 3.3 缓存机制

| 缓存文件 | 用途 | TTL |
|----------|------|-----|
| `.stream_cache.json` | 流测试结果 | 4小时 |
| `.source_cache.json` | 源文件内容 | 2小时 |
| `.cdn_cache.json` | CDN 测试结果 | 6小时 |

### 3.4 频道分类

- 省份频道：通过 `PROVINCE_ALIASES` + `COMMON_CHANNEL_SUFFIXES` 匹配
- 智能分类：通过 `SMART_CATEGORY_KEYWORDS` 匹配（港澳台、体育、少儿动漫等）
- 文本归一化：`normalize_text_for_match()` 统一繁简体、去标点

---

## 四、Web 服务规范（server.py）

### 4.1 功能模块

| 路径前缀 | 功能 |
|----------|------|
| `/proxy/` | CORS 代理，转发外部流媒体请求（流式 + 预加载） |
| `/transcode/` | 音频转码，AC3/EAC3 → AAC |
| `/tstream/` | 转码流管理，HLS 分片 |

### 4.2 流式代理与预加载

**流式代理**（`_stream_proxy_body`）：
- 非 m3u8 响应（.ts 分片等）使用读写并行双线程转发
- 读线程从上游拉 chunk 放入 `queue.Queue(maxsize=8)`，主线程从 queue 取出写给浏览器
- 首块 8KB 快速出首字节，后续 64KB
- `None` 哨兵标记结束，`reader_error` list 传递读线程异常

**智能预加载**（`preload_segments`）：
- m3u8 解析完 URL 列表后立即触发预加载（在 rewrite + write 之前）
- 使用 `concurrent.futures.ThreadPoolExecutor`（4 线程）替代裸线程
- **前 `PRELOAD_SYNC_FIRST` 个分片同步等待**：使用 `future.result()` 阻塞直到预加载完成，确保浏览器请求时已缓存命中
- **`PRELOAD_SYNC_ALL` 模式**：设为 true 时**所有**分片同步等待，返回 m3u8 时全部已在缓存中，全程零延迟
- 后续分片（非 SYNC_ALL 时）异步提交，不阻塞返回
- **持续预热管道**（`start_preload_pipeline`）：m3u8 返回后启动后台守护线程 `_preload_pipeline`
  - 每 `PRELOAD_PIPELINE_INTERVAL`（3s）刷新一次 m3u8
  - 提取新 .ts 分片 URL 并调用 `preload_segments` 预加载
  - daemon 线程，异常或超时自动退出并从 `preload_pipelines` 字典移除
  - 同一 m3u8 URL 只启动一个管道（`preload_pipelines` 去重）
  - **根治 HLS 动态刷新导致的播放卡顿**
- 缓存结构：`preload_cache = {url: {data, ct, ts}}`
- 淘汰策略：LRU（`preload_order` FIFO）+ TTL（120s）双重淘汰
- 限制：最大 500 条目 / 500MB
- 请求进入 `_handle_proxy` 时先查缓存，命中则**流式分块发送**（64KB + flush），不等整个文件写完

### 4.3 FFmpeg / FFprobe 查找顺序

1. 系统 PATH（`shutil.which`）
2. 项目目录 `ffmpeg/bin/`
3. 虚拟环境 `.venv/ffmpeg/bin/`
4. Homebrew 路径（`HOMEBREW_PREFIX/bin/`）
5. Linux 常见路径（`/usr/local/bin` 等）

**FFprobe 查找**：与 FFmpeg 同目录，`find_ffprobe()` 先检查 FFmpeg 同目录下是否有 ffprobe，再检查系统 PATH。

**FFprobe 缺失处理**：`check_ffmpeg_installed()` 同时检查 ffmpeg 和 ffprobe，如果 ffprobe 缺失则返回 False，触发 `_install_ffprobe_only()` 补充安装。

### 4.3 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `IPTV_SERVER_PORT` | 8000 | Web 服务端口 |
| `IPTV_PROXY_TIMEOUT` | 15 | 代理超时（秒） |
| `IPTV_TRANSCODE_SESSION_TIMEOUT` | 600 | 转码会话超时（秒） |
| `IPTV_TRANSCODE_AUDIO_BITRATE` | 128k | 转码音频码率 |
| `IPTV_MAX_CONTENT_LENGTH` | 50MB | 代理最大内容长度 |
| `IPTV_PRELOAD_MAX_ENTRIES` | 500 | 预加载缓存最大条目数 |
| `IPTV_PRELOAD_MAX_SIZE` | 500MB | 预加载缓存最大总内存 |
| `IPTV_PRELOAD_TTL` | 180 | 预加载缓存过期时间（秒） |
| `IPTV_PRELOAD_WORKERS` | 6 | 预加载线程池工作线程数 |
| `IPTV_PRELOAD_SYNC_FIRST` | 3 | 同步等待前 N 个分片完成（消除首屏卡顿） |
| `IPTV_PRELOAD_SYNC_ALL` | false | 设为 true 则**所有**分片同步预加载完再返回 m3u8 |
| `IPTV_PRELOAD_PIPELINE_INTERVAL` | 3 | 持续预热管道刷新间隔（秒） |
| `IPTV_PRELOAD_PIPELINE_MAX_AGE` | 300 | 持续预热管道最大存活时间（秒） |

---

## 五、变更通知规范（notify.py）

### 5.1 工作原理

```
采集完成 → notify.py → 计算 M3U/M3U8 的 MD5 → 与上次对比 → 有变更则发邮件
```

### 5.2 配置文件（config/notify.json）

```json
{
  "email_notification_enabled": false,
  "email_smtp_host": "smtp.qq.com",
  "email_smtp_port": 587,
  "email_smtp_user": "your_email@qq.com",
  "email_smtp_password": "your_smtp_authorization_code",
  "email_from_name": "IPTV直播源监控",
  "email_to": "recipient@example.com",
  "watch_files": ["best_sorted.m3u", "best_sorted.m3u8"],
  "email_cooldown_seconds": 300,
  "email_max_fail_count": 3,
  "email_fail_cooldown_seconds": 1800
}
```

### 5.3 邮件发送逻辑

- 支持 SMTP SSL（端口 465）和 STARTTLS（端口 587）
- 邮件同时包含纯文本和 HTML 两种格式
- 冷却机制：同一收件人 `email_cooldown_seconds` 内不重复发送
- 失败保护：连续失败 `email_max_fail_count` 次后暂停 `email_fail_cooldown_seconds` 秒
- 变更状态通过 `.notify_hashes.json` 持久化

### 5.4 集成方式

在 `iptv_tool.sh` 的 `run_collection()` 末尾调用：

```bash
if [ -f "$WORK_DIR/script/notify.py" ]; then
    echo "[*] 检测文件变更并发送通知..."
    $PYTHON_CMD "$WORK_DIR/script/notify.py"
fi
```

---

## 六、GitHub Actions 规范

### 6.1 工作流配置

```yaml
on:
  schedule:
    - cron: '0 */4 * * *'
  workflow_dispatch:
```

### 6.2 采集步骤

1. Checkout 代码
2. 设置 Node.js 24
3. 设置 Python 3.10
4. 安装 aiohttp
5. 运行 `iptv.py`
6. 更新 README.md 中的时间戳和文件链接
7. 提交变更

---

## 七、编码风格速查

| 项目 | 规范 |
|------|------|
| Python 版本 | 3.9+ |
| 缩进 | 4 空格 |
| 字符串 | 优先 f-string 格式化 |
| 编码 | 所有文件 UTF-8，读写始终指定 `encoding='utf-8'` |
| 换行 | LF（`.sh`），CRLF/LF 均可（其他文件） |
| JSON 缩进 | 2 空格，`ensure_ascii=False` |
| 路径拼接 | Python 用 `pathlib.Path`，Shell 用 `os.path.join` 或变量拼接 |
| 异步框架 | `aiohttp` + `asyncio` |
| 环境变量 | 所有可调参数通过 `os.environ.get()` 读取，提供默认值 |
| 进程管理 | macOS/Linux: `pkill`，Windows: `taskkill` |
| 敏感信息 | 配置模板用占位符，`.gitignore` 排除正式配置 |
| Shell 输出 | 全中文，统一前缀格式 |
| 版本号 | 唯一来源 `README.md`，格式 `### v1.2.3 (2026-06-30)` |
| 依赖管理 | `pip install aiohttp`（最小依赖），虚拟环境 `.venv` |
## FFmpeg 多平台支持

### 预编译二进制文件位置

项目根目录 fmpeg/ 文件夹包含所有平台的预编译版本：

`
ffmpeg/
├── windows/bin/     # Windows (ffmpeg.exe, ffprobe.exe, ffplay.exe)
├── linux/bin/       # Linux (ffmpeg, ffprobe)
└── macos/bin/       # macOS (ffmpeg, ffprobe) - evermeet.cx
`

### 自动检测逻辑

程序运行时会自动检测操作系统并选择对应的 FFmpeg 路径：

**支持的系统标识符:**
- windows: Windows 10/11 (x64/ARM64)
- linux: Ubuntu/Debian/CentOS (x64/ARM64)
- macos / darwin: macOS (Intel/Apple Silicon)

**二进制文件路径映射:**
`python
FFMPEG_PATHS = {
    'windows': 'ffmpeg/windows/bin/{binary}.exe',
    'linux': 'ffmpeg/linux/bin/{binary}',
    'macos': 'ffmpeg/macos/bin/{binary}',
}
`

### 安装源

| 平台 | 主要来源 | 备用来源 |
|------|---------|---------|
| **Windows** | BtbN GitHub | Gyan.dev, npm 淘宝镜像 |
| **Linux** | BtbN GitHub | 系统包管理器 (apt/yum) |
| **macOS** | evermeet.cx | Homebrew, npm 淘宝镜像 |

### 使用说明

1. **自动模式**: 运行 python server.py 或启动脚本，程序会自动检测并使用对应平台
2. **手动指定**: 可通过环境变量或配置文件强制指定 FFmpeg 路径
3. **权限设置**: Linux/macOS 二进制文件已设置为可执行权限 (755)

### 维护命令

如需更新 FFmpeg 到最新版本，可运行：
`ash
# 使用内置下载脚本
python download_all_ffmpeg.py

# 或手动替换对应平台的二进制文件
cp ffmpeg-new ffmpeg/<platform>/bin/ffmpeg
`

---

**最后更新**: 2026-07-01  
**维护者**: Auto-generated  
