"""
Configuracion central del frontend.

Aqui se definen las rutas de RetroArch y la lista de sistemas soportados.
Para anadir un nuevo sistema, basta con anadir una entrada al diccionario SYSTEMS.
"""

import os

# Rutas principales
RETROARCH_DIR = r"C:\RetroArch-Win64"
RETROARCH_EXE = os.path.join(RETROARCH_DIR, "retroarch.exe")
ROMS_DIR = os.path.join(RETROARCH_DIR, "roms")
CORES_DIR = os.path.join(RETROARCH_DIR, "cores")

# Cada sistema tiene: nombre para mostrar, carpeta de ROMs, core, y extensiones validas
SYSTEMS = {
    "snes": {
        "name": "Super Nintendo",
        "roms_folder": "snes",
        "core": "snes9x_libretro.dll",
        "extensions": [".sfc", ".smc"],
    },
    "megadrive": {
        "name": "Mega Drive",
        "roms_folder": "megadrive",
        "core": "picodrive_libretro.dll",
        "extensions": [".md", ".bin"],
    },
}

# Pantalla
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Colores (RGB)
COLOR_BG = (15, 15, 25)
COLOR_TEXT = (255, 255, 255)
COLOR_SELECTED = (80, 140, 255)
COLOR_HEADER = (200, 200, 220)
COLOR_DIMMED = (120, 120, 140)
COLOR_PANEL_BG = (25, 25, 40)
COLOR_DESCRIPTION = (180, 180, 200)
COLOR_SEPARATOR = (50, 50, 70)

# Assets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Fuente retro (Google Fonts - Press Start 2P)
FONT_URL = "https://fonts.gstatic.com/s/pressstart2p/v16/e3t4euO8T-267oIAQAu6jDQyK0nS.ttf"
FONT_FILENAME = "PressStart2P-Regular.ttf"

# LibRetro Thumbnails (portadas)
THUMBNAIL_BASE_URL = "https://raw.githubusercontent.com/libretro-thumbnails"
THUMBNAIL_REPOS = {
    "snes": "Nintendo_-_Super_Nintendo_Entertainment_System",
    "megadrive": "Sega_-_Mega_Drive_-_Genesis",
}

# Descripciones de juegos
DESCRIPTIONS_FILE = os.path.join(BASE_DIR, "game_descriptions.json")
