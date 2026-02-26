import PySide6.QtWidgets as QtW
from PySide6.QtWidgets import QFrame, QVBoxLayout
from PySide6.QtCore import Qt
from gui_styles.stylesheets import *


class ParameterPanel(QFrame):
    """
    Panel widget designed to display and manage parameter views within the application.

    This panel is a fixed-width container with a vertical layout housing
    a QStackedWidget to switch between different parameter configurations or forms.

    Attributes:
        main_window: Reference to the main application window.
        parameters_view (QStackedWidget): Container for multiple parameter view widgets.
    """

    def __init__(self, main_window):
        """
        Initialize the ParameterPanel with fixed width and custom styling.

        Args:
            main_window: Reference to the parent/main application window.
        """
        super().__init__()
        self.main_window = main_window

        # Set base styling for the panel
        self.setStyleSheet("background-color: #fbfcfc; border-radius: 0px;")
        self.setFixedWidth(640)
        self.setSizePolicy(QtW.QSizePolicy.Policy.Fixed, QtW.QSizePolicy.Policy.Expanding)

        # Create vertical layout with minimal margins to hold parameter views
        parameters_layout = QVBoxLayout(self)
        parameters_layout.setContentsMargins(0, 5, 5, 5)

        # Initialize stacked widget to hold multiple parameter views
        self.parameters_view = QtW.QStackedWidget()
        self.parameters_view.setObjectName("Parameters_Views")

        # Apply custom stylesheet to differentiate the stacked widget visually
        self.parameters_view.setStyleSheet("""
            QStackedWidget#Parameters_Views {
                background-color: #2c2c2c;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)

        # Add the stacked widget to the panel layout
        parameters_layout.addWidget(self.parameters_view)

        # Debug log statement
        print("DEBUG: ParameterPanel initialized with fixed width and stacked parameter views.")
