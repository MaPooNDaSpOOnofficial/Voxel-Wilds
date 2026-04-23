"""
World generation and chunk management for Voxel Wilds

Handles procedural terrain generation, chunk loading/unloading,
and modification tracking.
"""

import math
import random
from OpenGL.GL import (
    glGenLists, glNewList, glEndList, GL_COMPILE, glBegin, glEnd, GL_QUADS,
    glNormal3fv, glColor4f, glTexCoord2f, glVertex3f, glCallList, glDepthMask,
    GL_FALSE, GL_TRUE, glDeleteLists
)
from config import (
    CHUNK_SIZE, WORLD_HEIGHT, SEA_LEVEL, AIR, STONE, GRASS, DIRT, SAND, WATER,
    LOG, LEAVES, COAL, IRON, GOLD, GRAVEL, DIAMOND, EMERALD, SOLID, PASSABLE
)
from utils import generate_perlin_hash, lerp, fade, gradient


def fbm(wx, wz, seed):
    """
    Fractal Brownian Motion for terrain height generation.
    
    Args:
        wx, wz: World coordinates
        seed: Random seed
        
    Returns:
        Height value (0-WORLD_HEIGHT)
    """
    def pn(x, z, sc):
        """Perlin noise at a given scale."""
        xs, zs = x / sc, z / sc
        x0, z0 = int(math.floor(xs)), int(math.floor(zs))
        sx, sz = fade(xs - x0), fade(zs - z0)
        return lerp(
            lerp(gradient(x0, z0, xs, zs, seed), gradient(x0 + 1, z0, xs, zs, seed), sx),
            lerp(gradient(x0, z0 + 1, xs, zs, seed), gradient(x0 + 1, z0 + 1, xs, zs, seed), sx),
            sz,
        )

    # Multi-octave noise
    c = (
        pn(wx, wz, 130) * 0.5
        + pn(wx + 500, wz + 500, 50) * 0.3
        + pn(wx + 900, wz + 900, 20) * 0.2
    )
    return int(8 + (c * 0.5 + 0.5) * 26)


def generate_chunk(cx, cz, seed):
    """
    Generate a single chunk of terrain.
    
    Args:
        cx, cz: Chunk coordinates
        seed: Random seed for reproducible generation
        
    Returns:
        dict: Mapping of (lx, y, lz) -> block_id
    """
    blocks = {}
    ox, oz = cx * CHUNK_SIZE, cz * CHUNK_SIZE

    # Generate height map for this chunk
    heights = {
        (lx, lz): max(3, min(fbm(ox + lx, oz + lz, seed), WORLD_HEIGHT - 6))
        for lx in range(CHUNK_SIZE)
        for lz in range(CHUNK_SIZE)
    }

    # Fill blocks
    for lx in range(CHUNK_SIZE):
        for lz in range(CHUNK_SIZE):
            wx, wz = ox + lx, oz + lz
            surf = heights[(lx, lz)]
            ocean = surf < SEA_LEVEL
            beach = not ocean and surf <= SEA_LEVEL + 2

            for y in range(WORLD_HEIGHT):
                if y == 0:
                    blocks[(lx, y, lz)] = STONE
                    continue

                if y > surf:
                    if y <= SEA_LEVEL and ocean:
                        blocks[(lx, y, lz)] = WATER
                    continue

                # Terrain layers
                if y < surf - 4:
                    # Cave check
                    if 2 < y < surf - 6:
                        if (generate_perlin_hash(wx, y * 2 + wz, seed) % 100) < 8 and (
                            generate_perlin_hash(wx * 2 + wz, y, seed) % 100
                        ) < 8:
                            continue

                    # Ore distribution
                    rv = generate_perlin_hash(wx * 997 + y * 31337, wz * 1009 + y * 7919, seed) % 1000
                    if rv < 3 and y < 14:
                        b = DIAMOND
                    elif rv < 8 and y < 22:
                        b = GOLD
                    elif rv < 12 and y > 30:
                        b = EMERALD
                    elif rv < 35:
                        b = IRON
                    elif rv < 80:
                        b = COAL
                    else:
                        b = STONE
                elif y < surf - 1:
                    b = DIRT
                elif y < surf:
                    b = SAND if beach else DIRT
                else:
                    b = SAND if (ocean or beach) else GRASS

                blocks[(lx, y, lz)] = b

    # Generate trees
    trng = random.Random(seed ^ (cx * 997331) ^ (cz * 991807))
    for _ in range(trng.randint(0, 2)):
        tx, tz = trng.randint(3, CHUNK_SIZE - 4), trng.randint(3, CHUNK_SIZE - 4)
        surf = heights[(tx, tz)]

        # Skip trees in water or near ceiling
        if surf <= SEA_LEVEL + 2 or surf > WORLD_HEIGHT - 10:
            continue

        th = trng.randint(4, 6)

        # Trunk
        for y in range(surf + 1, surf + th + 1):
            if y < WORLD_HEIGHT:
                blocks[(tx, y, tz)] = LOG

        # Layered canopy
        for dy in range(th - 3, th + 1):
            rad = 2 if dy < th - 1 else (1 if dy < th else 0)
            for dx in range(-rad, rad + 1):
                for dz in range(-rad, rad + 1):
                    # Skip some edges for organic look
                    if rad > 0 and (abs(dx) == rad or abs(dz) == rad) and trng.random() < 0.2:
                        continue

                    nx, ny, nz = tx + dx, surf + dy + 1, tz + dz
                    if 0 <= nx < CHUNK_SIZE and 0 <= nz < CHUNK_SIZE and 0 < ny < WORLD_HEIGHT:
                        if (nx, ny, nz) not in blocks:
                            blocks[(nx, ny, nz)] = LEAVES

    return blocks


