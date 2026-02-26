# magnetic_graphic_process.py

import os
import sys
import json

# Añadir al path el directorio raíz del proyecto para importar módulos personalizados
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from models.simulation_state import SimulationState
from project_paths import model
from magnetic_field_solver_cpu import B_Field

# Configurar backend no interactivo de matplotlib para generación sin GUI
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    # Cargar el estado de la simulación desde archivo JSON
    try:
        state = SimulationState.load_from_json(model("simulation_state.json"))
    except Exception as e:
        print(f"Error loading simulation state: {e}")
        sys.exit(1)

    # Extraer y validar parámetros esenciales
    try:
        mode_magnetic = state.mode_magnetic.lower()
        nSteps = int(state.nSteps)
        N_turns = int(state.N_turns)
        I = float(state.I)
        kwargs = state.kwargs
        output_file = state.output_file
    except (AttributeError, ValueError, TypeError) as e:
        print(f"Invalid simulation state data: {e}")
        sys.exit(1)

    if not output_file:
        print("No output file specified.")
        sys.exit(1)

    # Mostrar los parámetros para fines de depuración
    print("Parameters before B_Field initialization:")
    print(f"  nSteps = {nSteps}")
    print(f"  N_turns = {N_turns}")
    print(f"  I = {I}")
    print(f"  Mode = {mode_magnetic}")

    # Instanciar el objeto responsable del cálculo del campo magnético
    bfield = B_Field(nSteps=nSteps, N=N_turns, I=I)

    # Ejecutar el modo de visualización seleccionado
    try:
        if mode_magnetic == "fieldlines":
            result = bfield.B_Field_Lines(**kwargs)
        elif mode_magnetic == "heatmap":
            result = bfield.B_Field_Heatmap(**kwargs)
        elif mode_magnetic == "solenoid_points":
            result = bfield.Solenoid_points_plot(**kwargs)
        else:
            print(f"Invalid magnetic visualization mode: {mode_magnetic}")
            sys.exit(1)
        if result is not None and isinstance(result, tuple) and len(result) == 2:
            fig, ax = result
        else:
            raise RuntimeError("B_Field_Lines no retornó una tupla válida (fig, ax)")
    except Exception as e:
        print(f"Error during magnetic field visualization: {e}")
        sys.exit(1)

    # Guardar la figura generada en el archivo especificado
    try:
        fig.savefig(output_file, dpi=150)
        print(f"Figure saved successfully to {output_file}")
    except Exception as e:
        print(f"Failed to save figure: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
