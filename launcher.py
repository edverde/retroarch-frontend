"""
Lanzador de RetroArch.

Construye y ejecuta el comando para lanzar RetroArch
con el core y ROM seleccionados.
"""

import os
import subprocess
from config import RETROARCH_EXE, CORES_DIR, SYSTEMS, ASSETS_DIR

# Config override para hotkeys
OVERRIDE_CFG = os.path.join(ASSETS_DIR, "retroarch_override.cfg")


def launch_game(system_id, rom_path):
    """
    Lanza RetroArch como proceso no bloqueante (Popen).
    Devuelve el proceso para que la UI pueda esperar mientras mantiene
    la pantalla negra activa.
    Devuelve None si hay error.
    """
    system = SYSTEMS[system_id]
    core_path = os.path.join(CORES_DIR, system["core"])

    if not os.path.isfile(RETROARCH_EXE):
        print(f"ERROR: No se encuentra RetroArch en {RETROARCH_EXE}")
        return None

    if not os.path.isfile(core_path):
        print(f"ERROR: No se encuentra el core {core_path}")
        return None

    if not os.path.isfile(rom_path):
        print(f"ERROR: No se encuentra la ROM {rom_path}")
        return None

    cmd = [RETROARCH_EXE, "-L", core_path, "--fullscreen", rom_path]

    # Aplicar override de hotkeys si existe (formato --appendconfig=path)
    if os.path.isfile(OVERRIDE_CFG):
        cmd.append(f"--appendconfig={OVERRIDE_CFG}")

    try:
        proc = subprocess.Popen(cmd)
        return proc
    except Exception as e:
        print(f"ERROR al lanzar RetroArch: {e}")
        return None
