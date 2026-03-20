"""
Interfaz grafica del frontend con Pygame.

Dos pantallas:
  1. Seleccion de sistema (SNES, Mega Drive...)
  2. Lista de juegos con portada y descripcion
"""

import os
import json
import ctypes
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    COLOR_BG, COLOR_TEXT, COLOR_SELECTED, COLOR_HEADER, COLOR_DIMMED,
    COLOR_PANEL_BG, COLOR_DESCRIPTION, COLOR_SEPARATOR, COLOR_CHEEVOS,
    SYSTEMS, DESCRIPTIONS_FILE, CONSOLE_IMAGES, BACKGROUNDS,
)
from controller import (
    Controller, ACTION_UP, ACTION_DOWN, ACTION_CONFIRM, ACTION_BACK,
    ACTION_START, ACTION_SELECT, ACTION_LEFT, ACTION_RIGHT,
)
from scanner import scan_all
from launcher import launch_game
from assets_manager import AssetsManager
from settings import load_settings, save_settings


# Pantallas
SCREEN_MAIN = "main"
SCREEN_SYSTEMS = "systems"
SCREEN_GAMES = "games"
SCREEN_OPTIONS = "options"
SCREEN_RA_LOGIN = "ra_login"

# Layout de la pantalla de sistemas (con imagen de consola)
CONSOLE_IMG_MAX_W = 320
CONSOLE_IMG_MAX_H = 200

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

        # Fuentes Orbitron para titulos/items
        bold_path = self.assets.get_bold_font_path()
        if font_path:
            self.font_logo = pygame.font.Font(bold_path or font_path, 38)
            self.font_title = pygame.font.Font(bold_path or font_path, 24)
            self.font_item = pygame.font.Font(font_path, 18)
            self.font_small = pygame.font.Font(font_path, 13)
        else:
            self.font_logo = pygame.font.SysFont("segoeui", 56, bold=True)
            self.font_title = pygame.font.SysFont("segoeui", 48, bold=True)
            self.font_item = pygame.font.SysFont("segoeui", 28)
            self.font_small = pygame.font.SysFont("segoeui", 18)
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

        # Fondos de pantalla
        self.bg_cache = {}
        self._load_backgrounds()

        # Cache de imagenes de consolas
        self.console_cache = {}
        self._load_console_images()

        # Estado
        self.current_screen = SCREEN_MAIN
        self.main_index = 0
        self.main_items = ["Sistemas", "Opciones"]
        self.system_index = 0
        self.game_index = 0
        self.selected_system = None
        self.running = True
        self.restart_requested = False

        # Estado del menu de opciones
        self.options_index = 0
        self.options_items = [
            "RetroAchievements",
            "Reiniciar frontend",
            "Salir del frontend",
        ]

        # Estado de la pantalla RetroAchievements
        self.ra_index = 0
        self.ra_editing = False  # True cuando se esta escribiendo en un campo
        self.settings = load_settings()

        # Teclado en pantalla
        self.osk_rows = [
            list("1234567890"),
            list("QWERTYUIOP"),
            list("ASDFGHJKL_"),
            list("ZXCVBNM.-@"),
            ["ESPACIO", "BORRAR", "ACEPTAR"],
        ]
        self.osk_row = 0
        self.osk_col = 0

        # Notificacion temporal
        self.notification_text = ""
        self.notification_until = 0  # timestamp en ms

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

            # Entrada de texto fisico para RetroAchievements (teclado real)
            if self.current_screen == SCREEN_RA_LOGIN and self.ra_editing:
                if event.type == pygame.TEXTINPUT:
                    self._ra_text_input(event.text)
                    continue
                if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                    self._ra_text_backspace()
                    continue
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.ra_editing = False
                    continue

            action = self.controller.handle_event(event)
            if action is None:
                continue

            if self.current_screen == SCREEN_MAIN:
                self._handle_main_action(action)
            elif self.current_screen == SCREEN_SYSTEMS:
                self._handle_systems_action(action)
            elif self.current_screen == SCREEN_GAMES:
                self._handle_games_action(action)
            elif self.current_screen == SCREEN_OPTIONS:
                self._handle_options_action(action)
            elif self.current_screen == SCREEN_RA_LOGIN:
                self._handle_ra_action(action)

    def _handle_main_action(self, action):
        """Maneja acciones en el menu principal."""
        if action == ACTION_UP:
            self.main_index = (self.main_index - 1) % len(self.main_items)
        elif action == ACTION_DOWN:
            self.main_index = (self.main_index + 1) % len(self.main_items)
        elif action == ACTION_CONFIRM:
            if self.main_items[self.main_index] == "Sistemas":
                self.system_index = 0
                self.current_screen = SCREEN_SYSTEMS
            elif self.main_items[self.main_index] == "Opciones":
                self.options_index = 0
                self.current_screen = SCREEN_OPTIONS
        elif action == ACTION_BACK:
            self.running = False

    def _handle_systems_action(self, action):
        """Maneja acciones en la pantalla de seleccion de sistema."""
        if not self.system_ids:
            if action == ACTION_BACK:
                self.current_screen = SCREEN_MAIN
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
            self.current_screen = SCREEN_MAIN

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
        elif action == ACTION_SELECT:
            self._toggle_cheevos()

    def _handle_options_action(self, action):

        """Maneja acciones en el menu de opciones."""
        if action == ACTION_UP:
            self.options_index = (self.options_index - 1) % len(self.options_items)
        elif action == ACTION_DOWN:
            self.options_index = (self.options_index + 1) % len(self.options_items)
        elif action == ACTION_CONFIRM:
            selected = self.options_items[self.options_index]
            if selected == "RetroAchievements":
                self.ra_index = 0
                self.ra_editing = False
                self.settings = load_settings()
                self.current_screen = SCREEN_RA_LOGIN
            elif selected == "Reiniciar frontend":
                self.restart_requested = True
                self.running = False
            elif selected == "Salir del frontend":
                self.running = False
        elif action == ACTION_BACK:
            self.current_screen = SCREEN_MAIN

    def _handle_ra_action(self, action):
        """Maneja acciones en la pantalla de RetroAchievements."""
        # ra_index: 0=activar, 1=usuario, 2=contraseña, 3=guardar
        if self.ra_editing:
            self._handle_osk_action(action)
            return

        if action == ACTION_UP:
            self.ra_index = (self.ra_index - 1) % 4
        elif action == ACTION_DOWN:
            self.ra_index = (self.ra_index + 1) % 4
        elif action == ACTION_CONFIRM:
            if self.ra_index == 0:
                # Toggle activar/desactivar
                self.settings["cheevos_enable"] = not self.settings["cheevos_enable"]
            elif self.ra_index in (1, 2):
                # Entrar en modo edicion con teclado en pantalla
                self.ra_editing = True
                self.osk_row = 0
                self.osk_col = 0
                pygame.key.start_text_input()
            elif self.ra_index == 3:
                # Guardar
                save_settings(self.settings)
                self.current_screen = SCREEN_OPTIONS
        elif action in (ACTION_LEFT, ACTION_RIGHT) and self.ra_index == 0:
            self.settings["cheevos_enable"] = not self.settings["cheevos_enable"]
        elif action == ACTION_BACK:
            self.current_screen = SCREEN_OPTIONS

    def _handle_osk_action(self, action):
        """Maneja la navegacion del teclado en pantalla."""
        row = self.osk_rows[self.osk_row]

        if action == ACTION_UP:
            self.osk_row = (self.osk_row - 1) % len(self.osk_rows)
            # Ajustar columna si la fila nueva es mas corta
            new_row = self.osk_rows[self.osk_row]
            self.osk_col = min(self.osk_col, len(new_row) - 1)
        elif action == ACTION_DOWN:
            self.osk_row = (self.osk_row + 1) % len(self.osk_rows)
            new_row = self.osk_rows[self.osk_row]
            self.osk_col = min(self.osk_col, len(new_row) - 1)
        elif action == ACTION_LEFT:
            self.osk_col = (self.osk_col - 1) % len(row)
        elif action == ACTION_RIGHT:
            self.osk_col = (self.osk_col + 1) % len(row)
        elif action == ACTION_CONFIRM:
            key = row[self.osk_col]
            if key == "ACEPTAR":
                self.ra_editing = False
            elif key == "BORRAR":
                self._ra_text_backspace()
            elif key == "ESPACIO":
                self._ra_text_input(" ")
            else:
                self._ra_text_input(key.lower())
        elif action == ACTION_BACK:
            self.ra_editing = False

    def _ra_text_input(self, text):
        """Añade texto al campo activo de RetroAchievements."""
        key = "cheevos_username" if self.ra_index == 1 else "cheevos_password"
        self.settings[key] += text

    def _ra_text_backspace(self):
        """Borra ultimo caracter del campo activo de RetroAchievements."""
        key = "cheevos_username" if self.ra_index == 1 else "cheevos_password"
        self.settings[key] = self.settings[key][:-1]

    def _load_backgrounds(self):
        """Carga y escala los fondos de pantalla."""
        for key, path in BACKGROUNDS.items():
            if not os.path.isfile(path):
                continue
            try:
                img = pygame.image.load(path).convert()
                img = pygame.transform.smoothscale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                # Oscurecer para que el texto sea legible
                dark = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                dark.fill((0, 0, 0, 160))
                img.blit(dark, (0, 0))
                self.bg_cache[key] = img
            except Exception:
                pass

    def _draw_bg(self, key):
        """Dibuja un fondo de pantalla. Si no existe, usa color solido."""
        bg = self.bg_cache.get(key)
        if bg:
            self.screen.blit(bg, (0, 0))
        else:
            self.screen.fill(COLOR_BG)

    def _toggle_cheevos(self):
        """Activa/desactiva RetroAchievements y muestra notificacion."""
        self.settings["cheevos_enable"] = not self.settings["cheevos_enable"]
        save_settings(self.settings)
        if self.settings["cheevos_enable"]:
            self.notification_text = "RetroAchievements ACTIVADOS"
        else:
            self.notification_text = "RetroAchievements DESACTIVADOS"
        self.notification_until = pygame.time.get_ticks() + 2000

    def _load_console_images(self):
        """Carga y escala las imagenes de consolas."""
        for sys_id, path in CONSOLE_IMAGES.items():
            if not os.path.isfile(path):
                continue
            try:
                img = pygame.image.load(path).convert_alpha()
                w, h = img.get_size()
                scale = min(CONSOLE_IMG_MAX_W / w, CONSOLE_IMG_MAX_H / h)
                img = pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))
                self.console_cache[sys_id] = img
            except Exception:
                pass

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

    def _draw_panel(self, x, y, w, h, alpha=140):
        """Dibuja un panel oscuro semitransparente para legibilidad."""
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((10, 10, 20, alpha))
        self.screen.blit(panel, (x, y))

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
        if self.current_screen == SCREEN_MAIN:
            self._draw_bg("main")
            self._draw_main()
        elif self.current_screen == SCREEN_SYSTEMS:
            # Fondo dinamico segun sistema seleccionado
            if self.system_ids:
                self._draw_bg(self.system_ids[self.system_index])
            else:
                self._draw_bg("main")
            self._draw_systems()
        elif self.current_screen == SCREEN_GAMES:
            self._draw_bg(self.selected_system)
            self._draw_games()
        elif self.current_screen == SCREEN_OPTIONS:
            self._draw_bg("options")
            self._draw_options()
        elif self.current_screen == SCREEN_RA_LOGIN:
            self._draw_bg("options")
            self._draw_ra_login()

        # Info del mando en la esquina inferior
        info = self.font_small.render(self.controller.get_info(), True, COLOR_DIMMED)
        self.screen.blit(info, (20, SCREEN_HEIGHT - 35))

        # Controles
        if self.current_screen == SCREEN_MAIN:
            hint = "A/Enter: Seleccionar   B/Esc: Salir"
        elif self.current_screen == SCREEN_SYSTEMS:
            hint = "A/Enter: Seleccionar   B/Esc: Volver"
        elif self.current_screen == SCREEN_GAMES:
            hint = "A/Enter: Jugar   Select/RShift: Logros   B/Esc: Volver"
        elif self.current_screen == SCREEN_RA_LOGIN:
            hint = "A/Enter: Editar   B/Esc: Volver"
        else:
            hint = "A/Enter: Seleccionar   B/Esc: Volver"
        hint_surface = self.font_small.render(hint, True, COLOR_DIMMED)
        hint_rect = hint_surface.get_rect(bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 12))
        self.screen.blit(hint_surface, hint_rect)

        # Notificacion temporal
        if self.notification_text and pygame.time.get_ticks() < self.notification_until:
            notif_color = COLOR_CHEEVOS if self.settings.get("cheevos_enable") else (220, 100, 100)
            notif_surface = self.font_item.render(self.notification_text, True, notif_color)
            notif_rect = notif_surface.get_rect(centerx=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT - 80)
            # Fondo para legibilidad
            bg_rect = notif_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, COLOR_BG, bg_rect)
            pygame.draw.rect(self.screen, notif_color, bg_rect, 1)
            self.screen.blit(notif_surface, notif_rect)

        pygame.display.flip()

    def _draw_main(self):
        """Dibuja el menu principal con titulo retro."""
        # Panel central para el contenido
        panel_w, panel_h = 600, 350
        self._draw_panel(
            (SCREEN_WIDTH - panel_w) // 2, 50,
            panel_w, panel_h
        )

        # Titulo con efecto de sombra
        title_text = "The House of The eD"
        # Sombra
        shadow = self.font_logo.render(title_text, True, (30, 30, 60))
        shadow_rect = shadow.get_rect(centerx=SCREEN_WIDTH // 2 + 3, y=83)
        self.screen.blit(shadow, shadow_rect)
        # Titulo principal
        title = self.font_logo.render(title_text, True, COLOR_SELECTED)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=80)
        self.screen.blit(title, title_rect)

        # Linea decorativa bajo el titulo
        line_y = title_rect.bottom + 20
        line_w = 400
        pygame.draw.line(
            self.screen, COLOR_SEPARATOR,
            (SCREEN_WIDTH // 2 - line_w // 2, line_y),
            (SCREEN_WIDTH // 2 + line_w // 2, line_y), 2
        )

        # Opciones del menu principal
        start_y = 320
        for i, item in enumerate(self.main_items):
            is_selected = i == self.main_index
            color = COLOR_SELECTED if is_selected else COLOR_TEXT
            prefix = "> " if is_selected else "  "

            surface = self.font_item.render(f"{prefix}{item}", True, color)
            rect = surface.get_rect(centerx=SCREEN_WIDTH // 2, y=start_y + i * 60)
            self.screen.blit(surface, rect)

            if is_selected:
                bar = pygame.Rect(rect.x - 15, rect.y + 3, 4, 30)
                pygame.draw.rect(self.screen, COLOR_SELECTED, bar)

    def _draw_systems(self):
        """Dibuja la pantalla de seleccion de sistema con imagenes de consolas."""
        # Panel izquierdo
        self._draw_panel(20, 15, SEPARATOR_X - 40, SCREEN_HEIGHT - 70)
        # Panel derecho
        self._draw_panel(SEPARATOR_X + 10, 15, SCREEN_WIDTH - SEPARATOR_X - 30, SCREEN_HEIGHT - 70)

        title = self.font_title.render("Selecciona un sistema", True, COLOR_HEADER)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=30)
        self.screen.blit(title, title_rect)

        if not self.system_ids:
            msg = self.font_item.render("No se encontraron juegos", True, COLOR_DIMMED)
            msg_rect = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(msg, msg_rect)
            return

        # Separador vertical
        pygame.draw.line(
            self.screen, COLOR_SEPARATOR,
            (SEPARATOR_X, 70), (SEPARATOR_X, SCREEN_HEIGHT - 50), 2
        )

        # Panel izquierdo: lista de sistemas
        start_y = 120
        for i, sys_id in enumerate(self.system_ids):
            system = SYSTEMS[sys_id]
            num_games = len(self.games_by_system[sys_id])
            is_selected = i == self.system_index

            color = COLOR_SELECTED if is_selected else COLOR_TEXT
            prefix = "> " if is_selected else "  "

            text = f"{prefix}{system['name']}"
            surface = self.font_item.render(text, True, color)

            y = start_y + i * 70
            x = 80
            self.screen.blit(surface, (x, y))

            # Contador de juegos debajo
            count_text = f"  {num_games} juegos"
            count_surface = self.font_small.render(count_text, True, COLOR_DIMMED)
            self.screen.blit(count_surface, (x, y + 28))

            # Barra de seleccion
            if is_selected:
                bar = pygame.Rect(x - 15, y + 3, 4, 40)
                pygame.draw.rect(self.screen, COLOR_SELECTED, bar)

        # Panel derecho: imagen de la consola seleccionada
        selected_id = self.system_ids[self.system_index]
        console_img = self.console_cache.get(selected_id)
        if console_img:
            img_x = PANEL_X + (PANEL_W - console_img.get_width()) // 2
            img_y = 120 + (300 - console_img.get_height()) // 2
            self.screen.blit(console_img, (img_x, img_y))

        # Nombre del sistema debajo de la imagen
        sys_name = SYSTEMS[selected_id]["name"]
        name_surface = self.font_title.render(sys_name, True, COLOR_HEADER)
        name_rect = name_surface.get_rect(centerx=PANEL_X + PANEL_W // 2, y=450)
        self.screen.blit(name_surface, name_rect)

    def _draw_games(self):
        """Dibuja la pantalla de juegos con panel de detalle."""
        system = SYSTEMS[self.selected_system]
        games = self.games_by_system.get(self.selected_system, [])

        # Paneles
        self._draw_panel(20, 10, SEPARATOR_X - 40, SCREEN_HEIGHT - 60)
        self._draw_panel(SEPARATOR_X + 10, 10, SCREEN_WIDTH - SEPARATOR_X - 30, SCREEN_HEIGHT - 60)

        # Titulo del sistema (dorado si cheevos activos)
        title_color = COLOR_CHEEVOS if self.settings.get("cheevos_enable") else COLOR_HEADER
        title = self.font_title.render(system["name"], True, title_color)
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

    def _draw_options(self):
        """Dibuja el menu de opciones."""
        self._draw_panel(SCREEN_WIDTH // 2 - 300, 40, 600, 300)
        title = self.font_title.render("Opciones", True, COLOR_HEADER)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=60)
        self.screen.blit(title, title_rect)

        start_y = 200
        for i, item in enumerate(self.options_items):
            is_selected = i == self.options_index
            color = COLOR_SELECTED if is_selected else COLOR_TEXT
            prefix = "> " if is_selected else "  "

            surface = self.font_item.render(f"{prefix}{item}", True, color)
            y = start_y + i * 60
            x = SCREEN_WIDTH // 2 - 180
            self.screen.blit(surface, (x, y))

            if is_selected:
                bar = pygame.Rect(x - 15, y + 3, 4, 40)
                pygame.draw.rect(self.screen, COLOR_SELECTED, bar)

    def _draw_ra_login(self):
        """Dibuja la pantalla de configuracion de RetroAchievements."""
        self._draw_panel(SCREEN_WIDTH // 2 - 380, 40, 760, 420)
        title = self.font_title.render("RetroAchievements", True, COLOR_HEADER)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=60)
        self.screen.blit(title, title_rect)

        x = SCREEN_WIDTH // 2 - 250
        start_y = 180
        fields = [
            ("Activar", "Si" if self.settings["cheevos_enable"] else "No"),
            ("Usuario", self.settings["cheevos_username"]),
            ("Password", "*" * len(self.settings["cheevos_password"])),
            ("", "[ Guardar ]"),
        ]

        for i, (label, value) in enumerate(fields):
            is_selected = i == self.ra_index
            y = start_y + i * 70
            color = COLOR_SELECTED if is_selected else COLOR_TEXT

            if i == 3:
                # Boton Guardar centrado
                surface = self.font_item.render(value, True, color)
                rect = surface.get_rect(centerx=SCREEN_WIDTH // 2, y=y)
                self.screen.blit(surface, rect)
                if is_selected:
                    bar = pygame.Rect(rect.x - 15, y + 3, 4, 30)
                    pygame.draw.rect(self.screen, COLOR_SELECTED, bar)
            else:
                # Label
                label_surface = self.font_item.render(f"{label}:", True, COLOR_DIMMED)
                self.screen.blit(label_surface, (x, y))

                # Campo de valor
                if i == 0:
                    # Toggle
                    val_color = (100, 220, 100) if self.settings["cheevos_enable"] else (220, 100, 100)
                    val_surface = self.font_item.render(value, True, val_color)
                else:
                    display = value if value else "..."
                    # Cursor parpadeante en modo edicion
                    if is_selected and self.ra_editing:
                        ticks = pygame.time.get_ticks()
                        cursor = "|" if (ticks // 500) % 2 == 0 else " "
                        display = value + cursor
                    val_surface = self.font_item.render(display, True, color)

                self.screen.blit(val_surface, (x + 280, y))

                # Barra de seleccion
                if is_selected:
                    bar = pygame.Rect(x - 15, y + 3, 4, 30)
                    pygame.draw.rect(self.screen, COLOR_SELECTED, bar)

        # Teclado en pantalla cuando se esta editando
        if self.ra_editing:
            self._draw_osk()

    def _draw_osk(self):
        """Dibuja el teclado en pantalla."""
        # Fondo semitransparente
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Texto que se esta editando arriba del teclado
        key = "cheevos_username" if self.ra_index == 1 else "cheevos_password"
        field_label = "Usuario" if self.ra_index == 1 else "Password"
        current_text = self.settings[key]
        if self.ra_index == 2:
            display_text = "*" * len(current_text)
        else:
            display_text = current_text
        ticks = pygame.time.get_ticks()
        cursor = "|" if (ticks // 500) % 2 == 0 else " "
        display_text += cursor

        label_surface = self.font_item.render(f"{field_label}:", True, COLOR_DIMMED)
        text_surface = self.font_item.render(display_text, True, COLOR_TEXT)
        self.screen.blit(label_surface, (SCREEN_WIDTH // 2 - 300, 200))
        self.screen.blit(text_surface, (SCREEN_WIDTH // 2 - 100, 200))

        # Dibujar filas del teclado
        key_w = 50
        key_h = 45
        gap = 6
        osk_start_y = 280

        for row_i, row in enumerate(self.osk_rows):
            # Calcular ancho total de la fila para centrarla
            if row_i < 4:
                total_w = len(row) * (key_w + gap) - gap
            else:
                # Fila de botones especiales: calcular con anchos variables
                total_w = 0
                for k in row:
                    total_w += (len(k) * 16 + 20) + gap
                total_w -= gap

            row_x = (SCREEN_WIDTH - total_w) // 2
            y = osk_start_y + row_i * (key_h + gap)

            for col_i, key_char in enumerate(row):
                is_selected = row_i == self.osk_row and col_i == self.osk_col

                # Ancho variable para botones especiales
                if row_i == 4:
                    w = len(key_char) * 16 + 20
                else:
                    w = key_w

                # Fondo de la tecla
                rect = pygame.Rect(row_x, y, w, key_h)
                if is_selected:
                    pygame.draw.rect(self.screen, COLOR_SELECTED, rect)
                    text_color = COLOR_BG
                else:
                    pygame.draw.rect(self.screen, COLOR_PANEL_BG, rect)
                    text_color = COLOR_TEXT
                pygame.draw.rect(self.screen, COLOR_SEPARATOR, rect, 1)

                # Texto de la tecla
                label = key_char
                char_surface = self.font_small.render(label, True, text_color)
                char_rect = char_surface.get_rect(center=rect.center)
                self.screen.blit(char_surface, char_rect)

                row_x += w + gap

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
