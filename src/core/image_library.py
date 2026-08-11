"""src/core/image_library.py — 图片库管理模块。

负责扫描用户配置的图片文件夹、过滤有效图片、管理跳过列表和收藏夹。
不依赖任何 GUI 框架，纯 Python 标准库 + pathlib。
"""

import hashlib
import logging
import random
from pathlib import Path
from typing import Callable, List, Optional, Set

logger = logging.getLogger(__name__)

# 默认扩展名集合（小写）
DEFAULT_EXTENSIONS: Set[str] = {"jpg", "jpeg", "png", "webp"}


class ImageLibrary:
    """壁纸图片库管理器。

    提供目录递归扫描、扩展名过滤、随机选取、跳过/收藏黑名单等功能。
    所有路径统一使用绝对路径（str），方便序列化到 JSON。
    """

    def __init__(
        self,
        directories: Optional[List[str]] = None,
        extensions: Optional[Set[str]] = None,
    ) -> None:
        """初始化图片库。

        Args:
            directories: 要扫描的图片文件夹列表；空列表则跳过扫描。
            extensions: 允许的扩展名集合（不含点，全部小写）。
        """
        self._directories: List[str] = directories or []
        self._extensions = (
            {e.lower().lstrip(chr(46)) for e in extensions}
            if extensions
            else set(DEFAULT_EXTENSIONS)
        )
        # 运行时状态
        self._all_images: List[str] = []  # scan() 的结果缓存
        self._skip_set: Set[str] = set()   # 去重用
        self._favorite_set: Set[str] = set()

    # ==================== 公开 API ====================

    def scan(self) -> List[str]:
        """递归扫描所有配置的文件夹，返回可用图片路径。

        结果按文件路径排序以保证可重复性。
        会同步更新内置缓存 _all_images。

        Returns:
            符合条件的图片绝对路径列表。
        """
        images: List[str] = []
        supported = self._extensions

        for dir_str in self._directories:
            root = Path(dir_str)
            if not root.is_dir():
                logger.warning("跳过无效目录: %s", dir_str)
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lstrip(".").lower() in supported:
                    images.append(str(path.resolve()))

        # 去重 + 排序
        unique: List[str] = []
        seen: Set[str] = set()
        for img in sorted(images):
            if img not in seen:
                seen.add(img)
                unique.append(img)
        self._all_images = unique
        logger.info("扫描完成: %d 张图片", len(unique))
        return unique

    def refresh(self) -> List[str]:
        """快捷调用 scan + reload 的组合。"""
        return self.scan()

    def list_available(self) -> List[str]:
        """获取当前可用的图片列表（排除已跳过的）。

        Returns:
            未被标记为 skip 的图片路径。
        """
        return [img for img in self._all_images if img not in self._skip_set]

    def get_random(self) -> Optional[str]:
        """从可用列表中随机选择一张图片。

        Returns:
            图片路径或 None（无可用图片时）。
        """
        available = self.list_available()
        if not available:
            logger.warning("没有可用图片，请先添加图片目录")
            return None
        return random.choice(available)

    def add_directory(self, path: str, scan: bool = True) -> bool:
        """动态添加扫描目录。

        Args:
            path: 文件夹路径。
            scan: 是否立即重新扫描目录。

        Returns:
            True 表示目录有效且已添加。
        """
        p = Path(path)
        if not p.is_dir():
            logger.warning("无法添加无效目录: %s", path)
            return False
        if path not in self._directories:
            self._directories.append(path)
            logger.info("添加图片目录: %s", path)
        if scan:
            self.scan()
        return True

    def remove_directory(self, path: str, scan: bool = True) -> bool:
        """移除扫描目录。

        Args:
            path: 要移除的目录路径。
            scan: 是否立即重新扫描目录。

        Returns:
            True 表示成功移除。
        """
        if path in self._directories:
            self._directories.remove(path)
            if scan:
                self.scan()
            logger.info("移除图片目录: %s", path)
            return True
        return False

    # ==================== 黑白名单管理 ====================

    def skip(self, image_path: str) -> bool:
        """将图片加入跳过列表（不删除原文件，仅标记）。

        Args:
            image_path: 要跳过的图片路径。

        Returns:
            True 表示新增了跳过项；该路径已在跳过列表中则返回 False。
        """
        resolved = Path(image_path).resolve()
        key = str(resolved)
        if key in self._skip_set:
            return False
        self._skip_set.add(key)
        logger.info("跳过图片: %s", key)
        return True

    def unskip(self, image_path: str) -> bool:
        """从跳过列表中移除一张图片。

        Args:
            image_path: 要恢复的图片路径。

        Returns:
            True 表示成功移除；不在跳过列表中则返回 False。
        """
        resolved = Path(image_path).resolve()
        key = str(resolved)
        removed = key in self._skip_set
        self._skip_set.discard(key)
        if removed:
            logger.info("取消跳过: %s", key)
        return removed

    def favorite(self, image_path: str) -> bool:
        """将图片加入收藏列表。

        Args:
            image_path: 要收藏的图片路径。

        Returns:
            True 表示新增收藏。
        """
        resolved = Path(image_path).resolve()
        key = str(resolved)
        added = key not in self._favorite_set
        self._favorite_set.add(key)
        if added:
            logger.info("收藏: %s", key)
        return added

    def is_favorite(self, image_path: str) -> bool:
        """判断图片是否已经收藏。"""
        resolved = Path(image_path).resolve()
        return str(resolved) in self._favorite_set

    def unfavorite(self, image_path: str) -> bool:
        """取消收藏。

        Args:
            image_path: 图片路径。

        Returns:
            True 表示取消了收藏。
        """
        resolved = Path(image_path).resolve()
        key = str(resolved)
        removed = key in self._favorite_set
        self._favorite_set.discard(key)
        if removed:
            logger.info("取消收藏: %s", key)
        return removed

    @property
    def skip_list(self) -> List[str]:
        """返回跳过列表的副本（可安全用于序列化）。"""
        return sorted(self._skip_set)

    @property
    def favorites(self) -> List[str]:
        """返回收藏列表的副本。"""
        return sorted(self._favorite_set)

    # ==================== 状态查询 ====================

    def clear_skip(self) -> int:
        """清空跳过列表，返回被清除的数量。"""
        count = len(self._skip_set)
        self._skip_set.clear()
        logger.info("清空跳过列表: %d 项", count)
        return count

    def clear_favorites(self) -> int:
        """清空收藏列表，返回被清除的数量。"""
        count = len(self._favorite_set)
        self._favorite_set.clear()
        logger.info("清空收藏列表: %d 项", count)
        return count

    @property
    def total_count(self) -> int:
        """已扫描的总图片数（含已被跳过的）。"""
        return len(self._all_images)

    @property
    def available_count(self) -> int:
        """当前可用的图片数（排除跳过）。"""
        return len(self.list_available())

    @property
    def directory_count(self) -> int:
        """已配置的扫描目录数量。"""
        return len(self._directories)

    def to_dict(self) -> dict:
        """导出为可序列化的字典。"""
        return {
            "directories": list(self._directories),
            "extensions": sorted(self._extensions),
            "skip_list": self.skip_list,
            "favorites": self.favorites,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ImageLibrary":
        """从字典重建实例。"""
        lib = cls(
            directories=data.get("directories"),
            extensions=data.get("extensions"),
        )
        lib._skip_set = set(data.get("skip_list", []))
        lib._favorite_set = set(data.get("favorites", []))
        return lib
