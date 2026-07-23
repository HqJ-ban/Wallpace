# Wallpace 开发进度

> 最后更新: 2026-07-23

## Phase 1: 核心模块 ✅ COMPLETE
- [x] src/core/settings.py — JSON 配置管理，含校验/默认值/损坏恢复
- [x] src/core/image_library.py — 图片扫描、随机选择、skip/favorite
- [x] src/core/wallpaper_manager.py — Windows API ctypes SystemParametersInfoW
- [x] tests/test_settings.py — 14 个测试
- [x] tests/test_image_library.py — 19 个测试
- [x] tests/test_wallpaper_manager.py — 4 个测试
- [x] pytest 结果: **37 passed, 1 skipped, 0 failed**

## Phase 2: UI 实现 ✅ COMPLETE (本轮 2026-07-23 重写)
> 上一轮对话因旧 UI 文件被 PowerShell Set-Content 写入转义字符（`\"\"\"`）导致全不可导入，已删除后从零重建全部 6 个源文件。

- [x] src/__init__.py — __version__ = "0.1.0"
- [x] src/app/__init__.py — app 包初始化
- [x] src/app/theme.py — QSS 主题引擎，粉蓝渐变配色常量 + ThemeManager 类
- [x] src/app/widgets/__init__.py — widgets 包导出 PreviewCardWidget
- [x] src/app/widgets/preview_card.py — 壁纸预览卡片组件（缩略图 + 文件名 + 三按钮）
- [x] src/app/sidebar.py — 图标侧边栏导航（品牌区 + 4 NavButton + 底部状态），使用 .format() 避免 f-string/QSS `}` 冲突
- [x] src/app/tray.py — 系统托盘右键菜单（换一张/暂停/打开窗口/退出），补充 QWidget 导入
- [x] src/app/window.py — 主窗口 B 方案布局（渐变顶栏 + 侧边栏 + QStackedWidget 四页面 + 托盘集成）
- [x] 所有 6 个 UI 模块 import 验证通过

### 已知待修（非阻塞）
- [ ] sidebar.py 导航按钮无图标，仅有中文文字
- [ ] window.py 的 `_set_active_button` 目前是 pass，未真正联动 sidebar 的高亮切换

## Phase 2.5: 主程序集成 🔴 P0 — NEXT TASK
- [ ] src/main.py 取消 MainWindow 注释，完成完整启动链路
- [ ] 运行 `python src/main.py` 实际验证窗口能弹出且无崩溃

## Phase 3: 调度与集成
- [ ] src/core/scheduler.py — 定时切换（daily_random / interval_minutes）
- [ ] main.py 组装各模块完整工作流

## Phase 4: 开机自启
- [ ] 注册表写入 HKCU\Software\Microsoft\Windows\CurrentVersion\Run

## Phase 5: 文件监听
- [ ] src/core/file_watcher.py — watchdog 或 Qt 内置 QFileSystemWatcher

## Phase 6: PyInstaller 打包
- [ ] build.bat 完善（图标嵌入、资源打包）
- [ ] assets/icon.ico

---

## 文件清单（2026-07-23 更新后）

```
src/
├── __init__.py                # v0.1.0
├── main.py                    # 🔴 需改：启用 MainWindow
├── app/
│   ├── __init__.py
│   ├── theme.py               # QSS 主题引擎 + 配色常量
│   ├── sidebar.py             # 左侧导航栏
│   ├── tray.py                # 系统托盘
│   └── window.py              # 主窗口
│   └── widgets/
│       ├── __init__.py
│       └── preview_card.py    # 预览卡片
├── core/
│   ├── settings.py            # 配置管理
│   ├── image_library.py       # 图片库
│   ├── wallpaper_manager.py   # 壁纸设置
│   └── scheduler.py           # 待写
└── utils/
    └── __init__.py

tests/
├── conftest.py
├── test_settings.py           # 14 tests
├── test_image_library.py      # 19 tests
└── test_wallpaper_manager.py  # 4 tests
```

## 关键修复记录
1. `theme.py` 中 QSS 样式表改用 f-string 多行拼接，避免 heredoc 引号逃逸
2. `sidebar.py` 的 SidebarButton._base_style() 从 f-string 改为 `.format()`，解决 QSS `{}` 与 Python f-string `}` 冲突
3. `tray.py` 补充了 QWidget 导入（之前缺失导致 NameError）
4. `window.py` 统一使用 `from src.core.*` 而非 `from core.*`，避免 path 混乱
5. `preview_card.py` 按钮只有文字，后续可加 QIcon

## 继续开发时必读
- 运行命令: `cd D:\my_project\Desktop_wallpaper && python -c "import sys; sys.path.insert(0, 'src'); from src.app.window import MainWindow; print('OK')"`
- import 路径约定：**core 模块用 `src.core.*`，app 模块用 `src.app.*`**（避免混用 `core.*` 和 `src.core.*`）
- 环境: Python 3.13, PySide6 6.11.1 (已安装)
- 下一步优先做: 修改 main.py 启用 MainWindow → 运行验证 → 再推进 scheduler
