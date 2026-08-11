"""tests/conftest.py — 共享 fixtures。"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject
from PySide6.QtGui import QImage, QImageWriter

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

for env_var in ("PYTHONPATH", "TMPDIR", "TEMP", "TMP"):
    if env_var == "PYTHONPATH":
        os.environ.setdefault(env_var, str(ROOT))
    else:
        os.environ.setdefault(env_var, str(Path(tempfile.gettempdir())))


def _compat_qimagewriter_write(image: QImage, file_name, format_name=None):
    """兼容旧测试对 QImageWriter.write 的调用方式。"""
    fmt = "PNG"
    if format_name:
        fmt = str(format_name).upper()
        if fmt in {"JPG", "JPEG"}:
            fmt = "JPG"
    path = Path(file_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    return image.save(str(path), fmt)


QImageWriter.write = _compat_qimagewriter_write

if not hasattr(QMetaObject.Connection, "disconnect"):
    def _disconnect(self):
        return None

    QMetaObject.Connection.disconnect = _disconnect


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
