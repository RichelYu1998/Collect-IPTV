# Collect-IPTV 项目规则

## 项目概述
智能IPTV直播源采集工具，自动采集、去重、优选最佳直播源。

## 技术栈
- Python 3.9+ (aiohttp, asyncio)
- Shell (bash/bat)
- GitHub Actions
- FFmpeg 音视频转码

## 关键文件
- `.github/workflows/iptv.py` — 核心采集脚本
- `.github/workflows/iptv.yml` — GitHub Actions 工作流
- `.github/workflows/sync-upstream.yml` — 多仓库自动同步
- `server.py` — 本地Web服务（代理/转码/API）
- `script/notify.py` — 邮件通知
- `skill.md` — 代码规范文档

## 输出文件（file/ 目录）
- `best_sorted.m3u` / `.m3u8` — 播放列表（含EPG）
- `best_sorted.txt` — TXT频道列表
- `api_data.json` — REST API数据源
- `stats_report.json` — 采集统计报告
- `best_sorted_gh-proxy.m3u` / `best_sorted_ghproxy-mirror.m3u` — 代理加速版

## 代码规范
- 缩进：4空格
- 字符串：优先f-string
- 编码：UTF-8，读写始终指定 encoding='utf-8'
- JSON：2空格缩进，ensure_ascii=False
- 路径：Python用pathlib.Path
- 异步：aiohttp + asyncio
- 环境变量：os.environ.get() + 默认值

## 同步更新规则
README.md 和 skill.md 必须同步更新，版本号保持一致。

## Lint/检查命令
```bash
python -c "import ast; ast.parse(open('.github/workflows/iptv.py', encoding='utf-8').read()); print('OK')"
python -c "import ast; ast.parse(open('server.py', encoding='utf-8').read()); print('OK')"
```