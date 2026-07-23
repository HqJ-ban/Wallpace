"""src/app/theme.py — 粉蓝渐变 QSS 主题引擎。

为整个应用提供统一的视觉风格：粉蓝渐变背景、圆角卡片、图标按钮等。
遵循 dev-standards.md 的配色约定。
"""

from typing import Dict, Optional

from PySide6.QtGui import QColor, QFont, QFontDatabase
from PySide6.QtWidgets import QApplication


# ==================== 配色常量 ====================
COLOR_PINK_LIGHT = "#fce4ec"       # 极浅粉（背景）
COLOR_PINK_MID = "#f8bbd0"         # 中粉（装饰）
COLOR_PINK_ACCENT = "#e91e63"      # 玫红（主强调色）

COLOR_BLUE_LIGHT = "#bbdefb"       # 极浅蓝（背景）
COLOR_BLUE_MID = "#e3f2fd"         # 中蓝（卡片背景）
COLOR_BLUE_ACCENT = "#5c6bc0"      # 靛蓝（次要强调）
COLOR_BLUE_DARK = "#1a237e"        # 深蓝（文字标题）

COLOR_GRAY_50 = "#fafafa"          # 最浅灰（页面底色）
COLOR_GRAY_100 = "#f5f5f5"         # 浅灰（面板底色）
COLOR_GRAY_200 = "#eeeeee"         # 边线灰
COLOR_GRAY_500 = "#9e9e9e"         # 中灰（次文本）
COLOR_GRAY_800 = "#424242"         # 深灰（正文）

GRAY_COLORS: Dict[str, str] = {
    "50": COLOR_GRAY_50,
    "100": COLOR_GRAY_100,
    "200": COLOR_GRAY_200,
    "500": COLOR_GRAY_500,
    "800": COLOR_GRAY_800,
}


