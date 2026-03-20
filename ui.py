"""
Interfaz grafica del frontend con Pygame.

Dos pantallas:
  1. Seleccion de sistema (SNES, Mega Drive...)
  2. Lista de juegos con portada y descripcion
"""

import json
import ctypes
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    COLOR_BG, COLOR_TEXT, COLOR_SELECTED, COLOR_HEADER, COLOR_DIMMED,
    COLOR_PANEL_BG, COLOR_DESCRIPTION, COLOR_SEPARATOR,
    SYSTEMS, DESCRIPTIONS_FILE,
)
from controller import (
    Controller, ACTION_UP, ACTION_DOWN, ACTION_CONFIRM, ACTION_BACK,
)
from scanner import scan_all
from launcher import launch_game
from assets_manager import AssetsManager


# Pantallas
SCREEN_SYSTEMS = "systems"
SCREEN_GAMES = "games"

# Layout del panel de juegos
LIST_X = 40
LIST_W = 480
PANEL_X = 560
PANEL_W = 680
SEPARATOR_X = 540
BOXART_MAX_W = 280
BOXART_MAX_H = 350


class Frontend:
    """Aplicacion principal del frontend."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN
        )
        pygame.display.set_caption("RetroArch Frontend")
        self.clock = pygame.time.Clock()
        self.controller = Controller()

        # Mostrar pantalla de carga
        self._draw_loading("Cargando assets...")

        # Assets (fuentes y portadas)
        self.assets = AssetsManager()
        font_path = self.assets.get_font_path()

        # Fuentes: Press Start 2P para titulos/items, Segoe UI para descripciones
        if font_path:
            self.font_title = pygame.font.Font(font_path, 20)
            self.font_item = pygame.font.Font(font_path, 11)
            self.font_small = pygame.font.Font(font_path, 8)
        else:
            self.font_title = pygame.font.SysFont("segoeui", 48, bold=True)
            self.font_item = pygame.font.SysFont("segoeui", 32)
            self.font_small = pygame.font.SysFont("segoeui", 20)
        # Fuente legible para descripciones (soporta acentos y caracteres especiales)
        self.font_desc = pygame.font.SysFont("segoeui", 18)
        self.font_meta = pygame.font.SysFont("segoeui", 20, bold=True)

        # Escanear ROMs
        self._draw_loading("Escaneando ROMs...")
        self.games_by_system = scan_all()
        self.system_ids = list(self.games_by_system.keys())

        # Descargar portadas
        self._draw_loading("Descargando portadas...")
        self.assets.download_all_boxart(self.games_by_system)

        # Cargar descripciones
        self.descriptions = {}
        try:
            with open(DESCRIPTIONS_FILE, "r", encoding="utf-8") as f:
                self.descriptions = json.load(f)
        except Exception:
            pass

        # Cache de portadas cargadas como Surface
        self.boxart_cache = {}

        # Estado
        self.current_screen = SCREEN_SYSTEMS
        self.system_index = 0
        self.game_index = 0
        self.selected_system = None
        self.running = True

    def _draw_loading(self, text):
        """Muestra una pantalla de carga simple."""
        self.screen.fill(COLOR_BG)
        font = pygame.font.SysFont("segoeui", 28)
        surface = font.render(text, True, COLOR_DIMMED)
        rect = surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(surface, rect)
        pygame.display.flip()

    def run(self):
        """Bucle principal de la aplicacion."""
        while self.running:
            self._handle_events()
            self._draw()
            self.clock.tick(FPS)

        pygame.quit()

    def _handle_events(self):
        """Procesa eventos y traduce a acciones."""
        try:
            events = pygame.event.get()
        except SystemError:
            # Bug de pygame/SDL con hot-plug de mandos: evento corrupto en la cola
            return

        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return

            action = self.controller.handle_event(event)
            if action is None:
                continue

            if self.current_screen == SCREEN_SYSTEMS:
                self._handle_systems_action(action)
            elif self.current_screen == SCREEN_GAMES:
                self._handle_games_action(action)

    def _handle_systems_action(self, action):
        """Maneja acciones en la pantalla de seleccion de sistema."""
        if not self.system_ids:
            return

        if action == ACTION_UP:
            self.system_index = (self.system_index - 1) % len(self.system_ids)
        elif action == ACTION_DOWN:
            self.system_index = (self.system_index + 1) % len(self.system_ids)
        elif action == ACTION_CONFIRM:
            self.selected_system = self.system_ids[self.system_index]
            self.game_index = 0
            self.current_screen = SCREEN_GAMES
        elif action == ACTION_BACK:
            self.running = False

    def _handle_games_action(self, action):
        """Maneja acciones en la pantalla de lista de juegos."""
        games = self.games_by_system.get(self.selected_system, [])
        if not games:
            if action == ACTION_BACK:
                self.current_screen = SCREEN_SYSTEMS
            return

        if action == ACTION_UP:
            self.game_index = (self.game_index - 1) % len(games)
        elif action == ACTION_DOWN:
            self.game_index = (self.game_index + 1) % len(games)
        elif action == ACTION_CONFIRM:
            game = games[self.game_index]
            self._launch(game)
        elif action == ACTION_BACK:
            self.current_screen = SCREEN_SYSTEMS

    # --- Helpers ---

    def _launch(self, game):
        """Lanza un juego con transicion limpia (sin mostrar escritorio)."""
        # Pantalla negra mientras RetroArch carga
        self.screen.fill((0, 0, 0))
        pygame.display.flip()

        # Lanzar RetroArch (no bloqueante)
        proc = launch_game(self.selected_system, game["path"])
        if proc is None:
            return

        # Mantener pygame vivo con pantalla negra mientras RetroArch corre
        while proc.poll() is None:
            pygame.event.pump()
            pygame.time.wait(100)

        # Al volver: restaurar fullscreen
        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN
        )
        pygame.event.clear()

        # Forzar ventana al frente con API de Windows
        self._force_foreground()

        pygame.time.wait(200)
        pygame.event.clear()

    def _force_foreground(self):
        """Trae la ventana de pygame al frente en Windows."""
        try:
            hwnd = pygame.display.get_wm_info()["window"]
            user32 = ctypes.windll.user32
            # Simular Alt para desbloquear SetForegroundWindow
            user32.keybd_event(0x12, 0, 0, 0)  # Alt press
            user32.SetForegroundWindow(hwnd)
            user32.keybd_event(0x12, 0, 2, 0)  # Alt release
            # Asegurar que esta visible y maximizada
            SW_SHOWMAXIMIZED = 3
            user32.ShowWindow(hwnd, SW_SHOWMAXIMIZED)
        except Exception:
            pass

    def _load_boxart(self, system_id, game_name):
        """Carga y cachea la portada de un juego como Surface escalada."""
        key = (system_id, game_name)
        if key in self.boxart_cache:
            return self.boxart_cache[key]

        path = self.assets.get_boxart_path(system_id, game_name)
        if not path:
            self.boxart_cache[key] = None
            return None

        try:
            img = pygame.image.load(path).convert_alpha()
            # Escalar manteniendo proporcion
            w, h = img.get_size()
            scale = min(BOXART_MAX_W / w, BOXART_MAX_H / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = pygame.transform.smoothscale(img, (new_w, new_h))
            self.boxart_cache[key] = img
            return img
        except Exception:
            self.boxart_cache[key] = None
            return None

    def _wrap_text(self, text, font, max_width):
        """Divide texto en lineas que caben en max_width pixeles."""
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    # --- Dibujado ---

    def _draw(self):
        """Dibuja la pantalla actual."""
        self.screen.fill(COLOR_BG)

        if self.current_screen == SCREEN_SYSTEMS:
            self._draw_systems()
        elif self.current_screen == SCREEN_GAMES:
            self._draw_games()

        # Info del mando en la esquina inferior
        info = self.font_small.render(self.controller.get_info(), True, COLOR_DIMMED)
        self.screen.blit(info, (20, SCREEN_HEIGHT - 35))

        # Controles
        if self.current_screen == SCREEN_SYSTEMS:
            hint = "A/Enter: Seleccionar   B/Esc: Salir"
        else:
            hint = "A/Enter: Jugar   B/Esc: Volver"
        hint_surface = self.font_small.render(hint, True, COLOR_DIMMED)
        hint_rect = hint_surface.get_rect(bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 12))
        self.screen.blit(hint_surface, hint_rect)

        pygame.display.flip()

    def _draw_systems(self):
        """Dibuja la pantalla de seleccion de sistema."""
        title = self.font_title.render("Selecciona un sistema", True, COLOR_HEADER)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=60)
        self.screen.blit(title, title_rect)

        if not self.system_ids:
            msg = self.font_item.render("No se encontraron juegos", True, COLOR_DIMMED)
            msg_rect = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(msg, msg_rect)
            return

        start_y = 180
        for i, sys_id in enumerate(self.system_ids):
            system = SYSTEMS[sys_id]
            num_games = len(self.games_by_system[sys_id])
            is_selected = i == self.system_index

            color = COLOR_SELECTED if is_selected else COLOR_TEXT
            prefix = "> " if is_selected else "  "

            text = f"{prefix}{system['name']}"
            surface = self.font_item.render(text, True, color)

            y = start_y + i * 60
            x = SCREEN_WIDTH // 2 - 180
            self.screen.blit(surface, (x, y))

            # Contador de juegos debajo
            count_text = f"  {num_games} juegos"
            count_surface = self.font_small.render(count_text, True, COLOR_DIMMED)
            self.screen.blit(count_surface, (x, y + 28))

            # Barra de seleccion
            if is_selected:
                bar = pygame.Rect(x - 15, y + 3, 4, 40)
                pygame.draw.rect(self.screen, COLOR_SELECTED, bar)

    def _draw_games(self):
        """Dibuja la pantalla de juegos con panel de detalle."""
        system = SYSTEMS[self.selected_system]
        games = self.games_by_system.get(self.selected_system, [])

        # Titulo del sistema
        title = self.font_title.render(system["name"], True, COLOR_HEADER)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=20)
        self.screen.blit(title, title_rect)

        if not games:
            msg = self.font_item.render("No hay juegos", True, COLOR_DIMMED)
            msg_rect = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(msg, msg_rect)
            return

        # Linea separadora vertical
        pygame.draw.line(
            self.screen, COLOR_SEPARATOR,
            (SEPARATOR_X, 70), (SEPARATOR_X, SCREEN_HEIGHT - 50), 2
        )

        # --- Panel izquierdo: lista de juegos ---
        self._draw_game_list(games)

        # --- Panel derecho: detalle del juego seleccionado ---
        selected_game = games[self.game_index]
        self._draw_game_detail(selected_game)

    def _draw_game_list(self, games):
        """Dibuja la lista de juegos en el panel izquierdo."""
        max_visible = 10
        half = max_visible // 2
        if len(games) <= max_visible:
            start = 0
        elif self.game_index < half:
            start = 0
        elif self.game_index >= len(games) - half:
            start = len(games) - max_visible
        else:
            start = self.game_index - half
        end = min(start + max_visible, len(games))

        start_y = 80
        for draw_i, game_i in enumerate(range(start, end)):
            game = games[game_i]
            is_selected = game_i == self.game_index

            color = COLOR_SELECTED if is_selected else COLOR_TEXT
            prefix = "> " if is_selected else "  "

            # Truncar nombre si es muy largo
            name = game["name"]
            text = f"{prefix}{name}"
            surface = self.font_item.render(text, True, color)

            # Recortar si se sale del panel
            if surface.get_width() > LIST_W:
                surface = surface.subsurface((0, 0, LIST_W, surface.get_height()))

            y = start_y + draw_i * 50
            self.screen.blit(surface, (LIST_X, y))

            if is_selected:
                bar = pygame.Rect(LIST_X - 10, y + 2, 4, 30)
                pygame.draw.rect(self.screen, COLOR_SELECTED, bar)

        # Indicador de posicion
        pos_text = f"{self.game_index + 1} / {len(games)}"
        pos_surface = self.font_small.render(pos_text, True, COLOR_DIMMED)
        pos_rect = pos_surface.get_rect(centerx=LIST_X + LIST_W // 2, y=SCREEN_HEIGHT - 60)
        self.screen.blit(pos_surface, pos_rect)

    def _draw_game_detail(self, game):
        """Dibuja el panel de detalle: portada, metadatos y descripcion."""
        game_name = game["name"]
        y_cursor = 80

        # --- Portada ---
        boxart = self._load_boxart(self.selected_system, game_name)
        if boxart:
            img_x = PANEL_X + (PANEL_W - boxart.get_width()) // 2
            self.screen.blit(boxart, (img_x, y_cursor))
            y_cursor += boxart.get_height() + 15
        else:
            # Placeholder
            placeholder = pygame.Rect(
                PANEL_X + (PANEL_W - 200) // 2, y_cursor, 200, 150
            )
            pygame.draw.rect(self.screen, COLOR_PANEL_BG, placeholder)
            pygame.draw.rect(self.screen, COLOR_SEPARATOR, placeholder, 2)
            no_img = self.font_small.render("Sin caratula", True, COLOR_DIMMED)
            no_img_rect = no_img.get_rect(center=placeholder.center)
            self.screen.blit(no_img, no_img_rect)
            y_cursor += 165

        # --- Metadatos ---
        desc_data = self.descriptions.get(self.selected_system, {}).get(game_name, {})

        if desc_data:
            meta_parts = []
            if desc_data.get("genre"):
                meta_parts.append(desc_data["genre"])
            if desc_data.get("developer"):
                meta_parts.append(desc_data["developer"])
            if desc_data.get("year"):
                meta_parts.append(desc_data["year"])

            if meta_parts:
                meta_text = "  |  ".join(meta_parts)
                meta_surface = self.font_meta.render(meta_text, True, COLOR_SELECTED)
                meta_rect = meta_surface.get_rect(centerx=PANEL_X + PANEL_W // 2, y=y_cursor)
                self.screen.blit(meta_surface, meta_rect)
                y_cursor += 35

            # --- Descripcion ---
            description = desc_data.get("description", "")
            if description:
                lines = self._wrap_text(description, self.font_desc, PANEL_W - 40)
                for line in lines:
                    line_surface = self.font_desc.render(line, True, COLOR_DESCRIPTION)
                    self.screen.blit(line_surface, (PANEL_X + 20, y_cursor))
                    y_cursor += 24
        else:
            no_desc = self.font_desc.render("Sin descripcion disponible", True, COLOR_DIMMED)
            no_desc_rect = no_desc.get_rect(centerx=PANEL_X + PANEL_W // 2, y=y_cursor)
            self.screen.blit(no_desc, no_desc_rect)
