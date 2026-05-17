import PySide6.QtWidgets as QtW
from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QSizePolicy, QLabel
from PySide6.QtCore import Qt, QSize
import qtawesome as qta

from gui_styles.stylesheets import (
    button_activate_style,
    button_options_style,
    options_panel_style,
    COLOR_TEXT_ON_DARK,
    COLOR_BORDER,
)


class OptionsPanel(QFrame):
    """
    Vertical sidebar with navigation tabs.

    Each tab switches the QStackedWidget passed as 'parameters_view'.
    """

    SIDEBAR_WIDTH = 84
    ICON_SIZE = 22

    def __init__(self, main_window, parameters_view):
        super().__init__()
        self.main_window = main_window
        self.parameters_view = parameters_view

        self.parameters_view.setCurrentIndex(0)

        self.setObjectName("OptionsPanel")
        self.setStyleSheet(options_panel_style())
        self.setFixedWidth(self.SIDEBAR_WIDTH)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(6, 14, 6, 14)
        self.layout.setSpacing(4)

        self._add_brand()

        self.tab_buttons = []
        self.create_buttons()
        self.create_option_panels()

    def _add_brand(self):
        """Small brand mark at the top of the sidebar."""
        brand = QLabel("HET")
        brand.setAlignment(Qt.AlignCenter)
        brand.setStyleSheet(
            f"color: {COLOR_TEXT_ON_DARK}; font-weight: 700; "
            f"letter-spacing: 1px; font-size: 12px; padding: 4px 0 12px 0; "
            f"border-bottom: 1px solid {COLOR_BORDER}; margin-bottom: 6px;"
        )
        self.layout.addWidget(brand)

    def create_buttons(self):
        """
        Create the vertical navigation buttons.

        Each entry: (label, qtawesome icon name).
        """
        btn_info = [
            ("Home",       "fa5s.home"),
            ("Electric",   "fa5s.bolt"),
            ("Magnetic",   "fa5s.magnet"),
            ("Simulation", "fa5s.play"),
        ]

        for index, (name, icon_name) in enumerate(btn_info):
            btn = QPushButton(name)
            btn.setObjectName(f"{name}_Btn")
            btn.setToolTip(name)
            btn.setCursor(Qt.PointingHandCursor)

            is_active = (index == 0)
            self._apply_icon(btn, icon_name, is_active)
            btn.setStyleSheet(button_activate_style() if is_active else button_options_style())

            btn.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setMinimumHeight(60)
            btn.setProperty("icon_name", icon_name)

            btn.clicked.connect(
                lambda _, i=index, b=btn: self.main_window.on_dynamic_tab_clicked(i, b)
            )

            self.layout.addWidget(btn)
            self.tab_buttons.append(btn)

        self.layout.addStretch()

    def _apply_icon(self, btn: QPushButton, icon_name: str, active: bool):
        color = "#ffffff" if active else "#cbd5e1"
        btn.setIcon(qta.icon(icon_name, color=color))

    def refresh_icons(self, active_btn: QPushButton):
        """Update icon colors to match the current active/idle state."""
        for btn in self.tab_buttons:
            icon_name = btn.property("icon_name")
            if not icon_name:
                continue
            self._apply_icon(btn, icon_name, btn is active_btn)

    def create_option_panels(self):
        """Register the four panels in their navigation order."""
        self.parameters_view.addWidget(self.main_window.home_panel)        # index 0
        self.parameters_view.addWidget(self.main_window.field_panel)       # index 1
        self.parameters_view.addWidget(self.main_window.magnetic_panel)    # index 2
        self.parameters_view.addWidget(self.main_window.simulation_panel)  # index 3
