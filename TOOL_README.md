# 🚀 IPTV直播源自动采集工具

一个功能完整的跨平台IPTV采集系统，支持Windows、Linux和macOS。

## ✨ 核心特性

- **🤖 智能分类**：自动识别CCTV、各省市频道、主题频道等
- **⚡ 质量筛选**：测试延迟和可用性，优选最佳源
- **🌐 用户友好**：提供网页界面，支持搜索和筛选
- **🔄 持续更新**：每4小时自动更新，确保数据新鲜度
- **🐍 虚拟环境**：自动检测和管理Python虚拟环境
- **📱 跨平台**：支持Windows、Linux、macOS

## 📦 快速开始

### Windows用户

```cmd
# 双击运行或在命令行执行
iptv_tool.bat
```

### Linux/macOS用户

```bash
# 添加执行权限
chmod +x iptv_tool.sh

# 运行工具
./iptv_tool.sh
```

## 📋 功能菜单

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

## 📖 详细文档

- **[IPTV_TOOL_GUIDE.md](IPTV_TOOL_GUIDE.md)** - 完整使用指南
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - 项目总结和测试结果
- **[README.md](README.md)** - 项目主文档

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

## 📞 技术支持

- 📖 详细文档：[IPTV_TOOL_GUIDE.md](IPTV_TOOL_GUIDE.md)
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
- ✅ 完整测试通过

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

## 📊 项目状态

- ✅ **功能完整**：所有功能已实现并测试通过
- ✅ **跨平台支持**：Windows、Linux、macOS全部支持
- ✅ **文档完善**：提供详细的使用指南和故障排除
- ✅ **性能优化**：支持并发采集和智能筛选
- ✅ **用户友好**：提供完整的菜单系统和网页界面

---

**项目版本：v2.0.0 | 最后更新：2026-04-15**