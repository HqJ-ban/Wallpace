# Wallpace — P0 修复 + 配置迁移 + 架构拆分

## 背景（用户问题）
用户报告：开启「开机自启」后，之前改过的所有设置都丢失了。

**根因**：旧 `Settings` 默认配置路径是 `Path.cwd() / ".wallspace.json"`，与当前工作目录（CWD）绑定。开机自启经注册表启动时 CWD 是 `C:\Windows\system32`，读不到项目目录里的配置 → 回退默认值 → 表现为「设置全没了」。

## 本次改动

### 1. 配置位置与迁移（P0 核心修复）— `src/core/settings.py`
- 默认配置路径改为 `%APPDATA%/.wallpace/config.json`（与 CWD 无关），彻底解决开机自启丢配置。
- 首次无默认配置时，自动从旧位置（CWD / 项目根的 `.wallspace.json`）平滑迁移，保证既有配置（尤其是 `image_directories`）不丢失。
- 新增 `log_level` 配置项、`set_many()`（批量设置只落盘一次）、更严格的 `_merge_with_defaults` 校验。

### 2. 收藏 / 跳过持久化（P0）— `src/core/image_library.py` + `src/app/window.py`
- `ImageLibrary.load_persisted_state(skip_list, favorites)`：启动即还原用户收藏与跳过列表。
- 收藏 / 跳过操作后通过 `_persist_skip_favorites()` 写回 `favorites` / `skip_list`，重启不丢。

### 3. 卡死自诊断（P0）— `src/main.py`
- 启用 `faulthandler`，卡死时把主线程堆栈 dump 到 `%APPDATA%/.wallpace/logs/traceback.log`。
- 日志级别按 `log_level` 配置与 `--debug` 参数调整。

### 4. 收藏 UI（用户诉求）— `src/app/pages/gallery_page.py`（新增）
- 左侧「图片库」整页升级为 `GalleryPage`：全部 / 收藏 / 已跳过 三档筛选 + 缩略图网格。
- 每张缩略图可：点击设壁纸、★ 收藏/取消、恢复（取消跳过）。缩略图走 `image_loader` 异步解码。
- 扫描完成后（`_apply_scan_results`）自动刷新该页面。

### 5. 架构拆分「拆分 window.py」（用户诉求）— `src/app/pages/`
- `gallery_page.py`：图片库整页（见上）。
- `settings_page.py`：设置页抽为 `SettingsPage`（视图层 + 纯 UI 辅助），业务逻辑经回调回 `MainWindow`。这样 `AutostartManager` / `Scheduler` 引用仍留在 `window.py`，兼容既有测试（特别是对 `src.app.window.AutostartManager` 的 monkeypatch）。

### 6. 测试隔离修复（关键）— `tests/conftest.py` + `tests/test_window.py`
- `test_settings.py` 用 `core.settings`、`test_window.py` 用 `src.core.settings`，二者在 `sys.modules` 是**不同模块对象**。只 patch 一个名字会导致另一套 `Settings()` 写进真实 `%APPDATA%/.wallplace/config.json`，污染用户配置。
- `tmp_config_dir` 现对 `("src.core.settings","core.settings")` **两个名字都**重定向 `DEFAULT_CONFIG_PATH` 并清空 `LEGACY_CONFIG_PATHS`；`main_window` fixture 也改为依赖 `tmp_config_dir`。

## 本机配置抢救
用户真实配置在旧 `D:/my_project/wallpace/.wallspace.json`（`interval_minutes:100`、`auto_start:false`、图片目录 `D:/my_project/source picture`）。已备份 appdata 旧配置为 `config.json.bak.*`，并把该文件复制进 `%APPDATA%/.wallpace/config.json`，确保用户设置在开机自启后不丢。

## 验证
- 全量测试：`QT_QPA_PLATFORM=offscreen C:/Programs/Python/Python313/python.exe -m pytest -q` → **110 passed / 1 skipped**（基线保持）。
- offscreen 实跑：用真实配置构建 `MainWindow`，扫描出 22 张图，`_gallery_page` / `_settings_page` 均存在，`quit` 正常；全量测试跑完 appdata 配置保持不变。
- 修复的两个 bug：`gallery_page.py` 漏 import `QHBoxLayout`；`_apply_scan_results` 未刷新新整页画廊。

## 改动文件
- `src/core/settings.py`（配置路径迁移 + 迁移逻辑 + log_level + set_many）
- `src/core/image_library.py`（`load_persisted_state`）
- `src/main.py`（faulthandler + 日志级别）
- `src/app/window.py`（GalleryPage/SettingsPage 接线、持久化、扫描刷新、设置页回调）
- `src/app/pages/gallery_page.py`（新增）
- `src/app/pages/settings_page.py`（新增）
- `tests/conftest.py`、`tests/test_window.py`（测试隔离）
