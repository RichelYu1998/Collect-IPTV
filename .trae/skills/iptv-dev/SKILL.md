---
name: "iptv-dev"
description: "Collect-IPTV项目开发指南。修改server.py、index.html、notify.py、iptv_tool.bat/sh，或开发FFmpeg/hls.js/mpegts.js/邮件通知功能时调用。"
---

# Collect-IPTV 开发技能

## 项目概述

IPTV直播源智能采集工具，支持自动采集、去重、优选、在线播放、音频转码、邮件通知。

## 架构

```
server.py          → Web服务器(aiohttp)，CORS代理，FFmpeg转码，预加载缓存，音频探测
output/index.html  → 前端双引擎播放器(hls.js + mpegts.js)
script/notify.py   → 邮件通知(MD5哈希变更检测)
script/iptv_tool.bat/sh → 启动脚本(环境检测→采集→通知→Web服务)
.github/workflows/iptv.py → 采集脚本
config/notify.json → 邮件配置
```

## 关键规范

### 播放器 - 双引擎架构 (hls.js + mpegts.js)

**mpegts.js 不支持 HLS/m3u8** — 它只能处理原始 MPEG-TS 和 FLV 流。
所有 IPTV 源都是 HLS (m3u8) 格式，所以 hls.js 是主力播放器。

#### URL类型自动检测

```javascript
const isHlsUrl = proxiedUrl.includes('.m3u8') || proxiedUrl.includes('.m3u') || proxiedUrl.includes('/hls/') || proxiedUrl.includes('/tstream/');
```

#### HLS播放器 (hls.js) — 用于m3u8链接

- 初始化：`new Hls(config)`
- 加载：`loadSource(url)` 然后 `attachMedia(video)`
- 就绪事件：`Hls.Events.MANIFEST_PARSED`（流就绪）
- 错误：`Hls.Events.ERROR`，含 `Hls.ErrorTypes.NETWORK_ERROR` / `MEDIA_ERROR`
- 网络错误恢复：`startLoad()`（从上次位置重试）
- 媒体错误恢复：`recoverMediaError()`（重建MSE）
- 销毁：`hls.destroy()`
- 变量：`currentPlayer`（hls.js和mpegts.js共用）

#### hls.js 直播配置

```javascript
{
    enableWorker: true,
    lowLatencyMode: false,          // 非LL-HLS流开启反而增加卡顿
    backBufferLength: 10,           // 回看缓冲10秒
    maxBufferLength: 10,            // 前向缓冲10秒
    maxMaxBufferLength: 30,         // 最大缓冲上限30秒
    maxBufferSize: 30 * 1000 * 1000,
    maxBufferHole: 0.5,
    liveSyncDurationCount: 3,       // 从第3个分片开始同步
    liveMaxLatencyDurationCount: 6, // 最大延迟6个分片
    liveDurationInfinity: true,
    progressive: true,
    highBufferWatchdogPeriod: 2,
    abrEwmaDefaultEstimate: 800000,  // ABR初始带宽800kbps
    abrEwmaFastEstimate: 1500000,    // ABR快速带宽1.5Mbps
    abrBandWidthFactor: 0.7,
    abrBandWidthUpFactor: 1.5,
    startLevel: -1,
    fragLoadingTimeOut: 10000,       // 分片加载超时10秒
    fragLoadingMaxRetry: 3,          // 分片加载最大重试3次
    fragLoadingMaxRetryTimeout: 4000,
    manifestLoadingTimeOut: 10000,
    manifestLoadingMaxRetry: 3,
    levelLoadingTimeOut: 10000,
    levelLoadingMaxRetry: 3,
}
```

#### mpegts.js 播放器 — 仅用于原始TS/FLV链接

- 初始化：`mpegts.createPlayer({type:'mpegts', isLive:true, url}, config)`（不是'mse'）
- 加载：`attachMediaElement(video)` 然后 `load()`
- 就绪事件：`MEDIA_INFO`（主）, `METADATA_ARRIVED`, `loadeddata`, `canplay`（兜底）
- 错误：`mpegts.Events.ERROR`，含 `mpegts.ErrorTypes.NETWORK_ERROR` / `MEDIA_ERROR`
- 销毁：`unload()` → `detachMediaElement()` → `destroy()`
- 恢复：`unload()` → `load()` → `play()`

#### mpegts.js 直播配置

```javascript
{
    enableWorker: true,
    enableStashBuffer: true,        // 启用缓冲（false会导致网络波动卡死）
    stashInitialSize: 1024,         // 初始缓冲1KB（128太小）
    lazyLoad: false,
    autoCleanupSourceBuffer: true,
    autoCleanupMaxBackwardDuration: 30,
    autoCleanupMinBackwardDuration: 10,
    liveBufferLatencyChasing: true,
    liveBufferLatencyMaxLatency: 10, // 最大延迟10秒
    liveBufferLatencyMinRemain: 2,   // 保留2秒缓冲（0.5秒太激进）
}
```