class ThemeManager:
    """集中管理应用全局样式和字体设置。

    支持两种模式：
        - LightQSS: 仅轻量级 QSS 样式（兼容性好，渲染快）
        - Gradient: 渐变背景（效果更丰富，但需要 QPainter 配合）
    """

    MODE_LIGHT = "light_qss"
    MODE_GRADIENT = "gradient"

    def __init__(self) -> None:
        self._font_title: Optional[QFont] = None

    # ==================== QSS 样式表 ====================

    @staticmethod
    def light_qss() -> str:
        """返回基础浅色 QSS 样式表。

        这是轻量级方案，覆盖全局控件、布局、滚动条等。
        不需要 QPainter 自定义绘制。
        """
        return (
            f"\n"
            f"/* ===== 全局基座 ===== */\n"
            f"QWidget {{\n"
            f"    font-family: 'Microsoft YaHei UI', 'PingFang SC', sans-serif;\n"
            f"    color: {COLOR_GRAY_800};\n"
            f"    background-color: {COLOR_GRAY_50};\n"
            f"}}\n"
            f"QMainWindow {{\n"
            f"    background-color: {COLOR_GRAY_100};\n"
            f"}}\n"
            f"QLabel {{\n"
            f"    color: {COLOR_GRAY_800};\n"
            f"}}\n"
            f"QLabel[is-title='true'] {{\n"
            f"    font-size: 20px;\n"
            f"    font-weight: bold;\n"
            f"    color: {COLOR_BLUE_DARK};\n"
            f"}}\n"
            f"QLabel[is-subtitle='true'] {{\n"
            f"    font-size: 12px;\n"
            f"    color: {COLOR_GRAY_500};\n"
            f"}}\n"
            f"QLabel[is-stat-label='true'] {{\n"
            f"    font-size: 11px;\n"
            f"    color: {COLOR_GRAY_500};\n"
            f"}}\n"
            f"QLabel[is-stat-value='true'] {{\n"
            f"    font-size: 16px;\n"
            f"    font-weight: 600;\n"
            f"    color: {COLOR_BLUE_DARK};\n"
            f"}}\n"
            f"\n"
            f"/* ===== 按钮 ===== */\n"
            f"QPushButton {{\n"
            f"    border: none;\n"
            f"    border-radius: 8px;\n"
            f"    padding: 8px 20px;\n"
            f"    font-size: 13px;\n"
            f"    font-weight: 600;\n"
            f"    color: white;\n"
            f"    background-color: {COLOR_BLUE_ACCENT};\n"
            f"}}\n"
            f"QPushButton:hover {{\n"
            f"    background-color: {COLOR_PINK_ACCENT};\n"
            f"}}\n"
            f"QPushButton:pressed {{\n"
            f"    background-color: {COLOR_BLUE_DARK};\n"
            f"}}\n"
            f"QPushButton:disabled {{\n"
            f"    background-color: {COLOR_GRAY_200};\n"
            f"    color: {COLOR_GRAY_500};\n"
            f"}}\n"
            f"\n"
            f"/* ===== 切换按钮 ===== */\n"
            f"QToolButton {{\n"
            f"    border: none;\n"
            f"    border-radius: 10px;\n"
            f"    padding: 10px;\n"
            f"    font-size: 16px;\n"
            f"    color: {COLOR_GRAY_500};\n"
            f"}}\n"
            f"QToolButton:hover {{\n"
            f"    color: {COLOR_BLUE_DARK};\n"
            f"    background-color: {COLOR_BLUE_MID};\n"
            f"}}\n"
            f"QToolButton:checked {{\n"
            f"    color: white;\n"
            f"    background-color: {COLOR_BLUE_ACCENT};\n"
            f"}}\n"
            f"\n"
            f"/* ===== 侧边栏 ===== */\n"
            f"QStackedWidget > QWidget {{\n"
            f"    background-color: {COLOR_GRAY_50};\n"
            f"    border-top-left-radius: 16px;\n"
            f"    border-top-right-radius: 16px;\n"
            f"}}\n"
            f"\n"
            f"/* ===== 滚动条 ===== */\n"
            f"QScrollBar:vertical {{\n"
            f"    width: 6px;\n"
            f"    background: transparent;\n"
            f"    margin: 0;\n"
            f"}}\n"
            f"QScrollBar::handle:vertical {{\n"
            f"    background: {COLOR_GRAY_200};\n"
            f"    border-radius: 3px;\n"
            f"    min-height: 30px;\n"
            f"}}\n"
            f"QScrollBar::handle:vertical:hover {{\n"
            f"    background: {COLOR_GRAY_500};\n"
            f"}}\n"
            f"QScrollBar::add-line, QScrollBar::sub-line {{\n"
            f"    height: 0;\n"
            f"}}\n"
            f"\n"
            f"/* ===== 图片标签 ===== */\n"
            f"QLabel[role='preview-image'] {{\n"
            f"    border: 3px solid {COLOR_GRAY_200};\n"
            f"    border-radius: 12px;\n"
            f"    background-color: {COLOR_GRAY_100};\n"
            f"}}\n"
            f"QLabel[role='gallery-item'] {{\n"
            f"    border: 2px solid {COLOR_GRAY_200};\n"
            f"    border-radius: 6px;\n"
            f"    background-color: {COLOR_GRAY_100};\n"
            f"    margin: 2px;\n"
            f"}}\n"
            f"QLabel[role='gallery-item']:hover {{\n"
            f"    border-color: {COLOR_PINK_MID};\n"
            f"}}\n"
            f"\n"
            f"/* ===== 设置面板 ===== */\n"
            f"QGroupBox {{\n"
            f"    title-color: {COLOR_BLUE_DARK};\n"
            f"    border: 1px solid {COLOR_GRAY_200};\n"
            f"    border-radius: 8px;\n"
            f"    margin-top: 12px;\n"
            f"    padding-top: 20px;\n"
            f"    font-weight: 600;\n"
            f"}}\n"
            f"QGroupBox::title {{\n"
            f"    subcontrol-origin: margin;\n"
            f"    left: 12px;\n"
            f"    padding: 0 6px;\n"
            f"}}\n"
            f"QCheckBox {{\n"
            f"    spacing: 8px;\n"
            f"    font-size: 13px;\n"
            f"}}\n"
            f"QCheckBox::indicator {{\n"
            f"    width: 18px;\n"
            f"    height: 18px;\n"
            f"    border: 2px solid {COLOR_GRAY_200};\n"
            f"    border-radius: 4px;\n"
            f"}}\n"
            f"QCheckBox::indicator:checked {{\n"
            f"    background-color: {COLOR_BLUE_ACCENT};\n"
            f"    border-color: {COLOR_BLUE_ACCENT};\n"
            f"}}\n"
            f"QLineEdit {{\n"
            f"    border: 1px solid {COLOR_GRAY_200};\n"
            f"    border-radius: 6px;\n"
            f"    padding: 6px 10px;\n"
            f"    font-size: 13px;\n"
            f"    selection-background-color: {COLOR_PINK_MID};\n"
            f"}}\n"
            f"QLineEdit:focus {{\n"
            f"    border-color: {COLOR_BLUE_ACCENT};\n"
            f"}}\n"
            f"\n"
            f"/* ===== 菜单/弹出窗口 ===== */\n"
            f"QMenu {{\n"
            f"    border: 1px solid {COLOR_GRAY_200};\n"
            f"    border-radius: 8px;\n"
            f"    background-color: white;\n"
            f"    padding: 4px 0;\n"
            f"}}\n"
            f"QMenu::item {{\n"
            f"    padding: 8px 24px 8px 16px;\n"
            f"    font-size: 13px;\n"
            f"}}\n"
            f"QMenu::item:selected {{\n"
            f"    background-color: {COLOR_BLUE_LIGHT};\n"
            f"}}\n"
            f"QMenu::separator {{\n"
            f"    height: 1px;\n"
            f"    background-color: {COLOR_GRAY_200};\n"
            f"    margin: 4px 12px;\n"
            f"}}\n"
            f"\n"
            f"/* ===== 托盘图标区域 ===== */\n"
            f"QSystemTrayIcon {{\n"
            f"    background: transparent;\n"
            f"}}\n"
        )

    # ==================== 渐变顶栏 ====================

    @staticmethod
    def top_bar_gradient_css(top_color: str = COLOR_PINK_ACCENT,
                              bottom_color: str = COLOR_BLUE_ACCENT) -> str:
        """为顶栏组件生成 QLinearGradient 样式。

        Args:
            top_color: 顶部颜色（粉）。
            bottom_color: 底部颜色（蓝）。
        Returns:
            QSS 片段字符串，应用于 widget 的 setStyleSheet。
        """
        return (
            f"background: qlineargradient("
            f"x1:0, y1:0, x2:0, y2:1, "
            f"stop:0 {top_color}, "
            f"stop:1 {bottom_color}"
            ");"
        )

    # ==================== 渐变背景 ====================

    @staticmethod
    def body_bg_gradient_css(left_color: str = COLOR_BLUE_MID,
                              right_color: str = COLOR_PINK_LIGHT) -> str:
        """为内容区背景生成水平渐变。

        Args:
            left_color: 左侧颜色（蓝）。
            right_color: 右侧颜色（粉）。
        Returns:
            QSS 背景渐变。
        """
        return (
            f"background: qlineargradient("
            f"x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 {left_color}, "
            f"stop:1 {right_color}"
            ");"
        )

    # ==================== 字体加载 ====================

    def load_font(self, app: QApplication, family: str,
                   weight: int = QFont.Weight.Normal) -> None:
        """(预留) 加载自定义字体到 QFontDatabase。

        当前版本使用系统自带的中文字体，此处保留扩展接口。
        """
        pass
