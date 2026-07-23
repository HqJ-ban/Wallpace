# Desktop Wallpaper Changer (Wallpace)

## 项目概览

一个运行在 Windows 上的壁纸自动切换桌面小软件。用户配置图片库文件夹路径后，程序自动扫描并每天随机选一张设为系统壁纸。支持手动切换、跳过不喜欢、自定义间隔等特性。

**技术栈：** Python 3.13 + PySide6 (LGPL)  
**目标平台：** Windows 10/11

---

## 目录结构

```
Desktop_wallpaper/
├── README.md                    ← 本文件（项目总纲 + Obsidian 指引）
├── .superpowers/                ← brainstorm 草图与设计文档（可忽略）
│   └── brainstorming/
├── docs/                        ← 项目开发文档集
│   ├── superpowers/
│   │   └── specs/               ← 设计规范（brainstorming 产出）
│   ├── architecture.md          ← 架构设计文档
│   ├── api-design.md            ← API 设计文档
│   ├── dev-standards.md         ← 开发执行标准
│   └── changelog.md             ← 更新日志
├── src/                         ← 源代码
│   ├── main.py                  ← 入口点
│   ├── app/                     ← 应用模块
│   │   ├── __init__.py
│   │   ├── window.py            ← 主窗口
│   │   ├── tray.py              ← 系统托盘
│   │   └── widgets/             ← UI 组件
│   ├── core/                    ← 核心逻辑模块
│   │   ├── __init__.py
│   │   ├── wallpaper_manager.py ← 壁纸设置
│   │   ├── image_library.py     ← 图片库管理
│   │   ├── scheduler.py         ← 定时调度器
│   │   └── settings.py          ← 配置管理
│   └── utils/                   ← 工具模块
│       ├── __init__.py
│       └── helpers.py
├── tests/                       ← 测试代码
│   ├── conftest.py
│   ├── test_image_library.py
│   └── test_wallpaper_manager.py
├── requirements.txt             ← Python 依赖
├── pyproject.toml               ← 项目元数据
└── build.bat                    ← 打包脚本 (PyInstaller)
```

---

## 核心功能清单

| # | 功能 | 优先级 | 状态 |
|---|------|--------|------|
| 1 | 配置图片库文件夹路径 | P0 | 📋 待开发 |
| 2 | 自动扫描 JPG/PNG/WebP 图片 | P0 | 📋 待开发 |
| 3 | 文件夹变更监听（热加载） | P0 | 📋 待开发 |
| 4 | 每日随机切换壁纸 | P0 | 📋 待开发 |
| 5 | 手动触发"换一张" | P0 | 📋 待开发 |
| 6 | "不喜欢"跳过机制（不重复） | P0 | 📋 待开发 |
| 7 | 自定义时间间隔切换 | P1 | 📋 待开发 |
| 8 | 多显示器统一设置 | P0 | 📋 待开发 |
| 9 | 图标侧边栏导航 + 粉蓝渐变 UI | P0 | 📋 待开发 |
| 10 | 底部自定义栏（天气/日期/数量） | P1 | 📋 待开发 |
| 11 | 系统托盘后台运行 + 右键菜单 | P0 | 📋 待开发 |
| 12 | 设置面板（侧滑） | P1 | 📋 待开发 |
| 13 | 开机自启动 | P1 | 📋 待开发 |
| 14 | 预览图片库缩略图 | P1 | 📋 待开发 |

---

## 快速开始

### 环境准备

```bash
cd D:\my_project\Desktop_wallpaper
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 运行开发版

```bash
python src/main.py
```

### 打包发布

```bash
build.bat
```

---

## 开发流程（Superpowers Brainstorming 产出）

本项目基于 Superpowers 插件的 `brainstorming` 技能完成需求梳理。

| 步骤 | 说明 | 输出文件 |
|------|------|----------|
| 需求分析 | 与用户确认 5 轮问答 | docs/superpowers/specs/2026-07-23-wallpaper-scheduler-design.md |
| UI 草图 | 三个布局方向 A/B/C | mockups/layout-options.html |
| 深化设计 | B 方案详细页面 | mockups/detail-view.html |
| 计划编写 | 接下来执行 writing-plans | docs/architecture.md |
| 执行开发 | 按优先级逐步实现 | src/ 目录下源码 |

---

## Obsidian 使用指引

### 如何连接

如果你的 Obsidian 安装了 **Templater** 或 **Dataview** 插件，可以将以下模板作为快捷入口：

```
--{{dataview}}--
```

### 链接到各文档

| 文档 | 路径 | 用途 |
|------|------|------|
| 架构设计 | [[docs/architecture]] | 整体系统架构与模块划分 |
| API 设计 | [[docs/api-design]] | 各模块接口定义 |
| 开发标准 | [[docs/dev-standards]] | 编码规范、命名约定、测试要求 |
| 设计规范 | [[docs/superpowers/specs/*]] | brainstorming 产出的需求与设计文档 |
| 更新日志 | [[docs/changelog]] | 版本变更记录 |
| 每日开发记录 | 根目录 `dev-log/YYYY-MM-DD.md` | 当天完成事项与次日计划 |

### 每日开发记录

在根目录下创建 `dev-log/` 文件夹，每日自动生成一篇 Markdown 文件：

```
dev-log/
├── 2026-07-23.md
├── 2026-07-24.md
└── ...
```

每篇记录模板：

```markdown
## 📅 {{date:YYYY-MM-DD}}

### ✅ 今日完成
- [ ] 

### 📋 待办事项
- [ ]

### 💡 备注
- 
```

---

## 技术规范

- **Python 版本：** 3.10+（本项目使用 3.13）
- **UI 框架：** PySide6 >= 6.6
- **样式语言：** QSS（Qt Style Sheets），粉蓝渐变主题
- **配置格式：** JSON
- **构建工具：** PyInstaller
- **许可协议：** LGPL-2.1 (PySide6) + MIT (本项目代码)
