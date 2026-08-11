"""tests/test_autostart_registry.py — 开机自启注册表管理测试。"""

import logging
from unittest.mock import MagicMock, patch

import pytest

logger = logging.getLogger(__name__)


class TestAutostartManagerImport:
    """测试模块可正常导入。"""

    def test_import_module(self) -> None:
        from src.core.autostart_registry import AutostartManager

        assert AutostartManager is not None

    def test_get_exe_path_returns_string(self) -> None:
        from src.core.autostart_registry import _get_exe_path

        path = _get_exe_path()
        assert isinstance(path, str)
        assert len(path) > 0


@pytest.fixture
def mocked_manager():
    """构造使用 fake winreg 的 AutostartManager，避免触碰真实注册表。"""
    fake_winreg = MagicMock()
    fake_key = MagicMock()
    fake_winreg.HKEY_CURRENT_USER = MagicMock()
    fake_winreg.OpenKey.return_value = fake_key
    fake_winreg.REG_SZ = 1
    with patch.dict("sys.modules", {"winreg": fake_winreg}, create=True):
        from src.core.autostart_registry import AutostartManager

        yield AutostartManager()


class TestAutostartManagerPropertyEnabled:
    def test_is_enabled_no_crash(self, mocked_manager) -> None:
        result = mocked_manager.is_enabled
        assert isinstance(result, bool)


class TestAutostartManagerEnableDisable:
    def test_enable_no_crash(self, mocked_manager) -> None:
        result = mocked_manager.enable()
        assert isinstance(result, bool)

    def test_disable_no_crash(self, mocked_manager) -> None:
        result = mocked_manager.disable()
        assert isinstance(result, bool)

    def test_idempotent_enable(self, mocked_manager) -> None:
        mocked_manager.enable()
        mocked_manager.enable()


class TestAutostartManagerMockWinreg:
    """使用 mock winreg 验证核心逻辑。"""

    def test_is_enabled_true_when_exists(self) -> None:
        fake_winreg = MagicMock()
        fake_key = MagicMock()
        fake_winreg.HKEY_CURRENT_USER = MagicMock()
        fake_winreg.OpenKey.return_value = fake_key
        fake_winreg.QueryValueEx.return_value = ("some_path", None)

        with patch.dict("sys.modules", {"winreg": fake_winreg}, create=True):
            from src.core.autostart_registry import AutostartManager

            mgr = AutostartManager()
            assert mgr.is_enabled is True

    def test_is_enabled_false_when_not_found(self) -> None:
        fake_winreg = MagicMock()
        fake_key = MagicMock()
        fake_winreg.HKEY_CURRENT_USER = MagicMock()
        fake_winreg.OpenKey.return_value = fake_key
        fake_winreg.QueryValueEx.side_effect = FileNotFoundError()

        with patch.dict("sys.modules", {"winreg": fake_winreg}, create=True):
            from src.core.autostart_registry import AutostartManager

            mgr = AutostartManager()
            assert mgr.is_enabled is False

    def test_enable_writes_reg_value(self) -> None:
        fake_winreg = MagicMock()
        fake_key = MagicMock()
        fake_winreg.HKEY_CURRENT_USER = MagicMock()
        fake_winreg.OpenKey.return_value = fake_key
        fake_winreg.REG_SZ = 1

        with patch.dict("sys.modules", {"winreg": fake_winreg}, create=True):
            from src.core.autostart_registry import AutostartManager

            mgr = AutostartManager()
            result = mgr.enable()
            assert result is True
            fake_winreg.SetValueEx.assert_called_once()
            # call_args[0] = positional args: (hkey, lpValueName, Reserved, type, data)
            call_args = fake_winreg.SetValueEx.call_args[0]
            assert call_args[1] == "Wallpace"

    def test_disable_deletes_reg_value(self) -> None:
        fake_winreg = MagicMock()
        fake_key = MagicMock()
        fake_winreg.HKEY_CURRENT_USER = MagicMock()
        fake_winreg.OpenKey.return_value = fake_key

        with patch.dict("sys.modules", {"winreg": fake_winreg}, create=True):
            from src.core.autostart_registry import AutostartManager

            mgr = AutostartManager()
            result = mgr.disable()
            assert result is True
            fake_winreg.DeleteValue.assert_called_once()
