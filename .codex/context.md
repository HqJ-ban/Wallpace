# Wallpace 开发进度

> 最后更新: 2026-07-25 (Session 3)

## Session 3 更新摘要

### Bug 修复 ✅
- **scheduler.py**: `_do_daily_switch` 方法名不匹配导致 AttributeError → 统一改为 `_do_daily_timer`
- **日志权限**: main.py `logging.FileHandler` 在 Windows 沙箱下遇到 PermissionError，已确认目录存在且有用户权限（ICAcls），可能是之前会话残留锁。解决方法：在 Windows 上可手动删除旧 log 文件后重试。
- **完整启动链路验证通过**：Settings → ImageLibrary → WallpaperManager → Scheduler → MainWindow 全部创建成功，Scheduler.start() 正常运行。
- **测试套件**: 64 passed, 1 skipped — 全量验证通过

### 已知问题 ⚠️
- main.py 的 `logging.FileHandler(LOG_DIR / "wallpace.log")` 在有残留 Python 进程时会报 `Permission denied`。建议：将 FileHandler 改为 RotatingFileHandler 或包装 try-except fallback 到 StreamHandler。
- `image_directories` 在 config.json 中为空（`[]`），需用户在 Settings 页面添加图片扫描目录后软件才能正常工作。
- sidebar.py 导航按钮无图标，仅有中文文字
- window.py 的 `_set_active_button()` 目前是 pass，未真正联动 sidebar 高亮切换

---

## Phase 1: 核心模块 ✅ COMPLETE
- [x] src/core/settings.py — JSON 配置管理，含校验/默认值/损坏恢复
- [x] src/core/image_library.py — 图片扫描、随机选择、skip/favorite
- [x] src/core/wallpaper_manager.py — Windows API ctypes SystemParametersInfoW
- [x] tests/test_settings.py — 14 个测试
- [x] tests/test_image_library.py — 19 个测试
- [x] tests/test_wallpaper_manager.py — 4 个测试
- [x] pytest 结果: **37 passed, 1 skipped, 0 failed** (Phase 1)

## Phase 2: UI 实现 ✅ COMPLETE
- [x] src/__init__.py — __version__ = "0.1.0"
- [x] src/app/theme.py — QSS 主题引擎，粉蓝渐变配色常量 + ThemeManager 类
- [x] src/app/widgets/preview_card.py — 壁纸预览卡片组件（缩略图 + 文件名 + 三按钮）
- [x] src/app/sidebar.py — 图标侧边栏导航（品牌区 + 4 NavButton + 底部状态）
- [x] src/app/tray.py — 系统托盘右键菜单（换一张/暂停/打开窗口/退出）
- [x] src/app/window.py — 主窗口 B 方案布局（渐变顶栏 + 侧边栏 + QStackedWidget 四页面 + 托盘集成）
- [x] 所有 UI 模块 import 验证通过

### 已知待修（非阻塞）
- [ ] sidebar.py 导航按钮无图标，仅有中文文字
- [ ] window.py 的 `_set_active_button` 目前是 pass，未真正联动 sidebar 高亮切换

## Phase 2.5: 主程序集成 ✅ COMPLETE (2026-07-24)
- [x] src/main.py — 完整启动链路：Settings → ImageLibrary → WallpaperManager → MainWindow
- [x] Window 创建不再被注释，`--hidden` / `--test` 参数正常运作

## Phase 3: 调度器 ✅ COMPLETE (2026-07-25)
- [x] src/core/scheduler.py — 支持 daily_random / interval_minutes / manual 三种模式
  - `start()` / `stop()` / `pause()` / `resume()` / `trigger_now()`
  - `set_dependencies(library, wm)` 依赖注入
  - PySide6 QTimer 驱动
  - **已修复**: `_do_daily_timer` 方法名统一（原 `_do_daily_switch`）
- [x] tests/test_scheduler.py — 16 个测试全部通过
- [x] main.py 中 Scheduler 实例化、注入、启动链路完整

