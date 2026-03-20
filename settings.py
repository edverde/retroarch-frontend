"""
Gestion de ajustes persistentes del frontend.

Guarda y carga configuracion como RetroAchievements, preferencias, etc.
en un archivo JSON local.
"""

import json
import os
from config import SETTINGS_FILE

DEFAULTS = {
    "cheevos_enable": False,
    "cheevos_username": "",
    "cheevos_password": "",
}


def load_settings():
    """Carga ajustes desde disco. Devuelve defaults si no existe."""
    if not os.path.isfile(SETTINGS_FILE):
        return dict(DEFAULTS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Rellenar claves que falten con defaults
        for key, val in DEFAULTS.items():
            data.setdefault(key, val)
        return data
    except Exception:
        return dict(DEFAULTS)


def save_settings(settings):
    """Guarda ajustes a disco."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
