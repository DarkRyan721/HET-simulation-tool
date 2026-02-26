import io
import os
import sys
import json
import traceback
import numpy as np

# Add parent directory to path for imports from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from project_paths import model
from models.simulation_state import SimulationState

print("[DEBUG] Launching run_mesher.py...")

# Load simulation state from JSON file
state = SimulationState.load_from_json(model("simulation_state.json"))

# Main parameters with defaults if not specified in state
N = getattr(state, "N_particles", None) or 1000
frames = getattr(state, "frames", None) or 500

alpha = getattr(state, "alpha", None) or 0.9
sigma_ion = getattr(state, "sigma_ion", None) or 1e-11
dt = getattr(state, "dt", None) or 4e-8

GPU_ACTIVE = getattr(state, "GPU_ACTIVE", None) or False
# Import appropriate PIC implementation depending on GPU usage
if GPU_ACTIVE:
    from particle_in_cell import PIC
else:
    from particle_in_cell_cpu import PIC

# Gas type and associated properties
gas = getattr(state, "gas", "Xenon")

if gas == "Xenon":
    q_m = 7.35e5
    V_neutro = 200
elif gas == "Krypton":
    q_m = 11.5e5
    V_neutro = 220
elif gas == "Argon":
    q_m = 24.2e5
    V_neutro = 430
elif gas == "Helium":
    q_m = 41.9e5
    V_neutro = 1100
else:
    q_m = 7.35e5
    V_neutro = 200

# Debug output of parameters
print(f"[DEBUG] Simulation parameters:\n"
      f"  N = {N}\n"
      f"  frames = {frames}\n"
      f"  alpha = {alpha}\n"
      f"  sigma_ion = {sigma_ion}\n"
      f"  dt = {dt}\n"
      f"  GPU_ACTIVE = {GPU_ACTIVE}\n"
      f"  gas = {gas}")

print(f"[DEBUG] Physical properties:\n"
      f"  Charge-to-mass ratio (q/m) = {q_m}\n"
      f"  Neutral velocity (V_neutro) = {V_neutro}")

try:
    # Geometrical parameters (ensure keys match your JSON structure)
    Rin = state.R_small
    Rex = state.R_big
    L = state.H

    # Initialize Particle-in-Cell simulation
    pic = PIC(
        Rin=Rin,
        Rex=Rex,
        N=N,
        L=L,
        dt=dt,
        q_m=q_m,
        alpha=alpha,
        sigma_ion=sigma_ion
    )

    pic.initizalize_to_simulation(v_neutro=V_neutro, timesteps=frames)
    pic.render()

    specific_impulse = pic.specific_impulse
    state.impulso_especifico = specific_impulse * 0.2
    state.save_to_json(model("simulation_state.json"))
    with open(model("simulation_state.json"), "r") as fp:
        contenido = json.load(fp)
    print("[DEBUG] Contenido recién guardado:", contenido.get("impulso_especifico"))

except Exception as e:
    print("[ERROR] Mesh process failed:")
    traceback.print_exc()
    with open("run_mesher_error.log", "w") as error_file:
        error_file.write(traceback.format_exc())
    sys.exit(1)