# Precompute face data for rendering
FACES = [
    ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)], [(0, 0), (0, 1), (1, 1), (1, 0)]),  # Top
    ((0, -1, 0), [(0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 1)], [(0, 0), (0, 1), (1, 1), (1, 0)]),  # Bottom
    ((1, 0, 0), [(1, 0, 1), (1, 0, 0), (1, 1, 0), (1, 1, 1)], [(0, 0), (1, 0), (1, 1), (0, 1)]),  # Right
    ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)], [(0, 0), (1, 0), (1, 1), (0, 1)]),  # Left
    ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], [(0, 0), (1, 0), (1, 1), (0, 1)]),  # Front
    ((0, 0, -1), [(1, 0, 0), (0, 0, 0), (0, 1, 0), (1, 1, 0)], [(0, 0), (1, 0), (1, 1), (0, 1)]),  # Back
]

SHADE = [1.0, 0.45, 0.75, 0.75, 0.9, 0.9]


class ChunkManager:
    """
    Manages chunk generation, loading, and rendering.
    
    Handles all voxel data, tracks modifications, and
    optimizes rendering with display lists.
    """

    def __init__(self, seed, render_dist=3):
        """
        Initialize chunk manager.
        
        Args:
            seed: World seed for reproducible generation
            render_dist: Render distance in chunks
        """
        self.chunks = {}
        self.display_lists = {}
        self.alpha_lists = {}
        self.render_dist = render_dist
        self.seed = seed
        self.modifications = {}

    def get_block(self, wx, wy, wz):
        """
        Get a block at world coordinates.
        
        Args:
            wx, wy, wz: World coordinates
            
        Returns:
            Block ID
        """
        if wy < 0:
            return STONE
        if wy >= WORLD_HEIGHT:
            return AIR

        wx_i, wy_i, wz_i = int(math.floor(wx)), int(wy), int(math.floor(wz))

        # Check modifications first
        if (wx_i, wy_i, wz_i) in self.modifications:
            return self.modifications[(wx_i, wy_i, wz_i)]

        cx, lx = divmod(wx_i, CHUNK_SIZE)
        cz, lz = divmod(wz_i, CHUNK_SIZE)

        ch = self.chunks.get((cx, cz))
        return ch.get((lx, wy_i, lz), AIR) if ch else AIR

    def set_block(self, wx, wy, wz, bid, is_mod=True):
        """
        Set a block at world coordinates.
        
        Args:
            wx, wy, wz: World coordinates
            bid: Block ID
            is_mod: Whether this is a player modification
        """
        wx_i, wy_i, wz_i = int(math.floor(wx)), int(wy), int(math.floor(wz))

        # Drainable water logic
        if bid == AIR and wy_i <= SEA_LEVEL:
            surf = max(3, min(fbm(wx_i, wz_i, self.seed), WORLD_HEIGHT - 6))
            if wy_i <= SEA_LEVEL and surf < SEA_LEVEL:
                has_water_neighbor = False
                for dx, dy, dz in [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]:
                    if self.get_block(wx_i + dx, wy_i + dy, wz_i + dz) == WATER:
                        has_water_neighbor = True
                        break
                if has_water_neighbor:
                    bid = WATER

        if is_mod:
            self.modifications[(wx_i, wy_i, wz_i)] = bid

        cx, lx = divmod(wx_i, CHUNK_SIZE)
        cz, lz = divmod(wz_i, CHUNK_SIZE)
        key = (cx, cz)

        if key not in self.chunks:
            self.chunks[key] = generate_chunk(*key, self.seed)

        if bid == AIR:
            self.chunks[key].pop((lx, wy_i, lz), None)
        else:
            self.chunks[key][(lx, wy_i, lz)] = bid

        # Invalidate affected display lists
        keys_to_delete = [key]
        if lx == 0:
            keys_to_delete.append((cx - 1, cz))
        if lx == CHUNK_SIZE - 1:
            keys_to_delete.append((cx + 1, cz))
        if lz == 0:
            keys_to_delete.append((cx, cz - 1))
        if lz == CHUNK_SIZE - 1:
            keys_to_delete.append((cx, cz + 1))

        for k in keys_to_delete:
            if k in self.display_lists:
                glDeleteLists(self.display_lists.pop(k), 1)
            if k in self.alpha_lists:
                glDeleteLists(self.alpha_lists.pop(k), 1)

    def ensure_chunks(self, cx, cz):
        """
        Ensure a chunk is loaded, with priority for current chunk.
        
        Args:
            cx, cz: Chunk coordinates
        """
        if (cx, cz) not in self.chunks:
            self.chunks[(cx, cz)] = generate_chunk(cx, cz, self.seed)
            ox, oz = cx * CHUNK_SIZE, cz * CHUNK_SIZE
            for (mwx, mwy, mwz), mbid in self.modifications.items():
                if ox <= mwx < ox + CHUNK_SIZE and oz <= mwz < oz + CHUNK_SIZE:
                    self.chunks[(cx, cz)][(mwx - ox, mwy, mwz - oz)] = mbid
            return

        # Load surrounding chunks
        rd = self.render_dist
        count = 0
        for dcx in range(-rd - 1, rd + 2):
            for dcz in range(-rd - 1, rd + 2):
                k = (cx + dcx, cz + dcz)
                if k not in self.chunks:
                    self.chunks[k] = generate_chunk(*k, self.seed)
                    ox, oz = k[0] * CHUNK_SIZE, k[1] * CHUNK_SIZE
                    for (mwx, mwy, mwz), mbid in self.modifications.items():
                        if ox <= mwx < ox + CHUNK_SIZE and oz <= mwz < oz + CHUNK_SIZE:
                            self.chunks[k][(mwx - ox, mwy, mwz - oz)] = mbid
                    count += 1
                    if count >= 1:
                        return  # Throttle to 1 chunk per frame

    def w2c(self, wx, wz):
        """World to chunk coordinates."""
        return int(math.floor(wx)) // CHUNK_SIZE, int(math.floor(wz)) // CHUNK_SIZE

    def render(self, px, pz):
        """
        Render all visible chunks.
        
        Args:
            px, pz: Player position
        """
        from textures import get_tex_indices as TEX_MAP_func

        cx, cz = self.w2c(px, pz)
        rd = self.render_dist
        visible = []

        # Collect visible chunks
        for dcx in range(-rd, rd + 1):
            for dcz in range(-rd, rd + 1):
                k = (cx + dcx, cz + dcz)
                if k not in self.chunks:
                    continue
                if k not in self.display_lists or k not in self.alpha_lists:
                    self.display_lists[k], self.alpha_lists[k] = self._build(k)
                visible.append(k)

        # Pass 1: Opaque blocks
        for k in visible:
            glCallList(self.display_lists[k])

        # Pass 2: Transparent blocks (sorted back-to-front)
        glDepthMask(GL_FALSE)
        visible.sort(
            key=lambda k: (k[0] * CHUNK_SIZE + 8 - px) ** 2 + (k[1] * CHUNK_SIZE + 8 - pz) ** 2,
            reverse=True,
        )
        for k in visible:
            glCallList(self.alpha_lists[k])
        glDepthMask(GL_TRUE)

        # Simple water flow
        if self.chunks:
            for _ in range(20):
                ckey = random.choice(list(self.chunks.keys()))
                ch = self.chunks[ckey]
                if not ch:
                    continue
                lpos = random.choice(list(ch.keys()))
                if ch[lpos] == WATER:
                    lx, y, lz = lpos
                    wx, wz = ckey[0] * CHUNK_SIZE + lx, ckey[1] * CHUNK_SIZE + lz

                    if y > 1 and self.get_block(wx, y - 1, wz) == AIR:
                        self.set_block(wx, y - 1, wz, WATER)
                    else:
                        dx, dz = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                        if self.get_block(wx + dx, y, wz + dz) == AIR:
                            if y <= SEA_LEVEL:
                                self.set_block(wx + dx, y, wz + dz, WATER)

    def _build(self, key):
        """Build display lists for a chunk."""
        from textures import get_tex_indices as TEX_MAP_func

        cx, cz = key
        ox, oz = cx * CHUNK_SIZE, cz * CHUNK_SIZE
        ch = self.chunks.get(key)

        # Pre-fetch neighbors
        neighbors = {
            (1, 0): self.chunks.get((cx + 1, cz)),
            (-1, 0): self.chunks.get((cx - 1, cz)),
            (0, 1): self.chunks.get((cx, cz + 1)),
            (0, -1): self.chunks.get((cx, cz - 1)),
        }

        def get_nb(nx, ny, nz):
            if 0 <= nx < CHUNK_SIZE and 0 <= ny < WORLD_HEIGHT and 0 <= nz < CHUNK_SIZE:
                return ch.get((nx, ny, nz), AIR)
            nc = neighbors.get(
                (1 if nx >= CHUNK_SIZE else (-1 if nx < 0 else 0), 1 if nz >= CHUNK_SIZE else (-1 if nz < 0 else 0))
            )
            return nc.get((nx % CHUNK_SIZE, ny, nz % CHUNK_SIZE), AIR) if nc else AIR

        def get_ao(lx, y, lz, nrm, v):
            """Simple ambient occlusion."""
            side1 = (
                int(v[0] * 2 - 1) if nrm[0] == 0 else 0,
                int(v[1] * 2 - 1) if nrm[1] == 0 else 0,
                int(v[2] * 2 - 1) if nrm[2] == 0 else 0,
            )
            side2 = (
                0 if nrm[0] != 0 else (int(v[0] * 2 - 1) if side1[0] == 0 else 0),
                0 if nrm[1] != 0 else (int(v[1] * 2 - 1) if side1[1] == 0 else 0),
                0 if nrm[2] != 0 else (int(v[2] * 2 - 1) if side1[2] == 0 else 0),
            )
            dx, dy, dz = side1[0] + side2[0], side1[1] + side2[1], side1[2] + side2[2]
            occ = 0
            if get_nb(lx + nrm[0] + side1[0], y + nrm[1] + side1[1], lz + nrm[2] + side1[2]) not in PASSABLE:
                occ += 1
            if get_nb(lx + nrm[0] + side2[0], y + nrm[1] + side2[1], lz + nrm[2] + side2[2]) not in PASSABLE:
                occ += 1
            if occ == 2:
                occ = 3
            elif get_nb(lx + nrm[0] + dx, y + nrm[1] + dy, lz + nrm[2] + dz) not in PASSABLE:
                occ += 1
            return 1.0 - (occ * 0.18)

        # Opaque list
        dlo = glGenLists(1)
        glNewList(dlo, GL_COMPILE)
        if ch:
            glBegin(GL_QUADS)
            for (lx, y, lz), bid in ch.items():
                if bid in PASSABLE:
                    continue
                wx, wz = ox + lx, oz + lz
                for i, (nrm, verts, uvs) in enumerate(FACES):
                    nx, ny, nz = lx + nrm[0], y + nrm[1], lz + nrm[2]
                    if get_nb(nx, ny, nz) in PASSABLE:
                        ti = TEX_MAP_func(bid)[i]
                        tu, tv = (ti % 8) * 0.125, (ti // 8) * 0.125
                        s = SHADE[i]
                        glNormal3fv(nrm)
                        for j, (vx, vy, vz) in enumerate(verts):
                            ao = get_ao(lx, y, lz, nrm, (vx, vy, vz))
                            glColor4f(s * ao, s * ao, s * ao, 1.0)
                            glTexCoord2f(tu + uvs[j][0] * 0.125, tv + (1.0 - uvs[j][1]) * 0.125)
                            glVertex3f(wx + vx, y + vy, wz + vz)
            glEnd()
        glEndList()

        # Alpha list (water & leaves)
        dla = glGenLists(1)
        glNewList(dla, GL_COMPILE)
        if ch:
            glBegin(GL_QUADS)
            for (lx, y, lz), bid in ch.items():
                if bid != WATER and bid != LEAVES:
                    continue
                wx, wz = ox + lx, oz + lz
                for i, (nrm, verts, uvs) in enumerate(FACES):
                    nb = get_nb(lx + nrm[0], y + nrm[1], lz + nrm[2])
                    if (bid == WATER and nb != WATER and nb in PASSABLE) or (
                        bid == LEAVES and nb != LEAVES and nb in PASSABLE
                    ):
                        ti = TEX_MAP_func(bid)[i]
                        tu, tv = (ti % 8) * 0.125, (ti // 8) * 0.125
                        s = SHADE[i]
                        glNormal3fv(nrm)
                        for j, (vx, vy, vz) in enumerate(verts):
                            ao = get_ao(lx, y, lz, nrm, (vx, vy, vz)) if bid == LEAVES else 1.0
                            if bid == WATER:
                                glColor4f(s * 0.8, s * 0.9, s * 1.0, 0.6)
                            else:
                                glColor4f(s * ao, s * ao, s * ao, 1.0)
                            glTexCoord2f(tu + uvs[j][0] * 0.125, tv + (1.0 - uvs[j][1]) * 0.125)
                            glVertex3f(wx + vx, y + vy, wz + vz)
            glEnd()
        glEndList()

        return dlo, dla
