"""src/app/pages/gallery_page.py — 图片库页面。

提供「全部 / 收藏 / 已跳过」筛选 + 缩略图网格。每张缩略图可：
  - 点击大图：设为当前壁纸
  - ★ 按钮：收藏 / 取消收藏
  - 恢复按钮（仅已跳过项显示）：从跳过列表中移除
收藏与跳过变更通过 on_persist 回调写回配置，避免重启后丢失。

缩略图解码走 src.app.image_loader 的全局异步加载（后台线程解码，信号回主线程），
不在主线程同步解码，也不在非主线程操作任何 QWidget。
"""

import logging
from pathlib import Path
from typing import Callable, List, Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QPushButton,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.app import image_loader

logger = logging.getLogger(__name__)

THUMB_SIZE = QSize(160, 120)
GRID_COLS = 4


class _Tile(QWidget):
    """单张缩略图卡片：缩略图 + 收藏/恢复操作。"""

    def __init__(
        self,
        path: str,
        library,
        on_set: Callable[[str], None],
        on_persist: Callable[[], None],
        page: "GalleryPage",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._path = path
        self._library = library
        self._on_set = on_set
        self._on_persist = on_persist
        self._page = page

        self._thumb = QLabel()
        self._thumb.setFixedSize(THUMB_SIZE)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb.setStyleSheet(
            "QLabel { background: #f3f4f6; border-radius: 6px; }"
            "QLabel:hover { border: 2px solid #ec4899; }"
        )
        self._thumb.mousePressEvent = lambda _e: self._on_set(self._path)

        self._fav_btn = QPushButton("★" if library.is_favorite(path) else "☆")
        self._fav_btn.setFixedSize(28, 28)
        self._fav_btn.setStyleSheet("QPushButton { border: none; font-size: 16px; }")
        self._fav_btn.clicked.connect(self._toggle_fav)

        self._skip_btn = QPushButton("恢复")
        self._skip_btn.setFixedSize(40, 28)
        self._skip_btn.setStyleSheet(
            "QPushButton { border: 1px solid #ffcdd2; border-radius: 4px;"
            " color: #c62828; font-size: 11px; }"
        )
        self._skip_btn.setVisible(self._path in library.skip_list)
        self._skip_btn.clicked.connect(self._unskip)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.addWidget(self._fav_btn)
        btn_row.addWidget(self._skip_btn)
        btn_row.addStretch(1)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)
        vbox.addWidget(self._thumb)
        vbox.addLayout(btn_row)

        # 异步解码（后台线程，完成后经信号回主线程）
        self._conn = image_loader.connect_ready(self._on_image_ready)
        image_loader.load_async(path, THUMB_SIZE)

    def _on_image_ready(self, path: str, image: QImage) -> None:
        if path != self._path:
            return
        pix = QPixmap.fromImage(image)
        self._thumb.setPixmap(
            pix.scaled(
                THUMB_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _toggle_fav(self) -> None:
        if self._library.is_favorite(self._path):
            self._library.unfavorite(self._path)
        else:
            self._library.favorite(self._path)
        self._fav_btn.setText("★" if self._library.is_favorite(self._path) else "☆")
        self._on_persist()

    def _unskip(self) -> None:
        self._library.unskip(self._path)
        self._on_persist()
        # 当前已不在跳过列表，刷新页面以移除该卡片
        self._page.refresh()

    def cleanup(self) -> None:
        """断开全局解码信号连接，避免野回调。"""
        try:
            self._conn.disconnect()
        except Exception:
            pass


class GalleryPage(QWidget):
    """图片库页面：全部 / 收藏 / 已跳过 筛选 + 缩略图网格。"""

    def __init__(
        self,
        library,
        image_loader,
        on_set_wallpaper: Callable[[str], None],
        on_persist: Callable[[], None],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._library = library
        self._image_loader = image_loader
        self._on_set_wallpaper = on_set_wallpaper
        self._on_persist = on_persist
        self._filter = "all"  # all | favorites | skipped
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)

        title = QLabel("图片库")
        title.setObjectName("title")
        layout.addWidget(title)

        # 筛选按钮行
        filter_row = QHBoxLayout()
        self._btn_all = QPushButton("全部")
        self._btn_fav = QPushButton("收藏")
        self._btn_skip = QPushButton("已跳过")
        for btn, key in (
            (self._btn_all, "all"),
            (self._btn_fav, "favorites"),
            (self._btn_skip, "skipped"),
        ):
            btn.setCheckable(True)
            btn.clicked.connect(lambda _c, k=key: self._set_filter(k))
            filter_row.addWidget(btn)
        filter_row.addStretch(1)
        layout.addLayout(filter_row)

        # 滚动网格
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._content = QWidget()
        self._grid = QGridLayout(self._content)
        self._grid.setSpacing(10)
        self._scroll.setWidget(self._content)
        layout.addWidget(self._scroll, stretch=1)

        self._update_filter_buttons()
        self.refresh()

    def _set_filter(self, key: str) -> None:
        self._filter = key
        self._update_filter_buttons()
        self.refresh()

    def _update_filter_buttons(self) -> None:
        self._btn_all.setChecked(self._filter == "all")
        self._btn_fav.setChecked(self._filter == "favorites")
        self._btn_skip.setChecked(self._filter == "skipped")

    def _current_paths(self) -> List[str]:
        if self._filter == "favorites":
            return self._library.favorites
        if self._filter == "skipped":
            return self._library.skip_list
        return self._library.list_available()

    def refresh(self) -> None:
        """根据当前筛选重建缩略图网格。"""
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None:
                if isinstance(w, _Tile):
                    w.cleanup()
                w.deleteLater()

        paths = self._current_paths()
        for i, path in enumerate(paths):
            tile = _Tile(
                path,
                self._library,
                self._on_set_wallpaper,
                self._on_persist,
                self,
            )
            self._grid.addWidget(tile, i // GRID_COLS, i % GRID_COLS)

    def showEvent(self, event) -> None:  # noqa: ANN001
        # 切到该页时按最新 library 状态刷新
        self.refresh()
        super().showEvent(event)
