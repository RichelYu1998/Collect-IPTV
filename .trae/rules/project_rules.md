# Project Rules

## 三文件同步更新规则

以下三个文件必须**同步更新**，任何涉及功能变更、版本更新、文档修改的操作都必须同时修改这三个文件：

1. `README.md` — 项目文档（用户面向）
2. `skill.md` — 代码规范文档（开发者面向）
3. `.trae/skills/iptv-dev/SKILL.md` — AI 开发技能文档（Trae Skill）

### 更新流程

1. 同步修改三个文件的相关内容
2. `git add README.md skill.md .trae/skills/iptv-dev/SKILL.md`
3. `git commit -m "docs: 更新描述"`
4. `git push origin main`

### 版本号同步

版本号唯一来源为 `README.md`，格式 `### v1.2.3 (YYYY-MM-DD)`。
更新版本时，三个文件的版本号和更新日期必须保持一致。