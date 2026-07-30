"""src/core/settings.py — 配置管理模块。

负责读取、保存、验证应用 JSON 配置文件 (.wallpace.json)。
遵循 dev-standards.md 编码规范：Python 3.10+, docstring, 类型注解。
"""

import json
import logging
from pathlib import Path
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

# 默认配置常量
DEFAULT_CONFIG = {
    "image_directories": [],
    "extensions": ["jpg", "jpeg", "png", "webp"],
    "switch_mode": "daily_random",
    "daily_time": "08:00",
    "interval_minutes": None,
    "skip_list": [],
    "favorites": [],
    "enable_notifications": True,
    "auto_start": True,
    "minimize_to_tray": True,
}

VALID_SWITCH_MODES = ("daily_random", "interval_minutes", "manual")


class Settings:
    """应用配置管理器。

    管理 .wallpace.json 文件的读写，支持热加载和验证。
    首次运行时无配置文件会自动生成默认配置。
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """初始化配置管理器。

        Args:
            config_path: 配置文件路径；如未提供则使用 CWD 下的 .wallpace.json。
        """
        self.config_path = config_path or (Path.cwd() / ".wallpace.json")
        self._data: dict = {}
        self.load()

    # ==================== 公开方法 ====================

    def load(self) -> dict:
        """加载配置文件，不存在则回退到默认值。

        Returns:
            当前配置的字典。

        Raises:
            json.JSONDecodeError: 文件内容不是合法 JSON 时（内部已捕获）。
            OSError: 文件读取失败时（内部已记录日志）。
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                errors = self.validate(raw)
                if errors:
                    logger.warning("配置部分字段无效，自动修复: %s", errors)
                    raw = self._merge_with_defaults(raw)
                self._data = raw
                logger.info("已从 %s 加载配置", self.config_path.name)
            else:
                self._data = dict(DEFAULT_CONFIG)
                logger.info("配置文件不存在，使用默认配置")
        except json.JSONDecodeError as exc:
            logger.error("配置文件格式错误: %s，使用默认配置", exc)
            self._data = dict(DEFAULT_CONFIG)
        except OSError as exc:
            logger.error("无法读取配置文件: %s", exc)
            self._data = dict(DEFAULT_CONFIG)
        return self._data

    def save(self, data: Optional[dict] = None) -> None:
        """持久化配置到磁盘。

        Args:
            data: 要保存的配置字典；None 表示保存当前内存数据。
        """
        target = data if data is not None else self._data
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(target, f, indent=2, ensure_ascii=False)
            logger.info("配置已保存到 %s", self.config_path.name)
        except OSError as exc:
            logger.error("写入配置失败: %s", exc)
            raise RuntimeError(f"无法写入配置文件: {exc}") from exc

    def get(self, key: str, default: Any = None) -> Any:
        """获取单个配置项的值。

        Args:
            key: 配置键名，例如 'switch_mode'。
            default: 键不存在时的返回值。

        Returns:
            对应值，不存在则返回 default。
        """
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置一个配置项，同时写回磁盘。

        Args:
            key: 配置键名。
            value: 新值。
        """
        self._data[key] = value
        self.save()

    def reset_to_defaults(self) -> dict:
        """重置所有配置为出厂默认值，并立即保存。

        Returns:
            重置后的默认配置副本。
        """
        self._data = dict(DEFAULT_CONFIG)
        self.save()
        logger.info("配置已恢复为默认值")
        return dict(self._data)

    @staticmethod
    def validate(data: dict) -> List[str]:
        """校验配置合法性，不修改数据。

        Args:
            data: 待校验的配置字典。

        Returns:
            错误消息列表；空列表表示校验通过。
        """
        errors: List[str] = []
        mode = data.get("switch_mode")

        # --- image_directories ---
        dirs = data.get("image_directories")
        if not isinstance(dirs, list):
            errors.append("'image_directories' 必须是列表")
        else:
            for d in dirs:
                if not isinstance(d, str) or not d.strip():
                    errors.append(f"'image_directories' 中的路径不能为空字符串")

        # --- switch_mode ---
        if mode not in VALID_SWITCH_MODES:
            errors.append(
                f"'switch_mode' 必须为 {', '.join(VALID_SWITCH_MODES)} 之一"
            )

        # --- daily_time (仅 daily_random 模式检查) ---
        if mode == "daily_random":
            time_str = str(data.get("daily_time", ""))
            parts = time_str.split(":")
            if len(parts) != 2 or not all(p.isdigit() for p in parts):
                errors.append("'daily_time' 格式应为 HH:MM")
            elif not (0 <= int(parts[0]) <= 23 and 0 <= int(parts[1]) <= 59):
                errors.append("'daily_time' 超出 00:00-23:59 范围")

        # --- interval_minutes ---
        interval = data.get("interval_minutes")
        if interval is not None:
            if not isinstance(interval, int) or interval <= 0:
                errors.append("'interval_minutes' 必须是正整数或 null")

        # --- skip_list / favorites ---
        for field in ("skip_list", "favorites"):
            val = data.get(field)
            if not isinstance(val, list):
                errors.append(f"'{field}' 必须是列表")

        return errors

    # ==================== 私有方法 ====================

    def _merge_with_defaults(self, partial: dict) -> dict:
        """用默认值修复 partial 中无效的字段。

        只在 partial 缺失或完全非法时 fallback，保留合法覆盖。
        """
        merged = dict(DEFAULT_CONFIG)
        for k, v in partial.items():
            if k not in merged:
                continue
            # Allow matching types or None where appropriate
            default_type = type(merged[k])
            if v is None:
                # Allow None for nullable fields like interval_minutes
                if default_type is type(None) or hasattr(default_type, "__name__") and default_type.__name__ == "NoneType":
                    merged[k] = v
                continue
            # Type match
            if isinstance(v, default_type):
                merged[k] = v
            # Special handling for interval_minutes
            if k == "interval_minutes" and default_type is int:
                try:
                    merged[k] = int(v)
                except (ValueError, TypeError):
                    pass
            # For boolean settings
            elif k in ("enable_notifications", "auto_start", "minimize_to_tray") and default_type is bool:
                merged[k] = bool(v)
    @property
    def raw(self) -> dict:
        """只读快照，防止外部直接修改内部状态。"""
        return dict(self._data)
