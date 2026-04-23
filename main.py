#!/usr/bin/env python3
"""
VOXEL WILDS — 3D Survival & Crafting Game

A Minecraft-inspired sandbox game written in Python with OpenGL.

INSTALL:   pip install pygame PyOpenGL PyOpenGL_accelerate numpy
RUN:       python main.py

CONTROLS:
  WASD        — Move / Sprint (Shift)
  Mouse       — Look around
  Left Click  — Hold to mine block
  Right Click — Place block
  E           — Inventory & Crafting
  1-9         — Select hotbar slot
  Scroll      — Cycle hotbar
  Space       — Jump
  ESC         — Settings menu
"""

import sys
import os
import math
import random
import time
import json

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
from pygame.locals import *

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
except ImportError:
    print("PyOpenGL not found. Run: pip install PyOpenGL PyOpenGL_accelerate")
    sys.exit(1)

# Import all game modules
from config import (
    WIDTH, HEIGHT, FOV, NEAR, FAR, CHUNK_SIZE, WORLD_HEIGHT, SEA_LEVEL,
    GRAVITY, JUMP_SPEED, MOVE_SPEED, SPRINT_MULT, MOUSE_SENS, HUNGER_RATE,
    AIR, GRASS, DIRT, STONE, WOOD, LEAVES, SAND, WATER, LOG, PLANK, TORCH,
    COAL, IRON, GOLD, CRAFT_TABLE, GRAVEL, DIAMOND, EMERALD, STICK, MEAT,
    BLOCK_NAMES, BLOCK_HARDNESS, SOLID, PASSABLE, RECIPES, ANIMALS_DEF,
    SAVES_DIR, VERSION, GAME_TITLE
)
from textures import generate_texture_atlas, get_block_colors, get_tex_indices
from world import ChunkManager
from player import Player
from animals import Animal
from particles import Particle
from hud import HUD
from utils import _box