#### 共用函数

- `destroyPlayer()` — 检查 `instanceof Hls` 走hls.js销毁，否则走mpegts.js销毁流程
- `checkAudioTracksFromPlayer(info)` — 兼容hls.js和mpegts.js的音轨信息格式
- `currentPlayer` — 共用变量，可以是Hls实例或mpegts播放器实例

### 音频探测 (server.py)

#### 快速探测：`_probe_audio_fast(url)`

Python原生TS流解析器，非加密流无需ffprobe/ffmpeg：

1. 下载m3u8 → 解析第一个TS分片URL
2. 下载256KB TS数据
3. 解析TS包（188字节）：同步字节0x47、PID、PUSI标志
4. 处理adaptation field和pointer byte（PUSI包）
5. 识别PES stream_id：0xC0-0xDF = MPEG音频，0xBD = 私有流
6. 检测编解码：mp2/mp3（MPEG音频），ac3/eac3/dts（私有流sub_id）
7. 加密流检测：pointer byte > 183 → 切换ffmpeg探测

#### 探测优先级链

`_probe_audio_fast()` → `ffprobe` → `ffmpeg -i` → 返回错误

- 非加密流：约0.3-0.8秒（快速探测）
- 加密流：约2-4秒（ffmpeg探测）
- ffprobe：analyzeduration/probesize 256K，超时3秒
- ffmpeg加密流：probesize 256K，超时4秒
- ffmpeg非加密流：probesize 256K，超时3秒

### FFmpeg 转码参数

```python
cmd = [
    FFMPEG_PATH,
    '-nostdin',
    '-fflags', '+genpts+discardcorrupt+fastseek',
    '-analyzeduration', '3000000',
    '-probesize', '3000000',
    '-i', url,
    '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', TRANSCODE_AUDIO_BITRATE, '-ac', TRANSCODE_AUDIO_CHANNELS,
    '-sn',
    '-max_delay', '0',
    '-threads', '0',
    '-f', 'hls',
    '-hls_time', TRANSCODE_HLS_TIME,
    '-hls_list_size', TRANSCODE_HLS_LIST_SIZE,
    '-hls_flags', 'delete_segments+append_list+independent_segments',
    '-hls_segment_filename', os.path.join(output_dir, 'seg_%03d.ts'),
    os.path.join(output_dir, 'index.m3u8'),
    '-y',
    '-loglevel', 'error',
]
```

与v2.9的关键变更：
- 移除 `-re` 参数（限制输出速率为1x，直播流延迟会累积）
- analyzeduration/probesize：5M → 3M（更快启动）
- fflags添加 `+fastseek`

### 代理优化

- TS分片：**流式转发**（读64KB → 写 → 刷出），不再全部下载完再转发
- 预加载等待：200ms（原500ms）
- TS缓存：边转发边缓存，不阻塞转发

### 邮件通知 (notify.py)

- 监控文件：`file/best_sorted.m3u`、`file/best_sorted.m3u8`
- 哈希存储：`config/.notify_hashes.json`（持久化到 Git 仓库）
- 首次运行：发送邮件（标记为"new"）
- 文件变更（哈希不同）：发送邮件（标记为"updated"）
- 无变化：跳过发送
- 脚本调用：采集完成后执行 `notify.py --once`
- 配置：`config/notify.json`
- GitHub Actions：workflow 中自动调用，哈希记录提交到仓库

### GitHub Actions 工作流 (.github/workflows/iptv.yml)

**核心功能**：
- 自动化 CI/CD 流程（每 4 小时或手动触发）
- 完整流程：采集 → 生成 → 更新 README → 提交推送 → 邮件通知 → 保存哈希
- 极速运行：47-90 秒（性能优化后）

**关键配置**：
```yaml
permissions:
  contents: write                    # 允许 GITHUB_TOKEN 写入仓库

env:
  IPTV_TIMEOUT: 3                    # 单流测试超时 3 秒（与本地一致）
  IPTV_MAX_PARALLEL: 200             # 并发数 200（与本地一致）
  ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION: true  # 消除 Node.js 弃用警告
```

**工作流步骤**：
1. **Checkout repository**: `fetch-depth: 0` + token 用于后续推送
2. **Set up Python**: Python 3.10
3. **Install dependencies**: aiohttp
4. **Run scraping script**: 执行 iptv.py 采集 IPTV 源
5. **GetTime**: 获取当前时间戳
6. **Update README.md**: sed 替换时间和链接占位符
7. **Commit and push changes**:
   - 文件存在性检查
   - `git add -f file/best_sorted.m3u` 强制添加（绕过 .gitignore）
   - `git add -f file/best_sorted.m3u8` 强制添加
   - 动态分支引用 `${{ github.ref }}`
   - 无变更时跳过提交
