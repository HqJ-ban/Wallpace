"""src/app/image_loader.py — 异步图片解码加载器。

图片解码（尤其是 4K 壁纸）耗时数百毫秒，若在 UI 主线程同步执行会导致界面
卡顿冻结。此模块使用全局 QThreadPool（限制并发 4 线程）在后台线程解码图片，
解码完成通过 Qt 信号安全切回主线程更新 UI。

用法（推荐先 connect，再提交任务）:
    from src.app import image_loader
    image_loader.set_result_callback(lambda path, image: ...)
    image_loader.load_async(path, QSize(200, 160))
"""

import logging
from typing import Callable, Optional

from PySide6.QtCore import QObject, QRunnable, QSize, QThreadPool, Signal
from PySide6.QtGui import QImage, QImageReader

logger = logging.getLogger(__name__)


class _LoaderSignals(QObject):
    """后台解码完成后的信号载体（QObject 生命周期由模块级实例持有）。"""

    ready = Signal(str, object)  # (path, QImage)


# 模块级单例
_signals: _LoaderSignals = _LoaderSignals()
_pool: Optional[QThreadPool] = None


def _get_pool() -> QThreadPool:
    """返回应用级线程池，限制并发数避免同时解码过多大图。"""
    global _pool
    if _pool is None:
        _pool = QThreadPool.globalInstance()
        _pool.setMaxThreadCount(4)
    return _pool


def connect_ready(slot: Callable[[str, QImage], None]):
    """连接全局解码完成信号到槽函数。

    Args:
        slot: 回调，签名 slot(path: str, image: QImage)。在主线程执行。

    Returns:
        连接对象，可用于断开连接（调用 connection.disconnect()）。
    """
    return _signals.ready.connect(slot)


class _DecodeJob(QRunnable):
    """后台解码任务：读取图片 → 受限尺寸缩放 → 发信号回主线程。"""

    def __init__(self, path: str, target_size: QSize) -> None:
        super().__init__()
        self._path = path
        self._target_size = target_size

    def run(self) -> None:
        try:
            reader = QImageReader(self._path)
            reader.setAutoTransform(True)
            if self._target_size.isValid():
                reader.setScaledSize(self._target_size)
            image = reader.read()
            if image.isNull():
                logger.warning(
                    "图片解码失败: %s (%s)", self._path, reader.errorString()
                )
                return
            _signals.ready.emit(self._path, image)
        except RuntimeError:
            # 信号槽连接已断开或对象已销毁，静默忽略
            pass
        except Exception:
            logger.exception("后台解码异常: %s", self._path)


def load_async(path: str, target_size: Optional[QSize] = None) -> None:
    """异步解码图片，完成后触发全局 ready 信号。"""
    _get_pool().start(_DecodeJob(path, target_size or QSize(0, 0)))