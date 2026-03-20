# RetroArch Frontend

## Descripcion
Frontend personalizado para RetroArch desarrollado en Python con Pygame.
Interfaz fullscreen navegable con mando, pensada para ejecutarse al encender el PC.

## Estado actual
- Fase: Desarrollo inicial
- Version: 0.1.0

## Estructura del proyecto
```
retroarch-frontend/
  main.py          - Punto de entrada de la aplicacion
  config.py        - Configuracion de rutas, sistemas y cores
  scanner.py       - Escaneo de carpetas de ROMs
  controller.py    - Deteccion y gestion de mandos
  launcher.py      - Lanzamiento de RetroArch con core y ROM
  ui.py            - Interfaz grafica (Pygame)
  requirements.txt - Dependencias del proyecto
```

## Configuracion del entorno
- Python 3.x
- Dependencia principal: pygame

## Rutas importantes
- RetroArch: C:\RetroArch-Win64\retroarch.exe
- ROMs: C:\RetroArch-Win64\roms\
- Cores: C:\RetroArch-Win64\cores\

## Sistemas soportados
| Sistema    | Carpeta ROMs | Core                    | Extensiones |
|------------|-------------|-------------------------|-------------|
| SNES       | snes/       | snes9x_libretro.dll     | .sfc .smc   |
| Mega Drive | megadrive/  | picodrive_libretro.dll  | .md .bin    |

## Controles (mando)
- D-pad / Stick izquierdo: Navegacion
- A (boton sur): Seleccionar / Confirmar
- B (boton este): Volver / Atras
- Start: Menu principal

## Comandos utiles
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicacion
python main.py
```

## Notas de desarrollo
- Pygame se usa por ser ideal para interfaces fullscreen con input de mando
- El scanner detecta automaticamente juegos en las carpetas de ROMs
- El sistema de controladores usa pygame.joystick para detectar mandos
