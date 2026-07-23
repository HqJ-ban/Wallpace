# Wallpace — Implementation Plan

> 项目路径: `D:\my_project\Desktop_wallpaper`  
> 技术栈: Python 3.10+ / PySide6 (LGPL) / Windows  
> 最后更新: 2026-07-23

---

## 快速索引

| 文件 | 用途 | 何时读取 |
|------|------|----------|
| `README.md` | 项目总纲、功能清单、目录结构 | **每次会话必读** |
| `docs/dev-standards.md` | 编码规范、QSS 主题、Git 规范 | 首次阅读，后续按需查阅 |
| `docs/architecture.md` | 架构图、模块职责、数据流 | 首次阅读，实现跨模块时必读 |
| `docs/api-design.md` | 所有核心类接口定义 | **实现新模块前必读** |
| `context.md` | 本文件 — 当前阶段进度与计划 | **每个会话开头读** |
| `dev-log/YYYY-MM-DD.md` | 每日开发记录 | 读最新一篇，了解上次做了什么 |

---

## 已完成 ✅

### Phase 0: 需求与设计（已完成）
- [x] 5 轮需求问答确认（图片库、切换策略、UI、多显示器、打包）
- [x] UI 草图 A/B/C 三方案 + 选定 B（图标侧边栏 + 粉蓝渐变）
- [x] UI 细节深化（预览区、操作按钮、设置面板、底部栏）
- [x] mockups/layout-options.html — 三个布局方案对比
- [x] mockups/detail-view.html — B 方案完整页面
- [x] README.md — 项目总纲
- [x] docs/dev-standards.md — 开发标准
- [x] docs/architecture.md — 架构设计
- [x] docs/api-design.md — API 接口定义

### Phase 1: 环境搭建（进行中）
- [x] 创建 `src/app/`, `src/core/`, `src/utils/` 包
- [x] requirements.txt（PySide6, watchdog）
- [x] pyproject.toml（项目元数据）
- [x] .gitignore
- [x] build.bat（PyInstaller 打包脚本）
- [x] src/main.py（入口点骨架，含 `--hidden` 启动参数支持）

---

## 待完成 🚧

### Phase 1 剩余任务

1. **`src/core/settings.py`** — 配置管理
   - 参考 `docs/api-design.md` 第 4 节
   - 实现 load/save/get/set/reset/validate
   - 默认配置文件 `.wallpace.json`

2. **`src/core/image_library.py`** — 图片库管理
   - 参考 `docs/api-design.md` 第 2 节
   - scan() — 递归扫描 JPG/PNG/WebP/BMP
   - get_random() — 排除 skip_list，随机选一张
   - skip()/favorite()/list_available()

3. **`src/core/wallpaper_manager.py`** — 壁纸设置
   - 参考 `docs/api-design.md` 第 1 节
   - set_wallpaper(image_path) → bool
   - 使用 ctypes 调用 SystemParametersInfoW

4. **`tests/` 单元测试** — 以上三个模块各写对应测试

### Phase 2: UI 实现（下一阶段）

- [ ] `src/app/window.py` — 主窗口（B 方案图标侧边栏）
- [ ] `src/app/tray.py` — 系统托盘右键菜单
- [ ] `src/app/theme.py` — 粉蓝渐变 QSS 样式
- [ ] `src/app/widgets/` — 缩略图、信息卡片等组件

### Phase 3: 调度与集成

- [ ] `src/core/scheduler.py` — 定时切换
- [ ] 主程序集成（main.py 组装各模块）
- [ ] 开机自启注册表写入

### Phase 4: 文件监听

- [ ] `src/core/file_watcher.py` — 检测图片新增/删除

### Phase 5: 打包发布

- [ ] build.bat 完善（图标嵌入、资源打包）
- [ ] 创建 assets/icon.ico

---

## 开发注意事项

1. **不要跳步** — 先写完 core/ 模块再写 UI
2. **测试先行** — 写完模块立即写对应单测
3. **记录日志** — 每天在 `dev-log/` 下写当日记录
4. **一次一个 PR** — 代码变更保持小且聚焦
5. **中文注释** — 所有代码注释和 UI 文本用中文

## PyInstaller 注意事项

- `--windowed` 模式：不显示控制台窗口
- `--onefile`：打包成单个 exe
- 资源文件需要用 `sys._MEIPASS` 访问运行时临时目录
