"""
Configuration and Constants for Voxel Wilds

This module contains all game constants, block IDs, and tuning parameters.
"""

# ─────────────────────────────────────────────
#  DISPLAY & CAMERA
# ─────────────────────────────────────────────
WIDTH = 1280
HEIGHT = 720
FOV = 70
NEAR = 0.05
FAR = 200.0

# ─────────────────────────────────────────────
#  WORLD GENERATION
# ─────────────────────────────────────────────
CHUNK_SIZE = 16
WORLD_HEIGHT = 48
SEA_LEVEL = 14

# ─────────────────────────────────────────────
#  PHYSICS
# ─────────────────────────────────────────────
GRAVITY = 22.0
JUMP_SPEED = 9.0
MOVE_SPEED = 5.0
SPRINT_MULT = 1.7
MOUSE_SENS = 0.12
HUNGER_RATE = 80.0  # seconds per hunger point (Minecraft-ish)

# ─────────────────────────────────────────────
#  BLOCK IDs
# ─────────────────────────────────────────────
AIR = 0
GRASS = 1
DIRT = 2
STONE = 3
WOOD = 4
LEAVES = 5
SAND = 6
WATER = 7
LOG = 8
PLANK = 9
TORCH = 10
COAL = 11
IRON = 12
GOLD = 13
CRAFT_TABLE = 14
GRAVEL = 15
DIAMOND = 16
EMERALD = 17
STICK = 18
MEAT = 19

# ─────────────────────────────────────────────
#  BLOCK PROPERTIES
# ─────────────────────────────────────────────
BLOCK_NAMES = {
    AIR: "Air",
    GRASS: "Grass",
    DIRT: "Dirt",
    STONE: "Stone",
    WOOD: "Wood",
    LEAVES: "Leaves",
    SAND: "Sand",
    WATER: "Water",
    LOG: "Log",
    PLANK: "Plank",
    TORCH: "Torch",
    COAL: "Coal Ore",
    IRON: "Iron Ore",
    GOLD: "Gold Ore",
    CRAFT_TABLE: "Crafting Table",
    GRAVEL: "Gravel",
    DIAMOND: "Diamond Ore",
    EMERALD: "Emerald Ore",
    STICK: "Stick",
    MEAT: "Raw Meat",
}

BLOCK_HARDNESS = {
    GRASS: 0.6,
    DIRT: 0.5,
    STONE: 1.5,
    WOOD: 1.0,
    LEAVES: 0.2,
    SAND: 0.5,
    WATER: 0,
    LOG: 1.0,
    PLANK: 0.8,
    TORCH: 0.05,
    COAL: 2.0,
    IRON: 2.5,
    GOLD: 2.5,
    CRAFT_TABLE: 1.0,
    GRAVEL: 0.6,
    DIAMOND: 3.5,
    EMERALD: 3.0,
}

SOLID = {GRASS, DIRT, STONE, WOOD, LOG, PLANK, SAND, COAL, IRON, GOLD, CRAFT_TABLE, GRAVEL, DIAMOND, EMERALD}
PASSABLE = {AIR, WATER, LEAVES, TORCH, STICK}

# ─────────────────────────────────────────────
#  CRAFTING RECIPES
# ─────────────────────────────────────────────
RECIPES = [
    ((LOG,), 1, PLANK, 4),
    ((PLANK,), 2, STICK, 4),
    ((PLANK,), 4, CRAFT_TABLE, 1),
    ((STICK, COAL), 2, TORCH, 4),
    ((STONE,), 1, GRAVEL, 2),
    ((STONE,), 4, WOOD, 1),
]

# ─────────────────────────────────────────────
#  ANIMALS
# ─────────────────────────────────────────────
ANIMALS_DEF = {
    "cow": ((0.88, 0.88, 0.88), (0.85, 0.90, 0.50), 2.0, MEAT, 10),
    "pig": ((0.95, 0.68, 0.68), (0.72, 0.60, 0.40), 2.5, MEAT, 8),
    "sheep": ((0.92, 0.92, 0.88), (0.72, 0.80, 0.45), 2.2, MEAT, 8),
    "chicken": ((0.95, 0.91, 0.68), (0.42, 0.50, 0.30), 3.0, MEAT, 4),
}

# ─────────────────────────────────────────────
#  UI/DISPLAY
# ─────────────────────────────────────────────
SAVES_DIR = "saves"
VERSION = "1.3.0"
GAME_TITLE = "VOXEL WILDS - World Manager"
