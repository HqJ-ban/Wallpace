"""src/main.py — Wallpace 入口点。

用法:
    python src/main.py          # 普通启动
    python src/main.py --hidden # 开机自启模式（不显示主窗口）
    python src/main.py --test   # 只运行核心模块测试
"""

import logging
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 日志配置
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "wallpace.log", encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ],
)


def run_tests() -> None:
    """仅运行核心模块单元测试，退出前打印汇总。"""
    import unittest

    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n所有测试通过！")
    else:
        print(
            f"\n失败 {len(result.failures)} 项，跳过 "
            f"{len(result.skipped)} 项"
        )
    sys.exit(0 if result.wasSuccessful() else 1)


def main() -> None:
    """程序入口。"""
    if "--test" in sys.argv:
        run_tests()
        return

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("Wallpace")
    app.setOrganizationName("wallpace")

    # Phase 1: 核心模块初始化
    from core.settings import Settings
    from core.image_library import ImageLibrary
    from core.wallpaper_manager import WallpaperManager

    settings = Settings()
    libraries = ImageLibrary(
        directories=settings.get("image_directories"),
        extensions=settings.get("extensions"),
    )
    wm = WallpaperManager()

    logger = logging.getLogger("main")

    # 验证壁纸管理器是否可用
    if not wm.is_supported:
        logger.error("当前平台不支持壁纸设置操作")

    # 显示基本信息
    logger.info(
        "Wallpace v0.1.0 启动 (骨架阶段)"
    )
    logger.info(
        "配置: %d 个图片目录, %d 张扫描图片",
        libraries.directory_count,
        libraries.total_count,
    )
    logger.info("当前壁纸: %s", wm.get_current_wallpaper())

    # TODO Phase 2: 创建 MainWindow
    # from app.window import MainWindow
    # window = MainWindow(settings=settings, library=libraries,
    #                     wallpaper_manager=wm)
    # if "--hidden" not in sys.argv:
    #     window.show()

    print("Wallpace 正在启动... (核心模块已加载)")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
