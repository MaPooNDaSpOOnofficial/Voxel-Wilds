"""
Texture generation and management for Voxel Wilds

This module handles all texture atlas generation and rendering.
Textures are procedurally generated with noise and patterns.
"""

import random
import pygame
from config import (
    GRASS, DIRT, STONE, SAND, WATER, LOG, LEAVES, PLANK,
    COAL, IRON, GOLD, GRAVEL, CRAFT_TABLE, DIAMOND, EMERALD,
    STICK, MEAT
)


# ─────────────────────────────────────────────
#  TEXTURE INDICES (Atlas 8x8 grid)
# ─────────────────────────────────────────────
TEX_GRASS_TOP = 0
TEX_GRASS_SIDE = 1
TEX_DIRT = 2
TEX_STONE = 3
TEX_SAND = 4
TEX_WATER = 5
TEX_WOOD_SIDE = 6
TEX_WOOD_TOP = 7
TEX_LEAVES = 8
TEX_PLANK = 9
TEX_COAL = 10
TEX_IRON = 11
TEX_GOLD = 12
TEX_GRAVEL = 13
TEX_CRAFT_SIDE = 14
TEX_CRAFT_TOP = 15
TEX_DIAMOND = 16
TEX_EMERALD = 17
TEX_STICK = 18
TEX_MEAT = 19


def get_tex_indices(bid):
    """
    Get texture indices for all 6 faces of a block.
    Returns a tuple of (top, bottom, right, left, front, back).
    
    Args:
        bid: Block ID
        
    Returns:
        Tuple of 6 texture indices for each face
    """
    mapping = {
        GRASS: (TEX_GRASS_TOP, TEX_DIRT, TEX_GRASS_SIDE, TEX_GRASS_SIDE, TEX_GRASS_SIDE, TEX_GRASS_SIDE),
        DIRT: (TEX_DIRT,) * 6,
        STONE: (TEX_STONE,) * 6,
        SAND: (TEX_SAND,) * 6,
        WATER: (TEX_WATER,) * 6,
        LOG: (TEX_WOOD_TOP, TEX_WOOD_TOP, TEX_WOOD_SIDE, TEX_WOOD_SIDE, TEX_WOOD_SIDE, TEX_WOOD_SIDE),
        LEAVES: (TEX_LEAVES,) * 6,
        PLANK: (TEX_PLANK,) * 6,
        COAL: (TEX_COAL,) * 6,
        IRON: (TEX_IRON,) * 6,
        GOLD: (TEX_GOLD,) * 6,
        GRAVEL: (TEX_GRAVEL,) * 6,
        DIAMOND: (TEX_DIAMOND,) * 6,
        EMERALD: (TEX_EMERALD,) * 6,
        STICK: (TEX_STICK,) * 6,
        MEAT: (TEX_MEAT,) * 6,
        CRAFT_TABLE: (TEX_CRAFT_TOP, TEX_WOOD_TOP, TEX_CRAFT_SIDE, TEX_CRAFT_SIDE, TEX_CRAFT_SIDE, TEX_CRAFT_SIDE),
    }
    return mapping.get(bid, (TEX_DIRT,) * 6)


