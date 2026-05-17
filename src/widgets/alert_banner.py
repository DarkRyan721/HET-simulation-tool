"""
Reusable inline alert banner.

Renders as a flat card with a colored left border, an icon, a title and a body.
Useful for non-modal prerequisite warnings at the top of a panel.
"""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
import qtawesome as qta

from gui_styles.stylesheets import alert_banner_style


_LEVEL_ICON = {
    "warning": ("fa5s.exclamation-triangle", "#b45309"),
    "info":    ("fa5s.info-circle",          "#2563eb"),
    "success": ("fa5s.check-circle",         "#15803d"),
    "danger":  ("fa5s.times-circle",         "#b91c1c"),
}


class AlertBanner(QFrame):
    """Inline status card with icon + title + message."""

    def __init__(self, title: str = "", message: str = "", level: str = "warning", parent=None):
        super().__init__(parent)
        self.setObjectName("AlertBanner")
        self._level = level
        self.setStyleSheet(alert_banner_style(level))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(12)

        self.icon_label = QLabel()
        self.icon_label.setObjectName("AlertIcon")
        self.icon_label.setFixedSize(QSize(22, 22))
        self.icon_label.setAlignment(Qt.AlignCenter)
        outer.addWidget(self.icon_label, 0, Qt.AlignTop)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("AlertTitle")
        self.title_label.setWordWrap(True)

        self.body_label = QLabel(message)
        self.body_label.setObjectName("AlertBody")
        self.body_label.setWordWrap(True)

        text_col.addWidget(self.title_label)
        text_col.addWidget(self.body_label)
        outer.addLayout(text_col, 1)

        self._refresh_icon()
        if not title:
            self.title_label.hide()
        if not message:
            self.body_label.hide()

    def set_content(self, title: str = None, message: str = None, level: str = None):
        if level is not None and level != self._level:
            self._level = level
            self.setStyleSheet(alert_banner_style(level))
            self._refresh_icon()
        if title is not None:
            self.title_label.setText(title)
            self.title_label.setVisible(bool(title))
        if message is not None:
            self.body_label.setText(message)
            self.body_label.setVisible(bool(message))

    def _refresh_icon(self):
        icon_name, color = _LEVEL_ICON.get(self._level, _LEVEL_ICON["warning"])
        pix = qta.icon(icon_name, color=color).pixmap(20, 20)
        self.icon_label.setPixmap(pix)
