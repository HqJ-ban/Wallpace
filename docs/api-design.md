# API 设计文档

## Core 模块接口定义

### 1. WallpaperManager

```python
class WallpaperManager:
    """设置 Windows 桌面壁纸。"""

    def set_wallpaper(self, image_path: str) -> bool:
        """将指定图片设置为系统壁纸。
        
        Args:
            image_path: 图片的绝对路径。
            
        Returns:
            True 表示设置成功，False 表示失败。
        """
        ...

    def get_current_wallpaper(self) -> Optional[str]:
        """获取当前壁纸文件路径（从注册表读取）。
        
        Returns:
            当前壁纸路径，如果无法获取则返回 None。
        """
        ...
```

### 2. ImageLibrary

```python
class ImageLibrary:
    """管理壁纸图片库的扫描、筛选和随机选择。"""

    def __init__(self, directories: List[str], extensions: Optional[List[str]] = None):
        ...

    def scan(self) -> List[str]:
        """递归扫描所有配置的目录。
        
        Returns:
            所有可用图片的绝对路径列表。
        """
        ...

    def list_available(self) -> List[str]:
        """获取所有可用图片（排除已跳过和无效的）。
        
        Returns:
            可用图片路径列表。
        """
        ...

    def get_random(self) -> Optional[str]:
        """随机选择一张可用图片。
        
        Returns:
            图片路径，如果无可用的则返回 None。
        """
        ...

    def skip(self, path: str) -> None:
        """标记某张图片为"不喜欢"，后续随机不会选中。
        
        Args:
            path: 要跳过的图片路径。
        """
        ...

    def unskip(self, path: str) -> None:
        """从跳过列表中移除某张图片。
        
        Args:
            path: 要取消跳过的图片路径。
        """
        ...

    def favorite(self, path: str) -> None:
        """将图片加入收藏列表。
        
        Args:
            path: 要收藏的图片路径。
        """
        ...

    def unfavorite(self, path: str) -> None:
        """取消收藏。"""
        ...

    def get_favorite_list(self) -> List[str]:
        """获取收藏列表。"""
        ...

    def reload(self) -> None:
        """重新扫描图片库（监听器变更后调用）。"""
        ...
```

### 3. Scheduler

```python
class Scheduler:
    """控制壁纸切换的时间和触发方式。"""

    SWITCH_MODE_DAILY = "daily_random"
    SWITCH_MODE_INTERVAL = "interval_minutes"
    SWITCH_MODE_MANUAL = "manual"

    def __init__(self, mode: str = SWITCH_MODE_DAILY, 
                 daily_time: str = "08:00",
                 interval_minutes: Optional[int] = None):
        ...

    def start(self, on_switch: Callable[[str], None]) -> None:
        """启动定时任务。
        
        Args:
            on_switch: 切换完成后的回调函数，参数为新壁纸路径。
        """
        ...

    def trigger_now(self, on_switch: Callable[[str], None]) -> None:
        """立即触发一次切换。
        
        Args:
            on_switch: 回调函数。
        """
        ...

    def pause(self) -> None:
        """暂停定时任务。"""
        ...

    def resume(self) -> None:
        """恢复已暂停的任务。"""
        ...

    def stop(self) -> None:
        """停止并销毁定时器。"""
        ...

    def is_active(self) -> bool:
        """是否正在运行。"""
        ...

    def is_paused(self) -> bool:
        """是否被暂停。"""
        ...
```

### 4. Settings

```python
class Settings:
    """管理应用配置文件的读写。"""

    CONFIG_FILE = ".wallpace.json"

    def __init__(self, config_path: Optional[str] = None):
        ...

    def load(self) -> dict:
        """加载配置文件。如果不存在则返回默认值。"""
        ...

    def save(self, data: dict) -> None:
        """保存配置到文件。"""
        ...

    def get(self, key: str, default=None):
        """获取指定配置项的值。"""
        ...

    def set(self, key: str, value) -> None:
        """设置单个配置项并自动保存。"""
        ...

    def reset_to_defaults(self) -> dict:
        """重置为默认配置。"""
        ...

    @staticmethod
    def validate(data: dict) -> List[str]:
        """验证配置合法性。
        
        Returns:
            错误信息列表，为空则配置合法。
        """
        ...
```

---

## UI 层接口定义

### 5. MainWindow

```python
class MainWindow(QWidget):
    """主窗口，包含侧边栏导航 + 内容区 + 底部状态栏。"""

    # 信号
    switch_requested = Signal()           # 用户请求换壁纸
    next_requested = Signal()             # 点击"下一个"按钮
    favorite_requested = Signal(str)      # 收藏某张图片
    settings_opened = Signal()            # 打开设置面板
    minimize_requested = Signal()         # 最小化到托盘

    def __init__(self, settings: Settings, scheduler: Scheduler):
        ...

    def show(self):
        """显示窗口。"""
        ...

    def hide_and_tray(self):
        """隐藏窗口，最小化到托盘。"""
        ...

    def update_wallpaper_info(self, path: str, index: int):
        """更新当前壁纸信息（预览图、文件名、序号）。"""
        ...

    def refresh_gallery(self, images: List[str]):
        """刷新缩略图预览。"""
        ...
```

### 6. TrayIcon

```python
class TrayIcon(QSystemTrayIcon):
    """系统托盘图标和右键菜单。"""

    def __init__(self, parent: QMainWindow, settings: Settings, scheduler: Scheduler):
        super().__init__()
        ...

    def create_menu(self) -> QMenu:
        """创建托盘右键菜单。"""
        # 换一张
        # 暂停 / 继续
        # 打开设置
        # 退出
        ...
```

---

## 数据模型

### WallpaperInfo（用于 UI 展示）

```python
@dataclass
class WallpaperInfo:
    """单张壁纸的信息。"""
    path: str                        # 完整路径
    filename: str                    # 文件名（不含路径）
    directory: str                   # 所属目录
    index: int                       # 全局索引
    size_kb: float                   # 文件大小 (KB)
    dimensions: Optional[tuple]      # (宽, 高), 可能为 None（读取失败时）
    added_at: datetime               # 添加到库的时间
```

### AppSettings（配置对象）

```python
@dataclass
class AppSettings:
    """应用完整配置。"""
    image_directories: List[str]     = field(default_factory=list)
    extensions: List[str]            = field(default_factory=["jpg", "jpeg", "png", "webp"])
    switch_mode: str                 = "daily_random"
    daily_time: str                  = "08:00"
    interval_minutes: Optional[int]  = None
    skip_list: List[str]             = field(default_factory=list)
    favorites: List[str]             = field(default_factory=list)
    enable_notifications: bool       = True
    auto_start: bool                 = True
    minimize_to_tray: bool           = True
```
