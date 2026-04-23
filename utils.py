"""
Utility functions for Voxel Wilds

General-purpose helpers for rendering, math, and geometry.
"""

import math
from OpenGL.GL import glBegin, glEnd, glNormal3f, glVertex3f, GL_QUADS


def _box(x, y, z, w, h, d):
    """
    Draw a wireframe box using OpenGL.
    
    Used for rendering animals, particles, and debug geometry.
    
    Args:
        x, y, z: Position
        w, h, d: Width, height, depth
    """
    glBegin(GL_QUADS)

    # Front face
    glNormal3f(0, 0, -1)
    for i, j in [(0, 0), (w, 0), (w, h), (0, h)]:
        glVertex3f(x + i, y + j, z)

    # Back face
    glNormal3f(0, 0, 1)
    for i, j in [(0, 0), (w, 0), (w, h), (0, h)]:
        glVertex3f(x + i, y + j, z + d)

    # Bottom face
    glNormal3f(0, -1, 0)
    for i, j in [(0, 0), (w, 0), (w, d), (0, d)]:
        glVertex3f(x + i, y, z + j)

    # Top face
    glNormal3f(0, 1, 0)
    for i, j in [(0, 0), (w, 0), (w, d), (0, d)]:
        glVertex3f(x + i, y + h, z + j)

    # Left face
    glNormal3f(-1, 0, 0)
    for i, j in [(0, 0), (h, 0), (h, d), (0, d)]:
        glVertex3f(x, y + i, z + j)

    # Right face
    glNormal3f(1, 0, 0)
    for i, j in [(0, 0), (h, 0), (h, d), (0, d)]:
        glVertex3f(x + w, y + i, z + j)

    glEnd()


def generate_perlin_hash(x, z, seed):
    """
    Simple hash function for procedural generation.
    
    Args:
        x, z: Coordinates
        seed: Seed value
        
    Returns:
        Pseudo-random integer
    """
    h = seed ^ (int(x) * 1664525 + int(z) * 1013904223)
    h = (h ^ (h >> 14)) * 2246822519 & 0xFFFFFFFF
    return (h ^ (h >> 31)) & 0xFFFFFFFF


def lerp(a, b, t):
    """Linear interpolation."""
    return a + (b - a) * t


def fade(t):
    """Smooth step function for interpolation."""
    return t * t * t * (t * (t * 6 - 15) + 10)


def gradient(ix, iz, x, z, seed):
    """Calculate gradient vector for Perlin noise."""
    v = generate_perlin_hash(ix, iz, seed)
    dx, dz = x - ix, z - iz
    return [dx + dz, -dx + dz, dx - dz, -dx - dz][v & 3]
