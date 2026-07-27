"""tests/test_settings.py — Settings 模块测试。

覆盖：加载、保存、get/set、重置、验证、JSON 解析错误处理。
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest

from core.settings import DEFAULT_CONFIG, Settings


class TestSettingsLoadSave:
    """配置文件的读取与写入。"""

    def test_default_when_no_file(self, tmp_config_dir: Path):
        s = Settings()
        assert isinstance(s.get("switch_mode"), str)

    def test_save_and_reload(self, tmp_config_dir: Path):
        s = Settings()
        s.set("custom_key", "custom_value")
        config_path = s.config_path
        assert config_path.exists()

        s2 = Settings(config_path=config_path)
        assert s2.get("custom_key") == "custom_value"

    def test_reset_to_defaults(self, tmp_config_dir: Path):
        s = Settings()
        s.set("custom_key", "value")
        result = s.reset_to_defaults()
        assert "custom_key" not in result
        assert result["switch_mode"] == "daily_random"

    def test_save_returns_none_not_data(self, tmp_config_dir: Path):
        s = Settings()
        assert s.save() is None


class TestSettingsValidation:
    """validate() 静态方法的各种非法输入。"""

    def test_valid_empty(self):
        assert Settings.validate(DEFAULT_CONFIG) == []

    def test_invalid_image_directories_not_list(self):
        data = dict(DEFAULT_CONFIG)
        data["image_directories"] = "/not/a/list"
        errs = Settings.validate(data)
        assert any("必须是列表" in e for e in errs)

    def test_invalid_image_directories_empty_string(self):
        data = dict(DEFAULT_CONFIG)
        data["image_directories"] = [""]
        errs = Settings.validate(data)
        assert any("不能为空" in e for e in errs)

    def test_valid_nonexistent_directory_is_ok(self):
        """非存在目录不应导致校验失败——只检查格式，不检查路径是否存在。"""
        data = dict(DEFAULT_CONFIG)
        data["image_directories"] = ["/tmp/wallpace_test_images"]
        errs = Settings.validate(data)
        # Should pass because we no longer check path existence
        assert all("无效" not in e and "文件夹" not in e for e in errs)

    def test_invalid_switch_mode(self):
        data = {"switch_mode": "invalid_mode"}
        errs = Settings.validate(data)
        assert any("必须为" in e for e in errs)

    def test_invalid_daily_time(self):
        data = {**DEFAULT_CONFIG, "switch_mode": "daily_random", "daily_time": "25:99"}
        errs = Settings.validate(data)
        assert any("超出" in e or "HH:MM" in e for e in errs)

    def test_invalid_interval(self):
        data = {**DEFAULT_CONFIG, "interval_minutes": -5}
        errs = Settings.validate(data)
        assert any("正整数" in e for e in errs)

    def test_invalid_skip_list_type(self):
        data = {"skip_list": "not_a_list"}
        errs = Settings.validate(data)
        assert any("'skip_list'" in e for e in errs)


class TestSettingsSetGet:
    """get() 和 set() 基本操作。"""

    def test_get_default_missing(self):
        s = Settings()
        assert s.get("nonexistent_key") is None

    def test_set_and_get(self, tmp_config_dir: Path):
        config_path = tmp_config_dir / ".wallpace.json"
        s = Settings(config_path=config_path)
        s.set("my_test_key", 12345)
        assert s.get("my_test_key") == 12345

    def test_raw_is_copy(self):
        s = Settings()
        raw1 = s.raw
        raw2 = s.raw
        assert raw1 is not raw2


class TestSettingsCorruptedFile:
    """配置文件损坏时的降级行为。"""

    def test_corrupt_json_reverts_to_default(self, tmp_config_dir: Path):
        config_path = tmp_config_dir / ".wallpace.json"
        config_path.write_text("{not valid json!!!")
        s = Settings(config_path=config_path)
        assert s.get("switch_mode") == "daily_random"
