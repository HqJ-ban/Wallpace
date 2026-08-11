"""tests/test_window.py — MainWindow 集成测试。

测试主窗口的关键交互逻辑，使用 offscreen 平台避免 GUI 依赖。

注意：图片库扫描已改为后台线程异步执行（修复 UI 卡死），
依赖扫描结果的断言需先通过 _wait_for_scan() 等待扫描完成。
"""

import sys
import time
from pathlib import Path

import pytest
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def _wait_for_scan(window, timeout: float = 5.0) -> None:
    """等待 MainWindow 的后台扫描完成（驱动事件循环以投递完成信号）。"""
    deadline = time.time() + timeout
    while window._scan_running and time.time() < deadline:
        QApplication.processEvents()
        time.sleep(0.005)
    QApplication.processEvents()


@pytest.fixture
def app():
    """确保有 QApplication 实例。"""
    import os
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    if not QApplication.instance():
        QApplication([])
    yield


@pytest.fixture
def main_window(app):
    """创建 MainWindow 实例。"""
    from src.core.settings import Settings
    from src.core.image_library import ImageLibrary
    from src.core.wallpaper_manager import WallpaperManager
    from src.core.scheduler import Scheduler
    from src.app.window import MainWindow

    settings = Settings()
    library = ImageLibrary(directories=[], extensions=set())
    wm = WallpaperManager()
    scheduler = Scheduler(mode="manual")
    scheduler.set_dependencies(library, wm)

    window = MainWindow(
        settings=settings,
        library=library,
        wallpaper_manager=wm,
        scheduler=scheduler,
    )
    yield window
    window.close()


class TestMainWindowInit:
    """测试主窗口初始化。"""

    def test_window_created(self, main_window):
        assert main_window is not None

    def test_window_title(self, main_window):
        assert main_window.windowTitle() == "Wallpace"

    def test_minimum_size(self, main_window):
        assert main_window.minimumWidth() == 800
        assert main_window.minimumHeight() == 540

    def test_initial_size(self, main_window):
        assert main_window.width() == 960
        assert main_window.height() == 620


class TestMainWindowPages:
    """测试页面导航。"""

    def test_has_preview_page(self, main_window):
        assert hasattr(main_window, "_preview_page")
        assert main_window._preview_page is not None

    def test_has_settings_page(self, main_window):
        assert hasattr(main_window, "_stacked")

    def test_current_page_is_preview(self, main_window):
        assert main_window._stacked.currentWidget() == main_window._preview_page


class TestMainWindowGallery:
    """测试图片库相关功能。"""

    def test_refresh_gallery_empty(self, main_window):
        """测试空图片库刷新。"""
        main_window._refresh_gallery()
        # 应该显示空状态引导
        assert hasattr(main_window, "_empty_guide")

    def test_refresh_gallery_with_images(self, main_window, tmp_path):
        """测试有图片时刷新。"""
        from PySide6.QtGui import QImageWriter
        from src.core.image_library import ImageLibrary

        # 创建测试图片
        img = QImage(100, 100, QImage.Format_RGB32)
        img.fill(0xFF0000)
        img_path = tmp_path / "test.jpg"
        QImageWriter.write(img, str(img_path), "JPG")

        # 添加到 library
        main_window._library.add_directory(str(tmp_path))
        main_window._refresh_gallery()
        _wait_for_scan(main_window)

        assert main_window._library.total_count > 0

    def test_gallery_thumbnails_refresh(self, main_window, tmp_path):
        """测试缩略图刷新。"""
        from PySide6.QtGui import QImageWriter

        # 创建多张测试图片
        for i in range(5):
            img = QImage(100, 100, QImage.Format_RGB32)
            img.fill(i * 50)
            path = tmp_path / f"test_{i}.jpg"
            QImageWriter.write(img, str(path), "JPG")

        main_window._library.add_directory(str(tmp_path))
        main_window._refresh_gallery()
        _wait_for_scan(main_window)

        # 应该有缩略图 widget
        assert main_window._gallery_layout.count() > 0


class TestMainWindowSettings:
    """测试设置页面功能。"""

    def test_open_settings(self, main_window):
        """测试打开设置页面。"""
        main_window.open_settings()
        assert main_window._stacked.currentWidget() is not None

    def test_add_directory(self, main_window, tmp_path):
        """测试添加目录。"""
        from PySide6.QtGui import QImageWriter
 
        # 创建测试图片
        img = QImage(100, 100, QImage.Format_RGB32)
        img.fill(0xFF0000)
        img_path = tmp_path / "test.jpg"
        QImageWriter.write(img, str(img_path), "JPG")
 
        # 模拟添加目录（绕过 QFileDialog）
        dirs = main_window._settings.get("image_directories", [])
        dirs.append(str(tmp_path))
        main_window._settings.set("image_directories", dirs)
        main_window._library.add_directory(str(tmp_path))
        main_window._refresh_gallery()
        _wait_for_scan(main_window)

        assert main_window._library.directory_count > 0
        assert main_window._library.total_count > 0

    def test_add_directory_does_not_double_scan(self, main_window, tmp_path, monkeypatch):
        """添加目录时应仅在 MainWindow 内部触发一次扫描。"""
        # 等待初始化时的后台扫描结束（扫描进行中 _add_directory 会被忽略）
        _wait_for_scan(main_window)
        monkeypatch.setattr(
            "src.app.window.QFileDialog.getExistingDirectory",
            lambda *args, **kwargs: str(tmp_path),
        )

        scan_flag = {}

        def fake_add_directory(path, scan=True):
            scan_flag["scan"] = scan
            return True

        monkeypatch.setattr(main_window._library, "add_directory", fake_add_directory)
        main_window._add_directory()

        assert scan_flag.get("scan") is False

    def test_remove_directory(self, main_window, tmp_path):
        """测试移除目录。"""
        from PySide6.QtGui import QImageWriter

        # 先添加目录
        img = QImage(100, 100, QImage.Format_RGB32)
        img.fill(0xFF0000)
        img_path = tmp_path / "test.jpg"
        QImageWriter.write(img, str(img_path), "JPG")

        main_window._library.add_directory(str(tmp_path))
        main_window._refresh_gallery()
        _wait_for_scan(main_window)

        # 移除目录
        removed = main_window._library.remove_directory(str(tmp_path))
        main_window._refresh_gallery()
        _wait_for_scan(main_window)

        assert removed is True
        assert main_window._library.directory_count == 0


class TestMainWindowScheduler:
    """测试调度器相关功能。"""

    def test_scheduler_started(self, main_window):
        """测试调度器启动。"""
        assert main_window._scheduler is not None
        assert main_window._scheduler.mode == "manual"

    def test_pause_scheduler(self, main_window):
        """测试暂停调度器。"""
        main_window.pause_scheduler()
        assert not main_window._scheduler.is_active

    def test_resume_scheduler(self, main_window):
        """测试恢复调度器。"""
        # manual 模式调度器默认 is_running=False
        # 需要先启动再暂停才能恢复
        main_window._scheduler.start()
        main_window.pause_scheduler()
        main_window.resume_scheduler()
        assert main_window._scheduler.is_running
