from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFrame, QStyle
)
from PySide6.QtCore import Qt

from gui_styles.stylesheets import advanced_toggle_style, advanced_content_style


class CollapsibleBox(QWidget):
    """
    A collapsible container with a toggle button on top and a hidden frame below.

    The button shows the current title and an arrow icon that flips between
    "collapsed" and "expanded" states.
    """

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)

        self.toggle_button = QPushButton(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.setStyleSheet(advanced_toggle_style())
        self.toggle_button.setIcon(
            self.style().standardIcon(QStyle.SP_ArrowRight)
        )
        self.toggle_button.toggled.connect(self.toggle_content)

        self.content_area = QFrame()
        self.content_area.setFrameShape(QFrame.StyledPanel)
        self.content_area.setStyleSheet(advanced_content_style())
        self.content_area.setVisible(False)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(6)
        self.layout.addWidget(self.toggle_button)
        self.layout.addWidget(self.content_area)

    def setContentLayout(self, content_layout):
        self.content_area.setLayout(content_layout)

    def toggle_content(self, checked: bool):
        self.content_area.setVisible(checked)
        icon = self.style().standardIcon(
            QStyle.SP_ArrowDown if checked else QStyle.SP_ArrowRight
        )
        self.toggle_button.setIcon(icon)
