"""tests/test_image_library.py -- ImageLibrary module tests."""

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.image_library import DEFAULT_EXTENSIONS, ImageLibrary


class TestImageLibraryScan:
    def test_scan_empty_directories(self):
        lib = ImageLibrary(directories=[])
        images = lib.scan()
        assert images == []
        assert lib.total_count == 0

    def test_scan_invalid_directory(self, sample_image_files):
        lib = ImageLibrary(directories=["/nonexistent/path"])
        images = lib.scan()
        assert images == []

    def test_scan_valid_images(self, sample_image_files):
        lib = ImageLibrary(directories=[sample_image_files])
        images = lib.scan()
        # bmp not in default extensions; a.jpg, b.png, c.webp, sub/e.jpg
        assert len(images) == 4
        for img in images:
            ext = Path(img).suffix.lower().lstrip(".")
            assert ext in {"jpg", "png", "webp"}

    def test_scan_excludes_txt(self, sample_image_files):
        lib = ImageLibrary(directories=[sample_image_files])
        images = lib.scan()
        names = [Path(i).name for i in images]
        assert "readme.txt" not in names

    def test_scan_respects_extensions(self, sample_image_files):
        lib = ImageLibrary(
            directories=[sample_image_files],
            extensions={"jpg"},
        )
        images = lib.scan()
        assert all(i.endswith(".jpg") for i in images)

    def test_scan_returns_absolute_paths(self, sample_image_files):
        lib = ImageLibrary(directories=[sample_image_files])
        images = lib.scan()
        for img in images:
            assert Path(img).is_absolute()


class TestImageLibraryRandom:
    def test_get_random_empty(self):
        lib = ImageLibrary(directories=["/nonexistent"])
        result = lib.get_random()
        assert result is None

    def test_get_random_returns_valid_path(self, sample_image_files):
        lib = ImageLibrary(directories=[sample_image_files])
        lib.scan()
        path = lib.get_random()
        assert path is not None
        assert Path(path).exists()

    def test_get_random_from_available_only(self, sample_image_files):
        lib = ImageLibrary(directories=[sample_image_files])
        lib.scan()
        for img in list(lib.list_available()):
            lib.skip(img)
        result = lib.get_random()
        assert result is None


class TestImageLibrarySkipFavorite:
    def test_skip_marks_image(self, sample_image_files):
        lib = ImageLibrary(directories=[sample_image_files])
        lib.scan()
        first = lib.list_available()[0]
        added = lib.skip(first)
        assert added is True
        available = lib.list_available()
        assert first not in available
        assert first in lib.skip_list

    def test_skip_already_skipped(self, sample_image_files):
        lib = ImageLibrary(directories=[sample_image_files])
        lib.scan()
        first = lib.list_available()[0]
        lib.skip(first)
        assert lib.skip(first) is False

    def test_unskip_restores_image(self, sample_image_files):
        lib = ImageLibrary(directories=[sample_image_files])
        lib.scan()
        first = lib.list_available()[0]
        lib.skip(first)
        removed = lib.unskip(first)
        assert removed is True
        assert first in lib.list_available()

    def test_favorite_and_unfavorite(self, sample_image_files):
        lib = ImageLibrary(directories=[sample_image_files])
        lib.scan()
        first = lib.list_available()[0]
        assert lib.favorite(first) is True
        assert first in lib.favorites
        assert lib.unfavorite(first) is True
        assert first not in lib.favorites

    def test_clear_skip(self, sample_image_files):
        lib = ImageLibrary(directories=[sample_image_files])
        lib.scan()
        for img in list(lib.list_available()):
            lib.skip(img)
        count = lib.clear_skip()
        assert count > 0
        assert lib.total_count > 0
        assert len(lib.list_available()) == lib.total_count

    def test_clear_favorites(self, sample_image_files):
        lib = ImageLibrary(directories=[sample_image_files])
        lib.scan()
        avail = lib.list_available()[:2]
        for img in avail:
            lib.favorite(img)
        count = lib.clear_favorites()
        assert count > 0
        assert len(lib.favorites) == 0


class TestImageLibraryDirectories:
    def test_add_directory(self, sample_image_files):
        lib = ImageLibrary()
        assert lib.add_directory(sample_image_files) is True
        assert lib.directory_count == 1

    def test_add_invalid_directory(self):
        lib = ImageLibrary()
        assert lib.add_directory("/nonexistent/path") is False

    def test_remove_directory(self, sample_image_files):
        lib = ImageLibrary(directories=[sample_image_files])
        lib.scan()
        assert lib.remove_directory(sample_image_files) is True
        assert lib.directory_count == 0
        assert lib.total_count == 0


class TestImageLibrarySerialize:
    def test_to_dict_round_trip(self, sample_image_files):
        lib1 = ImageLibrary(directories=[sample_image_files])
        lib1.scan()
        data = lib1.to_dict()
        lib2 = ImageLibrary.from_dict(data)
        assert lib2._directories == lib1._directories
        assert lib2._extensions == lib1._extensions
