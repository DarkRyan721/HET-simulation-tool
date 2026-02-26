import io
import os
import sys
import json
import traceback
import numpy as np

# Add parent directory to path for imports relative to project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from project_paths import model
from models.simulation_state import SimulationState
from mesh_generator import HallThrusterMesh

print("[DEBUG] Launching run_mesher.py...")

try:
    # Load simulation state from JSON file
    state = SimulationState.load_from_json(model("simulation_state.json"))

    # Extract parameters from simulation state
    H = state.H
    R_big = state.R_big
    R_small = state.R_small
    refinement_level = state.refinement_level
    min_physical_scale = state.min_physics_scale
    max_elements = state.max_elements

    # Debug print for all extracted parameters
    print(f"[DEBUG] Parameters extracted from simulation state:\n"
        f"  H = {H}\n"
        f"  R_big = {R_big}\n"
        f"  R_small = {R_small}\n"
        f"  refinement_level = {refinement_level}\n"
        f"  min_physical_scale = {min_physical_scale}\n"
        f"  max_elements = {max_elements}")


    # Create and generate mesh for Hall Thruster geometry
    mesh = HallThrusterMesh(
        R_big=R_big,
        R_small=R_small,
        H=H,
        refinement_level=refinement_level
    )
    mesh.generate()

except Exception as e:
    print("[ERROR] Mesh generation process failed:")
    traceback.print_exc()
    with open("run_mesher_error.log", "w") as error_file:
        error_file.write(traceback.format_exc())
    sys.exit(1)
