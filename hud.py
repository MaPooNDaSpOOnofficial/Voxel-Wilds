"""
HUD (Heads-Up Display) system for Voxel Wilds

Renders the user interface including inventory, crafting, settings menus,
and in-game HUD elements.
"""

import time
import math
import pygame
from pygame.locals import *
from config import (
    WIDTH, HEIGHT, BLOCK_NAMES, RECIPES, AIR, CRAFT_TABLE, MEAT,
    VERSION
)
from textures import get_block_colors


class HUD:
    """Renders all user interface elements."""

    def __init__(self, surf):
        """
        Initialize HUD.
        
        Args:
            surf: pygame.Surface for HUD rendering
        """
        self.surf = surf
        pygame.font.init()

        # Fonts
        self.fc = pygame.font.SysFont("sans-serif", 24, bold=True)
        self.fl = pygame.font.SysFont("sans-serif", 32, bold=True)
        self.fs = pygame.font.SysFont("sans-serif", 18, bold=True)
        self.ft = pygame.font.SysFont("monospace", 13)

        self.last_state = None
        self.last_mouse = (0, 0)

    def needs_redraw(self, game):
        """
        Check if HUD needs redrawing.
        
        Optimizes by only redrawing when state changes.
        """
        if game.state in ["TITLE", "WORLD_SELECT", "WORLD_CREATE", "SETTINGS_MENU", "DEV_MENU"]:
            return True
        if game.loading:
            return True

        p = game.player
        mx, my = pygame.mouse.get_pos()
        mstate = (mx, my) if (game.show_inv or game.show_settings) else (0, 0)

        state = (
            game.state,
            p.health,
            p.hunger,
            p.selected_slot,
            game.show_inv,
            game.show_settings,
            p.inventory.copy(),
            p.mining_progress,
            game.show_fps,
            game.fog,
            game.high_q,
            game.vsync,
            game.fps_idx,
            game.fullscreen,
            mstate,
            int(time.time() * 5) % 2,  # Cursor blink
        )

        if state != self.last_state:
            self.last_state = state
            return True
        return False

    def box(self, col, rect, alpha=200, border=None, bw=2, radius=8):
        """Draw a rounded box."""
        s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        pygame.draw.rect(s, (*col[:3], alpha), (0, 0, rect[2], rect[3]), border_radius=radius)
        self.surf.blit(s, (rect[0], rect[1]))
        if border:
            pygame.draw.rect(self.surf, border, rect, bw, border_radius=radius)

    def btn(self, text, rect, mx, my, col=(50, 50, 60), hcol=(70, 70, 100), tcol=(255, 255, 255), active=True):
        """Draw a button."""
        hover = rect.collidepoint(mx, my) and active
        self.box(hcol if hover else col, rect, 240 if hover else 200, (255, 255, 255) if hover else (80, 80, 90), bw=2 if hover else 1)
        tc = tcol if active else (100, 100, 110)
        text_size = self.fs.size(text)
        self.stext(self.fs, text, tc, rect.x + rect.width // 2 - text_size[0] // 2, rect.y + rect.height // 2 - 10)
        return hover

    def stext(self, font, text, col, x, y, shadow=True):
        """Draw text with optional shadow."""
        if shadow:
            self.surf.blit(font.render(text, True, (0, 0, 0)), (x + 1, y + 1))
        self.surf.blit(font.render(text, True, col), (x, y))

    def draw(self, game, loading=False, progress=0.0):
        """
        Render the HUD.
        
        Args:
            game: Game instance
            loading: Whether game is loading
            progress: Loading progress (0-1)
        """
        self.surf.fill((0, 0, 0, 0))
        W, H = self.surf.get_size()
        s = game.state

        if s == "TITLE":
            self._draw_title(W, H, game.save_exists)
            return
        if s == "WORLD_SELECT":
            self._draw_worlds(W, H, game.saves)
            return
        if s == "WORLD_CREATE":
            self._draw_create(W, H, game.temp_name)
            return
        if s == "SETTINGS_MENU":
            self._draw_settings(W, H, game.show_fps, game.fog, game.high_q, game, menu=True)
            return
        if s == "DEV_MENU":
            self._draw_dev(W, H, game)
            return
        if loading:
            self._draw_splash(W, H, progress)
            return

        # In-game HUD
        player = game.player
        cx, cy = W // 2, H // 2

        # Crosshair
        pygame.draw.line(self.surf, (255, 255, 255, 120), (cx - 12, cy), (cx + 12, cy), 2)
        pygame.draw.line(self.surf, (255, 255, 255, 120), (cx, cy - 12), (cx, cy + 12), 2)

        # Hotbar
        sz, nb = 56, len(player.hotbar)
        hx, hy = W // 2 - nb * sz // 2, H - sz - 12
        for i, bid in enumerate(player.hotbar):
            sel = i == player.selected_slot
            bg = (255, 180, 0) if sel else (30, 30, 35)
            self.box(bg, (hx + i * sz, hy, sz - 4, sz - 4), 220 if sel else 160, (255, 255, 255) if sel else (60, 60, 70))
            if bid != AIR:
                c = get_block_colors(bid)[0]
                bc = tuple(int(v * 255) for v in c)
                pygame.draw.rect(self.surf, bc, (hx + i * sz + 8, hy + 8, sz - 20, sz - 20), border_radius=4)
                cnt = player.inventory.get(bid, 0)
                if cnt > 0:
                    self.surf.blit(
                        self.ft.render(str(cnt), True, (255, 255, 255)),
                        (hx + i * sz + sz - 22, hy + sz - 24),
                    )

        # Block name
        sb = player.selected_block()
        if sb != AIR:
            name = BLOCK_NAMES.get(sb, "?").upper()
            name_size = self.fl.size(name)
            self.stext(self.fl, name, (255, 255, 255), W // 2 - name_size[0] // 2, H - sz - 55)

        # Health & Hunger bars
        for i in range(10):
            x2, y2 = 20 + i * 24, H - 120
            pygame.draw.circle(self.surf, (220, 40, 40) if player.health > i * 2 else (40, 10, 10), (x2 + 8, y2 + 8), 8)
            pygame.draw.circle(self.surf, (180, 100, 20) if player.hunger > i * 2 else (30, 20, 5), (x2 + 8, y2 + 34), 8)

        # Mining progress
        if player.mining_progress > 0:
            bw, bh, bx, by = 260, 12, W // 2 - 130, H - sz - 130
            self.box((20, 20, 25), (bx, by, bw, bh), 200, (80, 80, 90))
            self._draw_rainbow_bar(bx + 2, by + 2, int((bw - 4) * player.mining_progress), bh - 4)

        # FPS counter
        if game.show_fps:
            t = f"FPS: {game.clock.get_fps():.0f}"
            t_size = self.ft.size(t)
            self.stext(self.ft, t, (150, 150, 160), W - t_size[0] - 20, 20)

        # Menus
        if game.show_inv:
            self._draw_inv(player, W, H)
        if game.show_settings:
            self._draw_settings(W, H, game.show_fps, game.fog, game.high_q, game)

    def _draw_worlds(self, W, H, saves):
        """Draw world select screen."""
        self._bg_gradient(W, H)
        cx, cy = W // 2, H // 2
        mx, my = pygame.mouse.get_pos()

        self.stext(self.fl, "RESUME YOUR ADVENTURE", (255, 255, 255), cx - self.fl.size("RESUME YOUR ADVENTURE")[0] // 2, 60)
        bw, bh = 480, 52
        for i, s in enumerate(saves):
            bx, by = cx - bw // 2, 140 + i * 65
            name = s.replace(".json", "")
            self.btn(name.upper(), pygame.Rect(bx, by, bw, bh), mx, my, col=(35, 35, 42))
        self.btn("BACK TO MENU", pygame.Rect(cx - bw // 2, H - 90, bw, bh), mx, my, col=(60, 30, 30))

    def _draw_create(self, W, H, name):
        """Draw world creation screen."""
        self._bg_gradient(W, H)
        cx, cy = W // 2, H // 2
        mx, my = pygame.mouse.get_pos()

        self.stext(self.fl, "FOUND A NEW WORLD", (255, 255, 255), cx - self.fl.size("FOUND A NEW WORLD")[0] // 2, 150)
        self.box((20, 20, 30), (cx - 180, cy - 35, 360, 60), 255, (100, 255, 150), radius=10)
        self.stext(
            self.fs,
            name + ("_" if int(time.time() * 2) % 2 else ""),
            (255, 255, 255),
            cx - 160,
            cy - 15,
            shadow=False,
        )
        self.stext(self.ft, "Enter World Name (Alphanumeric)", (130, 130, 145), cx - 160, cy + 35)

        bw, bh = 360, 52
        valid = 0 < len(name) <= 16 and name.isalnum()
        self.btn("INITIALIZE WORLD", pygame.Rect(cx - bw // 2, cy + 110, bw, bh), mx, my, col=(40, 80, 60) if valid else (30, 30, 35), active=valid)
        self.stext(self.ft, "PRESS ESC TO ABANDON", (110, 110, 120), cx - self.ft.size("PRESS ESC TO ABANDON")[0] // 2, H - 40)

    def _bg_gradient(self, W, H):
        """Draw background gradient."""
        for i in range(H):
            c = max(10, min(50, int(50 - (i / H) * 40)))
            pygame.draw.line(self.surf, (c, c, c + 12), (0, i), (W, i))

    def _draw_title(self, W, H, save_exists):
        """Draw title screen."""
        self._bg_gradient(W, H)
        cx, cy = W // 2, H // 2
        mx, my = pygame.mouse.get_pos()

        fl = pygame.font.SysFont("sans-serif", 130, bold=True)
        t1 = fl.render("VOXEL ", True, (255, 255, 255))
        hue = (int(time.time() * 50) % 360)
        t2c = pygame.Color(0, 0, 0)
        t2c.hsva = (hue, 80, 100, 100)
        t2 = fl.render("WILDS", True, (t2c.r, t2c.g, t2c.b))
        tw = t1.get_width() + t2.get_width()
        tx = cx - tw // 2
        self.surf.blit(t1, (tx, cy - 230))
        self.surf.blit(t2, (tx + t1.get_width(), cy - 230))

        bw, bh = 420, 52
        btns = [
            ("CREATE NEW WORLD", True),
            ("LOAD SAVED WORLD", save_exists),
            ("SYSTEM SETTINGS", True),
            ("QUIT TO DESKTOP", True),
        ]
        for i, (text, active) in enumerate(btns):
            bx, by = cx - bw // 2, cy - 40 + i * 75
            self.btn(text, pygame.Rect(bx, by, bw, bh), mx, my, col=(40, 40, 45) if active else (25, 25, 28))

        self.stext(self.ft, f"VOXEL WILDS v{VERSION} - THE ORE UPDATE", (110, 110, 120), 20, H - 30)

    def _draw_splash(self, W, H, progress):
        """Draw loading splash screen."""
        self._bg_gradient(W, H)
        cx, cy = W // 2

        self._draw_rainbow_ring(cx, cy, 115, progress, 18, brightness=25, alpha=60)
        self._draw_rainbow_ring(cx, cy, 110, progress, 10, brightness=100, alpha=255)

        font_main = pygame.font.SysFont("sans-serif", 85, bold=True)
        t1 = font_main.render("VOXEL ", True, (255, 255, 255))
        hue = (int(time.time() * 100) % 360)
        t2_col = pygame.Color(0, 0, 0)
        t2_col.hsva = (hue, 80, 100, 100)
        t2 = font_main.render("WILDS", True, (t2_col.r, t2_col.g, t2_col.b))
        tw = t1.get_width() + t2.get_width()
        tx = cx - tw // 2
        self.surf.blit(t1, (tx, cy - 200))
        self.surf.blit(t2, (tx + t1.get_width(), cy - 200))

        pct = self.fl.render(f"{int(progress * 100)}", True, (255, 255, 255))
        self.surf.blit(pct, (cx - pct.get_width() // 2, cy - 12))

        load_t = self.ft.render("SYNCHRONIZING WORLD DATA...", True, (140, 140, 160))
        self.surf.blit(load_t, (cx - load_t.get_width() // 2, cy + 160))

    def _draw_rainbow_bar(self, x, y, w, h):
        """Draw a horizontal rainbow gradient bar."""
        if w <= 0:
            return
        for i in range(w):
            hue = (i / 260.0 * 360) % 360
            col = pygame.Color(0, 0, 0)
            col.hsva = (hue, 80, 100, 100)
            pygame.draw.line(self.surf, (col.r, col.g, col.b), (x + i, y), (x + i, y + h))

    def _draw_rainbow_ring(self, cx, cy, r, progress, width, brightness, alpha):
        """Draw a circular rainbow progress indicator."""
        steps = int(360 * progress)
        for i in range(steps):
            rad = math.radians(i - 90)
            col = pygame.Color(0, 0, 0)
            col.hsva = (i % 360, 75, brightness, 100)
            pygame.draw.circle(
                self.surf,
                (col.r, col.g, col.b, alpha),
                (int(cx + math.cos(rad) * r), int(cy + math.sin(rad) * r)),
                width // 2,
            )

    def _draw_inv(self, player, W, H):
        """Draw inventory and crafting menu."""
        IX, IY, IW, IH = W // 2 - 400, H // 2 - 260, 800, 520
        mx, my = pygame.mouse.get_pos()

        self.box((10, 10, 20), (IX, IY, IW, IH), 250, (100, 100, 120), radius=12)
        self.stext(self.fl, "SURVIVAL GEAR", (255, 255, 255), IX + 30, IY + 25)

        # Left panel: Inventory
        self.box((30, 30, 40), (IX + 25, IY + 75, 370, 410), 180, (60, 60, 70))
        self.stext(self.fs, "INVENTORY", (150, 150, 180), IX + 35, IY + 85)

        items = [(b, c) for b, c in player.inventory.items() if c > 0 and b != AIR]
        sw, sh, cols = 85, 85, 4
        for idx, (bid, cnt) in enumerate(items):
            r, c = divmod(idx, cols)
            x, y = IX + 40 + c * sw, IY + 120 + r * sh
            rect = pygame.Rect(x, y, sw - 10, sh - 10)
            hov = rect.collidepoint(mx, my)
            bc = tuple(int(v * 255) for v in get_block_colors(bid)[0])
            self.box((50, 50, 65) if hov else (40, 40, 50), rect, 200 if hov else 160, (255, 255, 255) if hov else (70, 70, 85))
            pygame.draw.rect(self.surf, bc, (x + 15, y + 15, sw - 40, sh - 40), border_radius=8)
            self.stext(self.ft, str(cnt), (255, 255, 255), x + sw - 25, y + sh - 25)
            if hov:
                self.stext(self.ft, BLOCK_NAMES.get(bid, "?").upper(), (255, 255, 255), IX + 40, IY + IH - 30)

        # Right panel: Crafting
        self.box((30, 30, 40), (IX + 405, IY + 75, 370, 410), 180, (60, 60, 70))
        self.stext(self.fs, "CRAFTING", (150, 255, 180), IX + 415, IY + 85)

        for ri, (inp, need, out, ocnt) in enumerate(RECIPES):
            ry = IY + 120 + ri * 65
            ned = {}
            for b in inp:
                ned[b] = ned.get(b, 0) + 1

            can = all(player.inventory.get(b, 0) >= n for b, n in ned.items())
            rect = pygame.Rect(IX + 415, ry, 350, 60)
            hov = rect.collidepoint(mx, my)
            self.box(
                (50, 60, 50) if hov and can else ((40, 40, 45) if can else (30, 30, 35)),
                rect,
                180,
                (255, 255, 255) if hov else (60, 70, 60),
            )
            self.stext(self.fs, f"{BLOCK_NAMES.get(out, '?')} x{ocnt}", (255, 255, 255) if can else (100, 100, 110), IX + 430, ry + 15)

            # Requirements
            req_txt = " + ".join([f"{BLOCK_NAMES.get(b, '?')[:3]}x{n}" for b, n in ned.items()])
            self.stext(self.ft, f"NEED: {req_txt}", (120, 255, 150) if can else (120, 60, 60), IX + 430, ry + 38)

            if hov:
                self.stext(self.ft, f"PRESS [{ri + 1}] TO CRAFT", (255, 255, 255), IX + 415, IY + IH - 30)

    def _draw_dev(self, W, H, game):
        """Draw developer console."""
        self._bg_gradient(W, H)
        cx, cy = W // 2, H // 2
        self.stext(self.fl, "DEVELOPER CONSOLE", (255, 100, 255), cx - 110, 50)

        opts = [
            (f"CUSTOM FPS LIMIT: {game.dev_fps}", (game.dev_fps - 1) / 999.0),
            (f"RENDER DISTANCE (CHUNKS): {game.dev_rd}", (game.dev_rd - 1) / 12.0),
            (f"FIELD OF VIEW: {game.dev_fov}", (game.dev_fov - 30) / 120.0),
            (f"FLY MODE: {'ENABLED' if game.dev_fly else 'DISABLED'}", 1.0 if game.dev_fly else 0.0),
            (f"SPEED MULTIPLIER: {game.dev_speed:.1f}x", (game.dev_speed - 0.5) / 4.5),
        ]

        for i, (lbl, val) in enumerate(opts):
            oy = cy - 130 + i * 60
            self.stext(self.ft, lbl, (200, 200, 220), cx - 150, oy - 20)
            self.box((30, 30, 40), (cx - 150, oy, 300, 10), 200, (80, 80, 90))
            self.box((255, 100, 255), (cx - 150, oy, int(300 * val), 10), 255)

        self.stext(self.ft, "CLICK BARS TO ADJUST - ESC/BACK TO RETURN", (100, 100, 110), cx - 140, H - 40)

    def _draw_settings(self, W, H, show_fps, fog, quality, game_ref=None, menu=False):
        """Draw settings menu."""
        SW, SH, SX, SY = 500, 500, W // 2 - 250, H // 2 - 250
        mx, my = pygame.mouse.get_pos()

        self.box((10, 10, 20), (SX, SY, SW, SH), 252, (110, 110, 140), radius=12)
        self.stext(self.fl, "SETTINGS", (255, 255, 255), SX + 30, SY + 30)

        opts = [("PERFORMANCE OVERLAY", show_fps), ("VOLUMETRIC FOG", fog), ("HI-RES TEXTURES", quality)]
        if game_ref:
            fps_val = "UNLTD" if game_ref.fps_options[game_ref.fps_idx] == 0 else str(game_ref.fps_options[game_ref.fps_idx])
            opts += [("FRAME LIMIT", fps_val), ("V-SYNC", game_ref.vsync), ("FULLSCREEN", game_ref.fullscreen)]

        for i, (lbl, state) in enumerate(opts):
            oy = SY + 85 + i * 58
            rect = pygame.Rect(SX + 25, oy, SW - 50, 52)
            hov = rect.collidepoint(mx, my)
            self.box((40, 40, 55) if hov else (30, 30, 40), rect, 180, (100, 100, 120) if hov else (70, 70, 90))
            self.stext(self.fs, lbl, (220, 220, 230), SX + 40, oy + 16)

            label = str(state) if not isinstance(state, bool) else ("ON" if state else "OFF")
            col = (50, 230, 100) if state else (220, 60, 60)
            if not isinstance(state, bool):
                col = (80, 120, 240)

            self.box(col, (SX + SW - 110, oy + 12, 75, 28), 230, (255, 255, 255))
            st = self.ft.render(label, True, (255, 255, 255))
            self.surf.blit(st, (SX + SW - 110 + 37 - st.get_width() // 2, oy + 18))

        qy = SY + SH - 70
        label = "BACK TO MENU" if menu else "SAVE AND QUIT"
        self.btn(label, pygame.Rect(SX + 25, qy, SW - 50, 48), mx, my, col=(200, 50, 50) if not menu else (45, 45, 55))
