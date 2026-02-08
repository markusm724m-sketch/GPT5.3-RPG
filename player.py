"""Player logic: movement, jump/dash, stats, inventory and isekai abilities."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pygame

from world import TILE_SIZE


@dataclass
class Player:
    x: float = 200
    y: float = 180
    w: int = 24
    h: int = 34
    vx: float = 0
    vy: float = 0
    speed: float = 190
    dash_speed: float = 420
    dash_time: float = 0.0
    dash_cooldown: float = 0.0
    jump_time: float = 0.0
    facing: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(1, 0))

    hp: int = 100
    hp_max: int = 100
    mana: int = 80
    mana_max: int = 80
    level: int = 1
    exp: int = 0
    reputation: int = 0
    cheat_mode: bool = False

    hotbar: list[dict] = field(default_factory=list)
    inventory: list[dict] = field(default_factory=list)
    selected_hotbar: int = 0

    summon_cooldown: float = 0.0
    time_slow: float = 0.0

    def __post_init__(self) -> None:
        if not self.hotbar:
            self.hotbar = [{"id": "wood", "count": 10}, {"id": "ore", "count": 6}] + [{} for _ in range(8)]
        if not self.inventory:
            self.inventory = [{} for _ in range(50)]
            self.inventory[0] = {"id": "cheat_fruit", "count": 1}

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    @property
    def center(self) -> tuple[float, float]:
        return self.x + self.w / 2, self.y + self.h / 2

    def gain_exp(self, amount: int) -> int:
        self.exp += amount
        level_ups = 0
        need = 70 + self.level * 35
        while self.exp >= need:
            self.exp -= need
            self.level += 1
            level_ups += 1
            self.hp_max += 8
            self.mana_max += 6
            self.hp = self.hp_max
            self.mana = self.mana_max
            need = 70 + self.level * 35
        return level_ups

    def add_item(self, item_id: str, count: int = 1) -> None:
        for slot in self.hotbar + self.inventory:
            if slot.get("id") == item_id:
                slot["count"] = slot.get("count", 0) + count
                return
        for slot in self.hotbar + self.inventory:
            if not slot:
                slot.update({"id": item_id, "count": count})
                return

    def consume_item(self, item_id: str, count: int = 1) -> bool:
        for slot in self.hotbar + self.inventory:
            if slot.get("id") == item_id and slot.get("count", 0) >= count:
                slot["count"] -= count
                if slot["count"] <= 0:
                    slot.clear()
                return True
        return False

    def handle_inputs(self, dt: float, keys, world) -> None:
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move.x += 1

        if move.length_squared() > 0:
            move = move.normalize()
            self.facing = move

        speed = self.speed
        if world.weather == "rain":
            speed *= 0.92
        if self.cheat_mode:
            speed *= 1.25

        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        if self.dash_time > 0:
            self.dash_time -= dt
            speed = self.dash_speed

        self.vx = move.x * speed
        self.vy = move.y * speed

    def trigger_dash(self, cooldown_scale: float = 1.0) -> None:
        if self.dash_cooldown <= 0:
            self.dash_time = 0.18
            self.dash_cooldown = max(0.45, 1.2 * cooldown_scale)

    def trigger_jump(self) -> None:
        self.jump_time = 0.35

    def use_cheat_fruit(self) -> bool:
        if self.consume_item("cheat_fruit", 1):
            self.cheat_mode = True
            self.hp_max += 60
            self.mana_max += 80
            self.hp = self.hp_max
            self.mana = self.mana_max
            return True
        return False

    def cast_time_slow(self) -> bool:
        if self.mana >= 20:
            self.mana -= 20
            self.time_slow = 3.5
            return True
        return False

    def update(self, dt: float, world, mana_regen_mult: float = 1.0) -> None:
        if self.jump_time > 0:
            self.jump_time -= dt
        if self.time_slow > 0:
            self.time_slow -= dt

        next_x = self.x + self.vx * dt
        test_rect = pygame.Rect(int(next_x), int(self.y), self.w, self.h)
        if not world.is_rect_blocked(test_rect):
            self.x = next_x

        next_y = self.y + self.vy * dt
        test_rect = pygame.Rect(int(self.x), int(next_y), self.w, self.h)
        if not world.is_rect_blocked(test_rect):
            self.y = next_y

        self.x = max(-200000, min(200000, self.x))
        self.y = max(-200000, min(200000, self.y))

        self.mana = min(self.mana_max, self.mana + int(6 * mana_regen_mult * dt))

    def draw(self, surface: pygame.Surface, camera, t: float) -> None:
        sx, sy = camera.world_to_screen(self.x, self.y)
        bob = math.sin(t * 8) * 2 if (abs(self.vx) + abs(self.vy)) > 0 else 0
        jump_offset = math.sin(max(0.0, self.jump_time) * math.pi * 2) * 12 if self.jump_time > 0 else 0

        body_rect = pygame.Rect(sx + 4, sy + 16 - int(bob) - int(jump_offset), self.w - 8, self.h - 16)
        pygame.draw.rect(surface, (82, 98, 245), body_rect, border_radius=6)

        head_pos = (sx + self.w // 2, sy + 10 - int(bob) - int(jump_offset))
        pygame.draw.circle(surface, (245, 220, 210), head_pos, 9)
        pygame.draw.circle(surface, (40, 70, 200), (head_pos[0] - 3, head_pos[1] - 1), 2)
        pygame.draw.circle(surface, (40, 70, 200), (head_pos[0] + 3, head_pos[1] - 1), 2)

        hair_color = (180, 80, 240) if not self.cheat_mode else (240, 230, 90)
        pygame.draw.line(surface, hair_color, (head_pos[0] - 8, head_pos[1] - 7), (head_pos[0], head_pos[1] - 12), 3)
        pygame.draw.line(surface, hair_color, (head_pos[0], head_pos[1] - 12), (head_pos[0] + 8, head_pos[1] - 7), 3)

        fx = int(head_pos[0] + self.facing.x * 13)
        fy = int(head_pos[1] + self.facing.y * 13)
        pygame.draw.line(surface, (255, 220, 120), head_pos, (fx, fy), 2)

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "hp_max": self.hp_max,
            "mana": self.mana,
            "mana_max": self.mana_max,
            "level": self.level,
            "exp": self.exp,
            "reputation": self.reputation,
            "cheat_mode": self.cheat_mode,
            "hotbar": self.hotbar,
            "inventory": self.inventory,
        }

    def load_dict(self, data: dict) -> None:
        self.x = data.get("x", self.x)
        self.y = data.get("y", self.y)
        self.hp = data.get("hp", self.hp)
        self.hp_max = data.get("hp_max", self.hp_max)
        self.mana = data.get("mana", self.mana)
        self.mana_max = data.get("mana_max", self.mana_max)
        self.level = data.get("level", self.level)
        self.exp = data.get("exp", self.exp)
        self.reputation = data.get("reputation", self.reputation)
        self.cheat_mode = data.get("cheat_mode", self.cheat_mode)
        self.hotbar = data.get("hotbar", self.hotbar)
        self.inventory = data.get("inventory", self.inventory)
