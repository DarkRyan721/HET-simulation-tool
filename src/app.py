import sys
import os
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QProcess
from main_window import MainWindow
import signal

from project_paths import data_file, project_file, worker


class LoadingScreen(QWidget):
    """
    Simple loading screen widget displaying a message while data or scripts are prepared.
    """
    def __init__(self, msg: str):
        """
        Initialize the loading screen with the given message.

        Args:
            msg (str): Message to be displayed on the loading screen.
        """
        super().__init__()
        # Keep window on top without title bar or system buttons
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)

        layout = QVBoxLayout(self)
        self.label = QLabel(msg)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.resize(400, 100)
        self.setWindowTitle("Preparing data...")


def run_app():
    """
    Entry point for the application.

    Checks for required script and data files, and if any are missing,
    launches a loading screen and runs a background process to generate
    initial files before starting the main window.

    If all files are present, it launches the main window directly.
    """
    # List of required script files relative to project root
    script_files = [
        "electric_field_solver.py",
        "magnetic_field_solver_cpu.py",
        "mesh_generator.py",
        "project_paths.py",
        "particle_in_cell_cpu.py"
    ]

    # List of required data files relative to data folder
    data_files = [
        "SimulationZone.msh",
        "E_Field_Laplace.npy",
        "E_Field_Poisson.npy",
        "Magnetic_Field_np.npy",
        "particle_simulation.npy"
    ]

    # Check for missing scripts and data files
    missing_scripts = [f for f in script_files if not os.path.isfile(project_file(f))]
    missing_data = [f for f in data_files if not os.path.isfile(data_file(f))]

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Allow Ctrl+C to terminate the application gracefully in terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if missing_scripts or missing_data:
        print("DEBUG: Missing files detected, launching loading screen and initialization process.")

        loading_screen = LoadingScreen("Generating initial files. Please wait...")
        loading_screen.show()

        process = QProcess()
        process.setProgram(sys.executable)
        # Run the worker script responsible for creating initial state files
        process.setArguments([worker("initial_state_process.py")])

        def on_process_finished(exitCode, exitStatus):
            print(f"DEBUG: Initialization process finished with exit code {exitCode}")
            loading_screen.label.setText(f"Generation completed. Exit code: {exitCode}")
            loading_screen.hide()

            # Instantiate and show the main application window
            window = MainWindow()
            window.show()

            # Optionally delete the loading screen widget
            # loading_screen.deleteLater()

        # Connect process finished signal to handler
        process.finished.connect(on_process_finished)

        # Start the background initialization process
        process.start()

        # Start the Qt event loop
        sys.exit(app.exec())

    else:
        print("DEBUG: All required files found. Launching main window directly.")
        window = MainWindow()
        window.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
