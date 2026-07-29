"""src/app/window.py — 主窗口 (B 方案: 图标侧边栏 + 粉蓝渐变)。

包含：顶栏、侧边导航、QStackedWidget 内容区、底部状态栏。
遵循 MVC 分离：UI 只负责展示和用户交互，业务逻辑委托给 core 层。
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLineEdit,
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
from src.app.theme import (
    COLOR_BLUE_DARK,
    COLOR_GRAY_100,
    COLOR_GRAY_50,
    COLOR_GRAY_800,
    COLOR_PINK_LIGHT,
    COLOR_BLUE_LIGHT,
    ThemeManager,
)
from src.app.tray import TrayIcon
from src.app.widgets.preview_card import PreviewCardWidget

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helper: clickable gallery thumbnail widget
# ---------------------------------------------------------------------------


class _GalleryThumbWidget(QLabel):
    """可点击的图片库缩略图，支持高亮当前选中项。"""

    clicked = Signal(str)  # emits image path on click

    def __init__(
        self,
        image_path: str,
        is_current: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._image_path = image_path
        self._is_current = is_current
        self.setFixedSize(80, 60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._load_pixmap()
        self._apply_style()

    def _load_pixmap(self) -> None:
        pixmap = QPixmap(self._image_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                80,
                60,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)

    def _apply_style(self) -> None:
        border_color = "#ec4899" if self._is_current else "#eeeeee"
        self.setStyleSheet(
            "QLabel { "
            f"border-radius: 6px; background-color: #f5f5f5; "
            f"border: 2px solid {border_color}; "
            "}"
        )

    def set_is_current(self, current: bool) -> None:
        self._is_current = current
        self._apply_style()

    def mousePressEvent(self, event) -> None:  # noqa: ANN001
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._image_path)
        super().mousePressEvent(event)


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
        self._clock_timer: Optional["QTimer"] = None

        self._setup_window()
        self._setup_ui()
        self._start_clock_timer()

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
            on_action_switch=self.request_switch,  # 虽然按钮被移除，但保留以防未来使用
            on_action_skip=self._handle_skip,
            on_action_favorite=self._handle_favorite,  # 连接到收藏处理
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

        # 空状态引导提示（默认隐藏）
        self._empty_guide = QLabel(
            "📂 还没有添加图片文件夹\n"
            "点击左侧「设置」→「添加文件夹」来选择壁纸文件夹"
        )
        self._empty_guide.setObjectName("empty_guide")
        self._empty_guide.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_guide.setWordWrap(True)
        self._empty_guide.setStyleSheet(
            "QLabel#empty_guide { "
            "background-color: #fafafa; "
            "border: 2px dashed #e0e0e0; border-radius: 12px; "
            "padding: 40px 20px; "
            "font-size: 14px; color: #9e9e9e; "
            "margin: 40px 24px; "
            "}"
        )
        self._empty_guide.setVisible(False)
        layout.addWidget(self._empty_guide)

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

        mode_name = self._settings.get("switch_mode", "daily_random")
        mode_display = {"daily_random": "每日随机", "interval_minutes": f"每{self._settings.get('interval_minutes', 60)}分钟", "manual": "手动"}
        self._method_card = self._make_info_card("切换方式", mode_display.get(mode_name, "每日随机"))
        info_layout.addWidget(self._method_card)

        info_layout.addSpacing(12)

        total = self._library.total_count
        next_time = f"明天 {self._settings.get('daily_time', '08:00')}" if total > 0 else "添加图片后"
        self._next_time_card = self._make_info_card(
            "下次切换", next_time, highlight=True
        )
        info_layout.addWidget(self._next_time_card)

        info_layout.addSpacing(12)

        self._count_card = self._make_info_card(
            "图片总数", str(total)
        )
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
        self._gallery_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._gallery_scroll.setWidgetResizable(True)
        self._gallery_content = QWidget()
        self._gallery_layout = QHBoxLayout(self._gallery_content)
        self._gallery_layout.setContentsMargins(0, 0, 0, 0)
        self._gallery_layout.setSpacing(8)
        self._gallery_scroll.setWidget(self._gallery_content)
        gallery_layout.addWidget(self._gallery_scroll)

        layout.addWidget(gallery_section)

        return page

    def _make_info_card(self, label: str, value: str, highlight: bool = False) -> QFrame:
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

        self._clock_time_label = QLabel(self._get_time_string())
        self._clock_time_label.setObjectName("title")
        self._clock_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._clock_time_label.setStyleSheet(
            f"font-size: 48px; color: {COLOR_BLUE_DARK}; font-weight: bold; "
        )
        layout.addWidget(self._clock_time_label)

        self._clock_date_label = QLabel(self._get_date_string())
        self._clock_date_label.setObjectName("sub-title")
        self._clock_date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._clock_date_label.setStyleSheet(
            f"font-size: 18px; color: {COLOR_GRAY_500}; margin-bottom: 20px;"
        )
        layout.addWidget(self._clock_date_label)

        # 下次切换信息
        self._clock_next_label = QLabel(self._get_next_switch_text())
        self._clock_next_label.setObjectName("sub-title")
        self._clock_next_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._clock_next_label.setStyleSheet(
            f"font-size: 14px; color: {COLOR_GRAY_800}; padding: 8px;"
        )
        layout.addWidget(self._clock_next_label)

        layout.addStretch()
        return page

    # ===== 时钟定时器 =====

    def _start_clock_timer(self) -> None:
        """启动一个定时器，每秒更新时钟显示。"""
        from PySide6.QtCore import QTimer

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)  # 每秒更新

    def _update_clock(self) -> None:
        """每秒更新时钟页面和顶部日期显示。"""
        now = datetime.now()
        if hasattr(self, "_clock_time_label"):
            self._clock_time_label.setText(now.strftime("%H:%M:%S"))
        if hasattr(self, "_clock_date_label"):
            self._clock_date_label.setText(now.strftime("%Y年%m月%d日  %A"))
        if hasattr(self, "_clock_next_label"):
            self._clock_next_label.setText(self._get_next_switch_text())

    def _get_next_switch_text(self) -> str:
        """获取下次切换时间的描述文本。"""
        if self._scheduler is None:
            return "调度器未启动"
        if not self._scheduler.is_active:
            return "● 调度已暂停"
        mode = self._scheduler.mode
        if mode == "daily_random":
            next_time = self._scheduler.get_next_switch_time()
            if next_time:
                delta = next_time - datetime.now()
                hours, remainder = divmod(int(delta.total_seconds()), 3600)
                minutes = remainder // 60
                return f"下次切换: {hours}小时{minutes}分钟后 ({next_time.strftime('%H:%M')})"
            return "下次切换: 明天自动切换"
        elif mode == "interval_minutes":
            mins = self._scheduler.interval_minutes or 60
            return f"每 {mins} 分钟自动切换一次"
        elif mode == "manual":
            return "手动模式，不会自动切换"
        return ""

    def _build_settings_page(self) -> QWidget:
        """构建设置页面，包含文件夹添加和模式切换功能。"""
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

        # 目录列表（每个目录显示路径 + 删除按钮）
        self._dirs_layout = QVBoxLayout()
        self._dirs_layout.setSpacing(4)
        self._refresh_dir_list()
        group_layout.addLayout(self._dirs_layout)

        # 添加/删除按钮行
        btn_row = QHBoxLayout()
        btn_add = QPushButton("添加文件夹")
        btn_add.setStyleSheet(
            "QPushButton { padding: 6px 16px; border-radius: 6px; }"
        )
        btn_add.clicked.connect(self._add_directory)
        btn_row.addWidget(btn_add)

        btn_remove = QPushButton("移除文件夹")
        btn_remove.setStyleSheet(
            "QPushButton { padding: 6px 16px; border-radius: 6px; "
            "color: #c62828; border: 1px solid #ffcdd2; }"
        )
        btn_remove.clicked.connect(self._remove_directory)
        btn_row.addWidget(btn_remove)
        btn_row.addStretch()
        group_layout.addLayout(btn_row)

        # 显示当前配置的图片目录数量
        self._dir_count_label = QLabel(f"共 {len(dirs)} 个目录")
        self._dir_count_label.setStyleSheet("font-size: 11px; color: #9e9e9e; margin-top: 4px;")
        group_layout.addWidget(self._dir_count_label)

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

        # 模式选择器
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["每日随机", "间隔时间", "手动"])
        current_mode = self._settings.get("switch_mode", "daily_random")
        # 映射内部模式名到显示文本
        mode_display_map = {
            "daily_random": "每日随机",
            "interval_minutes": "间隔时间",
            "manual": "手动",
        }
        display_text = mode_display_map.get(current_mode, "每日随机")
        self._mode_combo.setCurrentText(display_text)
        self._mode_combo.currentTextChanged.connect(self._on_mode_changed)
        switch_layout.addWidget(self._mode_combo)

        # 显示当前模式描述
        self._mode_desc = QLabel("")
        self._mode_desc.setStyleSheet("font-size: 12px; color: #424242; margin-top: 4px;")
        self._update_mode_description(current_mode)
        switch_layout.addWidget(self._mode_desc)

        # 间隔时间输入框（仅间隔模式可见）
        self._interval_group = QFrame()
        interval_layout = QVBoxLayout(self._interval_group)
        interval_layout.setContentsMargins(0, 4, 0, 0)
        interval_label = QLabel("间隔时间（分钟）:")
        interval_label.setStyleSheet("font-size: 12px;")
        self._interval_input = QLineEdit()
        self._interval_input.setPlaceholderText("例如：30")
        self._interval_input.setMaximumWidth(100)
        interval_layout.addWidget(interval_label)

        interval_input_row = QHBoxLayout()
        interval_input_row.addWidget(self._interval_input)
        btn_apply_interval = QPushButton("应用")
        btn_apply_interval.setFixedHeight(26)
        btn_apply_interval.setStyleSheet(
            "QPushButton { padding: 2px 12px; border-radius: 6px; "
            "background-color: #5c6bc0; color: white; font-weight: 600; font-size: 12px; }"
            "QPushButton:hover { background-color: #7986cb; }"
        )
        btn_apply_interval.clicked.connect(self._apply_interval)
        interval_input_row.addWidget(btn_apply_interval)
        interval_input_row.addStretch()
        interval_layout.addLayout(interval_input_row)

        self._interval_group.setVisible(False)
        switch_layout.addWidget(self._interval_group)

        layout.addWidget(group_switch)
        layout.addStretch()

        return page

    # ===== 设置页面的辅助方法 =====

    def _add_directory(self) -> None:
        """打开文件夹选择对话框，添加到图片目录列表。"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择图片文件夹", ""
        )
        if folder:
            dirs = self._settings.get("image_directories", [])
            if folder not in dirs:
                dirs.append(folder)
                self._settings.set("image_directories", dirs)
                self._library.scan()
                self._refresh_gallery()
                self._update_settings_page_display()
                logger.info("已添加图片目录: %s", folder)

    def _on_mode_changed(self, text: str) -> None:
        """处理模式切换。"""
        mode_display_map = {
            "daily_random": "每日随机",
            "interval_minutes": "间隔时间",
            "manual": "手动",
        }
        reverse_mode_map = {v: k for k, v in mode_display_map.items()}
        internal_mode = reverse_mode_map.get(text, "daily_random")

        # 保存模式到 settings
        self._settings.set("switch_mode", internal_mode)

        # 如果是 interval_minutes 模式，从 settings 读取现有的间隔值
        if internal_mode == "interval_minutes":
            interval_val = self._settings.get("interval_minutes", 60)
            if interval_val is None or interval_val <= 0:
                interval_val = 60
            # 将已有的间隔值显示到输入框
            self._interval_input.setText(str(interval_val))
            # 如果调度器存在但 interval 值不同，更新调度器的间隔值
            if self._scheduler and self._scheduler._interval_minutes != interval_val:
                self._scheduler._interval_minutes = interval_val
            self._interval_group.setVisible(True)
        else:
            self._interval_group.setVisible(False)

        # 管理调度器
        if self._scheduler is not None:
            if self._scheduler.is_running:
                self._scheduler.stop()
            self._scheduler.mode = internal_mode
            if internal_mode != "manual" and not self._scheduler.is_running:
                self._scheduler.start(on_switch=self.on_wallpaper_switched)

        self._update_mode_description(internal_mode)
        self._update_settings_page_display()

    def _update_mode_description(self, mode: str) -> None:
        """更新模式描述标签的文字。"""
        descriptions = {
            "daily_random": "每天指定时间随机切换一张壁纸",
            "interval_minutes": "每隔设定的时间自动切换",
            "manual": "只响应手动切换操作，无自动切换",
        }
        self._mode_desc.setText(descriptions.get(mode, ""))

    def _update_settings_page_display(self) -> None:
        """更新设置页面中显示的目录计数等信息。"""
        dirs = self._settings.get("image_directories", [])
        if hasattr(self, '_dir_count_label'):
            self._dir_count_label.setText(f"共 {len(dirs)} 个目录")
        self._refresh_dir_list()

    def _refresh_dir_list(self) -> None:
        """刷新设置页面的目录列表显示。"""
        if not hasattr(self, '_dirs_layout'):
            return
        # 清除旧的子 widget
        while self._dirs_layout.count():
            widget = self._dirs_layout.itemAt(0).widget()
            if widget:
                widget.deleteLater()
            else:
                self._dirs_layout.removeItem(self._dirs_layout.itemAt(0))

        dirs = self._settings.get("image_directories", [])
        if not dirs:
            empty_label = QLabel("未配置图片文件夹，请点击「添加文件夹」")
            empty_label.setStyleSheet(
                f"background-color: {COLOR_GRAY_100}; "
                "border-radius: 6px; padding: 8px; font-size: 12px; color: #9e9e9e;"
            )
            self._dirs_layout.addWidget(empty_label)
            return

        for i, d in enumerate(dirs):
            row = QHBoxLayout()
            path_label = QLabel(f"  {d}")
            path_label.setWordWrap(True)
            path_label.setStyleSheet(
                f"background-color: {COLOR_GRAY_100}; "
                "border-radius: 6px; padding: 6px 8px; font-size: 12px;"
            )
            path_label.setProperty("dir_index", i)
            row.addWidget(path_label, stretch=1)

            remove_btn = QPushButton("✕")
            remove_btn.setFixedSize(24, 24)
            remove_btn.setStyleSheet(
                "QPushButton { border: none; border-radius: 12px; "
                "background-color: #ffcdd2; color: #c62828; font-weight: bold; }"
                "QPushButton:hover { background-color: #ef9a9a; }"
            )
            remove_btn.clicked.connect(lambda checked, p=d: self._remove_single_dir(p))
            row.addWidget(remove_btn)

            frame = QFrame()
            frame.setLayout(row)
            self._dirs_layout.addWidget(frame)

    def _apply_interval(self) -> None:
        """应用间隔时间设置。"""
        try:
            interval_val_str = self._interval_input.text().strip()
            if not interval_val_str:
                logger.warning("请输入间隔时间")
                return
            interval_val = int(interval_val_str)
            if interval_val <= 0:
                logger.warning("间隔时间必须为正数")
                return
            self._settings.set("interval_minutes", interval_val)
            if self._scheduler:
                self._scheduler._interval_minutes = interval_val
                # 如果当前是间隔模式且运行中，重启调度器以应用新间隔
                mode = self._scheduler.mode
                if mode == "interval_minutes" and self._scheduler.is_running:
                    self._scheduler.stop()
                    self._scheduler.start(on_switch=self.on_wallpaper_switched)
            logger.info("间隔时间已应用: %d 分钟", interval_val)
            self._update_info_cards()
            self.update_top_status()
        except ValueError:
            logger.warning("间隔时间格式无效，请输入数字")

    def _remove_directory(self) -> None:
        """弹出选择框，让用户选择移除哪个文件夹。"""
        dirs = self._settings.get("image_directories", [])
        if not dirs:
            return
        # 如果有多个目录，用简易方式：移除最后一个
        removed = dirs.pop()
        self._settings.set("image_directories", dirs)
        self._library.remove_directory(removed)
        self._refresh_gallery()
        self._update_settings_page_display()
        logger.info("已移除图片目录: %s", removed)

    def _remove_single_dir(self, path: str) -> None:
        """移除指定路径的图片目录。"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要从壁纸库中移除「{path}」吗？\n（只是移除目录，不会删除文件）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            dirs = self._settings.get("image_directories", [])
            if path in dirs:
                dirs.remove(path)
                self._settings.set("image_directories", dirs)
                self._library.remove_directory(path)
                self._refresh_gallery()
                self._update_settings_page_display()
                logger.info("已移除图片目录: %s", path)

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
            self._update_info_cards()
            self.update_top_status()
            self.update_bottom_bar()
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

        self._update_info_cards()

    def _on_gallery_click(self, image_path: str) -> None:
        """User clicked a gallery thumbnail - update preview and set as wallpaper."""
        try:
            success = self._wallpaper_manager.set_wallpaper(image_path)
            if success:
                available = self._library.list_available()
                index = available.index(image_path) if image_path in available else 0
                self._update_preview(image_path, index)
                self._highlight_current_gallery_item(image_path)
            else:
                logger.error("壁纸设置失败: %s", image_path)
        except Exception:
            logger.exception("画廊点击处理失败")

    def _refresh_gallery(self) -> None:
        """刷新扫描并更新 UI。"""
        images = self._library.scan()
        if images:
            first = images[0]
            self._update_preview(first, 0)
            logger.info("刷新图片库: %d 张", len(images))
            self._refresh_gallery_thumbnails()
            if hasattr(self, "_empty_guide"):
                self._empty_guide.setVisible(False)
                self._preview_card.setVisible(True)
        else:
            logger.info("未发现可用图片")
            if hasattr(self, "_empty_guide"):
                self._empty_guide.setVisible(True)
                self._preview_card.setVisible(False)
        self._update_info_cards()
        self.update_bottom_bar()

    def _refresh_gallery_thumbnails(self) -> None:
        """Populate gallery horizontal scroll with thumbnails."""
        # Clear existing widgets
        for i in reversed(range(self._gallery_layout.count())):
            widget = self._gallery_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        images = self._library.list_available()
        current_path = getattr(self._preview_card, "_current_path", "")
        for img_path in images[:20]:  # Show first 20
            thumb = _GalleryThumbWidget(img_path, is_current=(img_path == current_path))
            thumb.clicked.connect(lambda p=img_path: self._on_gallery_click(p))
            self._gallery_layout.addWidget(thumb)

        self._gallery_items = images[:20]  # track for highlight updates

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
                self._top_status.setText(
                    f"● 已启用 · 明天 {next_switch.strftime('%H:%M')} 切换"
                )
            else:
                self._top_status.setText("● 已启用 · 明天自动切换")
        elif mode == "interval_minutes":
            mins = self._scheduler.interval_minutes or 60
            self._top_status.setText(f"● 已启用 · 每 {mins} 分钟")
        elif mode == "manual":
            self._top_status.setText("● 已启用 · 手动模式")

    def _update_info_cards(self) -> None:
        """更新信息网格卡片的内容。"""
        mode_name = self._settings.get("switch_mode", "daily_random")
        mode_display = {
            "daily_random": "每日随机",
            "interval_minutes": f"每{self._settings.get('interval_minutes', 60)}分钟",
            "manual": "手动",
        }
        total = self._library.total_count
        next_text = self._get_next_switch_text() if total > 0 else "添加图片后"

        self._update_card_value(self._method_card, mode_display.get(mode_name, "每日随机"))
        self._update_card_value(self._next_time_card, next_text)
        self._update_card_value(self._count_card, str(total))

    @staticmethod
    def _update_card_value(card: QFrame, value: str) -> None:
        """更新信息卡片的值标签文本。"""
        val_label = card.findChild(QLabel, "stat-value")
        if val_label:
            val_label.setText(value)

    def _highlight_current_gallery_item(self, current_path: str) -> None:
        """Update the visual highlight of the currently active gallery item."""
        for w_idx in range(self._gallery_layout.count()):
            widget = self._gallery_layout.itemAt(w_idx).widget()
            if isinstance(widget, _GalleryThumbWidget):
                widget.set_is_current(widget._image_path == current_path)

    def update_bottom_bar(self) -> None:
        """Update bottom status bar with current library info."""
        images = self._library.list_available()
        dirs = self._library._directories or ["未配置"]
        dir_text = ", ".join(dirs[:2])  # show first two dirs
        fav_count = len(self._library.favorites)
        enabled = "已启用" if self._scheduler and self._scheduler.is_active else "已暂停"
        icon_folder = "\U0001f4c2"  # 📂 folder
        self._bottom_source_label.setText(
            f"{icon_folder} {dir_text} ({len(images)}/{self._library.total_count})"
        )
        star_icon = "★"  # ★
        bell_icon = "\U0001f514"  # 🔔 bell
        self._bottom_fav_count.setText(f"{star_icon} {fav_count}")
        self._bottom_notifier_label.setText(f"{bell_icon} {enabled}")

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
        """托盘图标清理。"""
        super().closeEvent(event)
        if hasattr(self, "_tray") and self._tray is not None:
            self._tray.setVisible(False)
            self._tray.deleteLater()
        if hasattr(self, "_scheduler") and self._scheduler is not None:
            self._scheduler.stop()
