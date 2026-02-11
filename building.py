"""Building system: block placement and NPC settlement support."""

from __future__ import annotations

import random

import pygame

from localization import localize_role
from world import TILE_SIZE


class BuildingSystem:
    def __init__(self) -> None:
        self.preview_tile: tuple[int, int] | None = None
        self.settlers: list[dict] = []

    def world_tile_from_mouse(self, mouse_pos: tuple[int, int], camera) -> tuple[int, int]:
        mx, my = mouse_pos
        wx = mx + camera.x
        wy = my + camera.y
        return int(wx // TILE_SIZE), int(wy // TILE_SIZE)

    def can_place(self, world, tx: int, ty: int) -> bool:
        tile = world.get_tile(tx, ty)
        if tile in {"water", "stone"}:
            return False
        if (tx, ty) in world.player_blocks:
            return False
        return True

    def place_block(self, player, world, tx: int, ty: int) -> bool:
        if not self.can_place(world, tx, ty):
            return False
        if not player.consume_item("plank", 1):
            return False
        world.place_player_block(tx, ty, "wall")
        player.gain_exp(3)
        return True

    def remove_block(self, player, world, tx: int, ty: int) -> bool:
        if (tx, ty) not in world.player_blocks:
            return False
        world.remove_player_block(tx, ty)
        player.add_item("plank", 1)
        return True

    def try_spawn_settler(self, player, entities, world) -> dict | None:
        houses = sum(1 for b in world.player_blocks.values() if b == "wall")
        if houses < 25:
            return None
        if len([e for e in entities.entities if e.faction == "villagers"]) >= 12:
            return None
        if random.random() < 0.0025:
            angle = random.uniform(0, 6.28)
            sx = player.x + 180 * pygame.math.Vector2(1, 0).rotate_rad(angle).x
            sy = player.y + 180 * pygame.math.Vector2(1, 0).rotate_rad(angle).y
            role = random.choice(["villager", "merchant", "waifu"])
            from entities import BaseEntity

            new_ent = BaseEntity(sx, sy, role, "villagers", hp=70, speed=68, radius=12)
            entities.entities.append(new_ent)
            self.settlers.append({"x": sx, "y": sy, "role": role})
            player.reputation += 2
            return {"type": "settle", "text": f"Новый житель прибыл на базу: {localize_role(role)}."}
        return None

    def draw_preview(self, surface: pygame.Surface, camera, world, mouse_pos: tuple[int, int]) -> None:
        tx, ty = self.world_tile_from_mouse(mouse_pos, camera)
        self.preview_tile = (tx, ty)
        sx, sy = camera.world_to_screen(tx * TILE_SIZE, ty * TILE_SIZE)
        color = (120, 240, 160) if self.can_place(world, tx, ty) else (240, 90, 90)
        pygame.draw.rect(surface, color, (sx + 1, sy + 1, TILE_SIZE - 2, TILE_SIZE - 2), 2)
