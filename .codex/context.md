# Wallpace 开发进度

> 最后更新: 2026-07-26 (Session 4 - UI Polish)

## Session 4 更新摘要

### 底部状态栏 ✅
- **src/app/window.py**: 新增 28px 底部状态栏，显示图片库目录、收藏数、调度器状态、版本号
- `update_bottom_bar()` 方法在 gallery 刷新时调用
- `update_top_status()` 方法显示顶栏徽章（已启用/已暂停 + 切换频率）

### UI Polish 打磨 ✅ (对照 mockup detail-view.html)
1. **顶栏状态徽章**: 从空字符串改为实时显示 scheduler 状态（模式 + 下次切换时间）
2. **预览卡片尺寸**: 高度从 300px → 340px，更沉浸感
3. **预览卡片叠加层**: 渐变优化为三段（透明→柔和暗→强暗），更自然的过渡
4. **索引标签**: 从粉色小 badge 改为白色大号字体 + 半透明白底圆角
5. **操作按钮行**: 从三个小文字按钮改为 mockup 风格大按钮（"跳过·不喜" / "收藏·到精选" / "换一张"渐变）
6. **Info Grid**: 中间"下次切换"卡片使用粉蓝渐变高亮，其他保持灰色背景
7. **侧边栏收藏按钮**: ActionButton 支持双色图标 toggle（☆→★），与 _handle_favorite 联动
8. **修复 property 访问**: `favorites`, `total_count`, `directory_count` 是 @property 而非方法

### Bug 修复
- **scheduler.py timedelta**: 原因为 `datetime.timedelta` 导入错误，需用 `from datetime import timedelta` 或改用 `datetime.timedelta` 的正确引用方式（此 bug 已在之前 sessions 修复）
- **favorites() vs favorites**: ImageLibrary.favorites 是 @property 返回 list，不能用 () 调用
- **total_count() vs total_count**: 同样是 @property

## Phase 进度概览

| Phase | 内容 | 状态 |
|-------|------|------|
| Phase 1 | Core modules (settings, image_library, wallpaper_manager, scheduler) | ✅ Complete |
| Phase 2 | UI — narrow icon sidebar + preview card + gallery + top/bottom bars | ✅ Complete |
| Phase 2.5 | Main integration (main.py startup chain) | ✅ Complete |
| Phase 3 | Scheduler with 3 modes (daily, interval, manual) | ✅ Complete |
| Phase 4 | Autostart registry (Windows HKCU) | ✅ Complete |
| Phase 4.5 | UI Polish & mockup alignment | ✅ Complete (this session) |
| Phase 5 | File Watcher (`src/core/file_watcher.py`) | ⬜ TODO |
| Phase 6 | PyInstaller packaging (`build.bat`, icon.ico) | ⬜ TODO |

## Git History (master branch)

```
<latest> feat(ui): add bottom status bar with library info  ← current working tree clean
... d1e1fd3 ...
... cee8642 ...
... 9df81dd rename: project folder to 'wallpace'
... ae4f25d fix(main,window): P0 — 修复 import 路径与窗口创建
... f76ecd6 feat: Wallpace v0.1 - Initial project scaffold
```

## 图片扫描配置
- Config file: `~/.wallpace.json`
- Source directory: `D:\my_project\source picture` — 22 images (21 .png + 1 .jpg)
- Extensions: [.jpg, .jpeg, .png, .bmp, .gif, .webp]

## 待办事项 (优先级排序)

### UI Remaining
1. **Settings slide-in panel** — 将设置页从 QStackedWidget 页面改为右侧滑入面板 (QFrame overlay with animation)
2. **Gallery interaction** — 点击缩略图 → 更新预览卡片
3. **Sidebar nav icons** — 考虑用 Qt Icon/FontAwesome 替代 Emoji 字符

### Feature Modules
4. **Phase 5: File Watcher** (`src/core/file_watcher.py`) — 检测新增/删除图片，自动刷新 library
5. **Phase 6: PyInstaller packaging** — 生成单文件 .exe

### Housekeeping
6. **Git push** — 需要新的 GitHub PAT token（之前的可能已过期）
7. 清理 `src/app/tray.py` 中未使用的 imports（如果有）

## Tests
- **63 passed, 1 skipped** (sandbox PermissionError skip is expected)
- All core + UI import tests pass

## Key Files
- [src/app/window.py](D:\my_project\wallpace\src\app\window.py) — MainWindow
- [src/app/sidebar.py](D:\my_project\wallpace\src\app\sidebar.py) — 60px icon sidebar
- [src/app/widgets/preview_card.py](D:\my_project\wallpace\src\app\widgets\preview_card.py) — Preview widget
- [src/app/theme.py](D:\my_project\wallpace\src\app\theme.py) — Theme/QSS engine
- [src/main.py](D:\my_project\wallpace\src\main.py) — Entry point
- [D:/my_project/mockups/detail-view.html](D:/my_project/mockups/detail-view.html) — Visual reference

## Import Conventions
- Core modules: `from src.core.*`
- App modules: `from src.app.*`
- main.py handles `sys.path.insert(0, str(ROOT))`

## Running Commands
```powershell
cd D:\my_project\wallpace
python -m pytest tests/ --basetemp=C:/tmp/wallpace-pytest-temp -v   # tests
python src/main.py                                                   # visible window
python src/main.py --hidden                                          # tray mode (hidden window)
python src/main.py --test                                            # unittest only
```

## Environment
- Python 3.13, PySide6 6.11.1 (LGPL)
- Working dir: `D:\my_project\wallpace`
- Remote: `https://github.com/HqJ-ban/Wallpace.git`
- Sandbox: .git is read-only; git commands need escalation
