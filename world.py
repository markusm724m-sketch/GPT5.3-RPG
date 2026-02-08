"""Procedural chunk-based world with biomes, fog of war, weather and day/night."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

TILE_SIZE = 32
CHUNK_SIZE = 32

TILE_COLORS = {
    "grass": (70, 180, 90),
    "water": (55, 110, 210),
    "stone": (120, 120, 130),
    "dirt": (140, 95, 65),
    "sand": (210, 190, 120),
    "dungeon": (90, 70, 110),
    "ruins": (130, 100, 120),
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

    def _cell_rng(self, x: int, y: int) -> random.Random:
        value = (x * 73856093) ^ (y * 19349663) ^ (self.seed * 83492791)
        return random.Random(value)

    def _noise(self, x: int, y: int, freq: float = 0.06) -> float:
        return (
            math.sin((x + self.seed * 3) * freq)
            + math.cos((y - self.seed * 5) * freq * 0.8)
            + math.sin((x + y) * freq * 0.65)
        ) / 3.0

    def biome_at(self, tx: int, ty: int) -> str:
        n = self._noise(tx, ty)
        m = self._noise(tx + 999, ty - 431, 0.08)
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

                if biome == "plains":
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

    def draw(self, surface: pygame.Surface, camera, screen_w: int, screen_h: int) -> None:
        min_tx = int(camera.x // TILE_SIZE) - 2
        max_tx = int((camera.x + screen_w) // TILE_SIZE) + 2
        min_ty = int(camera.y // TILE_SIZE) - 2
        max_ty = int((camera.y + screen_h) // TILE_SIZE) + 2

        for ty in range(min_ty, max_ty + 1):
            for tx in range(min_tx, max_tx + 1):
                tile = self.get_tile(tx, ty)
                color = TILE_COLORS.get(tile, (255, 0, 255))
                sx, sy = camera.world_to_screen(tx * TILE_SIZE, ty * TILE_SIZE)
                pygame.draw.rect(surface, color, (sx, sy, TILE_SIZE, TILE_SIZE))

                block = self.player_blocks.get((tx, ty))
                if block:
                    pygame.draw.rect(surface, (160, 140, 200), (sx + 4, sy + 4, TILE_SIZE - 8, TILE_SIZE - 8), 2)

                if (tx, ty) not in self.discovered_tiles:
                    fog = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    fog.fill((12, 12, 22, 180))
                    surface.blit(fog, (sx, sy))

        # draw chunk props
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
                    if kind == "tree":
                        pygame.draw.line(surface, (90, 55, 40), (sx, sy + 8), (sx, sy - 2), 4)
                        pygame.draw.circle(surface, (35, 145, 60), (sx, sy - 8), 10)
                    elif kind == "rock":
                        pygame.draw.circle(surface, (100, 100, 110), (sx, sy), 8)
                    elif kind == "obelisk":
                        pygame.draw.polygon(surface, (180, 120, 240), [(sx, sy - 10), (sx + 6, sy + 10), (sx - 6, sy + 10)])
                    else:
                        pygame.draw.rect(surface, (150, 130, 150), (sx - 5, sy - 8, 10, 16), 2)

        if self.is_night:
            overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            overlay.fill((20, 14, 36, 95))
            surface.blit(overlay, (0, 0))

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
