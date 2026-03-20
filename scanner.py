"""
Escaner de ROMs.

Recorre las carpetas de ROMs definidas en config y devuelve
la lista de juegos disponibles para cada sistema.
"""

import os
from config import ROMS_DIR, SYSTEMS


def scan_system(system_id):
    """
    Escanea la carpeta de ROMs de un sistema y devuelve una lista de juegos.
    Cada juego es un dict con 'name' (nombre limpio) y 'path' (ruta completa).
    """
    system = SYSTEMS[system_id]
    folder = os.path.join(ROMS_DIR, system["roms_folder"])

    if not os.path.isdir(folder):
        return []

    games = []
    for filename in sorted(os.listdir(folder)):
        ext = os.path.splitext(filename)[1].lower()
        if ext in system["extensions"]:
            clean_name = os.path.splitext(filename)[0]
            games.append({
                "name": clean_name,
                "path": os.path.join(folder, filename),
            })

    return games


def scan_all():
    """
    Escanea todos los sistemas y devuelve un dict {system_id: [juegos]}.
    Solo incluye sistemas que tengan al menos un juego.
    """
    result = {}
    for system_id in SYSTEMS:
        games = scan_system(system_id)
        if games:
            result[system_id] = games
    return result
