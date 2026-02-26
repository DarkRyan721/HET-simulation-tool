# ──────────────────────────────────────────────
# Importación de librerías estándar
import os                      # Manejo de rutas y operaciones con archivos
import numpy as np             # Biblioteca para cálculos numéricos y álgebra matricial

# ──────────────────────────────────────────────
# Importación de módulos de PySide6 para la interfaz gráfica
import PySide6.QtWidgets as QtW  # Importación general de widgets Qt para construcción de la GUI
from PySide6 import QtCore        # Elementos centrales de Qt, incluyendo señales y soporte para hilos
from PySide6.QtWidgets import (  # Widgets específicos para la interfaz gráfica principal
    QWidget, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QVBoxLayout, QFormLayout, QGroupBox
)
from PySide6.QtWidgets import QMessageBox  # Diálogos emergentes para mostrar mensajes al usuario
from PySide6.QtCore import QThread, Signal, QObject, QTimer  # Clases para multitarea, señales y temporizadores

# ──────────────────────────────────────────────
# Módulos para visualización 3D y manejo de mallas
import pyvista as pv                 # Biblioteca para visualización y procesamiento 3D
from pyvistaqt import QtInteractor  # Integración de PyVista con Qt para interacción visual
import meshio                       # Herramienta para lectura y escritura de formatos de malla
import gmsh                         # Generación y refinamiento de mallas geométricas

# ──────────────────────────────────────────────
# Importación de módulos propios del proyecto
from electric_field_solver import ElectricFieldSolver           # Solucionador de campos eléctricos
from mesh_generator import HallThrusterMesh                     # Generador de malla para propulsor Hall
from project_paths import model                                  # Gestión de rutas dentro del proyecto
from widgets.panels.simulation_options import SimulationOptionsPanel  # Panel para opciones de simulación
from widgets.panels.magnetic_field.magnetic_options import MagneticOptionsPanel  # Panel de opciones para campo magnético
from widgets.panels.field_options import FieldOptionsPanel       # Panel de opciones para campo eléctrico
from gui_styles.stylesheets import *                             # Estilos CSS para personalización de la interfaz
from widgets.parameter_views import ParameterPanel               # Panel para visualización y edición de parámetros
from widgets.options_panel import OptionsPanel                   # Panel general para opciones diversas
from widgets.view_panel import ViewPanel                         # Panel principal para visualización 3D
from utils.loader_thread import LoaderWorker                     # Worker para tareas en segundo plano con hilos
from models.simulation_state import SimulationState              # Modelo que representa el estado actual de la simulación
from widgets.panels.home_options import HomeOptionsPanel         # Panel de opciones en la pantalla inicial
from PySide6.QtWidgets import QProgressDialog                    # Diálogo para mostrar progreso de tareas largas
from PySide6.QtCore import QThread, Signal, QObject, Qt         # Clases centrales para multitarea y gestión de eventos Qt
from PySide6.QtGui import QGuiApplication                        # Funciones para interacción con la pantalla y GUI

