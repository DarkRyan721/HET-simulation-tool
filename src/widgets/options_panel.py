import PySide6.QtWidgets as QtW
from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QSizePolicy
from gui_styles.stylesheets import *


class OptionsPanel(QFrame):
    """
    Panel containing navigation buttons to switch between different parameter views.

    This panel interacts with a QStackedWidget passed as 'parameters_view' to display
    the corresponding content panels based on button clicks.

    Attributes:
        main_window: Reference to the main application window.
        parameters_view (QStackedWidget): Widget managing the displayed parameter views.
        tab_buttons (list): List of QPushButton objects representing navigation tabs.
    """

    def __init__(self, main_window, parameters_view):
        """
        Initialize the OptionsPanel with buttons and link to the parameter views.

        Args:
            main_window: Reference to the parent/main application window.
            parameters_view (QStackedWidget): The stacked widget controlling parameter views.
        """
        super().__init__()
        self.main_window = main_window
        self.parameters_view = parameters_view

        # Set initial view index to 0 (default first panel)
        self.parameters_view.setCurrentIndex(0)

        # Set visual styling for the panel
        self.setStyleSheet("background-color: #131313; border-radius: 0px;")

        # Initialize vertical layout with zero margins
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.tab_buttons = []

        # Create navigation buttons and option panels
        self.create_buttons()
        self.create_option_panels()

        # Log initialization complete
        print("DEBUG: OptionsPanel initialized with navigation buttons and linked parameter views.")

    def create_buttons(self):
        """
        Create navigation buttons and add them to the panel layout.

        Each button corresponds to a different parameter view in 'parameters_view'.
        The first button is styled as active by default.
        """
        btn_info = [
            ("Home", "🏠"),
            ("LaPlace", "E"),
            ("Magnet", "B"),
            ("Simulation", "⯈")
        ]

        for index, (name, label) in enumerate(btn_info):
            btn = QPushButton(label)
            btn.setObjectName(f"{name}_Btn")

            # Apply active style to the first button, others receive default style
            if index == 0:
                btn.setStyleSheet(button_activate_style())
            else:
                btn.setStyleSheet(button_options_style())

            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            btn.setMinimumSize(60, 10)

            # Connect each button to the main window handler with its index and button reference
            btn.clicked.connect(lambda _, i=index, b=btn: self.main_window.on_dynamic_tab_clicked(i, b))

            self.layout.addWidget(btn)
            self.tab_buttons.append(btn)

        # Add stretch to push buttons to the top of the layout
        self.layout.addStretch()

        print("DEBUG: Navigation buttons created and added to OptionsPanel.")

    def create_option_panels(self):
        """
        Add the main window's panels as widgets in the 'parameters_view' stacked widget.

        The order of insertion corresponds to the button indices for correct navigation.
        """
        self.parameters_view.addWidget(self.main_window.home_panel)        # index 0
        self.parameters_view.addWidget(self.main_window.field_panel)       # index 1
        self.parameters_view.addWidget(self.main_window.magnetic_panel)    # index 2
        self.parameters_view.addWidget(self.main_window.simulation_panel)  # index 3

        print("DEBUG: Parameter view panels added to parameters_view stacked widget.")
