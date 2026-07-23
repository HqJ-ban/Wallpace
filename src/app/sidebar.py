"""src/app/sidebar.py — 图标侧边栏导航组件。

B 方案核心：左侧窄边栏，通过图标切换不同功能页面。
"""

import logging
from typing import Callable, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.app.theme import COLOR_BLUE_ACCENT, COLOR_BLUE_DARK, COLOR_GRAY_500, COLOR_BLUE_MID

logger = logging.getLogger(__name__)


class SidebarButton(QPushButton):
    """侧边栏单个导航按钮。"""

    def __init__(self, icon_text: str, label: str, page_id: str,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(icon_text + "  " + label, parent)
        self._page_id = page_id
        self.setObjectName("nav_button")
        self.setCheckable(True)
        self.setMinimumHeight(36)
        self.setMaximumWidth(220)
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self.setStyleSheet(self._base_style())

    @property
    def page_id(self) -> str:
        return self._page_id

    def _base_style(self) -> str:
        return (
            "QPushButton#nav_button {{ "
            "border: none; border-radius: 8px; "
            "padding: 8px 16px; text-align: left; "
            "color: {}; font-size: 13px; }}"
            "QPushButton#nav_button:hover {{ "
            "background-color: {}; "
            "color: {}; }}"
            "QPushButton#nav_button:checked {{ "
            "background-color: {}; "
            "color: white; "
            "font-weight: bold; }}"
        ).format(COLOR_GRAY_500, COLOR_BLUE_MID, COLOR_BLUE_DARK,
                  COLOR_BLUE_ACCENT)


class SidebarNavigation(QWidget):
    """左侧图标侧边栏。

    包含品牌标识、4 个页面导航按钮和底部状态信息。
    与右侧 QStackedWidget 配合使用，点击按钮切换页面。
    """

    WIDTH = 72
    EXPANDED_WIDTH = 220
    BRAND_ICON_TEXT = "WP"

    NAV_ITEMS = [
        ("home", "\u58c1\u7eb8\u9884\u89c8"),
        ("gallery", "\u56fe\u7247\u5e93"),
        ("clock", "\u65f6\u95f4"),
        ("settings", "\u8bbe\u7f6e"),
    ]

    def __init__(self, stacked: QStackedWidget,
                 on_settings_open: Callable[[], None],
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._stacked = stacked
        self._on_settings_open = on_settings_open
        self._buttons: Dict[str, SidebarButton] = {}

        self.setFixedWidth(self.EXPANDED_WIDTH)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(6)

        # === 品牌标识 ===
        brand = QFrame()
        brand.setObjectName("brand")
        brand.setFixedHeight(48)
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(6, 0, 6, 0)
        brand_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        brand_icon = QLabel(self.BRAND_ICON_TEXT)
        brand_icon.setStyleSheet(
            "color: white; font-size: 16px; font-weight: bold; "
            "background: qlineargradient(x1:0,y1:0,x2:0,y2:1, "
            "stop:0 #e91e63, stop:1 #5c6bc0); "
            "border-radius: 8px; padding: 4px 10px;"
        )
        brand_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        brand_text = QLabel("Wallpace")
        brand_text.setObjectName("subtitle")
        brand_text.setStyleSheet("padding-left: 8px;")

        brand_layout.addWidget(brand_icon)
        brand_layout.addWidget(brand_text)
        layout.addWidget(brand)

        layout.addStretch(2)

        # === 导航按钮 ===
        for page_id, label in self.NAV_ITEMS:
            btn = SidebarButton("", label, page_id, self)
            btn.toggled.connect(lambda checked, pid=page_id:
                                self._on_page_toggled(pid, checked))
            self._buttons[page_id] = btn
            layout.addWidget(btn)

        layout.addStretch(5)

        # === 底部状态 ===
        status_frame = QFrame()
        status_frame.setObjectName("sidebar_footer")
        status_frame.setFixedHeight(48)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(8, 4, 8, 4)

        self.status_label = QLabel()
        self.status_label.setObjectName("sub-title")
        self.status_label.setStyleSheet(
            "text-align: center; font-size: 11px; color: #9e9e9e;"
        )
        status_layout.addWidget(self.status_label)
        layout.addWidget(status_frame)

        # 默认选中首页
        self._buttons["home"].setChecked(True)
        self._stacked.setCurrentIndex(0)

    def _on_page_toggled(self, page_id: str, checked: bool) -> None:
        if not checked:
            return
        idx_map = {pid: i for i, (pid, _) in enumerate(self.NAV_ITEMS)}
        if page_id in idx_map:
            self._stacked.setCurrentIndex(idx_map[page_id])
        if page_id == "settings":
            self._on_settings_open()

    def update_status(self, text: str) -> None:
        self.status_label.setText(text)

    def set_active_button(self, page_id: str) -> None:
        for pid, btn in self._buttons.items():
            btn.setChecked(pid == page_id)
