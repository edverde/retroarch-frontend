"""
Deteccion y gestion de mandos.

Detecta mandos conectados via pygame.joystick, identifica el tipo
(Xbox, PlayStation, generico) y traduce los eventos a acciones
unificadas para la interfaz.
"""

import pygame


# Acciones unificadas que la UI entiende
ACTION_UP = "up"
ACTION_DOWN = "down"
ACTION_LEFT = "left"
ACTION_RIGHT = "right"
ACTION_CONFIRM = "confirm"
ACTION_BACK = "back"
ACTION_START = "start"
ACTION_SELECT = "select"

# Umbral para considerar movimiento del stick analogico
STICK_THRESHOLD = 0.5


def detect_controller_type(joystick):
    """
    Identifica el tipo de mando basandose en su nombre.
    Devuelve 'xbox', 'playstation' o 'generic'.
    """
    name = joystick.get_name().lower()

    if any(word in name for word in ["xbox", "xinput", "x-box"]):
        return "xbox"
    elif any(word in name for word in ["playstation", "ps4", "ps5", "dualshock", "dualsense"]):
        return "playstation"
    else:
        return "generic"


class Controller:
    """Gestiona la conexion de mandos y traduce inputs a acciones."""

    def __init__(self):
        pygame.joystick.init()
        self.joystick = None
        self.controller_type = "none"
        self._stick_was_moved = False
        self._refresh()

    def _refresh(self):
        """Detecta si hay un mando conectado."""
        count = pygame.joystick.get_count()
        if count > 0 and self.joystick is None:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.controller_type = detect_controller_type(self.joystick)
        elif count == 0:
            self.joystick = None
            self.controller_type = "none"

    def get_info(self):
        """Devuelve info del mando para mostrar en la UI."""
        if self.joystick is None:
            return "Sin mando detectado (usa teclado)"
        return f"{self.controller_type.upper()}: {self.joystick.get_name()}"

    def handle_event(self, event):
        """
        Traduce un evento de pygame a una accion unificada.
        Soporta: botones del mando, D-pad (hat), stick analogico y teclado.
        Devuelve None si el evento no corresponde a ninguna accion.
        """
        # Reconectar mando si se desconecto/conecto
        if event.type == pygame.JOYDEVICEADDED:
            try:
                self.joystick = pygame.joystick.Joystick(event.device_index)
                self.joystick.init()
                self.controller_type = detect_controller_type(self.joystick)
            except Exception:
                self.joystick = None
                self.controller_type = "none"
            return None

        if event.type == pygame.JOYDEVICEREMOVED:
            if self.joystick is not None:
                try:
                    self.joystick.quit()
                except Exception:
                    pass
            self.joystick = None
            self.controller_type = "none"
            # Reiniciar subsistema para limpiar estado interno de pygame
            pygame.joystick.quit()
            pygame.joystick.init()
            return None

        # --- Teclado (siempre disponible como respaldo) ---
        if event.type == pygame.KEYDOWN:
            mapping = {
                pygame.K_UP: ACTION_UP,
                pygame.K_DOWN: ACTION_DOWN,
                pygame.K_LEFT: ACTION_LEFT,
                pygame.K_RIGHT: ACTION_RIGHT,
                pygame.K_RETURN: ACTION_CONFIRM,
                pygame.K_SPACE: ACTION_CONFIRM,
                pygame.K_ESCAPE: ACTION_BACK,
                pygame.K_BACKSPACE: ACTION_BACK,
                pygame.K_TAB: ACTION_START,
                pygame.K_RSHIFT: ACTION_SELECT,
            }
            return mapping.get(event.key)

        # Si no hay mando conectado, ignorar eventos de joystick
        if self.joystick is None:
            return None

        # --- Botones del mando ---
        if event.type == pygame.JOYBUTTONDOWN:
            # Boton 0 = A (Xbox) / X (PS) = Confirmar
            # Boton 1 = B (Xbox) / O (PS) = Atras
            if event.button == 0:
                return ACTION_CONFIRM
            elif event.button == 1:
                return ACTION_BACK
            elif event.button == 6:
                return ACTION_START
            elif event.button == 7:
                return ACTION_SELECT

        # --- D-pad (hat) ---
        if event.type == pygame.JOYHATMOTION:
            x, y = event.value
            if y == 1:
                return ACTION_UP
            elif y == -1:
                return ACTION_DOWN
            elif x == -1:
                return ACTION_LEFT
            elif x == 1:
                return ACTION_RIGHT

        # --- Stick analogico izquierdo (eje 0=X, eje 1=Y) ---
        if event.type == pygame.JOYAXISMOTION:
            if event.axis == 1:  # Vertical
                if event.value < -STICK_THRESHOLD and not self._stick_was_moved:
                    self._stick_was_moved = True
                    return ACTION_UP
                elif event.value > STICK_THRESHOLD and not self._stick_was_moved:
                    self._stick_was_moved = True
                    return ACTION_DOWN
                elif abs(event.value) < STICK_THRESHOLD:
                    self._stick_was_moved = False
            elif event.axis == 0:  # Horizontal
                if event.value < -STICK_THRESHOLD and not self._stick_was_moved:
                    self._stick_was_moved = True
                    return ACTION_LEFT
                elif event.value > STICK_THRESHOLD and not self._stick_was_moved:
                    self._stick_was_moved = True
                    return ACTION_RIGHT
                elif abs(event.value) < STICK_THRESHOLD:
                    self._stick_was_moved = False

        return None
