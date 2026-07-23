"""tests/conftest.py — 共享 fixtures。"""

import json
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_config_dir(tmp_path: Path):
    """提供一个临时目录用于存放 .wallpace.json。"""
    # 切换到临时目录避免影响真实配置
    old_cwd = Path.cwd()
    try:
        import os
        os.chdir(str(tmp_path))
        yield tmp_path
    finally:
        os.chdir(str(old_cwd))


@pytest.fixture()
def sample_image_files(tmp_path: Path):
    """创建一个带图片文件的临时目录，供扫描测试使用。"""
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    for name in ("a.jpg", "b.png", "c.webp", "d.bmp"):
        (img_dir / name).write_text("fake")
    sub = img_dir / "sub"
    sub.mkdir()
    (sub / "e.jpg").write_text("fake")
    (sub / "readme.txt").write_text("ignore")
    return str(img_dir)
