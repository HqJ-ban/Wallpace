"""tests/test_wallpaper_manager.py -- WallpaperManager module tests."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.wallpaper_manager import (
    SPI_SETDESKWALLPAPER,
    WallpaperManager,
)


class TestWallpaperManagerBasic:
    @pytest.fixture()
    def wm(self):
        return WallpaperManager()

    def test_is_supported_returns_bool(self, wm):
        assert isinstance(wm.is_supported, bool)

    def test_verify_set_fails_when_not_supported(self):
        orig = sys.platform
        try:
            sys.platform = "linux"
            if "core.wallpaper_manager" in sys.modules:
                del sys.modules["core.wallpaper_manager"]
            from core.wallpaper_manager import WallpaperManager as WM2
            wm2 = WM2()
            assert not wm2.is_supported
        finally:
            sys.platform = orig


class TestWallpaperManagerGetCurrent:
    @pytest.mark.skipif(
        sys.platform != "win32",
        reason="Requires Windows environment",
    )
    def test_get_current_on_windows_real(self):
        wm = WallpaperManager()
        current = wm.get_current_wallpaper()
        assert current is None or isinstance(current, str)

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Skip on Windows",
    )
    def test_returns_none_when_not_supported(self):
        wm = WallpaperManager()
        assert not wm.is_supported
        assert wm.get_current_wallpaper() is None


class TestWallpaperManagerEdgeCases:
    @pytest.mark.skipif(
        sys.platform != "win32",
        reason="Requires Windows",
    )
    def test_set_nonexistent_image(self):
        wm = WallpaperManager()
        result = wm.set_wallpaper("/nonexistent/path/image.jpg")
        assert result is False
