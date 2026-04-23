# VOXEL WILDS

A Minecraft-inspired 3D survival and crafting game written in Python with OpenGL.

## Features

- **Procedurally Generated Worlds** – Infinite terrain using Perlin noise
- **Mining & Crafting** – Break blocks, collect resources, craft tools
- **Survival System** – Health, hunger, and day/night cycles
- **Animals** – Cows, pigs, sheep, and chickens with simple AI
- **Inventory Management** – Hotbar with 9 slots and crafting recipes
- **Multiplayer-Ready Architecture** – Clean, modular codebase

## Installation

### Requirements
- Python 3.8+
- pip (Python package manager)

### Setup

```bash
pip install pygame PyOpenGL PyOpenGL_accelerate numpy
python main.py
```

## Controls

| Action | Key(s) |
|--------|--------|
| Move | WASD |
| Sprint | Shift |
| Look | Mouse |
| Jump | Space |
| Mine (hold) | Left Click |
| Place Block | Right Click |
| Inventory | E |
| Hotbar Select | 1-9 |
| Hotbar Cycle | Mouse Wheel |
| Settings | ESC |
| Fullscreen | F11 |

## Project Structure

The codebase is modular and well-documented for easy extension:

```
voxel_wilds/
├── main.py              # Game loop and event handling
├── config.py            # Constants and configuration
├── textures.py          # Procedural texture generation
├── world.py             # Terrain generation and chunk management
├── player.py            # Player controller and physics
├── animals.py           # Animal entities and AI
├── particles.py         # Particle effect system
├── hud.py              # UI and menus
├── utils.py            # Common utility functions
└── saves/              # World save files (auto-created)
```

### Module Descriptions

#### `config.py`
Central configuration file containing:
- Display settings (resolution, FOV, render distance)
- Physics parameters (gravity, movement speed)
- Block definitions and properties
- Crafting recipes
- Animal definitions

**Why separate?** Makes tuning gameplay easy without touching code elsewhere.

#### `textures.py`
Handles all visual textures:
- Procedural texture atlas generation
- Block color definitions for UI
- Texture index mappings

**Why separate?** Texture generation is self-contained and can be customized independently.

#### `world.py`
Core world systems:
- `ChunkManager` – Manages chunk generation, loading, and caching
- Terrain generation with noise functions
- Block modification tracking
- Display list management for rendering

**Why separate?** World generation is complex and benefits from isolation.

#### `player.py`
Player mechanics:
- Position and velocity tracking
- Collision detection and physics
- Inventory management
- Raycast targeting

**Why separate?** Player logic is independent and reusable.

#### `animals.py`
Living creatures:
- `Animal` class with wandering AI
- Health system
- Drop mechanics

**Why separate?** Makes it easy to add new animal types or improve AI.

#### `particles.py`
Visual effects:
- Dust particles from mining
- Fade and physics

**Why separate?** Particle system is completely independent.

#### `hud.py`
User interface:
- Inventory and crafting screens
- Settings menus
- In-game HUD elements (health, hunger, FPS)
- Loading screens

**Why separate?** UI code is verbose and benefits from isolation.

#### `main.py`
Game engine:
- Main game loop
- Event handling
- OpenGL rendering setup
- Save/load system

#### `utils.py`
Shared utilities:
- Box rendering helper
- Perlin noise functions
- Math utilities

## Development

### Adding a New Block Type

1. **Add to `config.py`**:
   ```python
   MY_BLOCK = 20  # New block ID
   BLOCK_NAMES[MY_BLOCK] = "My Block"
   BLOCK_HARDNESS[MY_BLOCK] = 1.5
   SOLID.add(MY_BLOCK)  # If solid
   ```

2. **Add texture to `textures.py`**:
   ```python
   TEX_MY_BLOCK = 20
   # In generate_texture_atlas():
   draw_tex(TEX_MY_BLOCK, (r, g, b))  # RGB color
   # In get_tex_indices():
   MY_BLOCK: (TEX_MY_BLOCK,) * 6  # All 6 faces
   ```

3. **Update world generation** (optional):
   - Modify `generate_chunk()` in `world.py` to include your block

### Adding a New Animal

1. **Define in `config.py`**:
   ```python
   ANIMALS_DEF["my_animal"] = (
       (0.8, 0.6, 0.4),  # Body color
       (0.9, 0.7, 0.5),  # Leg color
       1.5,               # Size
       MEAT,              # Drop item
       10                 # Health
   )
   ```

2. **Spawn in `main.py`** (already done in `_spawn_animals()`)

### Performance Optimization

- **Render Distance**: Change `dev_rd` in game or adjust `render_dist` parameter in `ChunkManager`
- **Textures**: Use `high_q` setting to control resolution
- **Fog**: Enable in settings for better performance
- **FPS Cap**: Adjust in settings (higher = more CPU usage)

## Extending the Game

### Adding Multiplayer
The modular structure makes adding networking straightforward:
- Modify `Player.update()` to send state over network
- Modify `ChunkManager` to handle remote modifications
- Extend `Animal` for network synchronization

### Adding More Recipes
Recipes are stored in `config.RECIPES`:
```python
RECIPES.append((
    (INPUT_BLOCK, INPUT_BLOCK),  # Ingredients
    2,                            # Count needed
    OUTPUT_BLOCK,                 # Result
    4                             # Quantity produced
))
```

### Custom Terrain Generation
Replace `fbm()` in `world.py` with your own noise function. The function signature:
```python
def height_function(wx, wz, seed):
    return int_height_0_to_WORLD_HEIGHT
```

## Troubleshooting

### "PyOpenGL not found"
```bash
pip install PyOpenGL PyOpenGL_accelerate
```

### Low FPS
- Reduce render distance (Settings > Frame Limit)
- Enable fog (Settings > Volumetric Fog)
- Close other applications
- Use `-O` flag: `python -O main.py`

### Crashes on Startup
Ensure graphics drivers are up to date and support OpenGL 2.1+

## Architecture Principles

1. **Single Responsibility** – Each module has one job
2. **Minimal Coupling** – Modules depend on `config.py` mostly
3. **Configuration Over Code** – Tweak numbers in `config.py`, not source
4. **Documentation** – Every class and function is documented

## Performance Tips

- **Chunks** – Stored as display lists for fast GPU rendering
- **Modifications** – Tracked separately from generated chunks
- **Raycasting** – Fast block lookup via chunk coordinates
- **Rendering** – Two-pass (opaque then transparent) for proper blending

## License

Open source for educational and commercial use.

## Contributing

The modular structure makes contributions straightforward:

1. Fork the repository
2. Create a feature branch
3. Make changes following existing code style
4. Test in-game
5. Submit pull request

Common contributions:
- New block types
- New animals
- Biome systems
- Improved terrain generation
- UI enhancements

## Credits

Built as a learning project to demonstrate:
- Game engine architecture
- Procedural generation
- OpenGL rendering
- Python design patterns

Inspired by Minecraft and other voxel games.
