"""tests/test_image_loader.py — 异步图片解码器测试。

测试 image_loader 模块的线程池管理和异步解码功能。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from src.app import image_loader
from PySide6.QtCore import QSize, QCoreApplication
from PySide6.QtGui import QImage


class TestImageLoaderImport:
    """测试模块导入和基本结构。"""

    def test_load_async_exists(self):
        assert hasattr(image_loader, "load_async")
        assert callable(image_loader.load_async)

    def test_connect_ready_exists(self):
        assert hasattr(image_loader, "connect_ready")
        assert callable(image_loader.connect_ready)

    def test_pool_is_singleton(self):
        pool1 = image_loader._get_pool()
        pool2 = image_loader._get_pool()
        assert pool1 is pool2


class TestImageLoaderPool:
    """测试线程池配置。"""

    def test_max_thread_count(self):
        pool = image_loader._get_pool()
        assert pool.maxThreadCount() == 4

    def test_pool_is_global_instance(self):
        from PySide6.QtCore import QThreadPool
        pool = image_loader._get_pool()
        assert pool is QThreadPool.globalInstance()


class TestImageLoaderDecode:
    """测试实际图片解码（需要 QApplication 实例）。"""

    @pytest.fixture(autouse=True)
    def app(self):
        """确保有 QApplication 实例，且必须在 offscreen 模式。"""
        import os
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        from PySide6.QtWidgets import QApplication
        if not QApplication.instance():
            QApplication([])
        yield

    def test_decode_small_image(self, tmp_path):
        """测试解码小尺寸图片。"""
        from PySide6.QtGui import QImageWriter
        img = QImage(50, 50, QImage.Format_RGB32)
        img.fill(0xFF0000)  # 红色
        path = tmp_path / "red.png"
        QImageWriter.write(img, str(path), "PNG")

        results = []
        conn = image_loader.connect_ready(lambda p, img: results.append((p, img)))
        try:
            image_loader.load_async(str(path), QSize(50, 50))
            # 等待解码完成（最多 5 秒）
            for _ in range(50):
                if results:
                    break
                QCoreApplication.processEvents()
                import time; time.sleep(0.1)
        finally:
            conn.disconnect()

        assert len(results) == 1
        path_received, img_received = results[0]
        assert Path(path_received).name == "red.png"
        assert img_received.width() == 50
        assert img_received.height() == 50

    def test_decode_nonexistent_image(self, tmp_path):
        """测试解码不存在的图片不崩溃。"""
        results = []
        conn = image_loader.connect_ready(lambda p, img: results.append((p, img)))
        try:
            image_loader.load_async(str(tmp_path / "nonexistent.png"), QSize(50, 50))
            import time; time.sleep(0.5)
            QCoreApplication.processEvents()
        finally:
            conn.disconnect()

        # 不存在的图片不应该产生结果
        assert len(results) == 0

    def test_decode_jpeg(self, tmp_path):
        """测试解码 JPEG 图片。"""
        from PySide6.QtGui import QImageWriter
        img = QImage(100, 100, QImage.Format_RGB32)
        img.fill(0x00FF00)  # 绿色
        path = tmp_path / "green.jpg"
        QImageWriter.write(img, str(path), "JPG")

        results = []
        conn = image_loader.connect_ready(lambda p, img: results.append((p, img)))
        try:
            image_loader.load_async(str(path), QSize(100, 100))
            for _ in range(50):
                if results:
                    break
                QCoreApplication.processEvents()
                import time; time.sleep(0.1)
        finally:
            conn.disconnect()

        assert len(results) == 1
        _, img_received = results[0]
        assert img_received.width() == 100
        assert img_received.height() == 100