class Game:
    """Main game class handling rendering, events, and game loop."""

    def __init__(self):
        """Initialize the game."""
        self.fps_options = [30, 60, 120, 0]
        self.fps_idx = 1
        self.vsync = self.fullscreen = False
        self.dev_active = False
        self.dev_clicks = 0
        self.dev_fps = 60
        self.dev_rd = 4
        self.dev_fov = 70
        self.dev_fly = False
        self.dev_speed = 1.0

        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT),
            OPENGL | DOUBLEBUF | HWSURFACE,
            vsync=int(self.vsync)
        )
        pygame.display.set_caption(GAME_TITLE)

        # Create saves directory
        if not os.path.exists(SAVES_DIR):
            os.makedirs(SAVES_DIR)

        # Initialize graphics
        self.clock = pygame.time.Clock()
        self.hud_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._init_gl()

        # Game state
        self.state = "TITLE"
        self.loading = False
        self.progress = 0.0
        self.current_world = ""
        self.temp_name = ""

        # Game objects
        self.world = None
        self.player = None
        self.hud = HUD(self.hud_surf)
        self.particles = []
        self.animals = []

        # UI state
        self.show_inv = self.show_settings = self.mouse_cap = False
        self.fog = self.show_fps = self.high_q = True
        self.day = 0.3
        self.dt = 0.0
        self.running = True

        # World seed
        self.world_seed = random.randint(0, 0xFFFFFF)
        self.saves, self.save_exists = self._refresh_saves()

    def _refresh_saves(self):
        """Refresh list of available save files."""
        saves = [f for f in os.listdir(SAVES_DIR) if f.endswith(".json")][:10]
        return saves, len(saves) > 0

    def start_new_game(self, name, seed=None):
        """Start a new game."""
        base_name = name
        counter = 2
        while os.path.exists(os.path.join(SAVES_DIR, name + ".json")):
            suffix = f" {counter}"
            name = base_name[:16 - len(suffix)] + suffix
            counter += 1

        if seed is None:
            seed = random.randint(0, 0xFFFFFF)

        self.current_world = name
        self.world_seed = seed
        self.world = ChunkManager(seed, 4 if self.high_q else 2)
        self.player = Player(self.world)
        self.state = "LOADING"
        self.loading = True
        self.progress = 0.0

        # Ensure spawn area is loaded
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                self.world.ensure_chunks(dx, dz)

        # Find spawn height
        for sy in range(WORLD_HEIGHT - 1, 0, -1):
            if self.world.get_block(8, sy, 8) not in PASSABLE:
                self.player.y = sy + 1.9
                break

        self._spawn_animals()

    def save_game(self):
        """Save the current game state."""
        if not self.current_world or self.state in ["TITLE", "WORLD_SELECT", "WORLD_CREATE", "SETTINGS_MENU"]:
            return

        data = {
            "seed": self.world_seed,
            "name": self.current_world,
            "player": {
                "x": self.player.x,
                "y": self.player.y,
                "z": self.player.z,
                "health": self.player.health,
                "hunger": self.player.hunger,
                "inv": self.player.inventory,
                "hotbar": self.player.hotbar,
            },
            "mods": {f"{k[0]},{k[1]},{k[2]}": v for k, v in self.world.modifications.items()},
        }

        with open(os.path.join(SAVES_DIR, self.current_world + ".json"), "w") as f:
            json.dump(data, f)

    def load_game(self, filename):
        """Load a saved game."""
        with open(os.path.join(SAVES_DIR, filename), "r") as f:
            data = json.load(f)

        self.current_world = data["name"]
        self.world_seed = data["seed"]
        self.world = ChunkManager(self.world_seed, 4 if self.high_q else 2)
        self.player = Player(self.world)

        # Restore player state
        self.player.x = data["player"]["x"]
        self.player.y = data["player"]["y"]
        self.player.z = data["player"]["z"]
        self.player.health = data["player"]["health"]
        self.player.hunger = data["player"]["hunger"]
        self.player.inventory = {int(key): v for key, v in data["player"]["inv"].items()}
        self.player.hotbar = data["player"]["hotbar"]

        # Restore world modifications
        self.world.modifications = {tuple(map(int, k.split(","))): v for k, v in data["mods"].items()}

        self.state = "LOADING"
        self.loading = True
        self.progress = 0.0

        # Ensure chunks are loaded
        cx, cz = self.world.w2c(self.player.x, self.player.z)
        self.world.ensure_chunks(cx, cz)

        # Ensure safe spawn height
        safe_y = self.player.y
        for sy in range(WORLD_HEIGHT - 1, 0, -1):
            if self.world.get_block(self.player.x, sy, self.player.z) not in PASSABLE:
                safe_y = sy + 1.9
                break
        self.player.y = safe_y

        self._spawn_animals()

    def _spawn_animals(self):
        """Spawn animals in the world."""
        rng = random.Random(self.world_seed + 1)
        kinds = list(ANIMALS_DEF.keys())

        self.animals = []
        for _ in range(45):
            ax = rng.uniform(-80, 80)
            az = rng.uniform(-80, 80)
            kind = rng.choice(kinds)

            cx, cz = self.world.w2c(ax, az)
            if (cx, cz) not in self.world.chunks:
                continue

            for ay in range(WORLD_HEIGHT - 1, 0, -1):
                bid = self.world.get_block(int(ax), ay, int(az))
                if bid not in PASSABLE:
                    if bid != WATER:
                        self.animals.append(Animal(kind, ax, ay + 1.5, az))
                    break

    def _init_gl(self):
        """Initialize OpenGL settings."""
        glViewport(0, 0, WIDTH, HEIGHT)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [100, 200, 100, 0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.55, 0.55, 0.6, 1.0])
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)

        # Setup projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(FOV, WIDTH / HEIGHT, NEAR, FAR)
        glMatrixMode(GL_MODELVIEW)

        # Generate and bind texture atlas
        if not hasattr(self, "atlas_surf"):
            self.atlas_surf = generate_texture_atlas()
        if not hasattr(self, "atlas_id"):
            self.atlas_id = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, self.atlas_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

        atlas_data = pygame.image.tostring(self.atlas_surf, "RGBA", False)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA,
            self.atlas_surf.get_width(),
            self.atlas_surf.get_height(),
            0, GL_RGBA, GL_UNSIGNED_BYTE, atlas_data
        )

    def capture(self, state):
        """Capture/release mouse."""
        self.mouse_cap = state
        pygame.mouse.set_visible(not state)
        pygame.event.set_grab(state)
        if state:
            pygame.mouse.set_pos(WIDTH // 2, HEIGHT // 2)

    def sky(self):
        """Get sky color based on day/night cycle."""
        t = self.day
        if t < 0.25:
            f = t / 0.25
            return (0.05 + 0.5 * f, 0.05 + 0.62 * f, 0.15 + 0.68 * f)
        if t < 0.5:
            return (0.52, 0.68, 0.85)
        if t < 0.75:
            f = (t - 0.5) / 0.25
            return (0.52 - 0.4 * f, 0.68 - 0.55 * f, 0.85 - 0.65 * f)
        return (0.02, 0.02, 0.10)

    def _srects(self, menu=False):
        """Get UI rectangle positions for settings."""
        SW, SH, SX, SY = 480, 480, WIDTH // 2 - 240, HEIGHT // 2 - 240
        if menu:
            return {
                "fps": pygame.Rect(SX + 20, SY + 75, SW - 40, 48),
                "fog": pygame.Rect(SX + 20, SY + 130, SW - 40, 48),
                "qual": pygame.Rect(SX + 20, SY + 185, SW - 40, 48),
                "limit": pygame.Rect(SX + 20, SY + 240, SW - 40, 48),
                "vsync": pygame.Rect(SX + 20, SY + 295, SW - 40, 48),
                "fs": pygame.Rect(SX + 20, SY + 350, SW - 40, 48),
                "quit": pygame.Rect(SX + 20, SY + SH - 65, SW - 40, 45),
                "version": pygame.Rect(10, HEIGHT - 30, 300, 25),
            }

        ob = SY + 64
        py3 = ob + 3 * 56 + 8
        return {
            "fps": pygame.Rect(SX + 12, ob, SW - 24, 46),
            "fog": pygame.Rect(SX + 12, ob + 56, SW - 24, 46),
            "qual": pygame.Rect(SX + 12, ob + 112, SW - 24, 46),
            "limit": pygame.Rect(SX + 12, ob + 168, SW - 24, 46),
            "vsync": pygame.Rect(SX + 12, ob + 224, SW - 24, 46),
            "fs": pygame.Rect(SX + 12, ob + 280, SW - 24, 46),
            "low": pygame.Rect(SX + 12, py3 + 22, 190, 38),
            "high": pygame.Rect(SX + 222, py3 + 22, 190, 46),
            "quit": pygame.Rect(SX + 12, SY + SH - 52, SW - 24, 40),
        }

    def handle_events(self):
        """Handle all input events."""
        for e in pygame.event.get():
            if e.type == QUIT:
                self.save_game()
                self.running = False

            elif e.type == KEYDOWN:
                if e.key == K_F11:
                    self._toggle_fs()

                if self.state == "WORLD_CREATE":
                    if e.key == K_ESCAPE:
                        self.state = "TITLE"
                    elif e.key == K_BACKSPACE:
                        self.temp_name = self.temp_name[:-1]
                    elif e.key == K_RETURN and 0 < len(self.temp_name):
                        self.start_new_game(self.temp_name)
                    elif len(self.temp_name) < 16 and (e.unicode.isalnum() or e.unicode == " "):
                        self.temp_name += e.unicode

                elif self.state == "DEV_MENU":
                    if e.key == K_ESCAPE:
                        self.state = "TITLE"

                elif self.state == "PLAYING":
                    if e.key == K_ESCAPE:
                        if self.show_inv:
                            self.show_inv = False
                        elif self.show_settings:
                            self.show_settings = False
                        else:
                            self.show_settings = True
                        self.capture(not self.show_settings)

                    elif e.key == K_e and not self.show_settings:
                        self.show_inv = not self.show_inv
                        self.capture(not self.show_inv)

                    elif e.key in [K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_9]:
                        if self.show_inv:
                            idx = e.key - K_1
                            if idx < len(RECIPES):
                                self._craft(idx)
                        else:
                            self.player.selected_slot = e.key - K_1

            elif e.type == MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                cx, cy = WIDTH // 2, HEIGHT // 2

                if self.state == "TITLE":
                    vr = self._srects(menu=True)["version"]
                    if vr.collidepoint(mx, my):
                        self.dev_clicks += 1
                        if self.dev_clicks >= 5:
                            self.state = "DEV_MENU"
                            self.dev_clicks = 0
                            self.dev_active = True
                    else:
                        self.dev_clicks = 0

                    if cx - 200 < mx < cx + 200:
                        if -40 < my - cy < 10:
                            self.state = "WORLD_CREATE"
                            self.temp_name = ""
                        elif 30 < my - cy < 80 and self.save_exists:
                            self.state = "WORLD_SELECT"
                            self.saves, _ = self._refresh_saves()
                        elif 100 < my - cy < 150:
                            self.state = "SETTINGS_MENU"
                        elif 170 < my - cy < 220:
                            self.running = False

                elif self.state == "DEV_MENU":
                    if my > HEIGHT - 80:
                        self.state = "TITLE"
                    elif cy - 150 < my < cy + 150 and cx - 150 < mx < cx + 150:
                        val = (mx - (cx - 150)) / 300.0
                        if cy - 130 < my < cy - 90:
                            self.dev_fps = int(1 + val * 999)
                        elif cy - 70 < my < cy - 30:
                            self.dev_rd = int(1 + val * 12)
                            if self.world:
                                self.world.render_dist = self.dev_rd
                        elif cy - 10 < my < cy + 30:
                            self.dev_fov = int(30 + val * 120)
                            glMatrixMode(GL_PROJECTION)
                            glLoadIdentity()
                            gluPerspective(self.dev_fov, WIDTH / HEIGHT, NEAR, FAR)
                            glMatrixMode(GL_MODELVIEW)
                        elif cy + 50 < my < cy + 70:
                            self.dev_fly = not self.dev_fly
                        elif cy + 90 < my < cy + 130:
                            self.dev_speed = 0.5 + val * 4.5

                elif self.state == "WORLD_SELECT":
                    for i, s in enumerate(self.saves):
                        if cx - 225 < mx < cx + 225 and 120 + i * 55 < my < 120 + i * 55 + 48:
                            self.load_game(s)
                            break
                    if cx - 225 < mx < cx + 225 and HEIGHT - 80 < my < HEIGHT - 32:
                        self.state = "TITLE"

                elif self.state == "WORLD_CREATE":
                    if cx - 150 < mx < cx + 150 and cy + 100 < my < cy + 150 and 0 < len(self.temp_name):
                        self.start_new_game(self.temp_name)
                    if my > HEIGHT - 60:
                        self.state = "TITLE"

                elif self.state == "SETTINGS_MENU":
                    r = self._srects(menu=True)
                    if r["fps"].collidepoint(mx, my):
                        self.show_fps = not self.show_fps
                    elif r["fog"].collidepoint(mx, my):
                        self.fog = not self.fog
                    elif r["qual"].collidepoint(mx, my):
                        self.high_q = not self.high_q
                        self._apply_q()
                    elif r["limit"].collidepoint(mx, my):
                        self.fps_idx = (self.fps_idx + 1) % len(self.fps_options)
                    elif r["vsync"].collidepoint(mx, my):
                        self.vsync = not self.vsync
                        pygame.display.set_mode(
                            (WIDTH, HEIGHT),
                            OPENGL | DOUBLEBUF | HWSURFACE,
                            vsync=int(self.vsync),
                        )
                    elif r["fs"].collidepoint(mx, my):
                        self._toggle_fs()
                    elif r["quit"].collidepoint(mx, my):
                        self.state = "TITLE"

                elif self.state == "PLAYING":
                    if self.show_settings:
                        r = self._srects()
                        if r["fps"].collidepoint(mx, my):
                            self.show_fps = not self.show_fps
                        elif r["fog"].collidepoint(mx, my):
                            self.fog = not self.fog
                        elif r["qual"].collidepoint(mx, my):
                            self.high_q = not self.high_q
                            self._apply_q()
                        elif r["limit"].collidepoint(mx, my):
                            self.fps_idx = (self.fps_idx + 1) % len(self.fps_options)
                        elif r["vsync"].collidepoint(mx, my):
                            self.vsync = not self.vsync
                            pygame.display.set_mode(
                                (WIDTH, HEIGHT),
                                OPENGL | DOUBLEBUF | HWSURFACE,
                                vsync=int(self.vsync),
                            )
                        elif r["fs"].collidepoint(mx, my):
                            self._toggle_fs()
                        elif r["low"].collidepoint(mx, my):
                            self.high_q = False
                            self._apply_q()
                        elif r["high"].collidepoint(mx, my):
                            self.high_q = True
                            self._apply_q()
                        elif r["quit"].collidepoint(mx, my):
                            self.save_game()
                            self.state = "TITLE"
                            self.capture(False)
                            self.save_exists = True
                            self.saves, self.save_exists = self._refresh_saves()
                        return

                    if not self.mouse_cap and not self.show_inv:
                        self.capture(True)

                    if self.mouse_cap and e.button == 1:
                        # Attack animals
                        for a in self.animals:
                            if not a.alive:
                                continue
                            dist = math.sqrt((self.player.x - a.x) ** 2 + (self.player.y - a.y) ** 2 + (self.player.z - a.z) ** 2)
                            if dist < 3.5:
                                if a.hit(4):
                                    drops = random.randint(1, 3)
                                    for _ in range(8):
                                        self.particles.append(Particle(a.x, a.y, a.z, a.drop))
                                    self.player.add_item(a.drop, drops)
                                break

                    elif self.mouse_cap and e.button == 3:
                        # Place block or eat
                        sb = self.player.selected_block()
                        if sb == MEAT and self.player.hunger < 20:
                            if self.player.remove_item(MEAT):
                                self.player.hunger = min(20, self.player.hunger + 4)
                        else:
                            bpos, prev, _ = self.player.raycast(self.world)
                            bid = self.player.selected_block()
                            if bpos and prev and bid != AIR:
                                bx, by, bz = prev
                                px, py, pz = self.player.x, self.player.y, self.player.z
                                foot = int(math.floor(py - 1.8))
                                head = int(math.floor(py + 0.15))
                                ox, oz = int(math.floor(px)), int(math.floor(pz))
                                if (
                                    not (bx in range(ox - 1, ox + 2) and foot <= by <= head and bz in range(oz - 1, oz + 2))
                                    and self.player.remove_item(bid)
                                ):
                                    self.world.set_block(*prev, bid)

            elif e.type == MOUSEBUTTONUP:
                if self.player and e.button == 1:
                    self.player.mining_block = None
                    self.player.mining_progress = 0.0
                    self.player.mining_time = 0.0

            elif e.type == MOUSEWHEEL and self.player:
                self.player.selected_slot = (self.player.selected_slot - e.y) % len(self.player.hotbar)

            elif e.type == MOUSEMOTION and self.mouse_cap and self.player:
                dx, dy = e.rel
                self.player.yaw -= dx * MOUSE_SENS
                self.player.pitch = max(-89, min(89, self.player.pitch - dy * MOUSE_SENS))

    def _toggle_fs(self):
        """Toggle fullscreen."""
        global WIDTH, HEIGHT
        self.fullscreen = not self.fullscreen
        flags = OPENGL | DOUBLEBUF | HWSURFACE

        if self.fullscreen:
            try:
                d_sizes = pygame.display.get_desktop_sizes()
                target_w, target_h = d_sizes[0]
            except (AttributeError, IndexError):
                info = pygame.display.Info()
                target_w, target_h = info.current_w, info.current_h

            os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
            WIDTH, HEIGHT = target_w, target_h
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags | NOFRAME)
        else:
            WIDTH, HEIGHT = 1280, 720
            os.environ["SDL_VIDEO_WINDOW_POS"] = ""
            os.environ["SDL_VIDEO_CENTERED"] = "1"
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)

        self.hud_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.hud.surf = self.hud_surf
        if hasattr(self, "_htex"):
            glDeleteTextures([self._htex])
            delattr(self, "_htex")
        self.hud.last_state = None
        self._init_gl()

    def _apply_q(self):
        """Apply quality settings."""
        if self.world:
            self.world.render_dist = 4 if self.high_q else 2

    def _craft(self, recipe_idx):
        """Execute a crafting recipe."""
        if recipe_idx >= len(RECIPES):
            return

        inp, need, out, ocnt = RECIPES[recipe_idx]
        ned = {}
        for b in inp:
            ned[b] = ned.get(b, 0) + 1

        if all(self.player.inventory.get(b, 0) >= n for b, n in ned.items()):
            for b, n in ned.items():
                self.player.remove_item(b, n)
            self.player.add_item(out, ocnt)

    def update(self):
        """Update game state."""
        dt = min(self.dt, 0.05)

        # Menu states
        if self.state in ["TITLE", "WORLD_SELECT", "WORLD_CREATE", "SETTINGS_MENU", "DEV_MENU"]:
            return

        # Loading state
        if self.loading:
            cx, cz = self.world.w2c(self.player.x, self.player.z)
            self.world.ensure_chunks(cx, cz)
            for dx, dz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                self.world.ensure_chunks(cx + dx, cz + dz)

            self.progress += dt * 0.4
            if self.progress >= 1.0:
                for _ in range(5):
                    for dx, dz in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]:
                        self.world.ensure_chunks(cx + dx, cz + dz)
                self.progress = 1.0
                self.loading = False
                self.state = "PLAYING"
                self.capture(True)
            return

        # Update game
        keys = pygame.key.get_pressed()
        self.day = (self.day + dt / 120.0) % 1.0

        # Update lighting
        ang = self.day * 2 * math.pi
        glLightfv(GL_LIGHT0, GL_POSITION, [math.cos(ang) * 200, math.sin(ang) * 200, 50, 0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [max(0.2, abs(math.sin(ang))) * 0.6] * 3 + [1])

        if not self.show_inv and not self.show_settings:
            self.player.update(dt, keys, self.world, self)

            # Failsafe
            if self.player.y < -1:
                for sy in range(WORLD_HEIGHT - 1, 0, -1):
                    if self.world.get_block(self.player.x, sy, self.player.z) not in PASSABLE:
                        self.player.y = sy + 1.9
                        self.player.vy = 0
                        break

        # Mining
        if self.mouse_cap and pygame.mouse.get_pressed()[0]:
            bpos, _, bid = self.player.raycast(self.world)
            if bpos:
                if self.player.mining_block != bpos:
                    self.player.mining_block = bpos
                    self.player.mining_time = 0.0
                    self.player.mining_progress = 0.0
                self.player.mining_time += dt
                hard = BLOCK_HARDNESS.get(bid, 1.0)
                self.player.mining_progress = min(1.0, self.player.mining_time / hard)
                if self.player.mining_progress >= 1.0:
                    self.world.set_block(*bpos, AIR)
                    self.player.add_item(bid)
                    for _ in range(14):
                        self.particles.append(Particle(*bpos, bid))
                    self.player.mining_block = None
                    self.player.mining_progress = 0.0
                    self.player.mining_time = 0.0
            else:
                self.player.mining_block = None
                self.player.mining_progress = 0.0
        else:
            self.player.mining_block = None
            self.player.mining_progress = 0.0
            self.player.mining_time = 0.0

        # Update entities
        for a in self.animals:
            if a.alive:
                a.update(dt, self.world)

        cx, cz = self.world.w2c(self.player.x, self.player.z)
        self.world.ensure_chunks(cx, cz)

        # Update particles
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update(dt)

    def render(self):
        """Render the game."""
        sk = self.sky()

        if self.state in ["TITLE", "WORLD_SELECT", "WORLD_CREATE", "SETTINGS_MENU", "LOADING", "DEV_MENU"]:
            glClearColor(0, 0, 0, 1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self._hud()
            return

        in_water = self.world.get_block(self.player.x, self.player.y + 0.1, self.player.z) == WATER
        clr = [0.1, 0.3, 0.7] if in_water else sk
        glClearColor(*clr, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glLoadIdentity()
        dx, dy, dz = self.player.look_dir()
        ey = self.player.y + 0.1
        gluLookAt(
            self.player.x, ey, self.player.z,
            self.player.x + dx, ey + dy, self.player.z + dz,
            0, 1, 0
        )

        # Fog
        if self.fog or in_water:
            glEnable(GL_FOG)
            glFogi(GL_FOG_MODE, GL_LINEAR)
            fog_col = [0.1, 0.3, 0.7, 1.0] if in_water else [*sk, 1.0]
            glFogfv(GL_FOG_COLOR, fog_col)
            if in_water:
                glFogf(GL_FOG_START, 0.0)
                glFogf(GL_FOG_END, 12.0)
            else:
                rd = self.world.render_dist
                glFogf(GL_FOG_START, rd * CHUNK_SIZE * 0.45)
                glFogf(GL_FOG_END, rd * CHUNK_SIZE * 0.90)
        else:
            glDisable(GL_FOG)

        # Render world
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.atlas_id)
        self.world.render(self.player.x, self.player.z)
        glDisable(GL_TEXTURE_2D)

        # Render animals
        glDisable(GL_LIGHTING)
        for a in self.animals:
            if a.alive:
                a.draw()
        glEnable(GL_LIGHTING)

        # Block outline
        bpos, _, _ = self.player.raycast(self.world)
        if bpos:
            self._outline(*bpos)

        # Particles
        glDisable(GL_LIGHTING)
        for p in self.particles:
            p.draw()
        glEnable(GL_LIGHTING)

        # HUD
        self._hud()

    def _outline(self, x, y, z):
        """Draw block outline."""
        glDisable(GL_LIGHTING)
        glColor4f(0, 0, 0, 0.8)
        glLineWidth(2.0)
        e = 0.004

        v = [
            (x - e, y + 1 + e, z + 1 + e),
            (x + 1 + e, y + 1 + e, z + 1 + e),
            (x + 1 + e, y + 1 + e, z - e),
            (x - e, y + 1 + e, z - e),
            (x - e, y - e, z - e),
            (x + 1 + e, y - e, z - e),
            (x + 1 + e, y - e, z + 1 + e),
            (x - e, y - e, z + 1 + e),
            (x + 1 + e, y - e, z - e),
            (x + 1 + e, y + 1 + e, z - e),
            (x + 1 + e, y + 1 + e, z + 1 + e),
            (x + 1 + e, y - e, z + 1 + e),
            (x - e, y - e, z + 1 + e),
            (x - e, y + 1 + e, z + 1 + e),
            (x - e, y + 1 + e, z - e),
            (x - e, y - e, z - e),
            (x - e, y - e, z + 1 + e),
            (x + 1 + e, y - e, z + 1 + e),
            (x + 1 + e, y + 1 + e, z + 1 + e),
            (x - e, y + 1 + e, z + 1 + e),
            (x + 1 + e, y - e, z - e),
            (x - e, y - e, z - e),
            (x - e, y + 1 + e, z - e),
            (x + 1 + e, y + 1 + e, z - e),
        ]

        for i in range(0, len(v), 4):
            glBegin(GL_LINE_LOOP)
            for j in range(i, i + 4):
                glVertex3fv(v[j])
            glEnd()

        glLineWidth(1.0)
        glEnable(GL_LIGHTING)

    def _hud(self):
        """Render HUD."""
        if self.hud.needs_redraw(self):
            self.hud.draw(self, self.loading, self.progress)
            td = pygame.image.tostring(self.hud_surf, "RGBA", True)
            if not hasattr(self, "_htex"):
                self._htex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self._htex)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WIDTH, HEIGHT, 0, GL_RGBA, GL_UNSIGNED_BYTE, td)

        if hasattr(self, "_htex"):
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            glOrtho(0, WIDTH, 0, HEIGHT, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self._htex)
            glColor4f(1, 1, 1, 1)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0)
            glVertex2f(0, 0)
            glTexCoord2f(1, 0)
            glVertex2f(WIDTH, 0)
            glTexCoord2f(1, 1)
            glVertex2f(WIDTH, HEIGHT)
            glTexCoord2f(0, 1)
            glVertex2f(0, HEIGHT)
            glEnd()
            glDisable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)
            glPopMatrix()
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)

    def run(self):
        """Main game loop."""
        print("\nVOXEL WILDS — Survival & Crafting")
        while self.running:
            target = self.dev_fps if self.state == "PLAYING" and self.dev_active else self.fps_options[self.fps_idx]
            self.dt = self.clock.tick(target if target > 0 else 0) / 1000.0
            self.handle_events()
            self.update()
            self.render()
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