def generate_texture_atlas():
    """
    Generate a procedural texture atlas (8x8 grid, 16x16 tiles).
    
    Each tile is procedurally generated with noise and patterns to create
    a natural-looking appearance. Includes grass, ore patterns, leaves, etc.
    
    Returns:
        pygame.Surface: RGBA texture atlas (128x128)
    """
    ts = 16  # tile size
    size = ts * 8
    surf = pygame.Surface((size, size), pygame.SRCALPHA, 32)

    def draw_tex(idx, base_col, noise=0.12, pattern=None):
        """Draw a single texture tile to the atlas."""
        tx, ty = (idx % 8) * ts, (idx // 8) * ts

        for ly in range(ts):
            for lx in range(ts):
                # Apply noise to base color
                c = [
                    max(0, min(255, int(v * (1 + random.uniform(-noise, noise)))))
                    for v in base_col
                ]

                # Apply pattern-specific modifications
                if pattern == "grass_side" and ly < 5:
                    c = [
                        max(0, min(255, int(v * (1 + random.uniform(-noise, noise)))))
                        for v in (100, 180, 50)
                    ]
                elif pattern == "ore":
                    if random.random() >= 0.15:
                        c = [max(0, min(255, int(135 * (1 + random.uniform(-0.05, 0.05))))) for _ in range(3)]
                elif pattern == "leaves":
                    # Create a "leaf clump" pattern
                    if (lx % 4 == 0 or ly % 4 == 0) and random.random() < 0.6:
                        c = [max(0, min(255, int(v * 0.7))) for v in c]
                    alpha = 255
                    if random.random() < 0.15:
                        alpha = 0  # Random transparent "gaps"
                    elif random.random() < 0.1:
                        c = [int(v * 0.5) for v in c]  # Darker bits
                    c.append(alpha)
                    surf.set_at((tx + lx, ty + ly), c)
                    continue
                elif pattern == "bark":
                    if lx % 4 == 0 or random.random() < 0.1:
                        c = [max(0, min(255, int(v * 0.8))) for v in c]

                c.append(255)  # Alpha
                surf.set_at((tx + lx, ty + ly), c)

    # Draw all textures
    draw_tex(TEX_GRASS_TOP, (100, 180, 50))
    draw_tex(TEX_GRASS_SIDE, (125, 87, 48), pattern="grass_side")
    draw_tex(TEX_DIRT, (125, 87, 48))
    draw_tex(TEX_STONE, (135, 135, 135))
    draw_tex(TEX_SAND, (215, 200, 140))
    draw_tex(TEX_WATER, (40, 90, 210), noise=0.1)
    draw_tex(TEX_WOOD_SIDE, (110, 85, 50), pattern="bark")
    draw_tex(TEX_WOOD_TOP, (140, 115, 70))
    draw_tex(TEX_LEAVES, (35, 110, 25), noise=0.2, pattern="leaves")
    draw_tex(TEX_PLANK, (181, 145, 87), noise=0.05)
    draw_tex(TEX_COAL, (45, 45, 45), pattern="ore")
    draw_tex(TEX_IRON, (190, 160, 140), pattern="ore")
    draw_tex(TEX_GOLD, (230, 210, 60), pattern="ore")
    draw_tex(TEX_GRAVEL, (140, 138, 132), noise=0.15)
    draw_tex(TEX_CRAFT_SIDE, (140, 90, 40))
    draw_tex(TEX_CRAFT_TOP, (160, 110, 60))
    draw_tex(TEX_DIAMOND, (160, 240, 255), pattern="ore")
    draw_tex(TEX_EMERALD, (60, 230, 120), pattern="ore")
    draw_tex(TEX_STICK, (100, 75, 45))
    draw_tex(TEX_MEAT, (180, 60, 60), noise=0.1)

    return surf


def get_block_colors(bid):
    """
    Get RGB color tuples for each face of a block.
    Used for block highlighting in UI and rendering fallback.
    
    Args:
        bid: Block ID
        
    Returns:
        Tuple of 3 RGB colors for (top, bottom, sides)
    """
    colors = {
        GRASS: ((0.29, 0.72, 0.19), (0.44, 0.34, 0.19), (0.49, 0.34, 0.19)),
        DIRT: ((0.49, 0.34, 0.19),) * 3,
        STONE: ((0.53, 0.53, 0.53),) * 3,
        WOOD: ((0.59, 0.49, 0.29),) * 3,
        LEAVES: ((0.19, 0.53, 0.14),) * 3,
        SAND: ((0.84, 0.81, 0.59),) * 3,
        WATER: ((0.18, 0.38, 0.82),) * 3,
        LOG: ((0.54, 0.44, 0.24), (0.44, 0.31, 0.17), (0.44, 0.31, 0.17)),
        PLANK: ((0.71, 0.57, 0.34),) * 3,
        TORCH: ((0.94, 0.79, 0.19),) * 3,
        COAL: ((0.28, 0.28, 0.28),) * 3,
        IRON: ((0.64, 0.57, 0.51),) * 3,
        GOLD: ((0.89, 0.79, 0.19),) * 3,
        CRAFT_TABLE: ((0.59, 0.37, 0.17), (0.49, 0.27, 0.09), (0.49, 0.27, 0.09)),
        GRAVEL: ((0.55, 0.54, 0.52),) * 3,
        DIAMOND: ((0.63, 0.94, 1.0),) * 3,
        EMERALD: ((0.24, 0.90, 0.47),) * 3,
        MEAT: ((0.8, 0.3, 0.3),) * 3,
    }
    return colors.get(bid, ((0.8, 0.2, 0.8),) * 3)
