# RetroArch Frontend - The House of The eD

## Descripcion
Frontend personalizado para RetroArch desarrollado en Python con Pygame.
Interfaz fullscreen navegable con mando, pensada para ejecutarse al encender el PC.

## Estado actual
- Fase: Desarrollo activo
- Version: 0.2.0

## Estructura del proyecto
```
retroarch-frontend/
  main.py            - Punto de entrada (soporta reinicio)
  config.py          - Configuracion de rutas, sistemas, colores y assets
  scanner.py         - Escaneo de carpetas de ROMs
  controller.py      - Deteccion y gestion de mandos
  launcher.py        - Lanzamiento de RetroArch con core, ROM y cheevos
  ui.py              - Interfaz grafica (Pygame)
  settings.py        - Gestion de ajustes persistentes (JSON)
  assets_manager.py  - Descarga y cache de fuentes y portadas
  requirements.txt   - Dependencias del proyecto
  assets/
    fonts/           - Fuentes (Orbitron)
    boxart/          - Portadas de juegos (LibRetro Thumbnails)
    consoles/        - Imagenes de consolas
    backgrounds/     - Fondos de pantalla tematicos
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

## Pantallas
1. **Menu principal** - Titulo "The House of The eD", acceso a Sistemas y Opciones
2. **Sistemas** - Seleccion de consola con imagen y fondo tematico dinamico
3. **Juegos** - Lista de ROMs con portada, metadatos y descripcion
4. **Opciones** - RetroAchievements, reiniciar, salir
5. **RetroAchievements** - Login con teclado en pantalla para mando

## Controles (mando)
- D-pad / Stick izquierdo: Navegacion
- A (boton sur): Seleccionar / Confirmar
- B (boton este): Volver / Atras
- Start: Menu principal (desde sistemas)
- Select: Toggle RetroAchievements (en pantalla de juegos)

## Controles (teclado)
- Flechas: Navegacion
- Enter/Espacio: Confirmar
- Escape: Volver
- Tab: Start
- Right Shift: Select

## Archivos sensibles (no se suben a GitHub)
- settings.json - Credenciales de RetroAchievements
- assets/cheevos_override.cfg - Config generada para RetroArch

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
- Fuente: Orbitron (Google Fonts) - retro-futurista, legible
- Fondos tematicos por sistema con paneles semitransparentes para legibilidad
- RetroAchievements se pueden activar/desactivar rapidamente con Select