class MainWindow(QtW.QMainWindow):
    def __init__(self):
        super().__init__()
        self._active_threads = []

        # Definición del título principal de la ventana
        self.setWindowTitle("HET simulator")

        # Obtener dimensiones disponibles de la pantalla principal para dimensionar la ventana
        screen_size = QGuiApplication.primaryScreen().availableGeometry().size()
        width, height = screen_size.width(), screen_size.height()

        # Establecer tamaño mínimo y tamaño inicial basado en proporciones de la pantalla
        self.setMinimumSize(int(width * 0.8), int(height * 0.8))
        self.resize(int(width * 0.95), int(height * 0.8))

        # Definición de la ruta para el archivo JSON que contiene el estado de la simulación
        state_file = model("simulation_state.json")

        # Cargar estado de simulación si existe; si no, crear estado inicial y guardarlo
        if os.path.exists(state_file):
            print("[INFO] Estado de simulación cargado desde archivo JSON.")
            self.simulation_state = SimulationState.load_from_json(state_file)
            self.simulation_state.print_state()
        else:
            print("[INFO] Archivo de estado no encontrado. Se crea estado por defecto.")
            self.simulation_state = SimulationState()
            self.simulation_state.save_to_json(state_file)  # Guardar archivo inicial

        # Instanciación de los paneles principales que componen la interfaz de usuario
        self.home_panel = HomeOptionsPanel(self)
        self.field_panel = FieldOptionsPanel(self)
        self.magnetic_panel = MagneticOptionsPanel(self)
        self.simulation_panel = SimulationOptionsPanel(self)

        # Configuración general de la interfaz gráfica
        self._setup_ui()

        # Aplicar estilos personalizados definidos en el proyecto
        self.setStyleSheet(self_Style())

        # Añadir el visor del campo magnético al panel principal de visualización
        self.View_Part.add_viewer("magnetic", self.magnetic_panel.magnetic_viewer)

    def _setup_ui(self):
        # Configuración del widget central y distribución principal de la ventana

        central_widget = QtW.QWidget()  # Widget contenedor principal
        self.frame = QtW.QHBoxLayout()  # Layout horizontal para distribuir columnas
        self.frame.setSpacing(0)        # Eliminar espacios entre columnas
        self.frame.setContentsMargins(0, 0, 0, 0)  # Sin márgenes externos

        # Creación de las tres columnas principales: opciones, parámetros y vista principal
        self.Parameters = ParameterPanel(self)  # Panel para parámetros
        self.Options = OptionsPanel(self, self.Parameters.parameters_view)  # Panel para opciones con acceso a parámetros
        self.View_Part = ViewPanel(self)        # Panel principal para visualización 3D
        self.parameters_view = self.Parameters.parameters_view
        self.set_active_button(self.Options.tab_buttons[0])  # Seleccionar botón activo inicial

        # Añadir widgets al layout principal con distribución proporcional del espacio
        self.frame.addWidget(self.Options, stretch=0.3)
        self.frame.addWidget(self.Parameters, stretch=1)
        self.frame.addWidget(self.View_Part.view_stack, stretch=4)

        # Asignar layout al widget central y establecerlo como contenido principal de la ventana
        central_widget.setLayout(self.frame)
        self.setCentralWidget(central_widget)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Ajustar tamaño mínimo del contenido interno si existe el atributo 'frame_content'
        if hasattr(self, 'frame_content'):
            self.frame_content.setMinimumSize(self.width(), self.height())

    @property
    def current_viewer(self):
        # Retorna el widget de visualización actualmente activo
        return self.View_Part.view_stack.currentWidget()

    def on_dynamic_tab_clicked(self, index, btn):
        # Gestión del cambio de pestañas: actualizar vista de parámetros y panel de visualización

        self.parameters_view.setCurrentIndex(index)  # Cambiar índice de vista de parámetros
        self.set_active_button(btn)                   # Actualizar estilo del botón activo

        # Cambiar panel de visualización según la pestaña seleccionada
        if index == 0:
            self.View_Part.switch_view("mesh")
        elif index == 1:
            self.View_Part.switch_view("field")
            self.alert_if_field_or_magnetic_outdated()
        elif index == 2:
            self.View_Part.switch_view("magnetic")
            self.alert_if_field_or_magnetic_outdated()
        elif index == 3:
            self.View_Part.switch_view("simulation")
            self.alert_if_field_or_magnetic_outdated()

    def set_active_button(self, active_btn):
        # Actualizar estilos visuales para resaltar el botón actualmente activo
        for btn in self.Options.tab_buttons:
            if btn == active_btn:
                btn.setStyleSheet(button_activate_style())
            else:
                btn.setStyleSheet(button_options_style())

    def launch_worker(self, worker, finished_callback):
        # Crear y lanzar un hilo para ejecutar una tarea en segundo plano mediante un worker

        thread = QThread()
        self._active_threads.append(thread)
        worker.moveToThread(thread)

        print(f"[INFO] Iniciando worker con modo: {worker.mode}")

        # Conectar señales para gestión de ejecución y limpieza
        thread.started.connect(worker.run)
        worker.finished.connect(finished_callback)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)

        def cleanup():
            print(f"[INFO] Liberando recursos del hilo asociado al worker: {worker.mode}")
            if thread in self._active_threads:
                self._active_threads.remove(thread)
            thread.deleteLater()

        thread.finished.connect(cleanup)

        # Iniciar ejecución del hilo
        thread.start()

    def alert_if_field_or_magnetic_outdated(self):
        # Verificar si los campos eléctrico o magnético están desactualizados y notificar al usuario

        state = self.simulation_state

        # Actualizar estado visual de los botones relacionados con simulación y campo magnético
        self.simulation_panel.update_simulate_button_state()
        self.magnetic_panel.update_magnetic_button_state()

        message = ""
        if state.field_outdated and state.magnetic_outdated:
            message = (
                "Debe actualizar el campo eléctrico y el campo magnético "
                "tras modificar el dominio de simulación para obtener resultados precisos."
            )
        elif state.field_outdated:
            message = "Debe actualizar el campo eléctrico tras modificar el dominio de simulación."
        elif state.magnetic_outdated:
            message = "Debe actualizar el campo magnético tras modificar el dominio de simulación."

        # Mostrar diálogo de advertencia personalizado si es necesario
        if message:
            box = QMessageBox(self)
            box.setWindowTitle("Actualizar campos")
            box.setText(message)
            box.setIcon(QMessageBox.Warning)
            box.setStyleSheet("""
                QMessageBox {
                    background-color: #121212;
                    color: #f5f5f5;
                }
                QLabel {
                    color: #f5f5f5;
                }
                QPushButton {
                    background-color: #23272b;
                    color: #f5f5f5;
                    border: 1px solid #444;
                    border-radius: 6px;
                    padding: 6px 18px;
                }
                QPushButton:hover {
                    background-color: #32373a;
                }
            """)
            box.exec()
