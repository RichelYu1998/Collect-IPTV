# 📡 Collect-IPTV

> **智能IPTV直播源采集工具** - 自动采集、去重、优选最佳直播源，支持跨平台运行

[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue.svg)](https://github.com/your-repo)
[![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 目录

- [✨ 功能特性](#-功能特性)
- [🚀 快速开始](#-快速开始)
- [📋 系统要求](#-系统要求)
- [🔧 配置说明](#-配置说明)
- [📧 邮件通知](#-邮件通知)
- [🎯 智能分类](#-智能分类)
- [⚡ 性能优化](#-性能优化)
- [🔍 质量筛选](#-质量筛选)
- [🌐 Web界面](#-web界面)
- [🛠️ 技术架构](#️-技术架构)
- [❓ 常见问题](#-常见问题)
- [📝 更新日志](#-更新日志)

---

## ✨ 功能特性

### 核心功能

| 功能 | 描述 |
|------|------|
| 🤖 **智能采集** | 自动从多个源采集IPTV直播流，支持CDN加速 |
| ⚡ **质量优选** | 测试延迟和可用性，自动选择最佳直播源 |
| 🎬 **在线播放** | 内置Web播放器，支持HLS流媒体直接观看 |
| 🔊 **音频转码** | 自动检测并转码AC3/EAC3等不兼容音频格式 |
| 📧 **邮件通知** | 文件变更时自动发送邮件，含M3U/M3U8附件 |
| 🔄 **定时任务** | 每4小时自动更新，确保数据新鲜 |
| 📊 **统计报告** | 自动生成频道统计、延迟排行、分类报告 |
| 🔌 **REST API** | 提供频道查询/搜索/统计API接口 |
| 📝 **多格式输出** | 同时生成M3U/M3U8/TXT三种格式 |
| 🌐 **代理加速** | 自动生成gh-proxy镜像M3U，加速GitHub源访问 |

### 平台支持

- ✅ **Windows** 10/11 (x64)
- ✅ **Linux** Ubuntu/Debian/CentOS
- ✅ **macOS** Intel / Apple Silicon (M1/M2/M3)

### 高级特性

- **CORS代理**: 解决浏览器跨域限制，支持代理外部资源
- **流式代理**: 双线程并行转发，首字节响应时间减半
- **智能预加载**: M3U8返回时预拉取TS分片，实现零延迟播放
- **转码预加载**: FFmpeg转码TS分片异步预加载，转码流也零延迟
- **缓存等待**: 未命中时等待预加载完成，最大化缓存命中率
- **CDN轮询**: 自动测速选择最快的CDN节点
- **零配置**: 开箱即用，无需手动安装依赖

---

## 🚀 快速开始

### Windows

```cmd
# 方式1: 双击运行
双击 script\iptv_tool.bat

# 方式2: 命令行运行
cd D:\ws\Collect-IPTV
.\script\iptv_tool.bat
```

### Linux/macOS

```bash
# 添加执行权限
chmod +x script/iptv_tool.sh

# 运行脚本
./script/iptv_tool.sh
```

### 运行流程

```
启动脚本 → 环境检测 → 依赖安装 → IPTV采集 → 邮件通知 → 启动Web服务
   ↓          ↓          ↓           ↓          ↓           ↓
  1秒       4秒        3秒         2秒       <1秒       即时启动
```

**总计耗时**: ~10秒（首次运行，后续有缓存）

### 访问地址

启动成功后，可通过以下地址访问：

| 地址 | 说明 |
|------|------|
| http://localhost:8000 | 本地访问 |
| http://192.168.x.x:8000 | 局域网访问（手机/其他设备） |

---

## 📋 系统要求

### 必需组件

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.9+ | 核心运行环境 |
| FFmpeg | 预编译版本 | 音视频转码 |
| pip | 最新版 | 包管理器 |

### 自动安装

脚本会自动处理以下内容：

- ✅ Python虚拟环境（`.venv`）
- ✅ Python依赖包（`aiohttp`等）
- ✅ FFmpeg + FFprobe（按平台自动下载）
- ✅ PIP镜像源配置（自动选择最快）

### 推荐配置

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| 内存 | 512MB | 2GB+ |
| 磁盘 | 100MB | 1GB+ |
| 网络 | 10Mbps | 50Mbps+ |
| CPU | 单核 | 双核+ |

---

## 🔧 配置说明

### 目录结构

```
Collect-IPTV/
├── script/
│   ├── iptv_tool.bat      # Windows启动脚本
│   ├── iptv_tool.sh       # Linux/macOS启动脚本
│   └── notify.py          # 邮件通知模块
├── config/
│   └── notify.json        # 邮件配置文件
├── ffmpeg/                # FFmpeg预编译二进制
│   ├── windows/bin/       # Windows版本
│   ├── linux/bin/         # Linux版本
│   └── macos/bin/         # macOS版本
├── file/                  # 运行时数据
│   ├── best_sorted.m3u    # M3U播放列表
│   ├── best_sorted.m3u8   # M3U8播放列表
│   ├── best_sorted.txt    # TXT频道列表
│   ├── api_data.json      # API数据文件
│   └── stats_report.json  # 统计报告
├── output/                # Web服务器根目录
│   └── index.html         # Web界面
├── server.py              # 本地Web服务器
├── .venv/                 # Python虚拟环境
├── README.md              # 项目文档
└── skill.md               # 技术细节文档
```

### 环境变量

所有配置项都可通过环境变量自定义：

```bash
# 服务器端口（默认: 8000）
export SERVER_PORT=8080

# IPTV超时时间（默认: 3秒）
export IPTV_TIMEOUT=5

# 最大并发数（默认: 200）
export IPTV_MAX_PARALLEL=300
```

---

## 📧 邮件通知

### 功能概述

当 `best_sorted.m3u` 或 `best_sorted.m3u8` 文件发生变化时，系统会自动发送邮件通知，并将这两个文件作为附件一同发送。支持三种邮件发送方式：**SMTP**、**SendGrid API**、**Resend API**。

### 配置方法

编辑 `config/notify.json`，根据 `email_provider` 字段选择发送方式：

#### 方式1: SMTP（默认，本地运行推荐）

```json
{
  "email_provider": "smtp",
  "email_notification_enabled": true,
  "email_smtp_host": "smtp.qq.com",
  "email_smtp_port": 465,
  "email_smtp_user": "your@qq.com",
  "email_smtp_password": "your_auth_code",
  "email_from_name": "IPTV直播源监控",
  "email_to": "recipient@example.com",
  "github_repo": "RichelYu1998/Collect-IPTV",
  "github_branch": "main",
  "watch_files": ["file/best_sorted.m3u", "file/best_sorted.m3u8"]
}
```

#### 方式2: SendGrid API（GitHub Actions 推荐，无域名验证限制）

```json
{
  "email_provider": "sendgrid",
  "email_notification_enabled": true,
  "sendgrid_api_key": "SG.xxxxx",
  "sendgrid_from_email": "noreply@yourdomain.com",
  "email_from_name": "IPTV直播源监控",
  "email_to": "recipient@example.com",
  "github_repo": "RichelYu1998/Collect-IPTV",
  "github_branch": "main",
  "watch_files": ["file/best_sorted.m3u", "file/best_sorted.m3u8"]
}
```

#### 方式3: Resend API（GitHub Actions 备选，免费额度）

```json
{
  "email_provider": "resend",
  "email_notification_enabled": true,
  "resend_api_key": "re_xxxxx",
  "resend_from_email": "onboarding@resend.dev",
  "email_from_name": "IPTV直播源监控",
  "email_to": "recipient@example.com",
  "github_repo": "RichelYu1998/Collect-IPTV",
  "github_branch": "main",
  "watch_files": ["file/best_sorted.m3u", "file/best_sorted.m3u8"]
}
```

### GitHub Actions 邮件配置

GitHub Actions 通过 Secrets 环境变量注入 SMTP 配置，无需提交凭证到仓库：

| Secret 名称 | 说明 | 示例 |
|-------------|------|------|
| `SMTP_HOST` | SMTP 服务器地址 | `smtp.qq.com` |
| `SMTP_PORT` | SMTP 端口 | `465` |
| `SMTP_USER` | 发件邮箱账号 | `your@qq.com` |
| `SMTP_PASSWORD` | 授权码/密码 | `elracegpxeyabceb` |
| `EMAIL_TO` | 收件邮箱 | `recipient@example.com` |

Workflow 会自动在运行时生成 `config/notify.json`，使用 SMTP 方式发送。

### 发送策略

| 场景 | 行为 |
|------|------|
| **首次运行** | 立即发送当前文件（无历史记录） |
| **文件变更** | 立即发送更新后的文件 |
| **无变化** | 不发送邮件 |
| **发送失败** | 不重试，等待下次检测 |

### 邮件提供商对比

| 特性 | SMTP | SendGrid API | Resend API |
|------|------|-------------|------------|
| **适用场景** | 本地运行 | GitHub Actions | GitHub Actions |
| **端口限制** | 可能被封（587/465） | 无（HTTPS 443） | 无（HTTPS 443） |
| **域名验证** | 不需要 | 不需要 | 需要（免费额度） |
| **免费额度** | 取决于邮箱服务商 | 100封/天 | 100封/天 |
| **附件支持** | ✅ | ✅ | ✅ |
| **配置复杂度** | 低 | 低 | 中 |

### 支持的 SMTP 邮箱服务商

| 服务商 | SMTP服务器 | 端口 | 加密方式 |
|--------|-----------|------|---------|
| QQ邮箱 | smtp.qq.com | 465 | SSL |
| 163邮箱 | smtp.163.com | 465 | SSL |
| Gmail | smtp.gmail.com | 587 | STARTTLS |
| Outlook | smtp.office365.com | 587 | STARTTLS |

> 💡 **提示**: 请使用授权码而非登录密码，在邮箱设置的SMTP选项中获取。端口 465 使用 SSL 直连，端口 587 使用 STARTTLS 升级加密。

---

## 🎯 智能分类

### 频道类型

系统自动将采集到的频道进行智能分类：

#### 央视频道
- CCTV-1 ~ CCTV-16 综合频道
- CGTN 英语国际频道
- CHC 电影频道系列

#### 省市频道
覆盖全国31个省市自治区：
- 北京卫视、东方卫视、湖南卫视等省级卫视
- 各省市地面频道

#### 主题频道
- 📰 新闻频道
- ⚽ 体育频道
- 🎬 影视频道
- 👶 少儿频道
- 🎵 音乐频道
- 🎭 戏曲频道

#### 特色频道
- 港澳台：翡翠台、明珠台、东森、中天
- 文旅：景区风光、特色观光

### 分类算法

1. **关键词匹配**: 通过频道名称识别类型
2. **Geo定位**: 基于地理位置数据自动归类
3. **机器学习**: 使用预训练模型辅助分类

---

## ⚡ 性能优化

### 三级缓存体系

本项目实现了完整的三级缓存机制，性能提升显著：

```
┌─────────────────────────────────────────────────────┐
│                   缓存架构                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [L1] CDN测速缓存     → .cdn_cache.json             │
│       ↓ 保存时间: 24小时                             │
│                                                     │
│  [L2] 源文件内容缓存   → .source_cache.json          │
│       ↓ 保存时间: 2小时                              │
│                                                     │
│  [L3] 流测试结果缓存   → .stream_cache.json          │
│       ↓ 保存时间: 实时更新                            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 性能对比

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| **首次启动时间** | 2-3分钟 | ~10秒 | **15x** |
| **二次启动时间** | 30-60秒 | 1.3秒 | **25x** |
| **采集速度** | 串行处理 | 并发200线程 | **10x** |
| **首字节延迟** | >500ms | <100ms | **5x** |
| **缓存命中率** | 0% | >95% | **∞** |

### 并发处理

- **CDN测速**: 5个源并发测试
- **源文件下载**: 多线程并行获取
- **流可用性测试**: 200个并发连接
- **数据写入**: 异步IO批量保存

---

## 🔍 质量筛选

### 筛选流程

```
原始源 (1944个)
    ↓ 可用性测试
有效源 (1252个)  ← 过滤不可用链接
    ↓ 智能去重
唯一源 (770个)   ← 合并重复频道
    ↓ 延迟排序
最优源 (770个)   ← 每频道保留最佳URL
    ↓ 输出文件
best_sorted.m3u/m3u8
```

### 筛选标准

| 标准 | 方法 | 阈值 |
|------|------|------|
| **可用性** | HTTP HEAD请求 | 响应时间 < 3秒 |
| **延迟测试** | 连接建立时间 | < 500ms 为优 |
| **内容验证** | 检查M3U8格式 | 必须包含TS分片 |
| **去重算法** | MD5哈希对比 | 相同内容合并 |

### 数据统计

最近一次采集结果：
- 总采集源：**1944** 个
- 有效源数量：**1252** 个（64.4%）
- 去重后频道：**770** 个
- 平均延迟：**<200ms**

---

## 🌐 Web界面

### 功能特性

内置Web界面提供完整的IPTV管理和播放体验：

#### 播放器功能

- ▶️ 双引擎流媒体播放（HLS流用hls.js，TS/FLV流用mpegts.js）
- 🔊 音量控制与静音
- ⏯️ 播放/暂停切换
- 📱 全屏模式支持
- 🔄 错误自动重连

#### 界面功能

- 🔍 频道搜索（支持模糊匹配）
- 🏷️ 分类筛选（按类型/地区）
- 📊 台标显示（Logo展示）
- ⭐ 收藏功能（常用频道）
- 🌙 暗色主题（护眼模式）

### CORS代理

解决浏览器跨域限制问题：

```
浏览器请求 → http://localhost:8000/proxy/<encoded_url>
                    ↓
              server.py代理转发
                    ↓
              目标IPTV服务器
                    ↓
              返回数据（绕过CORS）
```

### API端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | Web界面首页 |
| `/proxy/<url>` | GET | CORS代理 |
| `/file/*.m3u` | GET | M3U播放列表 |
| `/file/*.m3u8` | GET | M3U8播放列表 |
| `/file/*.txt` | GET | TXT频道列表 |
| `/api/channels` | GET | 频道列表API（支持 `?group=` `?name=` `?region=` `?limit=` 参数） |
| `/api/stats` | GET | 采集统计报告API |
| `/api/groups` | GET | 频道分组API |
| `/api/search?q=关键词` | GET | 频道搜索API |

---

## 🛠️ 技术架构

### 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| **前端** | HTML5 + CSS3 + JavaScript | 用户界面 |
| **播放器** | hls.js + mpegts.js | HLS流/TS流双引擎播放 |
| **后端** | Python 3.9+ | 业务逻辑 |
| **框架** | aiohttp | 异步HTTP服务 |
| **转码** | FFmpeg | 音视频处理 |
| **任务调度** | Windows Task / Linux Cron | 定时采集 |

### 架构图

```
┌─────────────────────────────────────────────────┐
│                    用户层                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Web浏览器 │  │ bat脚本  │  │ sh脚本   │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
└───────┼─────────────┼─────────────┼─────────────┘
        │             │             │
┌───────▼─────────────▼─────────────▼─────────────┐
│                    服务层                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ server.py │  │ notify.py│  │ iptv.py  │      │
│  │ :8000端口 │  │ 邮件通知 │  │ 数据采集 │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
└───────┼─────────────┼─────────────┼─────────────┘
        │             │             │
┌───────▼─────────────▼─────────────▼─────────────┐
│                    数据层                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ file/    │  │ config/  │  │ ffmpeg/  │      │
│  │ M3U文件  │  │ 配置文件 │  │ 转码工具 │      │
│  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────┘
```

### 关键模块

#### server.py - Web服务器
- 静态文件服务
- CORS代理转发
- 音频实时转码（FFmpeg参数优化）
- 流式代理传输

#### iptv_tool.bat/sh - 启动脚本
- 环境自动检测
- 依赖自动安装
- 流程自动化
- 定时任务管理

#### notify.py - 邮件通知
- 文件变更检测（MD5哈希对比）
- 三种发送方式：SMTP / SendGrid API / Resend API
- SMTP_SSL (端口465) 和 STARTTLS (端口587) 双模式
- 附件自动添加（M3U/M3U8文件）
- 时区修正为 UTC+8 (CST)
- GitHub Actions 通过 Secrets 环境变量注入配置

---

## ❓ 常见问题

### Q1: 为什么有些频道无法播放？

**A**: 可能的原因：
1. 上游源失效（已过过滤）
2. 地区限制（某些IP无法访问）
3. 带宽不足（高清源需要>5Mbps）

**解决方案**:
- 等待下次自动更新（每4小时）
- 手动删除 `.stream_cache.json` 强制重新测试
- 检查网络连接是否正常

### Q2: 如何修改邮件接收地址？

**A**: 编辑 `config/notify.json`，修改以下字段：

```json
{
  "receiver_email": "your-email@example.com"
}
```

### Q3: FFmpeg安装失败怎么办？

**A**: 手动下载对应平台的FFmpeg：

```bash
# Windows
下载到: ffmpeg/windows/bin/

# Linux
下载到: ffmpeg/linux/bin/

# macOS
下载到: ffmpeg/macos/bin/
```

然后赋予执行权限（Linux/macOS）：
```bash
chmod +x ffmpeg/*/bin/*
```

### Q4: 如何更改Web服务器端口？

**A**: 设置环境变量：

```bash
# Windows (CMD)
set SERVER_PORT=8080

# Linux/macOS
export SERVER_PORT=8080
```

### Q5: 定时任务如何查看？

**Windows**:
```cmd
schtasks /query /tn "IPTV_Collection"
```

**Linux/macOS**:
```bash
crontab -l | grep iptv
```

---



## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 文档同步更新规则

以下两个文件必须**同步更新**，任何涉及功能变更、版本更新、文档修改的操作都必须同时修改：

| 文件 | 面向 | 作用 |
|------|------|------|
| `README.md` | 用户 | 项目文档 |
| `skill.md` | 开发者 & AI | 代码规范文档 & 开发技能文档 |

**更新流程**：同步修改 → `git add README.md skill.md` → `git commit` → `git push origin main`

**版本号同步**：版本号唯一来源为 `README.md`，格式 `### v1.2.3 (YYYY-MM-DD)`，两个文件的版本号和更新日期必须保持一致。

### 代码规范

| 项目 | 规范 |
|------|------|
| 缩进 | 4 空格 |
| 字符串 | 优先 f-string 格式化 |
| 编码 | UTF-8，读写始终指定 `encoding='utf-8'` |
| JSON | 2 空格缩进，`ensure_ascii=False` |
| 路径 | Python 用 `pathlib.Path` |
| 异步 | `aiohttp` + `asyncio` |
| 环境变量 | `os.environ.get()` + 默认值 |

### Lint/检查命令

```bash
python -c "import ast; ast.parse(open('.github/workflows/iptv.py', encoding='utf-8').read()); print('OK')"
python -c "import ast; ast.parse(open('server.py', encoding='utf-8').read()); print('OK')"
```

## 📧 联系方式

如有问题或建议，请通过以下方式联系：
- 📧 Email: [your-email@example.com]
- 💬 Issues: [GitHub Issues](https://github.com/your-repo/issues)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star！⭐**

Made with ❤️ by Collect-IPTV Team

</div>

---

## 📜 完整更新历史

### v2.14.0 (2026-07-04) - 多格式输出 & REST API & 代理加速 & 多仓库同步 & EPG节目单

#### ✨ 新功能
- ✅ **TXT格式频道列表**：自动生成 `best_sorted.txt`，兼容更多播放器，含分类统计信息
- ✅ **REST API 接口**：新增4个API端点（`/api/channels`、`/api/stats`、`/api/groups`、`/api/search`），支持按分组/名称/地区查询和模糊搜索
- ✅ **自动生成统计报告**：每次运行输出 `stats_report.json`，含频道数量、分类统计、延迟排行、最快/最慢频道
- ✅ **自动代理/加速**：生成 gh-proxy 和 ghproxy-mirror 镜像 M3U 文件，加速 GitHub 源访问
- ✅ **多仓库自动同步**：新增 `sync-upstream.yml` 工作流，Fork 玩家自动同步上游更新，冲突时保留本地修改
- ✅ **EPG节目单**：M3U/M3U8 文件头部自动写入 `url-tvg` EPG地址（fanmingming + 51zmt 双源），VLC/TiviMate 等播放器自动加载节目单

#### 📺 VLC/播放器订阅地址

| 格式 | 地址 |
|------|------|
| M3U | `https://raw.githubusercontent.com/RichelYu1998/Collect-IPTV/main/file/best_sorted.m3u` |
| M3U8 | `https://raw.githubusercontent.com/RichelYu1998/Collect-IPTV/main/file/best_sorted.m3u8` |
| CDN加速 | `https://cdn.jsdelivr.net/gh/RichelYu1998/Collect-IPTV@main/file/best_sorted.m3u` |
| gh-proxy | `https://gh-proxy.com/https://raw.githubusercontent.com/RichelYu1998/Collect-IPTV/main/file/best_sorted.m3u` |

#### 🔄 多仓库同步配置

Fork 玩家在 Settings → Secrets 中添加：
- `UPSTREAM_REPO`：上游仓库地址（如 `https://github.com/RichelYu1998/Collect-IPTV.git`）
- `UPSTREAM_BRANCH`：上游分支（默认 `main`）

---

### v2.13.0 (2026-07-02) - 多邮件提供商支持 & SMTP_SSL & 时区修复

#### ✨ 新功能
- ✅ **SendGrid API 邮件发送**：通过 HTTPS API 发送邮件，绕过 GitHub Actions SMTP 端口封锁，无域名验证限制
- ✅ **Resend API 邮件发送**：备选 HTTPS API 方式，免费额度 100 封/天，适合轻量使用
- ✅ **多提供商架构**：`email_provider` 字段切换发送方式（smtp / sendgrid / resend），统一接口
- ✅ **SMTP_SSL 支持**：端口 465 使用 `smtplib.SMTP_SSL` 直连，解决 GitHub Actions SMTP 连接问题
- ✅ **GitHub Actions 邮件配置自动化**：通过 Secrets 环境变量注入 SMTP 凭证，运行时自动生成 `notify.json`

#### 🔧 Bug修复
- ✅ **修复邮件通知时区**：时间戳从 UTC 改为 UTC+8 (CST)，邮件显示时间与本地一致
- ✅ **修复 SMTP 连接失败**：端口 465 使用 SSL 直连而非 STARTTLS，解决 GitHub Actions SMTP 端口封锁
- ✅ **修复邮件配置 JSON 格式错误**：GitHub Actions 生成 notify.json 时格式规范化
- ✅ **修复 Secrets 语法错误**：环境变量引用方式修正，避免 YAML 解析错误
- ✅ **增强邮件通知诊断**：更详细的发送状态日志（提供商、端口、连接方式、错误详情）

#### 📝 配置变更
- 📄 `config/notify.json`: 新增 `email_provider` 字段（smtp / sendgrid / resend）
- 📄 `config/notify.json`: SMTP 配置字段重命名（`smtp_server` → `email_smtp_host`，`smtp_port` → `email_smtp_port` 等）
- 📄 `.github/workflows/iptv.yml`: 新增 "Setup email notification config" 步骤，通过 Secrets 注入配置
- 📄 `script/notify.py`: 新增 `send_email_sendgrid()` 和 `send_email_resend()` 函数

#### 💡 使用体验提升
- 🌐 GitHub Actions 邮件不再被端口封锁，SMTP 465 SSL 直连可靠发送
- 🔑 凭证安全：SMTP 密码通过 GitHub Secrets 注入，不提交到仓库
- 📧 三种发送方式灵活切换，本地用 SMTP，云端用 API
- 🕐 邮件时间戳正确显示北京时间

---

### v2.12.0 (2026-07-01) - GitHub Actions 全面优化 & 智能邮件通知 & 性能提升

#### ✨ 新功能
- ✅ **GitHub Actions 自动化工作流**：实现完整的 CI/CD 流程，自动采集、生成、提交、推送
- ✅ **智能邮件通知系统**：文件变更时自动发送邮件（首次运行 + 内容变化时触发）
- ✅ **哈希持久化机制**：通知哈希记录保存到 Git 仓库，避免重复邮件
- ✅ **高性能配置**：IPTV_TIMEOUT=3s + 200 并发，运行速度提升 5 倍

#### 🔧 GitHub Actions 核心修复
- ✅ **路径错误修复**：git add 从根目录改为 `file/best_sorted.m3u` 和 `file/best_sorted.m3u8`
- ✅ **权限问题解决**：添加 `permissions: contents: write` 解决 GITHUB_TOKEN 403 错误
- ✅ **Git 操作健壮性**：增加文件存在性检查、无变更处理、动态分支引用
- ✅ **.gitignore 冲突解决**：使用 `git add -f` 强制添加被忽略的 M3U 文件
- ✅ **Node.js 弃用警告消除**：移除不必要的 Node.js 设置，添加环境变量
- ✅ **性能优化**：与本地脚本保持一致的 IPTV_TIMEOUT 和 IPTV_MAX_PARALLEL 参数

#### 📧 邮件通知功能详解
- 📬 **触发条件**：
  - 首次运行 → 发送"新文件"检测邮件（标记为 new）
  - 文件内容变化 → 发送"更新"邮件（标记为 updated）
  - 文件无变化 → 跳过发送（避免邮件轰炸）
- 🔒 **技术实现**：
  - 使用 MD5/SHA256 哈希对比文件内容
  - `.notify_hashes.json` 持久化到 Git 仓库
  - 支持冷却时间防止频繁发送
- 📊 **邮件内容包含**：时间戳、变更文件列表、下载链接、文件大小、频道数量

#### ⚡ 性能优化成果
| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 运行耗时 | 3-5 分钟 (180-300s) | 47-90 秒 | **5-6 倍** |
| 单流测试超时 | 10 秒 | 3 秒 | **3.3 倍** |
| 并发数 | 50 | 200 | **4 倍** |
| 总体提速 | - | - | **~10 倍** |

#### 🛠️ 技术架构改进
```yaml
# iptv.yml 关键配置
permissions:
  contents: write                    # 允许写入仓库

env:
  IPTV_TIMEOUT: 3                    # 快速超时（与本地一致）
  IPTV_MAX_PARALLEL: 200             # 高并发（与本地一致）

steps:
  - name: Run scraping script        # 采集 IPTV 源
  - name: Commit and push changes    # git add -f 强制添加
  - name: Send email notification    # notify.py --once
  - name: Save and commit hashes     # 哈希持久化
```

#### 📝 配置变更
- 📄 `.github/workflows/iptv.yml`: 完整重写，添加权限、性能优化、邮件通知步骤
- 📄 `.gitignore`: 允许 `!config/.notify_hashes.json` 跟踪
- 📄 `config/notify.json`: 已有配置复用（QQ邮箱 SMTP）
- 📄 `script/notify.py`: 复用现有逻辑（--once 参数）

#### 💡 使用体验提升
- 🤖 **全自动化**：无需人工干预，每 4 小时自动运行或手动触发
- ⚡ **极速响应**：47 秒完成采集+推送+通知（原需 3-5 分钟）
- 📧 **智能通知**：只在有意义的时候打扰用户（首次/变化时）
- 🔒 **可靠稳定**：所有边缘情况都已处理（权限、路径、冲突等）
- 💾 **数据持久化**：哈希记录保存在 Git，跨运行状态保持一致

#### 🎯 完整功能清单
1. ✅ 自动采集 IPTV 源（多源并发）
2. ✅ 生成 M3U/M3U8 文件（去重、优选）
3. ✅ 更新 README.md（时间戳 + 文件链接）
4. ✅ Git 自动提交推送（git add -f 绕过 .gitignore）
5. ⚡ 极速运行（50 秒内完成核心任务）
6. 🆕 智能邮件通知（首次 + 变化时发送）
7. 🆕 哈希记录持久化（避免重复邮件）

---

### v2.11.0 (2026-07-01) - 脚本健壮性增强 & FFmpeg自动修复 & 配置修正

#### ✨ 新功能
- ✅ **FFmpeg 自动检测和修复**：智能识别并修复权限问题、架构不匹配、嵌套目录结构
- ✅ **架构自适应**：macOS 下自动检测 arm64/x86_64 并选择正确版本
- ✅ **权限自动修复**：检测到无执行权限时自动添加 chmod +x
- ✅ **嵌套目录处理**：自动从 bin/bin/ 目录找到正确架构的 FFmpeg
- ✅ **安装后验证**：FFmpeg 安装后自动验证是否可正常运行

#### 🔧 Bug修复
- ✅ **修复脚本语法错误**：iptv_tool.sh 第204行多余 `fi` 导致无法启动
- ✅ **修复路径配置错误**：notify.json 中 watch_files 缺少 file/ 前缀导致监控失效
- ✅ **修复 WORK_DIR 变量覆盖**：setup_scheduled_task_and_web() 中错误重新定义 WORK_DIR 导致 server.py 找不到
- ✅ **修复 FFmpeg 架构不匹配**：Apple Silicon Mac 使用 x86_64 版本导致转码失败和无声音

#### 📝 配置变更
- 📄 notify.json: watch_files 路径修正为 `file/best_sorted.m3u` 和 `file/best_sorted.m3u8`
- 📄 iptv_tool.sh: 新增 fix_ffmpeg_issues() 自动修复函数
- 📄 server.py: 无变更（FFmpeg 修复在脚本层实现）

#### 💡 使用体验提升
- ⚡ 首次运行或 FFmpeg 异常时自动诊断和修复，无需手动干预
- ⚡ 支持 macOS Apple Silicon (M1/M2/M3) 和 Intel 双架构自动切换
- ⚡ 错误版本自动备份（带时间戳），保留历史记录便于排查

---

### v2.10.0 (2026-07-01) - 播放器架构重构 & 性能优化 & 音频探测加速

#### ✨ 新功能
- ✅ 双播放器架构：HLS流(m3u8)使用hls.js，原始TS/FLV流使用mpegts.js，自动识别URL类型
- ✅ Python原生TS流快速音频探测(_probe_audio_fast)：直接解析TS包结构，非加密流秒级完成
- ✅ 加密流自动检测：pointer byte异常时自动切换ffmpeg探测
- ✅ 前端probe请求10秒超时控制，防止无限等待

#### 🔧 优化改进 - 播放器架构
- 🎬 修复mpegts.js不支持HLS(m3u8)的根本问题——mpegts.js只能处理原始MPEG-TS/FLV流
- 🎬 同时加载hls.js和mpegts.js，根据URL类型自动选择播放器
- 🎬 HLS流：hls.js + MANIFEST_PARSED事件 + recoverMediaError恢复
- 🎬 TS/FLV流：mpegts.js + MEDIA_INFO/loadeddata/canplay多事件就绪检测
- 🎬 转码播放器(输出m3u8)改用hls.js
- 🎬 destroyPlayer兼容两种播放器销毁方式(Hls.destroy vs mpegts.unload+destroy)

#### 🔧 优化改进 - hls.js播放配置
- ⚡ lowLatencyMode: false（非LL-HLS流开启反而增加卡顿）
- ⚡ backBufferLength: 30→10（减少内存压力和GC停顿）
- ⚡ maxBufferLength: 30→10（直播流不需要大缓冲）
- ⚡ maxMaxBufferLength: 60→30（防止缓冲无限增长）
- ⚡ maxBufferSize: 60MB→30MB（减少内存占用）
- ⚡ ABR带宽估算优化：初始800k，快速1.5M，因子0.7/1.5
- ⚡ 分片/manifest/level加载超时10秒+3次重试

#### 🔧 优化改进 - 后端代理
- ⚡ TS分片流式转发：边读64KB边转发，不再全部读完再发（首字节延迟从数秒降到毫秒级）
- ⚡ 预加载等待时间：500ms→200ms（减少首次播放延迟）
- ⚡ TS分片缓存改为边转发边缓存，不阻塞转发

#### 🔧 优化改进 - FFmpeg转码
- ⚡ 移除-re参数（不再限制输出速率，减少延迟累积）
- ⚡ analyzeduration/probesize: 5M→3M（更快启动）
- ⚡ 添加+fastseek标志

#### 🔧 优化改进 - 音频探测
- ⚡ _probe_audio_fast：下载m3u8→解析TS分片URL→下载32KB TS数据→解析TS包结构
- ⚡ 支持mp2/mp3/ac3/eac3/dts编码识别
- ⚡ 加密流检测：pointer byte > 183说明加密，自动切换ffmpeg探测
- ⚡ 非加密流探测：约0.3-0.8秒（m3u8超时3秒、TS超时3秒、下载32KB）
- ⚡ 加密流探测：约2-4秒（ffmpeg probesize 256K、超时4秒）
- ⚡ ffprobe探测：analyzeduration/probesize 256K，超时3秒
- ⚡ ffmpeg非加密流回退：probesize 256K，超时3秒

#### 🐛 Bug修复
- ✅ 修复mpegts.js无法播放HLS流（根因：mpegts.js不支持m3u8播放列表解析）
- ✅ 修复METADATA_ARRIVED事件在HLS流中不触发（改用MEDIA_INFO+loadeddata+canplay多事件）
- ✅ 修复播放器MEDIA_ERROR无恢复操作（添加unload→load→play恢复链）
- ✅ 修复缓冲配置过于激进导致网络波动卡死（enableStashBuffer→true, stashInitialSize→1024）
- ✅ 修复TS PES解析中pointer byte处理（PUSI包payload首字节为pointer field）
- ✅ 修复转码播放器mpegts.js销毁方式不兼容（改用hls.js）

---

### v2.9.0 (2026-07-01) - 播放器升级 & FFmpeg优化 & 邮件检测增强

#### ✨ 新功能
- ✅ 播放器从HLS.js迁移到mpegts.js，直播流兼容性和稳定性大幅提升
- ✅ mpegts.js直播优化配置：低延迟追帧、自动清理缓冲、禁用stash缓冲
- ✅ FFmpeg转码参数全面优化：输入探测加速、错误恢复、多线程、分片自动清理
- ✅ 邮件通知监控路径更新为file/目录下的m3u/m3u8文件
- ✅ 邮件检测逻辑优化：首次运行发送一次，文件真正变更时才再次发送（无变化跳过）

#### 🔧 优化改进 - mpegts.js播放器
- 🎬 CDN从hls.js切换到mpegts.js@latest
- 🎬 播放器初始化使用mpegts.createPlayer()，type='mse'，isLive=true
- 🎬 主播放器配置：enableStashBuffer=false、stashInitialSize=128、liveBufferLatencyChasing=true
- 🎬 转码播放器同样使用mpegts.js，统一播放架构
- 🎬 事件监听从MANIFEST_PARSED改为METADATA_ARRIVED
- 🎬 错误处理适配mpegts.js的ErrorTypes（NETWORK_ERROR/MEDIA_ERROR）
- 🎬 媒体错误恢复策略：unload→load→play（替代HLS.js的recoverMediaError）
- 🎬 销毁流程：unload→detachMediaElement→destroy（完整释放资源）
- 🎬 函数重命名：destroyHls→destroyPlayer、checkAudioTracksFromHls→checkAudioTracksFromPlayer

#### 🔧 优化改进 - FFmpeg参数
- ⚡ 输入优化：-fflags +genpts+discardcorrupt（生成PTS+丢弃损坏包）
- ⚡ 探测加速：-analyzeduration 5000000 -probesize 5000000（缩短启动时间）
- ⚡ 交互禁用：-nostdin（避免阻塞）
- ⚡ 延迟控制：-max_delay 0（最小化延迟）
- ⚡ 多线程：-threads 0（自动利用所有CPU核心）
- ⚡ 分片管理：-hls_flags delete_segments+append_list+independent_segments

#### 🔧 优化改进 - 邮件通知
- 📧 监控文件路径从根目录改为file/目录（file/best_sorted.m3u、file/best_sorted.m3u8）
- 📧 修复变更检测逻辑：非首次运行时仅当文件哈希真正变化才发送邮件
- 📧 无变化时正确跳过发送，避免重复邮件
- 📧 bat/sh脚本已集成notify.py --once调用（采集完成后自动检测）

---

### v1.0.0 (2026-07-01) - 正式发布

#### ✨ 新功能
- ✅ 跨平台支持（Windows/Linux/macOS）
- ✅ 邮件通知系统（首次运行或变更即发送，含M3U/M3U8附件）
- ✅ Web界面（含HLS播放器和CORS代理）
- ✅ FFmpeg多平台预编译版本
- ✅ 三级缓存体系（性能提升15-25倍）
- ✅ 智能频道分类和去重
- ✅ bat/sh脚本统一调用notify.py --once单次模式

#### 🐛 Bug修复
- ✅ 修复bat脚本BOM编码问题（UTF-8 BOM → GBK）
- ✅ 修复Web服务器无法启动（移除exit /b 0提前退出）
- ✅ 修复notify.py无限循环阻塞（添加--once单次模式）
- ✅ 修复访问根路径404错误（创建output目录+index.html）
- ✅ 修复路径规范化问题（消除".."片段，使用.resolve()）
- ✅ 修复双击bat运行路径错误（添加cd /d "%~dp0..")

#### 🔧 优化改进
- ⚡ 首次启动时间：2-3分钟 → ~10秒
- ⚡ 二次启动时间：30-60秒 → 1.3秒
- ⚡ 采集速度提升：串行 → 200并发
- ⚡ 首字节延迟：>500ms → <100ms
- 🗑️ 移除公网地址相关模块，保留局域网地址
- 🗑️ FFmpeg二进制从Git历史中彻底清除（934MB → 0.29MB）
- 🗑️ .gitignore添加ffmpeg/忽略规则

---

### v2.8.0 (2026-07-01) - 预加载全面升级 & 转码异步预加载

#### ✨ 新功能
- ✅ 预加载缓存容量翻倍：500条目/500MB → 2000条目/1GB
- ✅ 缓存TTL延长：300秒 → 600秒
- ✅ 预加载线程池扩容：10线程 → 20线程
- ✅ 新增preload_pending跟踪机制，记录正在预加载中的URL
- ✅ 新增缓存等待机制：TS未命中时等待最多500ms让预加载完成
- ✅ 远程获取的TS分片自动写入缓存，同一分片绝不重复下载
- ✅ 转码流(tstream)异步预加载：m3u8解析后预拉取FFmpeg生成的TS
- ✅ 转码TS缓存命中检查，命中则直接从内存返回
- ✅ 转码TS等待机制：文件未生成时等待最多8秒
- ✅ Pipeline轮询间隔缩短：2秒 → 1秒，更快发现直播流新分片

#### 🔧 优化改进
- ⚡ 缓存命中率从约60%提升至>95%
- ⚡ 转码流播放延迟大幅降低
- ⚡ 新增X-Preload-Hit响应头，可观察缓存命中情况
- ⚡ 新增环境变量IPTV_PRELOAD_WAIT_MS控制等待时间

---

### v2.7.0 - 持续预热频道 & 性能优化

- 🚀 持续预热频道 - 根治HLS动态刷新导致的播放卡顿
- 🚀 全量预热模式 IPTV_PRELOAD_SYNC_ALL - 所有ts分片预加载完再返回m3u8
- 🔧 修复随机卡顿 - flush + 缓存流式发送 + 预加载参数调优
- 🔧 同步等待前3个分片预加载完成，消除前15秒卡顿
- 🔧 流式代理双线程转发 + 智能预加载，消灭播放卡顿
- 🔧 采集并发数从30提升到200，与iptv.py默认值对齐

---

### v2.6.0~v2.6.3 - 移动端适配 & 路径修复

- 📱 v2.6.0 移动端响应式适配 + 文件规范化：表格卡片化、触控优化、缓存文件移入file/
- 🐛 v2.6.1 修复路径错误：在do_collection函数开头添加cd命令
- 🐛 v2.6.2 修复重复.venv问题：在detect_venv函数开头添加cd命令
- 🐛 v2.6.3 修复FFmpeg检测：find_ffmpeg()添加PROJECT_ROOT/ffmpeg/bin路径检查

---

### v2.5.0 - 性能大优化

- 🚀 新增流测试缓存（4小时有效期），降低超时时间80%，首次16s/后续<5s

---

### v2.4.0~v2.4.2 - 项目结构重组

- 📦 v2.4.0 项目结构重组：FFmpeg功能整合进server.py，script目录精简为单一脚本，修复404 Bug
- 🐛 v2.4.1 修复路径错误：将启动脚本移回根目录，解决script/路径重复和404问题
- 🔧 v2.4.2 文件位置优化：启动脚本归入script/，server.py提升到根目录，清理重复.venv

---

### v2.3.0~v2.3.8 - FFprobe & FFmpeg优化

- 🎵 v2.3.0 FFprobe智能音频检测 + 采集性能优化5-10倍
- 🔧 v2.3.1 代理层透明自动音频转码
- 🔧 v2.3.2 优化FFmpeg自动安装，增加国内CDN镜像和错误诊断
- 🐛 v2.3.3 统一虚拟环境目录为.venv，移除venv路径
- 🐛 v2.3.4 修复CMD特殊字符解析导致FFmpeg下载失败
- 🐛 v2.3.5 用Python替代curl下载FFmpeg，彻底解决CMD特殊字符问题
- 🐛 v2.3.6 修复多行Python代码在CMD中逐行执行的问题
- 🐛 v2.3.7 用独立Python脚本替代bat内嵌代码，彻底解决CMD转义问题
- 🔧 v2.3.8 FFmpeg下载支持多CDN自动切换，速度过慢自动跳过

---

### v2.2.0 - Web播放 & CDN优化

- 🎬 音量控制、FFmpeg自动安装转码、CDN轮询测速、零硬编码、局域网访问

---

### v2.1.0 - 网页在线播放

- 🎬 新增网页在线播放、CORS代理、台标优化、采集流程改进

---

### v2.0.0 - 脚本整合

- 📦 整合所有文档到README.md，优化脚本为一键启动（自动注册定时任务+Web服务）

---

### v1.x - 初始版本

- 🎉 跨平台IPTV采集工具，智能分类，质量筛选，自动更新

---