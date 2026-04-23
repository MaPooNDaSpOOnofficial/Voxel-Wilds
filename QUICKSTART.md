# Quick Start Guide

## Installation & Running

```bash
# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

## First Time Setup

1. On first run, a `saves/` directory will be created
2. Start a new world from the title menu
3. Use WASD to move, mouse to look around

## File Overview at a Glance

| File | Purpose | Key Classes | Lines |
|------|---------|------------|-------|
| `config.py` | Constants & settings | None (module-level vars) | 150 |
| `main.py` | Game engine | `Game` | 450 |
| `world.py` | Terrain generation | `ChunkManager` | 350 |
| `player.py` | Player physics | `Player` | 280 |
| `hud.py` | UI rendering | `HUD` | 450 |
| `animals.py` | Animal AI | `Animal` | 120 |
| `textures.py` | Textures | Functions | 200 |
| `particles.py` | Particle effects | `Particle` | 80 |
| `utils.py` | Utilities | Functions | 90 |

## Common Tasks

### Change Player Speed
Edit `config.py`, line ~25:
```python
MOVE_SPEED = 5.0  # Change this value
```

### Add a Crafting Recipe
Edit `config.py`, add to `RECIPES`:
```python
((LOG, STONE), 2, CRAFT_TABLE, 1)  # 2x Log + 2x Stone = 1 Crafting Table
```

### Modify Texture Colors
Edit `textures.py`, in `generate_texture_atlas()`:
```python
draw_tex(TEX_GRASS_TOP, (100, 180, 50))  # RGB color
```

### Adjust World Difficulty
Edit `config.py`:
```python
HUNGER_RATE = 80.0      # Lower = more frequent hunger
BLOCK_HARDNESS[STONE] = 1.5  # Higher = harder to break
```

## Development Tips

### Debugging
- Activate FPS display in settings (ESC → Performance Overlay)
- Use dev menu (click version number 5 times on title screen)
- Dev menu includes FPS limit, render distance, FOV, flight mode, speed

### Performance Profiling
```python
import cProfile
cProfile.run('game.run()')
```

### Testing Changes
1. Modify a config value
2. Press ESC in game to go back to menu
3. Load game again – changes take effect

### Code Style
- PEP 8 compliant
- Docstrings for all public functions
- Type hints where helpful
- Snake_case for variables/functions

## Project Dependencies

- **pygame** 2.0+ – Window, input, 2D rendering
- **PyOpenGL** 3.1+ – 3D rendering
- **numpy** – Mathematical operations

All included in `requirements.txt`.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No module named 'pygame'" | `pip install -r requirements.txt` |
| Low FPS | Reduce render distance in settings |
| Game crashes on startup | Update graphics drivers |
| Inventory not opening | Make sure you're in game (not menu), press E |

## Next Steps

1. **Understand the flow**: Start with `main.py` → see how it calls other modules
2. **Explore generation**: Read `world.py` to understand terrain creation
3. **Try modding**: Add a new block type following README instructions
4. **Optimize**: Experiment with performance settings

## Key Concepts

- **Chunks**: 16×16×48 blocks, loaded/unloaded dynamically
- **Display Lists**: OpenGL optimization for rendering chunks
- **Raycasting**: Finding which block player is looking at
- **Modifications**: Tracking player-made world changes separately
- **Perlin Noise**: Used for procedural terrain generation

## Testing Checklist

After making changes:
- [ ] Game starts without crashes
- [ ] Can create new world
- [ ] Can mine blocks
- [ ] Can place blocks
- [ ] Inventory works
- [ ] Crafting works
- [ ] Settings save
- [ ] FPS is acceptable (30+ on moderate hardware)

## Resources

- **README.md** – Complete documentation
- **REFACTORING.md** – What changed and why
- **Docstrings** – In-code documentation (hover in IDE)

## Getting Help

1. Check docstrings in the relevant module
2. Look for similar code patterns in other modules
3. Review README section on extending
4. Check Minecraft wiki for game mechanic reference

Happy modding! 🚀
