import PySide6.QtWidgets as QtW
from PySide6.QtWidgets import QStackedWidget, QFrame, QVBoxLayout
from PySide6.QtCore import QTimer
import meshio
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6 import QtCore
from gui_styles.stylesheets import *
from utils.loader_thread import LoaderWorker


class ViewPanel(QFrame):
    """
    A container widget that manages multiple 3D view widgets using a QStackedWidget.

    This panel holds different visualization widgets (mesh, field, magnetic, simulation),
    allowing switching between them efficiently.

    Attributes:
        main_window: Reference to the main application window, used to access other panels.
        view_stack (QStackedWidget): Stacked widget holding all viewer widgets.
        viewers (dict): Dictionary mapping viewer names to their widget instances.
        current_data: Reference to the currently displayed data (optional).
    """

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setObjectName("VPartFrame")
        # Styling now lives in self_Style() (via QFrame#VPartFrame selector)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)

        # Initialize the stacked widget that will hold different views
        self.view_stack = QStackedWidget(self)
        layout.addWidget(self.view_stack)

        # Map viewer keys to existing viewer widgets from main_window's panels
        self.viewers = {
            "mesh": self.main_window.home_panel.home_viewer,
            "field": self.main_window.field_panel.field_viewer,
            "magnetic": self.main_window.magnetic_panel.magnetic_viewer,
            "simulation": self.main_window.simulation_panel.simulation_viewer
        }

        # Add each viewer widget to the stacked widget and log the action
        for name, viewer in self.viewers.items():
            print(f"DEBUG: Adding viewer '{name}' to view stack: {viewer}")
            self.view_stack.addWidget(viewer)

        self.current_data = None  # Store reference to current visualized data for potential future use

    def switch_view(self, name: str):
        """
        Switch the currently displayed viewer by name.

        Args:
            name (str): The key name of the viewer to display.

        Logs a warning if the requested viewer is not registered.
        """
        if name in self.viewers:
            print(f"DEBUG: Switching view to '{name}'.")
            self.view_stack.setCurrentWidget(self.viewers[name])
        else:
            print(f"WARNING: Viewer '{name}' not found in registered viewers.")

    def add_viewer(self, name: str, widget: QtW.QWidget):
        """
        Add a new viewer widget to the stack or replace an existing one by the same name.

        Args:
            name (str): Unique identifier for the viewer.
            widget (QWidget): The widget instance to add.

        If a viewer with the given name exists, it will be removed before adding the new one.
        Logs all relevant actions.
        """
        if name in self.viewers:
            print(f"DEBUG: Removing existing viewer '{name}' before adding new widget.")
            self.view_stack.removeWidget(self.viewers[name])
            del self.viewers[name]

        self.viewers[name] = widget
        self.view_stack.addWidget(widget)
        print(f"DEBUG: Added viewer '{name}' to view stack: {widget}")
