"""src/app/widgets/preview_card.py -- 壁纸预览卡片组件。

显示当前壁纸的缩略图、文件名和切换操作按钮。
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.app.theme import COLOR_GRAY_100, COLOR_GRAY_200, COLOR_GRAY_500

logger = logging.getLogger(__name__)


class PreviewCardWidget(QWidget):
    """当前壁纸预览卡片组件。

    包含：大图预览 + 文件名信息 + 切换操作按钮。
    """

    switch_clicked = Signal()
    skip_clicked = Signal()
    favorite_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._current_path: str = ""
        self._setup_ui()
        self._set_placeholder()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 预览图片
        self.preview_label = QLabel("(暂无预览)")
        self.preview_label.setObjectName("preview-image")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(480, 300)
        self.preview_label.setMaximumSize(480, 300)
        self.preview_label.setStyleSheet(
            "QLabel#preview-image { "
            "min-width: 480px; min-height: 300px; "
            "max-width: 480px; max-height: 300px; }"
        )
        layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 文件名和大小
        name_layout = QHBoxLayout()
        name_layout.addStretch()
        self.filename_label = QLabel("尚未选择图片")
        self.filename_label.setObjectName("subtitle")
        name_layout.addWidget(self.filename_label)

        self.size_label = QLabel()
        self.size_label.setObjectName("subtitle")
        name_layout.addWidget(self.size_label)
        name_layout.addStretch()
        layout.addLayout(name_layout)

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_skip = QPushButton("跳过")
        btn_skip.clicked.connect(self.skip_clicked)
        btn_skip.setMinimumWidth(80)

        btn_favorite = QPushButton("收藏")
        btn_favorite.clicked.connect(self.favorite_clicked)
        btn_favorite.setMinimumWidth(80)

        btn_switch = QPushButton("换一张")
        btn_switch.setObjectName("primary")
        btn_switch.setStyleSheet(
            "QPushButton#primary { "
            "padding: 10px 32px; "
            "font-size: 14px; font-weight: 700; "
            "border-radius: 10px; }"
        )
        btn_switch.clicked.connect(self.switch_clicked)
        btn_switch.setMinimumWidth(96)

        btn_layout.addWidget(btn_skip)
        btn_layout.addWidget(btn_favorite)
        btn_layout.addWidget(btn_switch)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _set_placeholder(self) -> None:
        self.preview_label.setStyleSheet(
            f"QLabel#preview-image {{ "
            f"border: 3px dashed {COLOR_GRAY_200}; "
            f"background-color: {COLOR_GRAY_100}; "
            f"font-size: 14px; color: {COLOR_GRAY_500}; }} "
            f"min-width: 480px; min-height: 300px; "
            f"max-width: 480px; max-height: 300px;"
        )

    def update_preview(self, image_path: str) -> None:
        self._current_path = image_path
        file_name = Path(image_path).stem
        file_size = ""
        try:
            stat = Path(image_path).stat()
            size_kb = stat.st_size / 1024
            file_size = f"{size_kb:.0f} KB"
        except OSError:
            pass

        self.filename_label.setText(file_name)
        self.size_label.setText(file_size)

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                480, 300,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview_label.setPixmap(scaled)
            self.preview_label.setStyleSheet(
                f"QLabel#preview-image {{ "
                f"border: 3px solid {COLOR_GRAY_200}; "
                f"border-radius: 12px; "
                f"background-color: transparent; "
                f"}}"
            )
        else:
            self._set_placeholder()

    def clear_preview(self) -> None:
        self._current_path = ""
        self.filename_label.setText("未选择图片")
        self.size_label.setText("")
        self.preview_label.clear()
        self._set_placeholder()
