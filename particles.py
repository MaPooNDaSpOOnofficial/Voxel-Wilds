"""
Particle system for Voxel Wilds

Handles visual effects like block dust and item drops.
"""

import random
from textures import get_block_colors
from utils import _box
from OpenGL.GL import glColor4f


class Particle:
    """
    A single particle effect (block dust, etc.).
    
    Particles are affected by gravity, fade out over time,
    and are used for visual feedback when breaking blocks or other events.
    """

    def __init__(self, x, y, z, bid):
        """
        Create a particle at the given position.
        
        Args:
            x, y, z: World position
            bid: Block ID (determines color)
        """
        # Add some randomness to spawn position
        self.x = x + random.uniform(0.1, 0.9)
        self.y = y + random.uniform(0.1, 0.9)
        self.z = z + random.uniform(0.1, 0.9)

        # Random velocity
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(2, 5)
        self.vz = random.uniform(-1.5, 1.5)

        # Lifetime
        self.life = random.uniform(0.5, 1.0)
        self.max_life = self.life

        # Color from block
        self.col = get_block_colors(bid)[0]

    def update(self, dt):
        """
        Update particle position and lifetime.
        
        Args:
            dt: Delta time since last update
        """
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        self.vy -= 14.0 * dt  # Apply gravity
        self.life -= dt

    def draw(self):
        """
        Render the particle as a small colored cube.
        Fades out as it ages.
        """
        alpha = self.life / self.max_life
        size = 0.05 * alpha

        glColor4f(*self.col, alpha)
        _box(self.x - size, self.y - size, self.z - size, size * 2, size * 2, size * 2)