## Phase 4: 开机自启 ✅ COMPLETE (2026-07-25)
- [x] src/core/autostart_registry.py — AutostartManager 类，HKCU 注册表读写（enable/disable/is_enabled）
- [x] tests/test_autostart_registry.py — 10 个测试
- [x] Window Settings 页面集成 Autostart 开关 UI
- [x] main.py 中根据 `--hidden` 参数决定是否启用 autostart
- ⚠️ Windows 沙箱环境无法验证注册表写入，需在用户机器上实际测试

## Critical Bug Fixes (2026-07-25 Session 3b)
- **image_library.py ext normalization**: Added .lstrip('.') in __init__ to strip leading dot from extension strings (e.g. .png -> png). Before this fix, scan() generated glob patterns like **/*..png (double-dot) matching zero files. Settings stores extensions WITH dots; ImageLibrary.__init__ was supposed to strip them but didn't. Now all 22 source images scan correctly.
- **scheduler.py method name mismatch**: _do_daily_timer callback reference fixed to match actual method name _do_daily_timer.

## 图片扫描配置 ✅ (2026-07-25)
- Config file: D:/my_project/wallpace/.wallpace.json
- Source directory: D:\my_project\source picture — 22 images (21 .png + 1 .jpg)
- Extensions: [.jpg, .jpeg, .png, .bmp, .gif, .webp]

---

## Phase 5: 文件监听 ⬜ TODO
- [ ] src/core/file_watcher.py — watchdog 或 Qt 内置 QFileSystemWatcher

## Phase 6: PyInstaller 打包 ⬜ TODO
- [ ] build.bat 完善（图标嵌入、资源打包）
- [ ] assets/icon.ico

---

## Git History (master branch)

```
d1e1fd3 feat(main,window,scheduler): 完整集成 Scheduler 到启动链路
cee8642 fix(tests): test_set_and_get now uses tmp_config_dir fixture
9df81dd rename: project folder to 'wallpace'
ae4f25d fix(main,window): P0 — 修复 import 路径与窗口创建，应用可启动
f76ecd6 feat: Wallpace v0.1 - Initial project scaffold
```

> Note: 当前可能有未推送的新 commit（Phase 4 开机自启相关）。先做 git status 确认。

## 关键修复记录
1. `theme.py` QSS 样式表改用 f-string 多行拼接，避免 heredoc 引号逃逸
2. `sidebar.py` SidebarButton._base_style() 从 f-string 改为 `.format()`，解决 QSS `{}` 冲突
3. `tray.py` 补充 QWidget 导入
4. `window.py` 统一使用 `from src.core.*` 而非 `from core.*`
5. `preview_card.py` 按钮只有文字，后续可加 QIcon
6. **scheduler.py** `_do_daily_switch` → `_do_daily_timer` 命名统一（本次 session）
7. **main.py** logging path 从 `ROOT / "logs"` 改为 `Path.home() / ".wallpace" / "logs"` 解决沙箱权限

## 继续开发时必读

### Import 路径约定
- **core 模块用 `src.core.*`，app 模块用 `src.app.*`**（避免混用 `core.*` 和 `src.core.*`）
- main.py 已处理 `sys.path.insert(0, str(ROOT))`

### 环境
- Python 3.13, PySide6 6.11.1 (LGPL)
- 工作目录: `D:\my_project\wallpace`
- 远程仓库: `https://github.com/HqJ-ban/Wallpace.git`

### 运行命令
```powershell
cd D:\my_project\wallpace
python -m pytest tests/ -v          # 全量测试
python src/main.py                  # 普通启动（需显示窗口）
python src/main.py --hidden         # 开机自启模式（隐藏主窗口）
python src/main.py --test           # 仅运行 unittest 测试
```

### Next Tasks (优先级排序)
1. **Git commit & push** — 确认 Phase 4 相关文件已提交并推送到 GitHub
2. **Phase 5: 文件监听器** (`src/core/file_watcher.py`) — 检测新增/删除图片，自动刷新 library
3. **Phase 6: PyInstaller 打包** (`build.bat`, icon.ico) — 生成单文件 .exe
4. 非阻塞 UI polish: sidebar 按钮加图标, `_set_active_button` 联动
