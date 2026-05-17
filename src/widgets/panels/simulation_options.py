import os
import time
import numpy as np
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import QMessageBox
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit, QLabel,
    QHBoxLayout, QPushButton, QCheckBox, QSlider, QComboBox
)
from PySide6.QtCore import QTimer
import subprocess
import json

from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QStyle
import PySide6.QtWidgets as QtW
from PySide6.QtCore import Qt
from PySide6.QtCore import QTimer

from project_paths import data_file, model, worker
from widgets.panels.collapse import CollapsibleBox
from PySide6.QtWidgets import QVBoxLayout, QPushButton, QWidget, QLabel, QFrame
from utils.loading_bar import ProgressBarWidget

from models.simulation_state import SimulationState
from simulation_engine_viewer import Simulation
from utils.ui_helpers import _input_with_unit
from gui_styles.stylesheets import *
from gui_styles.stylesheets import messagebox_style
from widgets.alert_banner import AlertBanner
from utils.loader_thread import LoaderWorker
from PySide6.QtWidgets import QHBoxLayout

class SimulationOptionsPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.simulation_state = self.main_window.simulation_state
        self.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.dependency_banner = AlertBanner(
            title="Prerequisites required",
            message="Update the electric and magnetic fields first.",
            level="warning",
        )
        self.dependency_banner.hide()
        layout.addWidget(self.dependency_banner)

        sim_box = QGroupBox("Simulation parameters")
        sim_box.setStyleSheet(box_render_style())
        sim_layout = QFormLayout()

        lbl_n_particles = QLabel("Number of particles (N):")
        lbl_n_particles.setToolTip("Total number of particles simulated in the domain.")
        self.input_N_particles_container, self.input_N_particles = _input_with_unit(
            str(self.simulation_state.N_particles), "[#]"
        )

        lbl_frames = QLabel("Animation frames:")
        lbl_frames.setToolTip("Number of simulation steps/frames displayed.")

        self.input_frames_container, self.input_frames = _input_with_unit(
            str(self.simulation_state.frames), "[#]"
        )

        sim_layout.addRow(lbl_n_particles, self.input_N_particles)
        sim_layout.addRow(lbl_frames, self.input_frames)

        lbl_gas = QLabel("Working gas:")
        lbl_gas.setToolTip("Gas used to simulate the discharge.")
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems([
            "Xenon (Xe) – propulsion standard",
            "Argon (Ar) – experimental, lower mass",
            "Helium (He) – high mobility, very light"
        ])
        self.view_mode_combo.setStyleSheet(box_render_style())
        sim_layout.addRow(lbl_gas, self.view_mode_combo)

        sim_box.setLayout(sim_layout)
        layout.addWidget(sim_box)

        controls_box = QGroupBox("Simulation controls")
        controls_box.setStyleSheet(box_render_style())
        controls_layout = QHBoxLayout()

        self.start_btn = QPushButton("Simulate")
        self.start_btn.setStyleSheet(button_parameters_style())
        self.start_btn.setToolTip("Start or resume the particle simulation.")
        self.start_btn.clicked.connect(self.on_run_simulation)
        controls_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("Run")
        self.pause_btn.setStyleSheet(button_parameters_style())
        self.pause_btn.clicked.connect(self.on_pause_resume_clicked)
        controls_layout.addWidget(self.pause_btn)

        self.enable_checkbox = QCheckBox("Enable GPU computation")
        self.enable_checkbox.setChecked(self.simulation_state.GPU_ACTIVE)
        self.enable_checkbox.setToolTip("Enable or disable CUDA (Nvidia) acceleration.")
        self.enable_checkbox.setStyleSheet(checkbox_style())
        controls_layout.addWidget(self.enable_checkbox)

        controls_box.setLayout(controls_layout)
        layout.addWidget(controls_box)

        advanced_toggle = QPushButton("Advanced options")
        advanced_toggle.setCheckable(True)
        advanced_toggle.setChecked(False)
        advanced_toggle.setStyleSheet(advanced_toggle_style())

        advanced_content = QFrame()
        advanced_content.setVisible(False)
        advanced_content.setStyleSheet(advanced_content_style())
        advanced_content_layout = QFormLayout(advanced_content)

        self.input_alpha_container, self.input_alpha = _input_with_unit(
            str(self.simulation_state.alpha), "[adim]"
        )
        self.input_alpha_container.setToolTip("Recombination / dimensionless model coefficient.")

        self.input_sigma_ion_container, self.input_sigma_ion = _input_with_unit(
            str(self.simulation_state.sigma_ion), "[m²]"
        )
        self.input_sigma_ion_container.setToolTip("Ionization cross-section (m²).")

        self.input_dt_container, self.input_dt = _input_with_unit(
            str(self.simulation_state.dt), "[s]"
        )
        self.input_dt_container.setToolTip("Integration time step.")

        advanced_content_layout.addRow("Alpha:", self.input_alpha_container)
        advanced_content_layout.addRow("Sigma ion:", self.input_sigma_ion_container)
        advanced_content_layout.addRow("Time step:", self.input_dt_container)

        def toggle_advanced():
            advanced_content.setVisible(advanced_toggle.isChecked())

        advanced_toggle.clicked.connect(toggle_advanced)
        layout.addWidget(advanced_toggle)

        layout.addWidget(advanced_content)

        self.progress_bar = ProgressBarWidget("Loading simulation...")
        layout.addWidget(self.progress_bar)
        self.progress_bar.hide()

        output_box = QGroupBox("Simulation results")
        output_box.setStyleSheet(box_render_style())
        output_layout = QVBoxLayout(output_box)
        self.label_impulso = QLabel(f"Specific impulse: <b>{self.simulation_state.impulso_especifico}</b>")
        self.label_tiempo = QLabel(f"Simulation time: <b>{self.simulation_state.time_simulation}</b>")
        self.label_frames = QLabel(f"Frame count: <b>{self.simulation_state.frames}</b>")
        output_layout.addWidget(self.label_impulso)
        output_layout.addWidget(self.label_tiempo)
        output_layout.addWidget(self.label_frames)
        layout.addWidget(output_box)

        self.progress_bar = ProgressBarWidget("Simulating particles...")
        layout.addWidget(self.progress_bar)
        self.progress_bar.hide()

        layout.addStretch()
        self.setLayout(layout)

        self.simulation_viewer = QtInteractor(self)
        self.simulation_instance = Simulation(plotter=self.simulation_viewer)
        self.simulation_running = False
        self.simulation_paused = False
        self.simulation_worker = LoaderSimulation(plotter=self.simulation_instance)
        self.simulation_thread = QThread()
        self.simulation_worker.moveToThread(self.simulation_thread)
        self.simulation_thread.started.connect(self.simulation_worker.run)
        self.simulation_worker.finished.connect(self.simulation_thread.quit)
        self.simulation_worker.finished.connect(self.simulation_worker.deleteLater)
        self.simulation_thread.finished.connect(self.simulation_thread.deleteLater)
        self.loader_worker_simulation = None

    def _reload_shared_state(self):
        """Reload state from disk and keep a single shared object across all panels."""
        loaded_state = SimulationState.load_from_json(model("simulation_state.json"))
        self.main_window.simulation_state.__dict__.update(loaded_state.__dict__)
        self.simulation_state = self.main_window.simulation_state

    def on_run_simulation(self):
        prereq_msg = self._missing_prerequisites_message()
        if prereq_msg:
            self.main_window.show_prerequisite_alert("Update fields", prereq_msg)
            return

        campos = {
            "N_particles": self.input_N_particles.text(),
            "frames": self.input_frames.text(),
            "alpha": self.input_alpha.text(),
            "sigma_ion": self.input_sigma_ion.text(),
            "dt": self.input_dt.text(),
        }
        opcionales = ["alpha", "sigma_ion", "dt"]

        try:
            valores = self.validar_numeros(campos, opcionales=opcionales)
        except ValueError as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Validation error", str(e))
            return

        N_particles = int(valores["N_particles"])
        frames = int(valores["frames"])
        alpha = valores["alpha"]
        sigma_ion = valores["sigma_ion"]
        dt = valores["dt"]

        self.simulation_state.N_particles = N_particles
        self.simulation_state.frames = frames
        self.simulation_state.alpha = alpha
        self.simulation_state.sigma_ion = sigma_ion
        self.simulation_state.dt = dt
        self.simulation_state.GPU_ACTIVE = self.enable_checkbox.isChecked()

        gas_combo_index = self.view_mode_combo.currentIndex()
        gas_combo_text = self.view_mode_combo.currentText()
        if "Xenon" in gas_combo_text or "Xenón" in gas_combo_text:
            gas = "Xenon"
        elif "Argon" in gas_combo_text or "Argón" in gas_combo_text:
            gas = "Argon"
        elif "Helium" in gas_combo_text or "Helio" in gas_combo_text:
            gas = "Helium"
        elif "Krypton" in gas_combo_text or "Kriptón" in gas_combo_text:
            gas = "Krypton"
        else:
            gas = "Xenon"

        gas_map = {
            0: "Xenon",
            1: "Argon",
            2: "Helium",
            3: "Krypton"
        }
        gas = gas_map.get(gas_combo_index, "Xenon")
        self.simulation_state.gas = gas

        new_params = (N_particles, frames, alpha, sigma_ion, dt, gas, self.enable_checkbox.isChecked())

        if new_params != self.simulation_state.prev_params_simulation:
            print("Simulation parameters changed:", new_params)
            self.simulation_state.prev_params_simulation = new_params
            self.simulation_state.save_to_json(model("simulation_state.json"))
            self.progress_bar.start("Running simulation...")
            self.run_solver_in_subprocess()
        else:
            from PySide6.QtWidgets import QMessageBox
            print("No changes detected in simulation parameters.")
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("No changes detected")
            msg.setText("You must change the parameters to run a new simulation.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet(messagebox_style())
            msg.exec()

    def update_simulate_button_state(self):
        """Keep the start button enabled; missing prerequisites are surfaced
        as a card on click and via the inline banner."""
        self.start_btn.setEnabled(True)
        self.start_btn.setToolTip("Start or resume the particle simulation.")

    def _missing_prerequisites_message(self) -> str | None:
        state = self.simulation_state
        if state.field_outdated and state.magnetic_outdated:
            return ("The electric field and the magnetic field must be updated "
                    "before running a new particle simulation.")
        if state.field_outdated:
            return "The electric field must be updated before running a new simulation."
        if state.magnetic_outdated:
            return "The magnetic field must be updated before running a new simulation."
        return None

    def refresh_banner(self):
        msg = self._missing_prerequisites_message()
        if msg:
            self.dependency_banner.set_content(
                title="Prerequisites required",
                message=msg,
                level="warning",
            )
            self.dependency_banner.show()
        else:
            self.dependency_banner.hide()

    def validar_numeros(self, campos, opcionales=None):
        if opcionales is None:
            opcionales = set()
        else:
            opcionales = set(opcionales)
        resultados = {}
        for nombre, texto in campos.items():
            texto = str(texto).strip()
            if not texto or texto.lower() == "none":
                if nombre in opcionales:
                    resultados[nombre] = None
                    continue
                else:
                    raise ValueError(f"Field '{nombre}' is required and is empty.")
            try:
                valor = float(texto)
            except ValueError:
                raise ValueError(f"Field '{nombre}' must be a valid number. Received: '{texto}'")
            resultados[nombre] = valor
        return resultados

    def run_solver_in_subprocess(self):
        self.start_btn.setEnabled(False)

        args = [
            'python3', worker("particle_in_cell_process.py")
        ]
        print("🔄 Ejecutando solver en subprocess...")
        self.solver_start_time = time.perf_counter()
        try:
            self.process = subprocess.Popen(args)
            self.process_finished = False
            print(f"[DEBUG] Proceso lanzado, PID: {self.process.pid}")
        except Exception as e:
            print(f"[ERROR] Failed to launch subprocess: {e}")
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Subprocess launch error")
            msg.setText(f"Could not start the solver: {e}")
            msg.setStyleSheet(messagebox_style())
            msg.exec()
            self.process = None
            self.start_btn.setEnabled(True)
            return

        def check_output():
            if self.process is None:
                self.timer.stop()
                return
            if self.process.poll() is not None:
                self.timer.stop()
                elapsed = time.perf_counter() - self.solver_start_time

                stdout, stderr = self.process.communicate()
                exit_code = self.process.returncode
                self.process = None
                self.progress_bar.finish()
                self.start_btn.setEnabled(True)

                self._reload_shared_state()

                if exit_code != 0:
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Critical)
                    msg.setWindowTitle("Solver error")
                    msg.setText(f"The solver failed with exit code {exit_code} after {elapsed:.2f} s.")
                    msg.setDetailedText(stderr if stderr else "No error output was received.")
                    msg.setStyleSheet(messagebox_style())
                    msg.exec()
                    self.start_btn.setEnabled(True)
                    self.progress_bar.finish()
                    print(f"[ERROR] Solver failed: {stderr}")
                    self.label_impulso.setText("Specific impulse: <b>N/A</b>")
                    self.label_tiempo.setText("Simulation time: <b>N/A</b>")
                    self.label_frames.setText(f"Frame count: <b>{self.simulation_state.frames}</b>")
                    self.simulation_state.prev_params_simulation = [None] * len(self.simulation_state.prev_params_simulation)
                    return
                print(f"[INFO] Solver finished successfully in {elapsed:.2f} s")
                self._reload_shared_state()
                try:
                    self.simulation_state.time_simulation = elapsed
                    self.simulation_state.save_to_json(model("simulation_state.json"))
                except Exception as e:
                    print(f"[ERROR] Could not read results: {e}")
                    self.simulation_state.impulso_especifico = "N/A"
                self.label_impulso.setText(f"Specific impulse: <b>{self.simulation_state.impulso_especifico} s</b>")
                self.label_tiempo.setText(f"Simulation time: <b>{elapsed:.2f} s</b>")
                self.label_frames.setText(f"Frame count: <b>{self.simulation_state.frames}</b>")
                self.simulation_instance.reload_data()
                self.simulation_instance.refresh_particles()

                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Simulation completed")
                msg.setText("The solver finished successfully.\nApp is ready.")
                msg.setStyleSheet(messagebox_style())
                msg.exec()

        self.timer = QTimer()
        self.timer.timeout.connect(check_output)
        self.timer.start(300)

    def on_pause_resume_clicked(self):
        self.pause_btn.setEnabled(False)
        self.simulation_instance._create_particle_actors()

        thread = QThread()
        self._pause_thread = thread
        worker = LoaderWorker(
            mode="simulation",
            plotter=self.simulation_instance,
            params={"neutral_visible": True}
        )

        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)

        def cleanup():
            print(f"🧹 Limpiando thread del worker: {worker.mode}")
            self.simulation_instance.reload_data()
            self.simulation_instance.refresh_particles()
            self.pause_btn.setEnabled(True)
            self._pause_thread = None
            thread.deleteLater()

        thread.finished.connect(cleanup)
        print(f"🚀 Lanzando worker en modo: {worker.mode}")
        thread.start()


    def on_restart_clicked(self):
        print("[DEBUG] Reiniciando simulación")
        if hasattr(self, 'loader_worker_simulation') and self.loader_worker_simulation is not None:
            self.loader_worker_simulation.stop()
        self.simulation_running = False
        self.simulation_paused = False

class LoaderSimulation(QObject):
    finished = Signal(object)
    started = Signal()
    progress = Signal(int)

    def __init__(self, params=None, plotter=None):
        super().__init__()
        self.params = params or {}
        self.plotter = plotter
        self._is_running = True

    @Slot()
    def run(self):
        print("🚀 Iniciando simulación de partículas...")
        if self.plotter is None:
            print("⚠️ Instancia de simulación no proporcionada.")
            return
        try:
            print("🔄 Ejecutando simulación...")
            self.plotter.Animation(neutral_visible=self.params.get("neutral_visible", False))
            self.finished.emit("Simulation completed")
        except Exception as e:
            print(f"❌ Error durante la simulación: {e}")

    def pause(self):
        print("Pausing simulation in worker.")
        self._is_paused = True

    def resume(self):
        print("Resuming simulation in worker.")
        self._is_paused = False

    def stop(self):
        print("Stopping simulation in worker.")
        self._is_running = False
        self._is_paused = False
