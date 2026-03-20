"""
RetroArch Frontend - Punto de entrada.

Ejecuta la interfaz grafica del frontend.
Soporta reinicio automatico desde el menu de opciones.
"""

from ui import Frontend


def main():
    while True:
        app = Frontend()
        app.run()
        if not app.restart_requested:
            break


if __name__ == "__main__":
    main()
