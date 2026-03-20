"""
Lanzador de RetroArch.

Construye y ejecuta el comando para lanzar RetroArch
con el core y ROM seleccionados.
"""

import os
import subprocess
from config import RETROARCH_EXE, CORES_DIR, SYSTEMS, ASSETS_DIR
from settings import load_settings

# Config override para hotkeys
OVERRIDE_CFG = os.path.join(ASSETS_DIR, "retroarch_override.cfg")
CHEEVOS_CFG = os.path.join(ASSETS_DIR, "cheevos_override.cfg")


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

    # Generar override de cheevos si esta activado
    _write_cheevos_cfg()

    # Aplicar overrides (hotkeys + cheevos si existe)
    configs = []
    if os.path.isfile(OVERRIDE_CFG):
        configs.append(OVERRIDE_CFG)
    if os.path.isfile(CHEEVOS_CFG):
        configs.append(CHEEVOS_CFG)
    if configs:
        cmd.append(f"--appendconfig={'|'.join(configs)}")

    try:
        proc = subprocess.Popen(cmd)
        return proc
    except Exception as e:
        print(f"ERROR al lanzar RetroArch: {e}")
        return None


def _write_cheevos_cfg():
    """Genera o elimina el override de cheevos segun los ajustes."""
    settings = load_settings()
    if settings.get("cheevos_enable") and settings.get("cheevos_username"):
        lines = [
            'cheevos_enable = "true"',
            f'cheevos_username = "{settings["cheevos_username"]}"',
            f'cheevos_password = "{settings["cheevos_password"]}"',
        ]
        with open(CHEEVOS_CFG, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    else:
        # Si esta desactivado, eliminar el archivo
        if os.path.isfile(CHEEVOS_CFG):
            os.remove(CHEEVOS_CFG)
