"""
Animal system for Voxel Wilds

Handles all living creatures in the world - cows, pigs, sheep, chickens, etc.
"""

import math
import random
from config import ANIMALS_DEF, PASSABLE, WATER


class Animal:
    """
    Represents a single animal entity in the world.
    
    Animals wander randomly, can be hit, drop items when killed,
    and have basic AI for avoiding danger.
    """

    def __init__(self, kind, x, y, z):
        """
        Initialize an animal.
        
        Args:
            kind: Animal type (e.g., 'cow', 'pig')
            x, y, z: World position
        """
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.vy = 0.0
        self.yaw = random.uniform(0, 360)
        self.timer = random.uniform(1, 4)
        self.moving = False
        self.alive = True
        self.kind = kind

        # Unpack animal definition: (body_color, leg_color, size, drop_item, health)
        self.col, self.leg_col, self.sz, self.drop, self.health = ANIMALS_DEF[kind]
        self.sw = self.sh = self.sd = self.sz
        self.hit_timer = 0.0

    def hit(self, dmg):
        """
        Deal damage to the animal.
        
        Args:
            dmg: Damage amount
            
        Returns:
            bool: True if animal died, False otherwise
        """
        self.health -= dmg
        self.hit_timer = 0.4
        self.timer = random.uniform(2, 3)
        self.moving = True  # Run away
        if self.health <= 0:
            self.alive = False
        return not self.alive

    def update(self, dt, world):
        """
        Update animal position and behavior.
        
        Args:
            dt: Delta time since last update
            world: ChunkManager instance for collision checks
        """
        if self.hit_timer > 0:
            self.hit_timer -= dt

        self.timer -= dt

        if self.timer <= 0:
            self.moving = not self.moving
            self.timer = random.uniform(1, 5)
            if self.moving:
                self.yaw = random.uniform(0, 360)

        # Move if currently moving
        if self.moving:
            yr = math.radians(self.yaw)
            s = self.sz * (2.0 if self.hit_timer > 0 else 1.0)  # Run faster when hit
            dx = -math.sin(yr) * s * dt
            dz = -math.cos(yr) * s * dt

            by = int(math.floor(self.y - 0.1))

            # Check X movement
            if world.get_block(int(math.floor(self.x + dx)), by, int(math.floor(self.z))) in PASSABLE:
                self.x += dx

            # Check Z movement
            if world.get_block(int(math.floor(self.x)), by, int(math.floor(self.z + dz))) in PASSABLE:
                self.z += dz

        # Apply gravity
        self.vy -= 15.0 * dt
        ny = self.y + self.vy * dt
        by = int(math.floor(ny - self.sh))

        # Collision with ground
        if world.get_block(int(self.x), by, int(self.z)) not in PASSABLE:
            ny = by + 1 + self.sh
            self.vy = 0

        self.y = ny

    def draw(self):
        """
        Render the animal using OpenGL.
        Uses a simple box model for body and head, with 4 legs.
        """
        from OpenGL.GL import glPushMatrix, glTranslatef, glRotatef, glColor4f, glPopMatrix
        from utils import _box

        glPushMatrix()
        glTranslatef(self.x, self.y - self.sh / 2, self.z)
        glRotatef(self.yaw, 0, 1, 0)

        # Flash red when hit
        c = (1.0, 0.4, 0.4) if self.hit_timer > 0 else self.col
        w, h, d = self.sw, self.sh, self.sd

        # Body
        glColor4f(*c, 1.0)
        _box(-w / 2, 0, -d / 2, w, h, d)

        # Head
        hs = min(w, h) * 0.38
        glColor4f(c[0] * 0.82, c[1] * 0.82, c[2] * 0.82, 1.0)
        _box(-hs / 2, h, -hs * 0.8, hs, hs, hs)

        # Legs
        lw, lh = w * 0.18, h * 0.45
        glColor4f(c[0] * 0.68, c[1] * 0.68, c[2] * 0.68, 1.0)
        for lx, lz in [(-w * 0.3, -d * 0.3), (w * 0.3, -d * 0.3), (-w * 0.3, d * 0.3), (w * 0.3, d * 0.3)]:
            _box(lx - lw / 2, -lh, lz - lw / 2, lw, lh, lw)

        glPopMatrix()
