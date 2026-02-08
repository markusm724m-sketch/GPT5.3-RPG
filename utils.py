"""Utility helpers for camera, collisions, particles and save/load."""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pygame


def clamp(value: float, vmin: float, vmax: float) -> float:
    return max(vmin, min(value, vmax))


def aabb_collision(a: pygame.Rect, b: pygame.Rect) -> bool:
    return a.colliderect(b)


@dataclass
class Camera:
    width: int
    height: int
    x: float = 0
    y: float = 0

    def update(self, target_x: float, target_y: float, smoothing: float = 0.12) -> None:
        self.x += (target_x - self.width // 2 - self.x) * smoothing
        self.y += (target_y - self.height // 2 - self.y) * smoothing

    def world_to_screen(self, wx: float, wy: float) -> tuple[int, int]:
        return int(wx - self.x), int(wy - self.y)

    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(rect.x - int(self.x), rect.y - int(self.y), rect.width, rect.height)


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    color: tuple[int, int, int]
    gravity: float = 0.0

    def update(self, dt: float) -> bool:
        self.life -= dt
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return self.life > 0

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        alpha = int(255 * max(0.0, self.life / self.max_life))
        radius = max(1, int(self.size * (0.3 + 0.7 * self.life / self.max_life)))
        sx, sy = camera.world_to_screen(self.x, self.y)
        p_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(p_surf, (*self.color, alpha), (radius, radius), radius)
        surface.blit(p_surf, (sx - radius, sy - radius))


class ParticleSystem:
    def __init__(self) -> None:
        self.particles: list[Particle] = []

    def emit_burst(
        self,
        x: float,
        y: float,
        amount: int,
        color: tuple[int, int, int],
        speed: float,
        life: float,
        gravity: float = 0.0,
    ) -> None:
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            magnitude = random.uniform(speed * 0.25, speed)
            vx = math.cos(angle) * magnitude
            vy = math.sin(angle) * magnitude
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=vx,
                    vy=vy,
                    life=life,
                    max_life=life,
                    size=random.uniform(1.5, 4.0),
                    color=color,
                    gravity=gravity,
                )
            )

    def update(self, dt: float) -> None:
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        for particle in self.particles:
            particle.draw(surface, camera)


def save_json(path: str | Path, data: dict[str, Any]) -> None:
    target = Path(path)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any] | None:
    target = Path(path)
    if not target.exists():
        return None
    return json.loads(target.read_text(encoding="utf-8"))
