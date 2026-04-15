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
- **🌐 用户友好**：提供网页界面，支持搜索和筛选
- **🔄 持续更新**：每4小时自动更新，确保数据新鲜度
- **🐍 虚拟环境**：自动检测和管理Python虚拟环境
- **📱 跨平台**：支持Windows、Linux、macOS

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

### 📋 功能菜单

```
============================================================
       IPTV Live Stream Collection Tool - Complete Version
============================================================

Menu:

  [1] Environment Check and Configuration
  [2] Virtual Environment Management
  [3] Run IPTV Collection
  [4] Start Local Web Server
  [5] Setup Scheduled Task
  [6] View Generated Files
  [7] Clean Temporary Files
  [8] View Help Documentation
  [0] Exit Program
```

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

### 📁 生成的文件

运行成功后，会在项目根目录生成：
- **best_sorted.m3u** - M3U格式播放列表
- **best_sorted.m3u8** - M3U8格式播放列表

### 🎬 使用生成的播放列表

#### 推荐播放器

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

#### 导入播放列表

1. 打开播放器
2. 找到"打开文件"或"导入播放列表"选项
3. 选择生成的 `best_sorted.m3u` 或 `best_sorted.m3u8` 文件
4. 开始观看直播

### 📖 详细文档

- **[IPTV_TOOL_GUIDE.md](IPTV_TOOL_GUIDE.md)** - 完整使用指南
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - 项目总结和测试结果
- **[TOOL_README.md](TOOL_README.md)** - 工具快速开始指南

---

## 📢 免责声明（个人学习测试专用）

本项目仅用于**网络协议、爬虫技术、自动化脚本开发等个人学习与测试用途**，不用于任何商业、盈利及违规用途。

- 所有节目源均来自互联网公开可访问链接，项目本身不生产、不存储、不篡改任何媒体内容。  
- 严禁将本项目及生成的播放列表用于商业传播、二次分发、公开分享等行为。  
- 所有频道版权均归原版权方所有，使用前请确保符合当地法律法规。  
- 因违规使用本项目产生的任何法律责任、版权纠纷，均由使用者自行承担。

详细免责声明请参阅 [`DISCLAIMER.md`](./DISCLAIMER.md)。

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
2. 选择 `[3]` 运行IPTV采集
3. 选择 `[4]` 启动本地网页服务
4. 访问 http://localhost:8000 查看网页界面
5. 使用生成的播放列表观看直播

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

## 📊 测试结果

### ✅ 环境检测测试
```
[1/6] Checking Python environment...
OK: Python version 3.14.3 (command: py)

[2/6] Checking virtual environment...
OK: Virtual environment detected: .venv

[3/6] Checking dependencies...
OK: aiohttp dependency is installed

[4/6] Checking script files...
OK: iptv.py script file exists
OK: index.html web file exists

[5/6] Checking IPTV configuration directory...
OK: IPTV configuration directory exists
OK: CCTV channel configuration file exists
OK: Provincial channel configuration files: 33

[6/6] Checking network connection...
OK: Network connection is normal
```

### ✅ IPTV采集测试
```
Loaded 6443 online geo tokens from: https://fastly.jsdelivr.net/gh/modood/Administrative-divisions-of-China/dist/pca-code.json
Online geo classification tokens merged.
Valid streams: 1976, deduplicated: 1127, best-per-channel: 678
Generated sorted M3U file: best_sorted.m3u
```

### ✅ 网页服务测试
```
Serving HTTP on :: port 8000 (http://[::]:8000/) ...
```

访问地址：http://localhost:8000/index.html

## 📞 技术支持

- 📖 详细文档：[IPTV_TOOL_GUIDE.md](IPTV_TOOL_GUIDE.md)
- 🌐 项目主页：https://zilong7728.github.io/Collect-IPTV/
- 💻 GitHub仓库：https://github.com/zilong7728/Collect-IPTV
- 📧 问题反馈：通过GitHub Issues提交

## 📝 更新日志

### v2.0.0 (2026-04-15)
- ✅ 新增跨平台本地运行工具
- ✅ 新增虚拟环境检测和管理
- ✅ 新增本地网页服务
- ✅ 新增定时任务配置
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

## 📊 项目状态

- ✅ **功能完整**：所有功能已实现并测试通过
- ✅ **跨平台支持**：Windows、Linux、macOS全部支持
- ✅ **文档完善**：提供详细的使用指南和故障排除
- ✅ **性能优化**：支持并发采集和智能筛选
- ✅ **用户友好**：提供完整的菜单系统和网页界面

---

**项目版本：v2.0.0 | 最后更新：2026-04-15**