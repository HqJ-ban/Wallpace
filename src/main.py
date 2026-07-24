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

# 日志配置 — 使用用户 home 目录避免权限问题
LOG_DIR = Path.home() / ".wallpace" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
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
    from src.core.settings import Settings
    from src.core.image_library import ImageLibrary
    from src.core.wallpaper_manager import WallpaperManager

    settings = Settings()
    library = ImageLibrary(
        directories=settings.get("image_directories"),
        extensions=settings.get("extensions"),
    )
    wm = WallpaperManager()

    logger = logging.getLogger("main")

    # 验证壁纸管理器是否可用
    if not wm.is_supported:
        logger.error("当前平台不支持壁纸设置操作")

    # Phase 3: 调度器初始化
    from src.core.scheduler import Scheduler

    switch_mode = settings.get("switch_mode", "daily_random")
    daily_time = settings.get("daily_time", "08:00")
    interval_minutes = settings.get("interval_minutes", None)

    scheduler = Scheduler(
        mode=switch_mode,
        daily_time=daily_time,
        interval_minutes=interval_minutes,
    )
    scheduler.set_dependencies(library, wm)

    # Phase 2: 创建 MainWindow
    from src.app.window import MainWindow

    window = MainWindow(
        settings=settings,
        library=library,
        wallpaper_manager=wm,
        scheduler=scheduler,
    )
    if "--hidden" not in sys.argv:
        window.show()

    logger.info("Wallpace v%s 启动", __import__("src").__version__)
    logger.info(
        "配置: %d 个图片目录, %d 张扫描图片",
        library.directory_count,
        library.total_count,
    )
    logger.info("当前壁纸: %s", wm.get_current_wallpaper())
    logger.info("切换模式: %s", scheduler.mode)

    # 启动调度器
    scheduler.start(on_switch=window.on_wallpaper_switched)
    logger.info("调度器已启动 (mode=%s)", scheduler.mode)

    print("Wallpace 正在启动...")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
