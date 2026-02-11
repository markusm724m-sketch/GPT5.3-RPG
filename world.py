"""Procedural chunk-based world with biomes, fog of war, weather and day/night."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

TILE_SIZE = 32
CHUNK_SIZE = 32

TILE_COLORS = {
    "grass": (80, 172, 92),
    "water": (58, 118, 210),
    "stone": (122, 124, 136),
    "dirt": (146, 100, 70),
    "sand": (210, 190, 120),
    "dungeon": (88, 72, 108),
    "ruins": (130, 100, 120),
    "castle_floor": (136, 130, 124),
    "castle_wall": (112, 108, 116),
    "village_house": (176, 145, 108),
    "village_road": (150, 122, 90),
}


@dataclass
class Chunk:
    tiles: list[list[str]]
    props: list[tuple[str, int, int]]


class World:
    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.chunks: dict[tuple[int, int], Chunk] = {}
        self.discovered_tiles: set[tuple[int, int]] = set()
        self.player_blocks: dict[tuple[int, int], str] = {}
        self.time_of_day = 8.0
        self.weather = "clear"
        self.weather_timer = 40.0

        self._tile_cache: dict[tuple[str, int], pygame.Surface] = {}
        self._tile_darkness_cache: dict[int, pygame.Surface] = {}
        self._fog_tile = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self._fog_tile.fill((12, 12, 22, 180))

    def _clamp_channel(self, value: int) -> int:
        return max(0, min(255, value))

    def _color_shift(self, color: tuple[int, int, int], delta: int) -> tuple[int, int, int]:
        return (
            self._clamp_channel(color[0] + delta),
            self._clamp_channel(color[1] + delta),
            self._clamp_channel(color[2] + delta),
        )

    def _cell_rng(self, x: int, y: int) -> random.Random:
        value = (x * 73856093) ^ (y * 19349663) ^ (self.seed * 83492791)
        return random.Random(value)

    def _noise(self, x: int, y: int, freq: float = 0.06) -> float:
        return (
            math.sin((x + self.seed * 3) * freq)
            + math.cos((y - self.seed * 5) * freq * 0.8)
            + math.sin((x + y) * freq * 0.65)
        ) / 3.0

    def _tile_variant(self, tx: int, ty: int) -> int:
        value = (tx * 92837111) ^ (ty * 689287499) ^ (self.seed * 283923481)
        return value & 3

    def _tile_key(self, tile: str, variant: int) -> int:
        return sum(ord(ch) for ch in tile) * 17 + variant * 101 + self.seed * 13

    def _build_tile_surface(self, tile: str, variant: int) -> pygame.Surface:
        base = TILE_COLORS.get(tile, (255, 0, 255))
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        rng = random.Random(self._tile_key(tile, variant))

        for y in range(TILE_SIZE):
            t = y / max(1, TILE_SIZE - 1)
            shade = int((t - 0.25) * 24)
            row_col = self._color_shift(base, -shade)
            pygame.draw.line(surf, row_col, (0, y), (TILE_SIZE - 1, y))

        # Fine variation to avoid flat blocks.
        for _ in range(34):
            px = rng.randint(0, TILE_SIZE - 1)
            py = rng.randint(0, TILE_SIZE - 1)
            delta = rng.randint(-18, 18)
            surf.set_at((px, py), self._color_shift(base, delta))

        if tile == "grass":
            for _ in range(8):
                x = rng.randint(2, TILE_SIZE - 3)
                y = rng.randint(10, TILE_SIZE - 2)
                h = rng.randint(2, 4)
                pygame.draw.line(surf, self._color_shift(base, -22), (x, y), (x + rng.randint(-1, 1), y - h), 1)
        elif tile == "water":
            for y in range(6, TILE_SIZE, 8):
                wave = rng.randint(-2, 2)
                pygame.draw.line(surf, (140, 180, 235), (2, y + wave), (TILE_SIZE - 3, y + wave), 1)
        elif tile in {"stone", "castle_floor", "castle_wall", "dungeon", "ruins"}:
            for _ in range(5):
                x0 = rng.randint(2, TILE_SIZE - 4)
                y0 = rng.randint(2, TILE_SIZE - 4)
                x1 = x0 + rng.randint(-6, 6)
                y1 = y0 + rng.randint(-6, 6)
                pygame.draw.line(surf, self._color_shift(base, -28), (x0, y0), (x1, y1), 1)
        elif tile in {"dirt", "village_road", "village_house"}:
            for _ in range(24):
                px = rng.randint(0, TILE_SIZE - 1)
                py = rng.randint(0, TILE_SIZE - 1)
                surf.set_at((px, py), self._color_shift(base, rng.randint(-26, 12)))

        return surf

    def _get_tile_surface(self, tile: str, tx: int, ty: int) -> pygame.Surface:
        variant = self._tile_variant(tx, ty)
        key = (tile, variant)
        cached = self._tile_cache.get(key)
        if cached is not None:
            return cached
        built = self._build_tile_surface(tile, variant)
        self._tile_cache[key] = built
        return built

    def _get_dark_tile(self, alpha: int) -> pygame.Surface:
        alpha = max(0, min(190, alpha))
        if alpha not in self._tile_darkness_cache:
            tile = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            tile.fill((8, 10, 18, alpha))
            self._tile_darkness_cache[alpha] = tile
        return self._tile_darkness_cache[alpha]

    def biome_at(self, tx: int, ty: int) -> str:
        n = self._noise(tx, ty)
        m = self._noise(tx + 999, ty - 431, 0.08)
        castle_dist = math.hypot(tx - 200, ty - 200)
        village_dist = math.hypot(tx - 400, ty - 300)

        if castle_dist < 50:
            return "castle_floor" if castle_dist < 30 else "castle_wall"

        if village_dist < 80:
            return "village_house" if village_dist < 60 else "village_road"

        if n < -0.22:
            return "mountains"
        if n < -0.05:
            return "forest"
        if n < 0.18:
            return "plains"
        if m > 0.25:
            return "village_ruins"
        return "dungeon"

    def generate_chunk(self, cx: int, cy: int) -> Chunk:
        tiles: list[list[str]] = [["grass" for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_SIZE)]
        props: list[tuple[str, int, int]] = []

        for ly in range(CHUNK_SIZE):
            for lx in range(CHUNK_SIZE):
                tx = cx * CHUNK_SIZE + lx
                ty = cy * CHUNK_SIZE + ly
                biome = self.biome_at(tx, ty)
                rng = self._cell_rng(tx, ty)
                val = self._noise(tx * 2, ty * 2, 0.1)

                if biome == "castle_floor":
                    tile = "castle_floor"
                    if rng.random() < 0.02:
                        props.append(("castle_tower", tx, ty))
                elif biome == "castle_wall":
                    tile = "castle_wall"
                    if rng.random() < 0.1:
                        props.append(("castle_wall_prop", tx, ty))
                elif biome == "village_house":
                    tile = "village_house"
                    if rng.random() < 0.15:
                        props.append(("house", tx, ty))
                elif biome == "village_road":
                    tile = "village_road"
                elif biome == "plains":
                    tile = "grass" if val > -0.1 else "dirt"
                elif biome == "forest":
                    tile = "grass" if val > -0.2 else "dirt"
                    if rng.random() < 0.08:
                        props.append(("tree", tx, ty))
                elif biome == "mountains":
                    tile = "stone" if val > -0.35 else "dirt"
                    if rng.random() < 0.05:
                        props.append(("rock", tx, ty))
                elif biome == "dungeon":
                    tile = "dungeon" if val > -0.3 else "stone"
                    if rng.random() < 0.025:
                        props.append(("obelisk", tx, ty))
                else:
                    tile = "ruins" if val > -0.2 else "dirt"
                    if rng.random() < 0.04:
                        props.append(("pillar", tx, ty))

                if self._noise(tx - 350, ty + 177, 0.12) > 0.45:
                    tile = "water"

                tiles[ly][lx] = tile
        return Chunk(tiles=tiles, props=props)

    def get_chunk(self, cx: int, cy: int) -> Chunk:
        key = (cx, cy)
        if key not in self.chunks:
            self.chunks[key] = self.generate_chunk(cx, cy)
        return self.chunks[key]

    def ensure_chunks_around(self, world_x: float, world_y: float, radius_chunks: int = 2) -> None:
        cx = int(world_x // (TILE_SIZE * CHUNK_SIZE))
        cy = int(world_y // (TILE_SIZE * CHUNK_SIZE))
        for oy in range(-radius_chunks, radius_chunks + 1):
            for ox in range(-radius_chunks, radius_chunks + 1):
                self.get_chunk(cx + ox, cy + oy)

    def get_tile(self, tx: int, ty: int) -> str:
        cx = tx // CHUNK_SIZE
        cy = ty // CHUNK_SIZE
        lx = tx % CHUNK_SIZE
        ly = ty % CHUNK_SIZE
        return self.get_chunk(cx, cy).tiles[ly][lx]

    def reveal_around(self, world_x: float, world_y: float, radius_tiles: int = 9) -> None:
        tx = int(world_x // TILE_SIZE)
        ty = int(world_y // TILE_SIZE)
        for y in range(ty - radius_tiles, ty + radius_tiles + 1):
            for x in range(tx - radius_tiles, tx + radius_tiles + 1):
                self.discovered_tiles.add((x, y))

    def is_solid_tile(self, tx: int, ty: int) -> bool:
        if (tx, ty) in self.player_blocks:
            return self.player_blocks[(tx, ty)] == "wall"
        tile = self.get_tile(tx, ty)
        return tile in {"water", "stone"}

    def is_rect_blocked(self, rect: pygame.Rect) -> bool:
        left = rect.left // TILE_SIZE
        right = (rect.right - 1) // TILE_SIZE
        top = rect.top // TILE_SIZE
        bottom = (rect.bottom - 1) // TILE_SIZE
        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                if self.is_solid_tile(tx, ty):
                    return True
        return False

    def place_player_block(self, tx: int, ty: int, block_type: str = "wall") -> None:
        self.player_blocks[(tx, ty)] = block_type

    def remove_player_block(self, tx: int, ty: int) -> None:
        self.player_blocks.pop((tx, ty), None)

    def update(self, dt: float) -> None:
        self.time_of_day = (self.time_of_day + dt * 0.28) % 24.0
        self.weather_timer -= dt
        if self.weather_timer <= 0:
            self.weather_timer = random.uniform(35, 65)
            self.weather = random.choice(["clear", "clear", "rain", "rain", "arcane_wind"])

    @property
    def is_night(self) -> bool:
        return self.time_of_day < 6 or self.time_of_day > 19

    def _ambient_light_factor(self) -> float:
        # Smooth 24h brightness curve (1.0 at noon, ~0.3 at midnight).
        day_cycle = (math.cos((self.time_of_day - 12.0) / 24.0 * math.tau) + 1.0) * 0.5
        ambient = 0.30 + day_cycle * 0.70
        if self.weather == "rain":
            ambient *= 0.92
        elif self.weather == "arcane_wind":
            ambient *= 0.88
        return max(0.22, min(1.0, ambient))

    def _draw_prop_shadow(self, surface: pygame.Surface, sx: int, sy: int, width: int = 24, alpha: int = 68) -> None:
        shadow = pygame.Surface((width, max(8, width // 3)), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, alpha), shadow.get_rect())
        surface.blit(shadow, (sx - width // 2, sy + 7))

    def _draw_prop(self, surface: pygame.Surface, kind: str, tx: int, ty: int, sx: int, sy: int) -> None:
        self._draw_prop_shadow(surface, sx, sy)

        if kind == "tree":
            sway = math.sin(self.time_of_day * 2.2 + tx * 0.15 + ty * 0.11) * 2.7
            trunk_x = int(sx + sway)
            pygame.draw.rect(surface, (86, 56, 38), (trunk_x - 2, sy - 4, 5, 13), border_radius=2)
            pygame.draw.circle(surface, (38, 122, 58), (trunk_x, sy - 12), 11)
            pygame.draw.circle(surface, (50, 150, 74), (trunk_x - 7, sy - 10), 8)
            pygame.draw.circle(surface, (32, 108, 54), (trunk_x + 8, sy - 9), 7)
            pygame.draw.circle(surface, (105, 186, 120), (trunk_x - 2, sy - 16), 4)
        elif kind == "rock":
            pygame.draw.ellipse(surface, (95, 100, 118), (sx - 8, sy - 2, 17, 12))
            pygame.draw.ellipse(surface, (145, 150, 166), (sx - 4, sy + 1, 7, 4))
        elif kind == "obelisk":
            glow = pygame.Surface((34, 46), pygame.SRCALPHA)
            pygame.draw.polygon(glow, (190, 120, 255, 45), [(17, 2), (30, 42), (4, 42)])
            surface.blit(glow, (sx - 17, sy - 25))
            pygame.draw.polygon(surface, (165, 110, 230), [(sx, sy - 12), (sx + 7, sy + 10), (sx - 7, sy + 10)])
            pygame.draw.line(surface, (220, 190, 255), (sx, sy - 8), (sx, sy + 8), 1)
        elif kind == "castle_tower":
            pygame.draw.rect(surface, (146, 126, 108), (sx - 8, sy - 21, 16, 31))
            pygame.draw.rect(surface, (118, 104, 92), (sx - 8, sy - 21, 5, 31))
            pygame.draw.polygon(surface, (112, 95, 78), [(sx - 11, sy - 21), (sx, sy - 31), (sx + 11, sy - 21)])
            pygame.draw.rect(surface, (86, 66, 50), (sx - 4, sy - 15, 3, 5))
            pygame.draw.rect(surface, (86, 66, 50), (sx + 1, sy - 15, 3, 5))
        elif kind == "castle_wall_prop":
            pygame.draw.rect(surface, (148, 128, 106), (sx - 12, sy - 8, 24, 16))
            pygame.draw.rect(surface, (120, 106, 90), (sx - 12, sy - 8, 4, 16))
            for i in range(3):
                pygame.draw.rect(surface, (148, 128, 106), (sx - 10 + i * 8, sy - 12, 4, 4))
        elif kind == "house":
            pygame.draw.rect(surface, (185, 156, 124), (sx - 11, sy - 6, 22, 15))
            pygame.draw.rect(surface, (150, 120, 95), (sx - 11, sy - 6, 4, 15))
            pygame.draw.polygon(surface, (124, 82, 60), [(sx - 13, sy - 6), (sx, sy - 17), (sx + 13, sy - 6)])
            pygame.draw.rect(surface, (86, 56, 38), (sx - 2, sy + 1, 4, 8))
            pygame.draw.rect(surface, (210, 220, 255), (sx + 5, sy - 2, 3, 3))
        else:
            pygame.draw.rect(surface, (150, 130, 150), (sx - 5, sy - 8, 10, 16), 2)

    def _apply_local_light(
        self,
        surface: pygame.Surface,
        camera,
        screen_w: int,
        screen_h: int,
        ambient: float,
        focus_world: tuple[float, float] | None,
    ) -> None:
        overlay_alpha = int((1.0 - ambient) * 170)
        if overlay_alpha <= 0:
            return

        tint = (14, 16, 30, overlay_alpha)
        if self.weather == "rain":
            tint = (10, 20, 36, min(200, overlay_alpha + 14))
        elif self.weather == "arcane_wind":
            tint = (20, 8, 34, min(200, overlay_alpha + 12))

        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill(tint)

        if focus_world is not None:
            px, py = camera.world_to_screen(focus_world[0], focus_world[1])
            radius = 200 if self.is_night else 150
            rgb = tint[:3]
            for i in range(7):
                ring_radius = int(radius - i * (radius / 7))
                ring_alpha = int(max(0, overlay_alpha * (0.68 - i * 0.09)))
                pygame.draw.circle(overlay, (*rgb, ring_alpha), (px, py), ring_radius)
            pygame.draw.circle(overlay, (0, 0, 0, 0), (px, py), int(radius * 0.32))

        surface.blit(overlay, (0, 0))

    def draw(
        self,
        surface: pygame.Surface,
        camera,
        screen_w: int,
        screen_h: int,
        focus_world: tuple[float, float] | None = None,
    ) -> None:
        min_tx = int(camera.x // TILE_SIZE) - 2
        max_tx = int((camera.x + screen_w) // TILE_SIZE) + 2
        min_ty = int(camera.y // TILE_SIZE) - 2
        max_ty = int((camera.y + screen_h) // TILE_SIZE) + 2

        ambient = self._ambient_light_factor()
        darkness_tile = self._get_dark_tile(int((1.0 - ambient) * 145))

        for ty in range(min_ty, max_ty + 1):
            for tx in range(min_tx, max_tx + 1):
                tile = self.get_tile(tx, ty)
                sx, sy = camera.world_to_screen(tx * TILE_SIZE, ty * TILE_SIZE)
                surface.blit(self._get_tile_surface(tile, tx, ty), (sx, sy))

                if tile == "water":
                    wave_shift = math.sin(self.time_of_day * 1.8 + tx * 0.7 + ty * 0.35)
                    y1 = sy + 9 + int(wave_shift * 1.6)
                    y2 = sy + 20 + int(wave_shift * 1.2)
                    pygame.draw.line(surface, (175, 210, 255), (sx + 3, y1), (sx + TILE_SIZE - 4, y1), 1)
                    pygame.draw.line(surface, (126, 168, 240), (sx + 2, y2), (sx + TILE_SIZE - 2, y2), 1)

                base_col = TILE_COLORS.get(tile, (120, 120, 120))
                top_edge = self._color_shift(base_col, 10)
                bottom_edge = self._color_shift(base_col, -16)
                pygame.draw.line(surface, top_edge, (sx, sy), (sx + TILE_SIZE - 1, sy), 1)
                pygame.draw.line(surface, bottom_edge, (sx, sy + TILE_SIZE - 1), (sx + TILE_SIZE - 1, sy + TILE_SIZE - 1), 1)

                if ambient < 0.995:
                    surface.blit(darkness_tile, (sx, sy))

                block = self.player_blocks.get((tx, ty))
                if block:
                    pygame.draw.rect(surface, (186, 162, 224), (sx + 4, sy + 4, TILE_SIZE - 8, TILE_SIZE - 8), 2)
                    pygame.draw.rect(surface, (122, 102, 162), (sx + 6, sy + 6, TILE_SIZE - 12, TILE_SIZE - 12), 1)

                if (tx, ty) not in self.discovered_tiles:
                    surface.blit(self._fog_tile, (sx, sy))

        min_cx = min_tx // CHUNK_SIZE - 1
        max_cx = max_tx // CHUNK_SIZE + 1
        min_cy = min_ty // CHUNK_SIZE - 1
        max_cy = max_ty // CHUNK_SIZE + 1
        for cy in range(min_cy, max_cy + 1):
            for cx in range(min_cx, max_cx + 1):
                chunk = self.get_chunk(cx, cy)
                for kind, tx, ty in chunk.props:
                    if (tx, ty) not in self.discovered_tiles:
                        continue
                    sx, sy = camera.world_to_screen(tx * TILE_SIZE + TILE_SIZE // 2, ty * TILE_SIZE + TILE_SIZE // 2)
                    self._draw_prop(surface, kind, tx, ty, sx, sy)

        self._apply_local_light(surface, camera, screen_w, screen_h, ambient, focus_world)

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "time_of_day": self.time_of_day,
            "weather": self.weather,
            "player_blocks": {f"{x},{y}": t for (x, y), t in self.player_blocks.items()},
            "discovered": [f"{x},{y}" for (x, y) in list(self.discovered_tiles)[:8000]],
        }

    def load_dict(self, data: dict) -> None:
        self.seed = data.get("seed", self.seed)
        self.time_of_day = data.get("time_of_day", self.time_of_day)
        self.weather = data.get("weather", self.weather)
        self.player_blocks = {}
        for key, value in data.get("player_blocks", {}).items():
            x, y = key.split(",")
            self.player_blocks[(int(x), int(y))] = value
        self.discovered_tiles = set()
        for p in data.get("discovered", []):
            x, y = p.split(",")
            self.discovered_tiles.add((int(x), int(y)))
