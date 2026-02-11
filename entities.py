"""Entities: mobs, NPCs, bosses with simple AI, factions, A* and dialogue trees."""

from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass, field

import pygame

from localization import localize_entity
from world import TILE_SIZE


def astar_path(start: tuple[int, int], goal: tuple[int, int], world, max_nodes: int = 300) -> list[tuple[int, int]]:
    if start == goal:
        return [start]

    def h(a: tuple[int, int], b: tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    open_set: list[tuple[int, tuple[int, int]]] = []
    heapq.heappush(open_set, (0, start))
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    g_score = {start: 0}
    explored = 0

    while open_set and explored < max_nodes:
        explored += 1
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        cx, cy = current
        for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
            if world.is_solid_tile(nx, ny):
                continue
            tentative = g_score[current] + 1
            if tentative < g_score.get((nx, ny), 10**9):
                came_from[(nx, ny)] = current
                g_score[(nx, ny)] = tentative
                f = tentative + h((nx, ny), goal)
                heapq.heappush(open_set, (f, (nx, ny)))
    return []


@dataclass
class BaseEntity:
    x: float
    y: float
    etype: str
    faction: str
    hp: int
    speed: float
    radius: int = 12
    state: str = "wander"
    talk_cooldown: float = 0.0
    ai_timer: float = 0.0
    dir: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(1, 0))

    def pos(self) -> tuple[float, float]:
        return self.x, self.y

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)


