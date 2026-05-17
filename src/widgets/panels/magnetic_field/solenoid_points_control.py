from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout

from gui_styles.stylesheets import button_parameters_style, box_render_style, checkbox_style

class SolenoidPointsControlPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Solenoid visualization", parent)
        self.setStyleSheet(box_render_style())
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        self.cb_inner = QCheckBox("Inner solenoid")
        self.cb_inner.setChecked(True)
        self.cb_1 = QCheckBox("Solenoid 1")
        self.cb_1.setChecked(True)
        self.cb_2 = QCheckBox("Solenoid 2")
        self.cb_2.setChecked(True)
        self.cb_3 = QCheckBox("Solenoid 3")
        self.cb_3.setChecked(True)
        self.cb_4 = QCheckBox("Solenoid 4")
        self.cb_4.setChecked(True)
        self.cb_cylinder = QCheckBox("Outer cylinder")
        self.cb_cylinder.setChecked(True)
        for cb in (self.cb_inner, self.cb_1, self.cb_2, self.cb_3, self.cb_4, self.cb_cylinder):
            cb.setStyleSheet(checkbox_style())

        row1 = QHBoxLayout()
        row1.addWidget(self.cb_inner)
        row1.addWidget(self.cb_1)
        row1.addWidget(self.cb_2)

        row2 = QHBoxLayout()
        row2.addWidget(self.cb_3)
        row2.addWidget(self.cb_4)
        row2.addWidget(self.cb_cylinder)

        layout.addLayout(row1)
        layout.addLayout(row2)

        self.btn_update = QPushButton("Update plot")
        self.btn_update.setStyleSheet(button_parameters_style())
        layout.addWidget(self.btn_update)

        self.setLayout(layout)

    def get_params(self):
        return dict(
            Solenoid_inner=self.cb_inner.isChecked(),
            Solenoid_1=self.cb_1.isChecked(),
            Solenoid_2=self.cb_2.isChecked(),
            Solenoid_3=self.cb_3.isChecked(),
            Solenoid_4=self.cb_4.isChecked(),
            Cylinder_ext=self.cb_cylinder.isChecked()
        )