"""
Gestor de assets externos.

Descarga y cachea fuentes (Google Fonts) y portadas (LibRetro Thumbnails).
Usa solo urllib (stdlib), sin dependencias extra.
"""

import os
import urllib.request
import urllib.parse

from config import (
    ASSETS_DIR, FONT_URL, FONT_FILENAME, FONT_BOLD_URL, FONT_BOLD_FILENAME,
    THUMBNAIL_BASE_URL, THUMBNAIL_REPOS,
)


class AssetsManager:
    """Descarga y cachea fuentes y portadas de juegos."""

    def __init__(self):
        self.fonts_dir = os.path.join(ASSETS_DIR, "fonts")
        self.boxart_dir = os.path.join(ASSETS_DIR, "boxart")
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Crea la estructura de carpetas de assets si no existe."""
        os.makedirs(self.fonts_dir, exist_ok=True)
        for system_id in THUMBNAIL_REPOS:
            os.makedirs(os.path.join(self.boxart_dir, system_id), exist_ok=True)

    def download_font(self):
        """Descarga la fuente Press Start 2P si no esta cacheada."""
        path = os.path.join(self.fonts_dir, FONT_FILENAME)
        if os.path.isfile(path):
            return path
        try:
            urllib.request.urlretrieve(FONT_URL, path)
            return path
        except Exception as e:
            print(f"AVISO: No se pudo descargar la fuente: {e}")
            return None

    def get_font_path(self):
        """Devuelve la ruta a la fuente cacheada, o None."""
        path = os.path.join(self.fonts_dir, FONT_FILENAME)
        if os.path.isfile(path):
            return path
        return self.download_font()

    def get_bold_font_path(self):
        """Devuelve la ruta a la fuente bold, o None."""
        path = os.path.join(self.fonts_dir, FONT_BOLD_FILENAME)
        if os.path.isfile(path):
            return path
        try:
            urllib.request.urlretrieve(FONT_BOLD_URL, path)
            return path
        except Exception:
            return None

    def _boxart_url(self, system_id, game_name):
        """Construye la URL de la portada en LibRetro Thumbnails."""
        repo = THUMBNAIL_REPOS.get(system_id)
        if not repo:
            return None
        # Caracteres que LibRetro reemplaza por _
        clean = game_name
        for ch in '&*/:`<>?\\|':
            clean = clean.replace(ch, "_")
        encoded = urllib.parse.quote(clean, safe="")
        return f"{THUMBNAIL_BASE_URL}/{repo}/master/Named_Boxarts/{encoded}.png"

    def download_boxart(self, system_id, game_name):
        """Descarga la portada de un juego si no esta cacheada."""
        dest = os.path.join(self.boxart_dir, system_id, f"{game_name}.png")
        if os.path.isfile(dest):
            return dest

        url = self._boxart_url(system_id, game_name)
        if not url:
            return None
        try:
            urllib.request.urlretrieve(url, dest)
            return dest
        except Exception as e:
            print(f"AVISO: No se pudo descargar portada de '{game_name}': {e}")
            return None

    def get_boxart_path(self, system_id, game_name):
        """Devuelve la ruta a la portada cacheada, o None."""
        path = os.path.join(self.boxart_dir, system_id, f"{game_name}.png")
        if os.path.isfile(path):
            return path
        return None

    def download_all_boxart(self, games_by_system):
        """Descarga todas las portadas de los juegos escaneados."""
        for system_id, games in games_by_system.items():
            for game in games:
                self.download_boxart(system_id, game["name"])
