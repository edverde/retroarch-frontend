"""
RetroArch Frontend - Punto de entrada.

Ejecuta la interfaz grafica del frontend.
"""

from ui import Frontend


def main():
    app = Frontend()
    app.run()


if __name__ == "__main__":
    main()
