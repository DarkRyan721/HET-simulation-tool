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
from utils.loader_thread import LoaderWorker
from PySide6.QtWidgets import QHBoxLayout

class SimulationOptionsPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.simulation_state = self.main_window.simulation_state
        self.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(self)

        sim_box = QGroupBox("🧮 Parámetros de Simulación")
        sim_box.setStyleSheet(box_render_style())
        sim_layout = QFormLayout()

        lbl_n_particles = QLabel("Número de partículas (N):")
        lbl_n_particles.setToolTip("Cantidad total de partículas simuladas en el dominio.")
        self.input_N_particles_container, self.input_N_particles = _input_with_unit(
            str(self.simulation_state.N_particles), "[#]"
        )

        lbl_frames = QLabel("Frames de animación:")
        lbl_frames.setToolTip("Número de pasos de simulación/frames visualizados.")

        self.input_frames_container, self.input_frames = _input_with_unit(
            str(self.simulation_state.frames), "[#]"
        )

        sim_layout.addRow(lbl_n_particles, self.input_N_particles)
        sim_layout.addRow(lbl_frames, self.input_frames)

        lbl_gas = QLabel("Gas de trabajo:")
        lbl_gas.setToolTip("Selecciona el gas con el que se simula la descarga.")
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems([
            "Xenón (Xe) – estándar en propulsión",
            "Argón (Ar) – experimental, menor masa",
            "Helio (He) – alta movilidad, muy ligero"
        ])
        self.view_mode_combo.setStyleSheet(box_render_style())
        sim_layout.addRow(lbl_gas, self.view_mode_combo)

        sim_box.setLayout(sim_layout)
        layout.addWidget(sim_box)

        controls_box = QGroupBox("Controles de simulación")
        controls_box.setStyleSheet(box_render_style())
        controls_layout = QHBoxLayout()

        self.start_btn = QPushButton("▶️ Simular")
        self.start_btn.setStyleSheet(button_parameters_style())
        self.start_btn.setToolTip("Inicia o reanuda la simulación de partículas.")
        self.start_btn.clicked.connect(self.on_run_simulation)
        controls_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("⏸️ Run")
        self.pause_btn.setStyleSheet(button_parameters_style())
        self.pause_btn.clicked.connect(self.on_pause_resume_clicked)
        controls_layout.addWidget(self.pause_btn)

        self.enable_checkbox = QCheckBox("Habilitar computacion grafica")
        self.enable_checkbox.setChecked(self.simulation_state.GPU_ACTIVE)
        self.enable_checkbox.setToolTip("Activa o desactiva el uso de CUDA (Nvidia).")
        controls_layout.addWidget(self.enable_checkbox)

        controls_box.setLayout(controls_layout)
        layout.addWidget(controls_box)

        advanced_toggle = QPushButton("Opciones avanzadas")
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
        self.input_alpha_container.setToolTip("Coeficiente de recombinación/adimensional para el modelo.")

        self.input_sigma_ion_container, self.input_sigma_ion = _input_with_unit(
            str(self.simulation_state.sigma_ion), "[m²]"
        )
        self.input_sigma_ion_container.setToolTip("Sección eficaz de ionización (m²).")

        self.input_dt_container, self.input_dt = _input_with_unit(
            str(self.simulation_state.dt), "[s]"
        )
        self.input_dt_container.setToolTip("Paso temporal de integración.")

        advanced_content_layout.addRow("Alpha:", self.input_alpha_container)
        advanced_content_layout.addRow("Sigma ion:", self.input_sigma_ion_container)
        advanced_content_layout.addRow("Delta time:", self.input_dt_container)

        def toggle_advanced():
            advanced_content.setVisible(advanced_toggle.isChecked())

        advanced_toggle.clicked.connect(toggle_advanced)
        layout.addWidget(advanced_toggle)

        layout.addWidget(advanced_content)

        self.progress_bar = ProgressBarWidget("Cargando simulación...")
        layout.addWidget(self.progress_bar)
        self.progress_bar.hide()

        output_box = QGroupBox("📊 Resultados de Simulación")
        output_box.setStyleSheet(box_render_style())
        output_layout = QVBoxLayout(output_box)
        self.label_impulso = QLabel(f"Impulso específico: <b>{self.simulation_state.impulso_especifico}</b>")
        self.label_tiempo = QLabel(f"Tiempo de simulación: <b>{self.simulation_state.time_simulation}</b>")
        self.label_frames = QLabel(f"Número de frames: <b>{self.simulation_state.frames}</b>")
        output_layout.addWidget(self.label_impulso)
        output_layout.addWidget(self.label_tiempo)
        output_layout.addWidget(self.label_frames)
        layout.addWidget(output_box)

        self.progress_bar = ProgressBarWidget("Simulando partículas...")
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
            QMessageBox.critical(self, "Error de validación", str(e))
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
        if "Xenón" in gas_combo_text:
            gas = "Xenon"
        elif "Argón" in gas_combo_text:
            gas = "Argon"
        elif "Helio" in gas_combo_text:
            gas = "Helium"
        elif "Kriptón" in gas_combo_text or "Krypton" in gas_combo_text:
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
            print("🔄 Parámetros de simulación cambiaron:", new_params)
            self.simulation_state.prev_params_simulation = new_params
            self.simulation_state.save_to_json(model("simulation_state.json"))
            self.progress_bar.start("Ejecutando simulación...")
            self.run_solver_in_subprocess()
        else:
            from PySide6.QtWidgets import QMessageBox
            print("⚠️ No se han realizado cambios en los parámetros de simulación.")
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Sin cambios detectados")
            msg.setText("Debe cambiar los parámetros para ejecutar una nueva simulación.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("QLabel{min-width: 300px;}")
            msg.exec()

    def update_simulate_button_state(self):
        """Deshabilita el botón si alguno de los campos está desactualizado."""
        if self.simulation_state.field_outdated or self.simulation_state.magnetic_outdated:
            self.start_btn.setEnabled(False)
            self.start_btn.setToolTip("Actualice el campo eléctrico y magnético antes de simular.")
        else:
            self.start_btn.setEnabled(True)
            self.start_btn.setToolTip("Inicia o reanuda la simulación de partículas.")

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
                    raise ValueError(f"El campo '{nombre}' es obligatorio y está vacío.")
            try:
                valor = float(texto)
            except ValueError:
                raise ValueError(f"El campo '{nombre}' debe ser un número válido. Valor recibido: '{texto}'")
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
            print(f"[ERROR] Fallo al lanzar el proceso: {e}")
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error al lanzar el subproceso")
            msg.setText(f"No se pudo iniciar el solver: {e}")
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
                    msg.setWindowTitle("Error en el solver")
                    msg.setText(f"El solver finalizó con error (código {exit_code}) después de {elapsed:.2f} s.")
                    msg.setDetailedText(stderr if stderr else "No se recibió salida de error.")
                    msg.exec()
                    self.start_btn.setEnabled(True)
                    self.progress_bar.finish()
                    print(f"[ERROR] Solver falló: {stderr}")
                    self.label_impulso.setText("Impulso específico: <b>N/A</b>")
                    self.label_tiempo.setText("Tiempo de simulación: <b>N/A</b>")
                    self.label_frames.setText(f"Número de frames: <b>{self.simulation_state.frames}</b>")
                    self.simulation_state.prev_params_simulation = [None] * len(self.simulation_state.prev_params_simulation)
                    return
                print(f"[INFO] Solver terminado exitosamente en {elapsed:.2f} s")
                self._reload_shared_state()
                try:
                    self.simulation_state.time_simulation = elapsed
                    self.simulation_state.save_to_json(model("simulation_state.json"))
                except Exception as e:
                    print(f"[ERROR] No se pudieron leer los resultados: {e}")
                    self.simulation_state.impulso_especifico = "N/A"
                self.label_impulso.setText(f"Impulso específico: <b>{self.simulation_state.impulso_especifico} s</b>")
                self.label_tiempo.setText(f"Tiempo de simulación: <b>{elapsed:.2f} s</b>")
                self.label_frames.setText(f"Número de frames: <b>{self.simulation_state.frames}</b>")
                self.simulation_instance.reload_data()
                self.simulation_instance.refresh_particles()

                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Simulación completada (Simulación)")
                msg.setText("✅ El solver se completó correctamente.\nApp is ready.")
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
