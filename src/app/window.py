"""src/app/window.py — 主窗口 (B 方案: 图标侧边栏 + 粉蓝渐变)。

包含：顶栏、侧边导航、QStackedWidget 内容区、底部状态栏。
遵循 MVC 分离：UI 只负责展示和用户交互，业务逻辑委托给 core 层。
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from src.core.image_library import ImageLibrary
    from src.core.scheduler import Scheduler
    from src.core.settings import Settings
    from src.core.wallpaper_manager import WallpaperManager

from src.app.sidebar import SidebarNavigation
from src.app.theme import COLOR_BLUE_DARK, COLOR_GRAY_50, COLOR_GRAY_800, COLOR_PINK_LIGHT, COLOR_BLUE_LIGHT, COLOR_GRAY_100, ThemeManager
from src.app.tray import TrayIcon
from src.app.widgets.preview_card import PreviewCardWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """主窗口，承载整个应用的 UI。

    结构：
        窗口
        ├── 顶栏（渐变背景 + 应用名称）
        └── 中心区域（水平布局）
            ├── 侧边栏导航（导航按钮 -> 切换 QStackedWidget）
            └── QStackedWidget
                ├── 页面 0: 壁纸预览 (PreviewCardWidget)
                ├── 页面 1: 图片库缩略图网格
                ├── 页面 2: 时钟信息页
                └── 页面 3: 设置面板
        └── 底部状态栏
    """

    SWITCH_REQUESTED = 1
    FAVORITE_REQUESTED = 2

    def __init__(
        self,
        settings: "Settings",
        library: "ImageLibrary",
        wallpaper_manager: "WallpaperManager",
        scheduler: Optional["Scheduler"] = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._settings = settings
        self._library = library
        self._wallpaper_manager = wallpaper_manager
        self._scheduler = scheduler

        self._current_image_index = 0

        self._setup_window()
        self._setup_ui()

    def _setup_window(self) -> None:
        """窗口基本属性。"""
        self.setWindowTitle("Wallpace")
        self.setMinimumSize(800, 540)
        self.resize(960, 620)
        logger.info("主窗口初始化完成")

    def _setup_ui(self) -> None:
        """构建所有 UI 组件。"""
        theme = ThemeManager()
        self.setStyleSheet(theme.light_qss())

        # 中心容器
        central = QWidget()
        self.setCentralWidget(central)
        # === 顶部渐变栏 ===
        top_bar = QFrame()
        top_bar.setObjectName("top_bar")
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet(theme.top_bar_gradient_css())
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(20, 10, 20, 10)

        self._top_title = QLabel("Wallpace")
        self._top_title.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold;"
        )
        top_bar_layout.addWidget(self._top_title)

        self._top_status = QLabel("● 未启动")
        self._top_status.setStyleSheet(
            "color: rgba(255,255,255,0.7); font-size: 12px;"
        )
        top_bar_layout.addWidget(self._top_status)
        top_bar_layout.setStretchFactor(self._top_status, 0)

        # === 侧边栏 + 内容区 ===
        body_layout = QHBoxLayout()
        body_layout.setSpacing(0)
        body_layout.setContentsMargins(0, 0, 0, 0)

        # 分隔线
        divider = QFrame()
        divider.setObjectName("sidebar_divider")
        divider.setFixedWidth(1)
        divider.setStyleSheet("background-color: #eeeeee;")

        # 右侧堆叠页面
        self._stacked = QStackedWidget()
        self._stacked.setContentsMargins(0, 0, 0, 0)

        # ---- 页面 0: 壁纸预览 ----
        self._preview_page = self._build_preview_page()
        self._stacked.addWidget(self._preview_page)

        # ---- 页面 1: 图片库（占位） ----
        gallery_placeholder = self._build_gallery_placeholder()
        self._stacked.addWidget(gallery_placeholder)

        # ---- 页面 2: 时钟（占位） ----
        clock_placeholder = self._build_clock_placeholder()
        self._stacked.addWidget(clock_placeholder)

        # ---- 页面 3: 设置面板 ----
        settings_page = self._build_settings_page()
        self._stacked.addWidget(settings_page)

        body_layout.addWidget(divider)
        body_layout.addWidget(self._stacked, stretch=1)

        # 侧边栏
        self._sidebar = SidebarNavigation(
            stacked=self._stacked,
            on_settings_open=self.open_settings,
            on_action_switch=self.request_switch,
            on_action_skip=self._handle_skip,
            on_action_favorite=lambda: None,  # handled via preview_card favorite signal
        )
        body_layout.insertWidget(0, self._sidebar)

        # 合并到中心布局
        vertical_layout = QVBoxLayout(central)
        vertical_layout.setContentsMargins(0, 0, 0, 0)
        vertical_layout.setSpacing(0)
        vertical_layout.addWidget(top_bar)
        vertical_layout.addLayout(body_layout)

        # === Bottom status bar ===
        self._bottom_bar = QFrame()
        self._bottom_bar.setObjectName("bottom_bar")
        self._bottom_bar.setFixedHeight(28)
        bottom_layout = QHBoxLayout(self._bottom_bar)
        bottom_layout.setContentsMargins(16, 4, 16, 4)
        bottom_layout.setSpacing(12)

        self._bottom_source_label = QLabel()
        self._bottom_source_label.setStyleSheet("font-size: 11px; color: #9e9e9e;")
        bottom_layout.addWidget(self._bottom_source_label)

        self._bottom_notifier_label = QLabel()
        self._bottom_notifier_label.setStyleSheet("font-size: 11px; color: #9e9e9e;")
        bottom_layout.addWidget(self._bottom_notifier_label)

        self._bottom_fav_count = QLabel()
        self._bottom_fav_count.setStyleSheet("font-size: 11px; color: #9e9e9e;")
        bottom_layout.addWidget(self._bottom_fav_count)

        bottom_layout.addStretch()

        self._bottom_version = QLabel("v0.1.0")
        self._bottom_version.setStyleSheet("font-size: 11px; color: #bdbdbd;")
        bottom_layout.addWidget(self._bottom_version)

        vertical_layout.addWidget(self._bottom_bar)

        # === 托盘 ===
        self._tray = TrayIcon(self)
        self._tray.show()

        # === 初始化数据 ===
        self._refresh_gallery()
        logger.info("UI 初始化完成")

    # ===== 页面构建 =====

    def _build_preview_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(8)

        # 标题行
        title_row = QHBoxLayout()
        title_row.setContentsMargins(24, 0, 0, 0)

        current_label = QLabel("当前壁纸")
        current_label.setObjectName("subtitle")
        title_row.addWidget(current_label)

        title_row.addStretch()

        date_label = QLabel()
        date_label.setObjectName("sub-title")
        date_label.setText(self._get_date_string())
        title_row.addWidget(date_label)

        layout.addLayout(title_row)

        # 预览卡片
        scroll = QFrame()
        scroll.setStyleSheet("QFrame { background-color: transparent; }")
        scroll_scroll_layout = QVBoxLayout(scroll)
        scroll_scroll_layout.setContentsMargins(24, 8, 24, 24)
        scroll_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._preview_card = PreviewCardWidget()
        self._preview_card.switch_clicked.connect(self._handle_switch)
        self._preview_card.skip_clicked.connect(self._handle_skip)
        self._preview_card.favorite_clicked.connect(self._handle_favorite)
        scroll_scroll_layout.addWidget(self._preview_card)
        layout.addWidget(scroll, stretch=1)


        # === Info Grid (3 stat cards) ===
        info_grid = QFrame()
        info_grid.setObjectName("info_grid")
        info_layout = QHBoxLayout(info_grid)
        info_layout.setContentsMargins(24, 8, 24, 8)
        info_layout.setSpacing(12)

        self._method_card = self._make_info_card("切换方式", "每日随机")
        info_layout.addWidget(self._method_card)

        info_layout.addSpacing(12)

        self._next_time_card = self._make_info_card("下次切换", "明天 08:00", highlight=True)
        info_layout.addWidget(self._next_time_card)

        info_layout.addSpacing(12)

        self._count_card = self._make_info_card("图片总数", str(self._library.total_count))
        info_layout.addWidget(self._count_card)

        layout.addWidget(info_grid)


        # === Gallery Horizontal Scroll Section ===
        gallery_section = QFrame()
        gallery_section.setObjectName("gallery-section")
        gallery_layout = QVBoxLayout(gallery_section)
        gallery_layout.setContentsMargins(24, 12, 24, 12)
        gallery_layout.setSpacing(8)

        gallery_title = QLabel("图片库")
        gallery_title.setObjectName("subtitle")
        gallery_layout.addWidget(gallery_title)

        # Horizontal scroll area for thumbnails
        self._gallery_scroll = QScrollArea()
        self._gallery_scroll.setFixedHeight(100)
        self._gallery_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._gallery_scroll.setWidgetResizable(True)
        self._gallery_content = QWidget()
        self._gallery_layout = QHBoxLayout(self._gallery_content)
        self._gallery_layout.setContentsMargins(0, 0, 0, 0)
        self._gallery_layout.setSpacing(8)
        self._gallery_scroll.setWidget(self._gallery_content)
        gallery_layout.addWidget(self._gallery_scroll)

        layout.addWidget(gallery_section)


        return page

    def _make_info_card(self, label, value, highlight=False):
        card = QFrame()
        card.setObjectName("info-card")
        if highlight:
            card.setProperty("highlight", "true")
            card.setStyleSheet(
                "QFrame#info-card { background-color: transparent; border-radius: 10px; padding: 10px; border: none; } "
                "QFrame#info-card[highlight='true'] { "
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #fce4ec, stop:1 #bbdefb); }"
            )
        else:
            card.setStyleSheet(
                "QFrame#info-card { background-color: #fafafa; border-radius: 10px; padding: 10px; border: 1px solid #eeeeee; }"
            )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)

        lbl = QLabel(label)
        lbl.setObjectName("sub-title")
        lbl.setStyleSheet("font-size: 11px; color: #9e9e9e;")
        card_layout.addWidget(lbl)

        val = QLabel(value)
        val.setObjectName("stat-value")
        val.setStyleSheet("font-size: 16px; font-weight: 600; color: #424242;")
        card_layout.addWidget(val)

        return card

    def _build_gallery_placeholder(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 16, 24, 16)

        title = QLabel("图片库")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        info = QLabel("添加图片文件夹后，这里会显示缩略图预览")
        info.setObjectName("sub-title")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("padding: 20px 0;")
        layout.addWidget(info)
        layout.addStretch()
        return page

    def _build_clock_placeholder(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 16, 24, 16)

        time_label = QLabel(self._get_time_string())
        time_label.setObjectName("title")
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_label.setStyleSheet(f"font-size: 48px; color: {COLOR_BLUE_DARK};")
        layout.addWidget(time_label)

        info = QLabel("切换策略设置后将实时更新")
        info.setObjectName("sub-title")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 16, 24, 16)

        title = QLabel("设置")
        title.setObjectName("title")
        layout.addWidget(title)
        layout.addSpacing(8)

        # --- 分组: 图片库 ---
        group_images = QFrame()
        group_images.setObjectName("settings_group")
        group_layout = QVBoxLayout(group_images)
        group_layout.setContentsMargins(12, 12, 12, 12)

        dir_label = QLabel("图片文件夹")
        dir_label.setObjectName("sub-title")
        group_layout.addWidget(dir_label)

        dirs = self._settings.get("image_directories", [])
        dirs_text = ", ".join(dirs) if dirs else "未配置（在设置中配置）"
        info_dirs = QLabel(dirs_text)
        info_dirs.setWordWrap(True)
        info_dirs.setStyleSheet(
            f"background-color: {COLOR_GRAY_100}; "
            "border-radius: 6px; "
            "padding: 8px; font-size: 12px;"
        )
        group_layout.addWidget(info_dirs)

        btn_add = QPushButton("添加文件夹")
        btn_add.setStyleSheet(
            "QPushButton { padding: 6px 16px; border-radius: 6px; }"
        )
        btn_add.clicked.connect(lambda: logger.info("添加文件夹（待实现）"))
        group_layout.addWidget(btn_add)

        layout.addWidget(group_images)
        layout.addSpacing(16)

        # --- 分组: 切换策略 ---
        group_switch = QFrame()
        group_switch.setObjectName("settings_group")
        switch_layout = QVBoxLayout(group_switch)
        switch_layout.setContentsMargins(12, 12, 12, 12)

        mode_label = QLabel("切换模式")
        mode_label.setObjectName("sub-title")
        switch_layout.addWidget(mode_label)

        mode_val = self._settings.get("switch_mode", "daily_random")
        mode_info = QLabel(f"当前: {mode_val}")
        mode_info.setStyleSheet(
            f"background-color: {COLOR_GRAY_100}; "
            "border-radius: 6px; "
            "padding: 8px; font-size: 12px;"
        )
        switch_layout.addWidget(mode_info)

        # 如果是 interval_minutes 模式，显示间隔时间
        if mode_val == "interval_minutes":
            interval = self._settings.get("interval_minutes")
            if interval:
                interval_info = QLabel(f"间隔: {interval} 分钟")
                interval_info.setStyleSheet(
                    f"background-color: {COLOR_GRAY_100}; "
                    "border-radius: 6px; "
                    "padding: 8px; font-size: 12px;"
                )
                switch_layout.addWidget(interval_info)

        layout.addWidget(group_switch)
        layout.addStretch()

        return page

    # ===== 业务操作 =====

    def _handle_switch(self) -> None:
        """处理用户点击'换一张'。"""
        if self._scheduler is not None:
            self._scheduler.trigger_now()
            return

        image_path = self._library.get_random()
        if image_path is None:
            logger.warning("无法获取随机图片")
            return

        success = self._wallpaper_manager.set_wallpaper(image_path)
        if success:
            available = self._library.list_available()
            index = available.index(image_path) if image_path in available else 0
            self._update_preview(image_path, index)
            logger.info("壁纸切换成功: %s", image_path)
        else:
            logger.error("壁纸设置失败: %s", image_path)

    def _handle_skip(self) -> None:
        """处理用户点击'跳过'。"""
        if not self._preview_card._current_path:
            return
        self._library.skip(self._preview_card._current_path)
        logger.info("已跳过: %s", self._preview_card._current_path)

    def _handle_favorite(self) -> None:
        """处理用户点击'收藏'。"""
        if not self._preview_card._current_path:
            return
        is_new_fav = self._library.favorite(self._preview_card._current_path)
        if is_new_fav:
            logger.info("已收藏: %s", self._preview_card._current_path)
        else:
            # It was already in fav_set (idempotent), try unfavorite
            self._library.unfavorite(self._preview_card._current_path)
            logger.info("取消收藏: %s", self._preview_card._current_path)
        # Update sidebar star icon
        if hasattr(self, "_sidebar") and self._sidebar:
            is_favorited = self._preview_card._current_path in self._library._favorite_set
            if len(getattr(self._sidebar, "_action_buttons", [])) >= 3:
                self._sidebar._action_buttons[2].set_active(is_favorited)

    @Slot(str)
    def on_wallpaper_switched(self, path: str) -> None:
        """调度器触发切换后的回调，更新 UI。"""
        try:
            available = self._library.list_available()
            index = available.index(path) if path in available else 0
            self._update_preview(path, index)
        except Exception:
            logger.exception("更新 UI 失败")

    def request_switch(self) -> None:
        """供托盘菜单调用的公共切换入口。"""
        self._handle_switch()

    def pause_scheduler(self) -> None:
        if self._scheduler is not None:
            self._scheduler.pause()
        self._tray.update_pause_status(True)
        logger.info("调度已暂停")

    def resume_scheduler(self) -> None:
        if self._scheduler is not None:
            self._scheduler.resume()
        self._tray.update_pause_status(False)
        logger.info("调度已恢复")

    # ===== UI 更新 =====

    def _update_preview(self, path: str, index: int) -> None:
        """更新预览卡片和页面状态。"""
        self._current_image_index = index
        self._preview_card.update_preview(path, index, self._library.total_count)


        file_name = Path(path).stem
        self._tray.setToolTip(f"Wallpace -- {file_name}")


    def _refresh_gallery(self) -> None:
        """刷新扫描并更新 UI。"""
        images = self._library.scan()
        if images:
            first = images[0]
            self._update_preview(first, 0)
            logger.info("刷新图片库: %d 张", len(images))
            self._refresh_gallery_thumbnails()
        else:

            pass
    def _refresh_gallery_thumbnails(self) -> None:
        """Populate gallery horizontal scroll with thumbnails."""
        # Clear existing widgets
        for i in reversed(range(self._gallery_layout.count())):
            widget = self._gallery_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        images = self._library.list_available()
        for img_path in images[:20]:  # Show first 20
            lbl = QLabel()
            lbl.setFixedSize(80, 60)
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(80, 60, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                lbl.setPixmap(scaled)
            lbl.setStyleSheet(
                "QLabel { border-radius: 6px; background-color: #f5f5f5; border: 1px solid #eeeeee; }"
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._gallery_layout.addWidget(lbl)


        # Update bottom and top status bars
        self.update_bottom_bar()
        self.update_top_status()

    def update_top_status(self) -> None:
        """Update the top bar status badge based on scheduler state."""
        if self._scheduler is None:
            self._top_status.setText("● 未启动")
            return
        mode = self._scheduler.mode
        if not self._scheduler.is_active:
            self._top_status.setText("● 已暂停")
        elif mode == "daily_random":
            next_switch = self._scheduler.get_next_switch_time()
            if next_switch:
                self._top_status.setText(f"● 已启用 · 明天 {next_switch.strftime('%H:%M')} 切换")
            else:
                self._top_status.setText("● 已启用 · 明天自动切换")
        elif mode == "interval_minutes":
            mins = self._scheduler.interval_minutes or 60
            self._top_status.setText(f"● 已启用 · 每 {mins} 分钟")
        elif mode == "manual":
            self._top_status.setText("● 已启用 · 手动模式")

    def update_bottom_bar(self) -> None:
        """Update bottom status bar with current library info."""
        images = self._library.list_available()
        dirs = self._library._directories or ["未配置"]
        dir_text = ", ".join(dirs[:2])  # show first two dirs
        fav_count = len(self._library.favorites)
        enabled = "已启用" if self._scheduler and self._scheduler.is_active else "已暂停"
        icon_folder = "\U0001f4c2"  # 📂 folder
        self._bottom_source_label.setText(
            icon_folder + " " + dir_text + " (" + str(len(images)) + "/" + str(self._library.total_count) + ")"
        )
        star_icon = chr(0x2605)
        bell_icon = chr(0x1f441)
        self._bottom_fav_count.setText(star_icon + " " + str(fav_count))
        self._bottom_notifier_label.setText(bell_icon + " " + enabled)

    def open_settings(self) -> None:
        """切换到设置页面。"""
        logger.debug("打开设置页面")
        self._stacked.setCurrentIndex(3)
        self._set_active_button("settings")

    def _set_active_button(self, page_id: str) -> None:
        """供 SidebarNavigation 外部调用。"""
        if hasattr(self, "_sidebar"):
            self._sidebar.set_active_button(page_id)

    def _get_time_string(self) -> str:
        now = datetime.now()
        return now.strftime("%H:%M:%S")

    def _get_date_string(self) -> str:
        now = datetime.now()
        return now.strftime("%Y年%m月%d日")

    def closeEvent(self, event) -> None:
        """托盘图标清理"""
        super().closeEvent(event)
        if hasattr(self, "_tray") and self._tray is not None:
            self._tray.setVisible(False)
            self._tray.deleteLater()
        if hasattr(self, "_scheduler") and self._scheduler is not None:
            self._scheduler.stop()
