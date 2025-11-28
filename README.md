# spaceGame

This is a small OpenGL space dodging game using Pygame + PyOpenGL, originally implemented as a single file `game.py`.

Enhancements added:

-   Start menu with game mode and difficulty options
-   Two distinct game modes: **Survival** and **Collector**
-   Improved camera and lighting system
-   Better scenario with more variety of obstacles, powerups, scoring
-   Improved code structure and assets loader
-   Time-based and score-based leaderboards

## Requirements

Install requirements with pip:

```bash
pip install -r requirements.txt
```

## Run

```bash
python game.py
```

## Project layout

-   `game.py` – tiny entry point that instantiates the `spacegame.Game` class.
-   `spacegame/constants.py` – gameplay constants, difficulty tables, global scale knobs.
-   `spacegame/state.py` – dataclasses describing player/camera/menu/leaderboard state.
-   `spacegame/rendering.py` – OpenGL renderer (skybox, models, UI overlays).
-   `spacegame/gameplay.py` – spawning logic, pickups, bullet/enemy interactions.
-   `spacegame/engine.py` – orchestration of events, updates, and rendering.

## Controls

-   Left / Right arrows — move ship left/right between lanes
-   Space — fire (needs charge, Survival mode only)
-   P or Esc — pause / resume
-   In menus use Up / Down / Left / Right + Enter to navigate and select options

## Game Modes

### Survival Mode (Original)

-   **Objective**: Survive as long as possible while avoiding obstacles
-   **Scoring**: Points-based (destroy enemies, collect pickups)
-   **Mechanics**:
    -   Avoid asteroids and enemy ships
    -   Shoot enemies with your charged weapon
    -   Collect power-ups for shields, slow motion, or instant weapon charge
-   **Game Over**: When you collide with an obstacle without a shield

### Collector Mode (NEW!)

-   **Objective**: Collect falling golden stars before they pass you
-   **Scoring**: Time-based - survive as long as possible!
-   **Mechanics**:
    -   Collect all the golden stars that fall from above
    -   Each star you miss counts against you
    -   No shooting - focus on collection!
-   **Difficulty Settings**:
    -   **Easy**: Miss up to 5 stars, slower speed
    -   **Normal**: Miss up to 3 stars, moderate speed
    -   **Hard**: Miss only 2 stars, fast speed
-   **Game Over**: When you miss too many stars (varies by difficulty)
-   **Display**: HUD shows Time, Stars Collected, and Misses remaining

## Gameplay notes

-   Both modes have separate leaderboards for each difficulty level
-   Pickups in Survival mode give temporary shields, slow-down enemies, or instantly refill your shot charge
-   Ship/asteroid/enemy/star models are lightweight display lists for fast rendering
-   Collector mode features bright golden stars with a distinctive visual effect

## Lightweight models

-   Tweak `MODEL_SCALE_SHIP` / `MODEL_SCALE_OBJECT` inside `spacegame/constants.py` to globally resize combatants.
-   For geometry tweaks, edit `Renderer._create_model_display_lists()` in `spacegame/rendering.py` or the draw helpers (`draw_ship`, `draw_asteroid`, `draw_enemy`).

## Moon tint fix

The textured moon and menu planet now set their own neutral material before drawing so they no longer adopt the emissive/specular colors from the last rendered model.

## Skybox textures

If you want to use a textured cubemap skybox rather than the procedural starfield, add a folder named `skybox` next to `game.py` containing six images named:

```
posx.png  negx.png  posy.png
negy.png  posz.png  negz.png
```

Supported image extensions are .png, .jpg, .jpeg. The game will automatically load these if present and render a textured skybox behind the scene.

## Notes

This game is a small demo. If you are on Windows ensure you have a working OpenGL implementation and the `pygame` package (pip) can create an OpenGL surface.
"# space-dodger" 
