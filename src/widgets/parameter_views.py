import PySide6.QtWidgets as QtW
from PySide6.QtWidgets import QFrame, QVBoxLayout
from PySide6.QtCore import Qt
from gui_styles.stylesheets import parameters_panel_style


class ParameterPanel(QFrame):
    """
    Panel hosting the QStackedWidget that swaps the four parameter views
    (Home, Electric, Magnetic, Simulation).
    """

    MIN_WIDTH = 420
    MAX_WIDTH = 560

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setObjectName("ParameterPanel")
        self.setStyleSheet(parameters_panel_style())
        self.setMinimumWidth(self.MIN_WIDTH)
        self.setMaximumWidth(self.MAX_WIDTH)
        self.setSizePolicy(
            QtW.QSizePolicy.Policy.Preferred,
            QtW.QSizePolicy.Policy.Expanding,
        )

        parameters_layout = QVBoxLayout(self)
        parameters_layout.setContentsMargins(12, 12, 12, 12)
        parameters_layout.setSpacing(0)

        self.parameters_view = QtW.QStackedWidget()
        self.parameters_view.setObjectName("Parameters_Views")

        parameters_layout.addWidget(self.parameters_view)
