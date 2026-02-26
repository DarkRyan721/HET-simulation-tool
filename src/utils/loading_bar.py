from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel
from PySide6.QtCore import Qt

class ProgressBarWidget(QWidget):
    """
    A custom widget combining a QLabel and a QProgressBar to indicate processing status.

    The progress bar is shown in indeterminate mode (busy indicator) until explicitly finished.

    Args:
        text (str): Initial text displayed above the progress bar. Default is "Processing...".
    """

    def __init__(self, text: str = "Processing..."):
        super().__init__()
        # Create a vertical layout for the label and progress bar
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label to display status text, centered horizontally
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignCenter)

        # Progress bar in indeterminate mode to show ongoing activity
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate mode: no specific progress value
        self.progress.setTextVisible(False)  # Hide percentage text on the bar

        # Add widgets to layout
        layout.addWidget(self.label)
        layout.addWidget(self.progress)

        # Set the layout for this widget
        self.setLayout(layout)

        # Initially hide the widget until processing starts
        self.hide()

    def start(self, text: str | None = None):
        """
        Show the progress bar widget and optionally update the label text.

        Args:
            text (str | None): Optional text to display when starting. If None, label remains unchanged.
        """
        if text:
            self.label.setText(text)
        self.show()

    def finish(self):
        """
        Hide the progress bar widget to indicate processing completion.
        """
        self.hide()