8. **Send email notification**: `python script/notify.py --once`
9. **Save and commit notify hashes**: 保存并推送 `.notify_hashes.json`

**已解决的技术问题**：

| 问题 | 解决方案 | 提交 |
|------|---------|------|
| 路径错误 | 改为 `file/` 目录 | a8c357f |
| .gitignore 阻止 | `git add -f` 强制添加 + 例外规则 | 82562be, 2520fd1 |
| Node.js 弃用警告 | 移除 Node.js 设置 + 环境变量 | e61f718, aac2981 |
| Git 操作健壮性 | 智能检查 + 动态分支 | e61f718 |
| **403 权限错误** | **`permissions: contents: write`** | **3b793ad** |
| **运行速度慢** | **IPTV_TIMEOUT=3 + MAX_PARALLEL=200** | **62eca5b** |
| **邮件通知缺失** | **添加 notify 步骤 + 哈希持久化** | **70a7796, ed522a5** |

**性能优化对比**：
```
优化前：3-5 分钟 (180-300s)
优化后：47-90 秒
提速比：5-6 倍
原因：IPTV_TIMEOUT 从 10s→3s，并发从 50→200
```

**邮件通知逻辑**：
```python
# 首次运行（无哈希记录）→ 发送 "new" 邮件 ✓
# 文件变化（哈希不同）→ 发送 "updated" 邮件 ✓
# 文件未变（哈希相同）→ 跳过发送（避免轰炸）✓
# 哈希持久化 → config/.notify_hashes.json 提交到 Git ✓
```

**触发方式**：
- 定时任务：`cron: '0 */4 * * *'`（每天 6 次）
- 手动触发：GitHub Actions 页面 "Run workflow" 按钮

### Shell脚本

- bat/sh都在IPTV采集后调用 `notify.py --once`
- bat：`%PYTHON_CMD% "%~dp0notify.py" --once`
- sh：`$PYTHON_CMD "$WORK_DIR/script/notify.py" --once`
- 工作目录：bat用 `cd /d "%~dp0.."`，sh用 `cd "$WORK_DIR"`
- 性能参数：`IPTV_TIMEOUT=3`, `IPTV_MAX_PARALLEL=200`（与 GitHub Actions 一致）

#### FFmpeg 自动修复 (iptv_tool.sh)

**函数**: `fix_ffmpeg_issues(ffmpeg_path)`

**自动检测和修复的问题**:
1. **执行权限缺失**: 检测到无 `-x` 权限时自动 `chmod +x`
2. **架构不匹配 (macOS)**: 
   - 使用 `uname -m` 获取系统架构
   - 使用 `file` 命令检测 FFmpeg 架构
   - 不匹配时从嵌套目录 `bin/bin/ffmpeg` 查找正确版本
   - 自动备份错误版本（带时间戳）
   - 同时处理 ffprobe
3. **安装后验证**: 安装完成后验证 FFmpeg 是否能正常运行

**调用时机**:
- `detect_ffmpeg()` 函数中每次检测 FFmpeg 时
- 系统 PATH 中的 FFmpeg
- 项目预编译版本 (`ffmpeg/{platform}/bin/ffmpeg`)
- .venv 目录中的 FFmpeg
- 安装后的新版本

**架构映射表**:
| 系统 | 正确路径 | 备选路径 |
|------|---------|---------|
| macOS ARM | `ffmpeg/macos/bin/ffmpeg` (arm64) | `ffmpeg/macos/bin/bin/ffmpeg` |
| macOS Intel | `ffmpeg/macos/bin/ffmpeg` (x86_64) | - |
| Linux x64 | `ffmpeg/linux/bin/ffmpeg` (x86_64) | - |

### Python风格

- 编码：始终指定 `encoding='utf-8'`
- 路径：使用 `pathlib.Path`
- 异步：`aiohttp` + `asyncio`
- 配置：环境变量 + `os.environ.get()` + 默认值
- 版本号：唯一来源 `README.md`，格式 `### v1.2.3 (YYYY-MM-DD)`

### 文件位置

- M3U/M3U8输出：`file/best_sorted.m3u`、`file/best_sorted.m3u8`
- Web静态文件：`output/` 目录
- FFmpeg二进制：`ffmpeg/{windows,linux,macos}/bin/`
- 缓存文件：`file/.cdn_cache.json`、`file/.stream_cache.json`、`file/.source_cache.json`
- 邮件哈希记录：`config/.notify_hashes.json`（Git 跟踪，用于持久化）
- GitHub Actions 配置：`.github/workflows/iptv.yml`
- 邮件配置：`config/notify.json`（含 SMTP 凭证，不提交到 Git）