# 架构设计文档

## 系统架构图

```
┌─────────────────────────────────────────────────────┐
│                     Wallpace App                      │
├──────────┬──────────────────────┬───────────────────┤
│ UI 层    │   业务逻辑层         │   系统交互层       │
│ src/app/ │   src/core/          │   src/utils/      │
├──────────┤                      ├───────────────────┤
│ MainWindow│                      │ WallpaperManager │
│ TrayIcon │◄──── 信号/槽 ───►   │ ImageLibrary     │
│ Widgets  │                      │ Scheduler        │
└──────────┘                      ├───────────────────┤
                                  │ Settings         │
                                  └───────────────────┘
                                          │
                                          ▼
                          ┌─────────────────────────────┐
                          │      Windows API (ctypes)    │
                          │  - SystemParametersInfoW     │
                          │  - winreg (开机自启)         │
                          └─────────────────────────────┘
```

---

## 模块职责

### 1. `src/main.py` — 入口点
- 创建 QApplication 实例
- 初始化主窗口
- 启动事件循环
- 处理命令行参数（开机启动模式等）

### 2. `src/app/window.py` — 主窗口
- 继承 `QWidget`
- 包含：顶部栏、图标侧边栏、内容区、底部栏
- 管理页面切换（当前壁纸 / 图片库 / 时间表 / 设置）
- 不直接调用 Windows API，通过信号与 core 层通信

### 3. `src/app/tray.py` — 系统托盘
- 最小化时隐藏窗口，显示托盘图标
- 右键菜单提供：换一张、暂停/继续、打开设置、退出
- 托盘点击可快速切换壁纸

### 4. `src/core/wallpaper_manager.py` — 壁纸管理器
- **职责：** 将指定图片设置为 Windows 桌面壁纸
- **核心方法：** `set_wallpaper(image_path: str) -> bool`
- 使用 ctypes 调用 `SystemParametersInfoW(SPI_SETDESKWALLPAPER)`
- 返回操作成功/失败状态

### 5. `src/core/image_library.py` — 图片库管理
- **职责：** 扫描、加载、管理壁纸图片
- **核心方法：**
  - `scan(directory: str) -> List[str]`: 递归扫描目录获取图片路径列表
  - `watch(directory: str, callback: Callable) -> FileSystemWatcher`: 监听文件夹变更
  - `get_random() -> Optional[str]`: 随机返回一张图片路径
  - `skip(path: str) -> None`: 标记为跳过（加入黑名单）
  - `favorite(path: str) -> None`: 加入收藏
  - `list_available() -> List[str]`: 获取所有可用图片（排除已跳过的）

### 6. `src/core/scheduler.py` — 定时调度器
- **职责：** 控制壁纸切换的时机
- **核心方法：**
  - `start() -> None`: 启动调度
  - `stop() -> None`: 停止调度
  - `pause() -> None`: 临时暂停
  - `trigger_now() -> None`: 立即触发一次
  - `is_active() -> bool`: 是否正在运行
- **切换策略支持：**
  - 每日固定时间（默认 08:00）
  - 自定义时间间隔（可选）
  - 手动触发（由用户主动调用）

### 7. `src/core/settings.py` — 配置管理
- **职责：** 读取、保存、验证用户配置
- **配置文件：** `.wallpace.json`（项目根目录）
- **默认值：** 内置 fallback 配置
- **核心方法：**
  - `load() -> dict`: 加载配置
  - `save(data: dict) -> None`: 保存配置
  - `get(key: str, default=None) -> Any`: 获取单项
  - `set(key: str, value: Any) -> None`: 修改单项
  - `validate() -> List[str]`: 验证配置合法性

---

## 数据流

```
用户操作 (UI) → 信号发射 → 业务逻辑 (core) → 系统调用 → 结果回传 → UI 更新
```

1. 用户点击"换一张"按钮
2. `MainWindow` 发射信号 `switch_requested()`
3. `Scheduler.trigger_now()` 被调用
4. `ImageLibrary.get_random()` 返回图片路径
5. `WallpaperManager.set_wallpaper(path)` 设置壁纸
6. 操作成功 → 发射 `switched(path)` 信号
7. `MainWindow` 接收信号 → 更新预览图和底部栏信息

---

## 关键类设计

### ImageLibrary

```python
class ImageLibrary:
    def __init__(self, directories: List[str], extensions: List[str] = None):
        ...

    def scan(self) -> List[str]:
        """扫描所有配置的目录，返回可用图片路径列表。"""
        ...

    def get_random(self) -> Optional[str]:
        """从可用图片中随机选一张（排除已跳过）。"""
        ...

    def skip(self, path: str) -> None:
        """将指定图片加入跳过列表。"""
        ...

    def favorite(self, path: str) -> None:
        """将指定图片加入收藏。"""
        ...

    def watch_directories(self, callback: Callable[[str, str], None]) -> None:
        """监听目录变更，新增文件时调用 callback(path)"""
        ...
```

### WallpaperManager

```python
class WallpaperManager:
    def set_wallpaper(self, image_path: str) -> bool:
        """使用 ctypes 调用 Windows API 设置壁纸。"""
        ...
```

### Scheduler

```python
class Scheduler:
    def __init__(self, settings: dict):
        self._daily_time = settings.get('daily_time', '08:00')
        self._interval = settings.get('interval_minutes')
        self._timer: Optional[QTimer] = None
        ...

    def start(self, on_switch: Callable) -> None:
        """启动定时任务。on_switch 是切换回调。"""
        ...

    def trigger_now(self, on_switch: Callable) -> None:
        """立即触发一次切换。"""
        ...

    def pause(self) -> None:
        """暂停定时任务（不删除定时器）。"""
        ...

    def resume(self) -> None:
        """恢复已暂停的任务。"""
        ...
```

---

## 技术选型理由

| 决策 | 选择 | 理由 |
|------|------|------|
| 壁纸设置方式 | ctypes + SPI_SETDESKWALLPAPER | 最轻量、无需额外依赖 |
| 文件监听 | watchdog 或 PySide6 QFileSystemWatcher | PySide6 自带，零依赖 |
| 配置存储 | JSON | Python 原生支持，可人工编辑 |
| 打包工具 | PyInstaller | 社区成熟，单 exe 输出 |
| UI 框架 | PySide6 (LGPL) | 免费、可闭源商用、Qt 生态完善 |
