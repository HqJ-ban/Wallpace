"""src/core/scheduler.py — 壁纸切换调度器。

控制壁纸自动/手动切换的时间策略。支持三种模式：
- daily_random: 每天指定时间随机切换一张
- interval_minutes: 每隔 N 分钟自动切换
- manual: 只响应手动触发

基于 PySide6 QTimer 实现，与 UI 线程生命周期一致。
遵循 docs/api-design.md Section 3 接口定义。
"""

import logging
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:  # pragma: nocover
    from src.core.image_library import ImageLibrary
    from src.core.wallpaper_manager import WallpaperManager

logger = logging.getLogger(__name__)

VALID_MODES = ("daily_random", "interval_minutes", "manual")


class Scheduler:
    """壁纸切换调度器。

    封装自动切换逻辑：根据配置的模式（每日随机 / 间隔 / 手动），
    在正确的时间调用回调函数完成壁纸切换。
    """

    SWITCH_MODE_DAILY = "daily_random"
    SWITCH_MODE_INTERVAL = "interval_minutes"
    SWITCH_MODE_MANUAL = "manual"

    def __init__(
        self,
        mode: str = SWITCH_MODE_DAILY,
        daily_time: str = "08:00",
        interval_minutes: Optional[int] = None,
    ) -> None:
        """初始化调度器。

        Args:
            mode: 切换模式，必须为 VALID_MODES 之一。
            daily_time: 每日切换时间，格式 "HH:MM"。
            interval_minutes: 间隔切换的分钟数（仅 interval_minutes 模式需要）。
        """
        if mode not in VALID_MODES:
            raise ValueError(
                f"无效模式 '{mode}'，应为 {', '.join(VALID_MODES)}"
            )

        self._mode: str = mode
        self._daily_time_str: str = daily_time
        self._daily_time: dt_time = self._parse_time(daily_time)
        self._interval_minutes: Optional[int] = interval_minutes
        self._is_running: bool = False
        self._is_paused: bool = False

        # PySide6 QTimer 实例
        self._timer: Optional["QTimer"] = None
        self._next_daily_timer: Optional["QTimer"] = None
        self._on_switch: Optional[Callable[[str], None]] = None
        self._library: Optional["ImageLibrary"] = None
        self._wallpaper_manager: Optional["WallpaperManager"] = None

        logger.info(
            "Scheduler 初始化: mode=%s, daily=%s, interval=%s",
            mode, daily_time, interval_minutes,
        )

    # ==================== 公开方法 ====================

    def set_dependencies(
        self,
        library: "ImageLibrary",
        wallpaper_manager: "WallpaperManager",
    ) -> None:
        """注入依赖对象（在 start() 之前调用）。

        Args:
            library: 图片库，用于获取壁纸路径。
            wallpaper_manager: 壁纸管理器，用于设置壁纸。
        """
        self._library = library
        self._wallpaper_manager = wallpaper_manager

    @property
    def mode(self) -> str:
        """当前切换模式。"""
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        """切换模式（停止旧定时器，如需要则启动新定时器）。"""
        old_mode = self._mode
        if value not in VALID_MODES:
            raise ValueError(f"无效模式 '{value}'")
        self._mode = value
        logger.info("模式变更: %s -> %s", old_mode, value)

        # 如果从定时模式切到手动或反向，需要重启定时器
        if (old_mode != "manual") != (value != "manual"):
            if self._is_running and not self._is_paused:
                self.stop()
                self.start(self._on_switch)
            elif self._is_running:
                # paused 状态：先停止再重新开始
                self.stop()
                self.resume()

    def start(self, on_switch: Optional[Callable[[str], None]] = None) -> None:
        """启动调度器。

        Args:
            on_switch: 切换完成后的回调函数（可选），参数为新壁纸路径。
        """
        if self._is_running and not self._is_paused:
            logger.warning("调度器已在运行，忽略 start()")
            return

        if self._is_paused:
            self._resume_timers()
            return

        self._on_switch = on_switch
        self._is_running = True
        self._is_paused = False

        # 需要在 Qt event loop 中运行，这里用 QTimer 延迟初始化
        if self._mode == self.SWITCH_MODE_DAILY:
            self._start_daily_timer()
        elif self._mode == self.SWITCH_MODE_INTERVAL:
            self._start_interval_timer()
        else:
            logger.info("手动模式: 不启动自动定时器")

    def trigger_now(self) -> None:
        """立即触发一次壁纸切换（无论什么模式）。"""
        if self._library is None or self._wallpaper_manager is None:
            logger.error("调度器未注入 library/wallpaper_manager")
            return

        image_path = self._library.get_random()
        if image_path is None:
            logger.warning("没有可用图片可切换")
            return

        success = self._wallpaper_manager.set_wallpaper(image_path)
        if success:
            logger.info("手动触发切换: %s", Path(image_path).name)
            if self._on_switch:
                self._on_switch(image_path)
        else:
            logger.error("手动切换失败")

    def pause(self) -> None:
        """暂停定时任务。"""
        if not self._is_running:
            logger.warning("调度器未运行，无法暂停")
            return
        self._is_paused = True
        self._pause_timers()
        logger.info("调度器已暂停")

    def resume(self) -> None:
        """恢复已暂停的任务。"""
        if not self._is_running:
            logger.warning("调度器未运行")
            return
        if not self._is_paused:
            logger.warning("调度器未在暂停状态")
            return
        self._is_paused = False
        self._resume_timers()
        logger.info("调度器已恢复")

    def stop(self) -> None:
        """停止并销毁所有定时器。"""
        self._is_running = False
        self._is_paused = False
        self._pause_timers()
        logger.info("调度器已停止")

    @property
    def is_active(self) -> bool:
        """是否正在运行。"""
        return self._is_running and not self._is_paused

    @property
    def is_paused(self) -> bool:
        """是否被暂停。"""
        return self._is_running and self._is_paused

    # ==================== 私有方法 ====================

    def _parse_time(self, time_str: str) -> "dt_time":
        """解析 HH:MM 时间字符串。"""
        try:
            h, m = map(int, time_str.split(":"))
            return dt_time(h, m)
        except (ValueError, AttributeError):
            raise ValueError(f"无效时间格式 '{time_str}'，应为 HH:MM")

    def _start_daily_timer(self) -> None:
        """启动每日定时任务：计算距下次切换时间的毫秒数。"""
        now = datetime.now()
        target_today = now.replace(
            hour=self._daily_time.hour,
            minute=self._daily_time.minute,
            second=0, microsecond=0,
        )
        # 如果今天已过目标时间，设定为明天同一时间
        if target_today <= now:
            target_today += datetime.timedelta(days=1)

        delay_ms = int((target_today - now).total_seconds() * 1000)
        logger.info(
            "每日模式: 距离下次切换 %.1f 秒 (%d ms)",
            delay_ms / 1000, delay_ms,
        )

        self._schedule_once(delay_ms, self._do_daily_switch)

    def _start_interval_timer(self) -> None:
        """启动间隔定时任务。"""
        if self._interval_minutes is None or self._interval_minutes <= 0:
            raise ValueError("interval_minutes 必须 > 0")
        delay_ms = self._interval_minutes * 60 * 1000
        logger.info(
            "间隔模式: 每 %d 分钟切换一次 (%d ms)",
            self._interval_minutes, delay_ms,
        )
        self._start_repeating_timer(delay_ms, self._do_interval_switch)

    def _schedule_once(self, delay_ms: int, callback: Callable) -> None:
        """调度一次性定时器（在 QApplication 可用时绑定 QTimer）。"""
        from PySide6.QtCore import QTimer
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(callback)
        timer.start(delay_ms)
        self._timer = timer

    def _start_repeating_timer(self, delay_ms: int, callback: Callable) -> None:
        """调度重复定时器。"""
        from PySide6.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(callback)
        timer.start(delay_ms)
        self._timer = timer

    def _resume_timers(self) -> None:
        """恢复已暂停的定时器。"""
        if self._mode == self.SWITCH_MODE_DAILY:
            self._start_daily_timer()
        elif self._mode == self.SWITCH_MODE_INTERVAL:
            self._start_interval_timer()

    def _pause_timers(self) -> None:
        """暂停/销毁所有定时器。"""
        if self._timer is not None:
            self._timer.stop()
            self._timer.deleteLater()
            self._timer = None

    def _do_daily_switch(self) -> None:
        """执行每日随机切换。"""
        if self._library is None or self._wallpaper_manager is None:
            logger.warning("library/wallpaper_manager 未就绪")
            return

        image_path = self._library.get_random()
        if image_path is None:
            logger.warning("无可用的图片")
            return

        success = self._wallpaper_manager.set_wallpaper(image_path)
        if success:
            logger.info("每日自动切换: %s", Path(image_path).name)
            if self._on_switch:
                self._on_switch(image_path)

        # 切换完成后重新调度下一天
        if self._is_running and not self._is_paused:
            self._start_daily_timer()

    def _do_interval_switch(self) -> None:
        """执行间隔切换。"""
        if self._library is None or self._wallpaper_manager is None:
            logger.warning("library/wallpaper_manager 未就绪")
            return

        image_path = self._library.get_random()
        if image_path is None:
            logger.warning("无可用的图片")
            return

        success = self._wallpaper_manager.set_wallpaper(image_path)
        if success:
            logger.info("间隔自动切换: %s", Path(image_path).name)
            if self._on_switch:
                self._on_switch(image_path)
