"""
Player class for Voxel Wilds

Handles all player state, movement, mining, and inventory.
"""

import math
from pygame.locals import K_w, K_s, K_a, K_d, K_LSHIFT, K_SPACE
from config import (
    MOVE_SPEED, SPRINT_MULT, MOUSE_SENS, GRAVITY, JUMP_SPEED,
    HUNGER_RATE, WORLD_HEIGHT, WATER, SOLID, PASSABLE,
    LOG, PLANK, STONE, DIRT, GRASS, TORCH, COAL, AIR, MEAT
)


class Player:
    """
    The player entity.
    
    Handles position, velocity, health, hunger, inventory,
    and raycast targeting for mining/building.
    """

    def __init__(self, world):
        """
        Initialize player at spawn point.
        
        Args:
            world: ChunkManager instance
        """
        self.world = world
        self.x = 8.5
        self.y = 22.0
        self.z = 8.5

        # Velocity
        self.vx = self.vy = self.vz = 0.0

        # Rotation
        self.yaw = 0.0
        self.pitch = 0.0

        # State
        self.on_ground = False
        self.height = 1.8

        # Health & Hunger
        self.health = self.max_health = 20
        self.hunger = self.max_hunger = 20
        self.hunger_acc = 0.0

        # Inventory & hotbar
        self.inventory = {LOG: 8, STONE: 12, DIRT: 16, GRASS: 6, PLANK: 4}
        self.hotbar = [GRASS, DIRT, STONE, LOG, PLANK, TORCH, COAL, AIR, AIR]
        self.selected_slot = 0

        # Mining
        self.mining_block = None
        self.mining_time = 0.0
        self.mining_progress = 0.0

    def look_dir(self):
        """Get the direction the player is looking."""
        yr = math.radians(self.yaw)
        pr = math.radians(self.pitch)
        return (
            -math.cos(pr) * math.sin(yr),
            math.sin(pr),
            -math.cos(pr) * math.cos(yr),
        )

    def update(self, dt, keys, world, game=None):
        """
        Update player state.
        
        Args:
            dt: Delta time
            keys: pygame key states
            world: ChunkManager
            game: Game instance for dev features
        """
        moving = any([keys[K_w], keys[K_s], keys[K_a], keys[K_d]])
        self.hunger_acc += dt

        drain_time = HUNGER_RATE * (0.7 if moving else 1.0)
        speed_mult = game.dev_speed if game else 1.0

        # Apply hunger
        if self.hunger_acc >= drain_time:
            self.hunger_acc -= drain_time
            if self.hunger > 0:
                self.hunger -= 1

        # Health regeneration
        if self.hunger >= 20 and self.health < self.max_health:
            self.health += dt * 1.5
        elif self.hunger >= 18 and self.health < self.max_health:
            self.health += dt * 0.4

        # Starvation damage
        if self.hunger == 0 and self.health > 1:
            self.health = max(1.0, self.health - dt * 0.3)

        # Movement direction
        yr = math.radians(self.yaw)
        fx, fz = -math.sin(yr), -math.cos(yr)
        sx, sz = math.cos(yr), -math.sin(yr)

        spd = MOVE_SPEED * (SPRINT_MULT if keys[K_LSHIFT] else 1.0) * speed_mult

        # Swimming
        if world.get_block(self.x, self.y - self.height + 0.1, self.z) == WATER:
            spd *= 0.5

        # Dev flight mode
        if game and game.dev_fly:
            mx = mz = my = 0
            if keys[K_w]:
                mx += fx
                mz += fz
            if keys[K_s]:
                mx -= fx
                mz -= fz
            if keys[K_a]:
                mx -= sx
                mz -= sz
            if keys[K_d]:
                mx += sx
                mz += sz
            if keys[K_SPACE]:
                my += 1
            if keys[K_LSHIFT]:
                my -= 1

            L = math.sqrt(mx * mx + mz * mz) or 1
            self.vx, self.vz, self.vy = mx / L * spd * 2, mz / L * spd * 2, my * spd * 2
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.z += self.vz * dt
            return

        # Normal movement
        mx = mz = 0
        if keys[K_w]:
            mx += fx
            mz += fz
        if keys[K_s]:
            mx -= fx
            mz -= fz
        if keys[K_a]:
            mx -= sx
            mz -= sz
        if keys[K_d]:
            mx += sx
            mz += sz

        L = math.sqrt(mx * mx + mz * mz) or 1
        self.vx, self.vz = mx / L * spd, mz / L * spd
        self.vy -= GRAVITY * dt

        if keys[K_SPACE] and self.on_ground:
            self.vy = JUMP_SPEED
            self.on_ground = False

        self._move(dt, world)

    def _move(self, dt, world):
        """Handle collision and physics."""
        nx = self.x + self.vx * dt
        ny = self.y + self.vy * dt
        nz = self.z + self.vz * dt
        self.on_ground = False

        # Vertical collision
        if self.vy > 0:
            by_ceil = int(math.floor(ny + 0.1))
            hit = False
            for bx in [int(math.floor(self.x - 0.3)), int(math.floor(self.x + 0.3))]:
                for bz in [int(math.floor(self.z - 0.3)), int(math.floor(self.z + 0.3))]:
                    if world.get_block(bx, by_ceil, bz) in SOLID:
                        hit = True
                        break
                if hit:
                    break
            if hit:
                self.vy = 0
                ny = by_ceil - 0.1
        else:
            by_floor = int(math.floor(ny - self.height - 0.02))
            hit = False
            for bx in [int(math.floor(self.x - 0.3)), int(math.floor(self.x + 0.3))]:
                for bz in [int(math.floor(self.z - 0.3)), int(math.floor(self.z + 0.3))]:
                    if world.get_block(bx, by_floor, bz) in SOLID:
                        hit = True
                        break
                if hit:
                    break
            if hit:
                ny = by_floor + 1 + self.height
                self.vy = 0
                self.on_ground = True

        # Ceiling clamp
        if self.on_ground:
            by_ceil = int(math.floor(ny + 0.02))
            if world.get_block(int(math.floor(self.x)), by_ceil, int(math.floor(self.z))) in SOLID:
                ny = by_ceil - 0.02

        # Horizontal collision
        bx_hit = int(math.floor(nx + math.copysign(0.3, self.vx)))
        move_x = True
        for by_check in [int(math.floor(ny - 0.1)), int(math.floor(ny - self.height + 0.1))]:
            for bz_check in [int(math.floor(self.z - 0.25)), int(math.floor(self.z + 0.25))]:
                if world.get_block(bx_hit, by_check, bz_check) in SOLID:
                    move_x = False
                    break
            if not move_x:
                break
        if not move_x:
            nx = self.x
            self.vx = 0

        bz_hit = int(math.floor(nz + math.copysign(0.3, self.vz)))
        move_z = True
        for by_check in [int(math.floor(ny - 0.1)), int(math.floor(ny - self.height + 0.1))]:
            for bx_check in [int(math.floor(nx - 0.25)), int(math.floor(nx + 0.25))]:
                if world.get_block(bx_check, by_check, bz_hit) in SOLID:
                    move_z = False
                    break
            if not move_z:
                break
        if not move_z:
            nz = self.z
            self.vz = 0

        self.x, self.y, self.z = nx, ny, nz

    def raycast(self, world, max_dist=6.0, step=0.05):
        """
        Cast a ray from player's eyes to find block/placement position.
        
        Args:
            world: ChunkManager
            max_dist: Maximum raycast distance
            step: Raycast step size
            
        Returns:
            Tuple of (block_pos, placement_pos, block_id) or (None, None, None)
        """
        dx, dy, dz = self.look_dir()
        ey = self.y + 0.1
        t = 0.1
        prev = None

        while t < max_dist:
            bx = int(math.floor(self.x + dx * t))
            by = int(math.floor(ey + dy * t))
            bz = int(math.floor(self.z + dz * t))
            bid = world.get_block(bx, by, bz)

            if bid in SOLID:
                return (bx, by, bz), prev, bid

            prev = (bx, by, bz)
            t += step

        return None, None, None

    def add_item(self, bid, n=1):
        """Add items to inventory."""
        self.inventory[bid] = self.inventory.get(bid, 0) + n

    def remove_item(self, bid, n=1):
        """Remove items from inventory."""
        if self.inventory.get(bid, 0) >= n:
            self.inventory[bid] -= n
            if self.inventory[bid] == 0:
                self.inventory.pop(bid, None)
            return True
        return False

    def selected_block(self):
        """Get currently selected block."""
        return self.hotbar[self.selected_slot % len(self.hotbar)]