class EntityManager:
    def __init__(self, world, seed: int = 77) -> None:
        self.world = world
        self.rng = random.Random(seed)
        self.entities: list[BaseEntity] = []
        self.dialogue_trees = {
            "villager": [
                "Вчера луна была фиолетовой...",
                "Пожалуйста, защити нашу маленькую деревню!",
                "Говорят, по ночам в руинах поёт дракон.",
            ],
            "merchant": [
                "Свежие зелья! Редкая руда! Лучшие товары!",
                "Принеси ядра монстров, и я щедро заплачу.",
                "Караван пропал на севере. Очень странно...",
            ],
            "waifu": [
                "Сэмпай, твоя аура становится всё сильнее!",
                "Я помогу твоей базе, если построишь дом.",
                "Герой-соперник бросил вызов твоей легенде.",
            ],
        }
        self.faction_relations: dict[tuple[str, str], int] = {
            ("player", "villagers"): 10,
            ("player", "monsters"): -80,
            ("villagers", "monsters"): -90,
        }
        self.spawn_initial_population()

    def spawn_initial_population(self) -> None:
        for _ in range(12):
            x = self.rng.randint(-700, 700)
            y = self.rng.randint(-700, 700)
            self.entities.append(BaseEntity(x, y, "slime", "monsters", hp=26, speed=70, radius=11))
        for _ in range(6):
            x = self.rng.randint(-900, 900)
            y = self.rng.randint(-900, 900)
            self.entities.append(BaseEntity(x, y, "goblin", "monsters", hp=38, speed=88, radius=12))
        for _ in range(5):
            x = self.rng.randint(-800, 800)
            y = self.rng.randint(-800, 800)
            self.entities.append(BaseEntity(x, y, "wolf", "monsters", hp=32, speed=105, radius=10))
        for role in ["villager", "villager", "merchant", "waifu"]:
            x = self.rng.randint(-400, 400)
            y = self.rng.randint(-400, 400)
            self.entities.append(BaseEntity(x, y, role, "villagers", hp=70, speed=68, radius=12))
        self.entities.append(BaseEntity(620, -420, "dragon", "boss", hp=360, speed=95, radius=20))
        self.entities.append(BaseEntity(-760, 500, "demon_lord", "boss", hp=460, speed=75, radius=22))

    def summon_ally(self, x: float, y: float, ally_type: str = "spirit") -> BaseEntity:
        stats = {
            "spirit": (95, 125, 10),
            "wolf_ally": (120, 140, 11),
            "knight": (170, 95, 13),
        }.get(ally_type, (90, 120, 10))
        ent = BaseEntity(x, y, ally_type, "allies", hp=stats[0], speed=stats[1], radius=stats[2])
        ent.state = "assist"
        self.entities.append(ent)
        return ent

    def spawn_near_player(self, player_x: float, player_y: float) -> None:
        if len(self.entities) > 55:
            return
        if self.rng.random() < 0.02:
            etype = self.rng.choice(["slime", "goblin", "wolf"])
            angle = self.rng.uniform(0, math.tau)
            dist = self.rng.uniform(280, 700)
            x = player_x + math.cos(angle) * dist
            y = player_y + math.sin(angle) * dist
            stats = {
                "slime": (25, 70, 10),
                "goblin": (35, 90, 12),
                "wolf": (30, 108, 10),
            }[etype]
            self.entities.append(BaseEntity(x, y, etype, "monsters", hp=stats[0], speed=stats[1], radius=stats[2]))

    def nearest_entity(self, x: float, y: float, max_dist: float, faction_filter: str | None = None) -> BaseEntity | None:
        found = None
        best = max_dist * max_dist
        for ent in self.entities:
            if ent.hp <= 0:
                continue
            if faction_filter and ent.faction != faction_filter:
                continue
            d2 = (ent.x - x) ** 2 + (ent.y - y) ** 2
            if d2 < best:
                best = d2
                found = ent
        return found

    def get_talk_line(self, ent: BaseEntity) -> str:
        lines = self.dialogue_trees.get(ent.etype, ["..."])
        return self.rng.choice(lines)

    def damage_entity(self, ent: BaseEntity, amount: int) -> bool:
        ent.hp -= amount
        return ent.hp <= 0

    def update(self, dt: float, player, events_system) -> list[dict]:
        logs: list[dict] = []
        scale = 0.45 if player.time_slow > 0 else 1.0
        for ent in self.entities:
            if ent.hp <= 0:
                continue
            ent.ai_timer -= dt * scale
            if ent.talk_cooldown > 0:
                ent.talk_cooldown -= dt

            dx = player.x - ent.x
            dy = player.y - ent.y
            dist = math.hypot(dx, dy)

            if ent.ai_timer <= 0:
                ent.ai_timer = random.uniform(0.6, 1.6)
                if ent.faction in {"monsters", "boss"} and dist < 300:
                    ent.state = "chase"
                elif ent.faction == "allies":
                    ent.state = "assist"
                elif ent.faction == "villagers" and dist < 130:
                    ent.state = "social"
                else:
                    ent.state = "wander"
                    angle = random.uniform(0, math.tau)
                    ent.dir = pygame.Vector2(math.cos(angle), math.sin(angle))

            if ent.state == "chase" and dist > 2:
                sx, sy = int(ent.x // TILE_SIZE), int(ent.y // TILE_SIZE)
                gx, gy = int(player.x // TILE_SIZE), int(player.y // TILE_SIZE)
                path = astar_path((sx, sy), (gx, gy), self.world, max_nodes=220)
                if len(path) > 1:
                    nx, ny = path[1]
                    target_x = nx * TILE_SIZE + TILE_SIZE / 2
                    target_y = ny * TILE_SIZE + TILE_SIZE / 2
                    vec = pygame.Vector2(target_x - ent.x, target_y - ent.y)
                    if vec.length_squared() > 0:
                        ent.dir = vec.normalize()
                else:
                    vec = pygame.Vector2(dx, dy)
                    if vec.length_squared() > 0:
                        ent.dir = vec.normalize()

                speed = ent.speed * scale
                ent.x += ent.dir.x * speed * dt
                ent.y += ent.dir.y * speed * dt

                if dist < 28:
                    player.hp = max(0, player.hp - (6 if ent.faction == "boss" else 3))
            elif ent.state == "social":
                if dist < 80 and ent.talk_cooldown <= 0 and random.random() < 0.003:
                    logs.append({"type": "dialogue", "text": f"{localize_entity(ent.etype)}: {self.get_talk_line(ent)}"})
                    ent.talk_cooldown = 8.0
            elif ent.state == "assist":
                target = self.nearest_entity(ent.x, ent.y, 260, faction_filter="monsters")
                if target is None:
                    target = self.nearest_entity(ent.x, ent.y, 300, faction_filter="boss")
                if target is not None:
                    vec = pygame.Vector2(target.x - ent.x, target.y - ent.y)
                    if vec.length_squared() > 0:
                        ent.dir = vec.normalize()
                    speed = ent.speed * scale
                    ent.x += ent.dir.x * speed * dt
                    ent.y += ent.dir.y * speed * dt
                    if vec.length() < ent.radius + target.radius + 10:
                        target.hp -= 5
                else:
                    vec = pygame.Vector2(player.x - ent.x, player.y - ent.y)
                    if vec.length_squared() > 40:
                        ent.dir = vec.normalize()
                        ent.x += ent.dir.x * ent.speed * 0.7 * dt
                        ent.y += ent.dir.y * ent.speed * 0.7 * dt
            else:
                speed = ent.speed * 0.45 * scale
                ent.x += ent.dir.x * speed * dt
                ent.y += ent.dir.y * speed * dt

            # basic collision correction with solid tiles
            tile_x = int(ent.x // TILE_SIZE)
            tile_y = int(ent.y // TILE_SIZE)
            if self.world.is_solid_tile(tile_x, tile_y):
                ent.x -= ent.dir.x * ent.speed * dt
                ent.y -= ent.dir.y * ent.speed * dt
                ent.dir *= -1

        # remove dead entities and produce loot logs
        alive: list[BaseEntity] = []
        for ent in self.entities:
            if ent.hp > 0:
                alive.append(ent)
            else:
                if ent.faction in {"monsters", "boss"}:
                    drop = random.choice(["wood", "ore", "core", "gold"])
                    logs.append({"type": "loot", "item": drop, "x": ent.x, "y": ent.y, "exp": 14 if ent.faction == "monsters" else 60})
        self.entities = alive

        self.spawn_near_player(player.x, player.y)
        return logs

    def draw(self, surface: pygame.Surface, camera) -> None:
        for ent in self.entities:
            if ent.hp <= 0:
                continue
            sx, sy = camera.world_to_screen(ent.x, ent.y)
            if ent.etype == "slime":
                pygame.draw.circle(surface, (90, 220, 170), (int(sx), int(sy)), ent.radius)
                pygame.draw.circle(surface, (255, 255, 255), (int(sx - 4), int(sy - 4)), 2)
                pygame.draw.circle(surface, (255, 255, 255), (int(sx + 4), int(sy - 4)), 2)
            elif ent.etype == "goblin":
                pygame.draw.circle(surface, (60, 170, 60), (int(sx), int(sy - 8)), ent.radius - 2)
                pygame.draw.rect(surface, (120, 90, 45), (int(sx - 8), int(sy - 2), 16, 16), border_radius=4)
            elif ent.etype == "wolf":
                pygame.draw.ellipse(surface, (140, 140, 155), (int(sx - 11), int(sy - 6), 22, 12))
                pygame.draw.polygon(surface, (180, 180, 200), [(sx - 8, sy - 8), (sx - 4, sy - 14), (sx - 1, sy - 7)])
                pygame.draw.polygon(surface, (180, 180, 200), [(sx + 8, sy - 8), (sx + 4, sy - 14), (sx + 1, sy - 7)])
            elif ent.etype in {"villager", "merchant", "waifu"}:
                body = (200, 120, 220) if ent.etype == "waifu" else (190, 165, 100) if ent.etype == "merchant" else (120, 140, 230)
                pygame.draw.rect(surface, body, (int(sx - 8), int(sy - 2), 16, 16), border_radius=5)
                pygame.draw.circle(surface, (250, 220, 210), (int(sx), int(sy - 10)), 8)
                pygame.draw.circle(surface, (40, 70, 200), (int(sx - 3), int(sy - 11)), 2)
                pygame.draw.circle(surface, (40, 70, 200), (int(sx + 3), int(sy - 11)), 2)
                pygame.draw.line(surface, (220, 100, 250), (int(sx - 7), int(sy - 14)), (int(sx + 7), int(sy - 14)), 2)
            elif ent.etype in {"spirit", "wolf_ally", "knight"}:
                if ent.etype == "spirit":
                    pygame.draw.circle(surface, (160, 230, 255), (int(sx), int(sy)), ent.radius)
                    pygame.draw.circle(surface, (230, 255, 255), (int(sx), int(sy)), 5)
                elif ent.etype == "wolf_ally":
                    pygame.draw.ellipse(surface, (200, 220, 255), (int(sx - 11), int(sy - 7), 24, 14))
                    pygame.draw.circle(surface, (235, 245, 255), (int(sx + 8), int(sy - 3)), 4)
                else:
                    pygame.draw.rect(surface, (180, 190, 255), (int(sx - 9), int(sy - 8), 18, 20), border_radius=5)
                    pygame.draw.polygon(surface, (130, 150, 240), [(sx, sy - 16), (sx + 8, sy - 6), (sx - 8, sy - 6)])
            elif ent.etype == "dragon":
                pygame.draw.circle(surface, (180, 50, 50), (int(sx), int(sy)), 22)
                pygame.draw.polygon(surface, (255, 140, 60), [(sx, sy - 26), (sx + 30, sy), (sx, sy + 12)])
                pygame.draw.polygon(surface, (255, 140, 60), [(sx, sy - 26), (sx - 30, sy), (sx, sy + 12)])
            else:
                pygame.draw.circle(surface, (95, 25, 120), (int(sx), int(sy)), 24)
                pygame.draw.circle(surface, (210, 70, 250), (int(sx), int(sy)), 10, 2)

            hp_ratio = max(0, ent.hp) / (460 if ent.etype == "demon_lord" else 360 if ent.etype == "dragon" else 70)
            pygame.draw.rect(surface, (25, 25, 35), (int(sx - 15), int(sy - ent.radius - 12), 30, 4))
            pygame.draw.rect(surface, (240, 70, 90), (int(sx - 15), int(sy - ent.radius - 12), int(30 * hp_ratio), 4))
