# Wallpace 开发进度

> 最后更新: 2026-07-24

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

## Phase 3: 调度器 ✅ COMPLETE (2026-07-24)
- [x] src/core/scheduler.py — 支持 daily_random / interval_minutes / manual 三种模式
  - `start()` / `stop()` / `pause()` / `resume()` / `trigger_now()`
  - `set_dependencies(library, wm)` 依赖注入
  - PySide6 QTimer 驱动
- [x] tests/test_scheduler.py — 16 个测试全部通过
- [x] 与 main.py 集成待做（见下方 Phase 3.5）

## Phase 4: 开机自启 ⬜ TODO
- [ ] 注册表写入 HKCU\Software\Microsoft\Windows\CurrentVersion\Run

## Phase 5: 文件监听 ⬜ TODO
- [ ] src/core/file_watcher.py — watchdog 或 Qt 内置 QFileSystemWatcher

## Phase 6: PyInstaller 打包 ⬜ TODO
- [ ] build.bat 完善（图标嵌入、资源打包）
- [ ] assets/icon.ico

---

## Git History

```
cee8642 fix(tests): test_set_and_get now uses tmp_config_dir fixture
9df81dd rename: project folder to 'wallpace'
ae4f25d fix(main,window): P0 — 修复 import 路径与窗口创建，应用可启动
f76ecd6 feat: Wallpace v0.1 - Initial project scaffold
```

## 关键修复记录
1. `theme.py` QSS 样式表改用 f-string 多行拼接，避免 heredoc 引号逃逸
2. `sidebar.py` SidebarButton._base_style() 从 f-string 改为 `.format()`，解决 QSS `{}` 冲突
3. `tray.py` 补充 QWidget 导入
4. `window.py` 统一使用 `from src.core.*` 而非 `from core.*`
5. `preview_card.py` 按钮只有文字，后续可加 QIcon

## 继续开发时必读

### Import 路径约定
- **core 模块用 `src.core.*`，app 模块用 `src.app.*`**（避免混用 `core.*` 和 `src.core.*`）
- main.py 已处理 `sys.path.insert(0, str(ROOT))`

### 环境
- Python 3.13, PySide6 6.11.1
- 工作目录: `D:\my_project\wallpace`
- 远程仓库: `https://github.com/HqJ-ban/Wallpace.git`

### 运行命令
```powershell
cd D:\my_project\wallpace
python -m pytest tests/ -v          # 全量测试
python src/main.py                  # 普通启动
python src/main.py --hidden         # 开机自启模式
python src/main.py --test           # 仅运行测试
```

### Next Tasks
1. **Phase 3.5**: 在 main.py 中实例化 Scheduler 并注入到 MainWindow 和 TrayIcon
2. **Phase 3.6**: 连接 MainWindow 的 switch/skip/favorite 按钮到 Scheduler.trigger_now()
3. **Phase 3.7**: 连接托盘菜单的"暂停/继续"到 Scheduler.pause()/resume()
4. Phase 4: 开机自启注册表
5. Phase 5: 文件监听器
6. Phase 6: PyInstaller 打包
