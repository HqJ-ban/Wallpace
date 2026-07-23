# 开发执行标准

## 1. Python 编码规范

### 1.1 基本约定
- 遵循 PEP 8 编码风格
- 所有文件使用 UTF-8 编码
- 行宽不超过 100 字符
- 使用 Black 格式化代码（如安装）

### 1.2 命名约定
| 类型 | 规则 | 示例 |
|------|------|------|
| 模块/包 | snake_case | `wallpaper_manager.py` |
| 类名 | CamelCase | `WallpaperManager` |
| 函数/方法 | snake_case | `set_wallpaper()` |
| 变量 | snake_case | `image_path`, `is_enabled` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| 私有成员 | _prefix | `_cache`, `_load_config()` |

### 1.3 类型注解
- 所有公共函数必须标注参数和返回值类型
- 复杂类型使用 typing 模块
- 可选参数使用 Optional[T] 或 T | None (Python 3.10+)

```python
from typing import Optional, List

def scan_images(directory: str) -> List[str]:
    """扫描目录中的所有图片文件。"""
    ...

def load_settings(path: Optional[str] = None) -> dict:
    """加载设置，默认为默认路径。"""
    ...
```

### 1.4 文档字符串
- 所有公共类、函数必须有 docstring
- 使用 Google 风格格式

```python
class ImageLibrary:
    """图片库管理器，负责扫描、加载和管理壁纸图片。

    Attributes:
        directory: 图片库根目录路径。
        extensions: 支持的图片扩展名列表。
    """

    def __init__(self, directory: str, extensions: Optional[List[str]] = None):
        """初始化图片库。

        Args:
            directory: 图片库文件夹路径。
            extensions: 支持的扩展名，默认为 ['jpg', 'jpeg', 'png', 'webp']。
        """
        ...
```

---

## 2. PySide6 开发标准

### 2.1 架构模式
- **MVC 分离：** UI 逻辑与业务逻辑分开
- UI 层 (`src/app/`) 只负责展示和用户交互
- 业务层 (`src/core/`) 不依赖任何 Qt 组件
- 通过信号/槽机制连接两层

### 2.2 样式表 (QSS)
- 全局主题定义在 `src/app/theme.py`
- 粉蓝渐变是主色调：
  - 粉红: `#fce4ec`, `#f8bbd0`, `#e91e63`
  - 蓝: `#bbdefb`, `#e3f2fd`, `#5c6bc0`, `#1a237e`
- 渐变色通过 `QLinearGradient` 实现
- 圆角统一为 8-12px

### 2.3 组件规范
- 自定义组件继承自 `QWidget`
- 布局使用 `QVBoxLayout` / `QHBoxLayout` / `QGridLayout`
- 避免硬编码尺寸，使用 `sizePolicy` 和 `stretch`
- Tooltip 始终为中文

### 2.4 托盘图标
- 图标文件放在 `assets/icons/`
- Windows 兼容格式：ICO (16x16, 32x32, 48x48, 256x256)
- 右键菜单使用 `QMenu`，选项从上到下排列

---

## 3. 文件结构规范

### 3.1 目录职责
| 目录 | 职责 | 不允许 |
|------|------|--------|
| `src/app/` | UI 相关（窗口、组件、样式） | 包含业务逻辑 |
| `src/core/` | 核心业务（壁纸设置、调度器、图片库） | 包含 Qt 导入 |
| `src/utils/` | 纯工具函数 | 包含业务规则 |
| `tests/` | 单元测试 | 集成到 src/ |
| `docs/` | 项目文档 | 放代码 |
| `assets/` | 图标、图片资源 | 放代码 |

### 3.2 模块大小限制
- 单个源文件不超过 300 行
- 超过则拆分到子模块
- 单个函数不超过 30 行（测试函数除外）

---

## 4. Git 提交规范

### 4.1 Commit Message
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型：**
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档变更
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具变更

**示例：**
```
feat(ui): 添加主窗口和图标侧边栏

- 实现 B 方案图标侧边栏布局
- 添加粉蓝渐变顶部栏
- 底部自定义状态栏
```

### 4.2 分支策略
- `main` — 稳定版本
- `dev` — 开发分支（日常开发在此进行）
- `feature/*` — 功能分支（如 `feature/tray-menu`）
- `hotfix/*` — 紧急修复

---

## 5. 日志规范

```python
import logging

logger = logging.getLogger(__name__)

# 级别使用
logger.debug("详细调试信息")      # 开发阶段查看
logger.info("壁纸已切换到 %s", path)    # 正常操作记录
logger.warning("图片扫描发现 3 张无效文件")  # 可恢复异常
logger.error("无法设置壁纸: %s", err)     # 错误
```

- 日志输出到 `logs/wallpaper.log`
- 每天一个日志文件（按日期轮转）
- 用户不可见（静默运行）

---

## 6. 配置管理

### 6.1 配置文件格式
- 文件名: `.wallpace.json`（项目根目录）
- JSON 格式
- 首次运行时自动生成默认配置

### 6.2 配置项
```json
{
    "image_directories": ["D:\\Wallpapers"],
    "extensions": ["jpg", "jpeg", "png", "webp", "bmp"],
    "switch_mode": "daily_random",
    "daily_time": "08:00",
    "interval_minutes": null,
    "skip_list": [],
    "favorites": [],
    "enable_notifications": true,
    "auto_start": true,
    "minimize_to_tray": true
}
```

---

## 7. Windows API 标准

### 7.1 壁纸设置
- 使用 `ctypes` 调用 Windows API：`SystemParametersInfoW(SPI_SETDESKWALLPAPER)`
- 不支持 COM 对象（兼容性更好）
- 需要发送 `SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE`

### 7.2 多显示器
- Windows API 自动处理：对 SPI_SETDESKWALLPAPER 的调用
  会应用到所有显示器
- 无需单独遍历每个显示器

### 7.3 开机自启
- 写入注册表: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
- 使用 `winreg` 模块操作
