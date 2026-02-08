"""Advanced procedural visual layers and anime-style FX helpers."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def color_lerp(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        int(lerp(c1[0], c2[0], t)),
        int(lerp(c1[1], c2[1], t)),
        int(lerp(c1[2], c2[2], t)),
    )


class SkyRenderer:
    def __init__(self) -> None:
        self.day_top = (110, 170, 255)
        self.day_bottom = (220, 245, 255)
        self.sunset_top = (190, 90, 160)
        self.sunset_bottom = (255, 180, 120)
        self.night_top = (28, 26, 64)
        self.night_bottom = (45, 38, 82)

    def _phase(self, time_of_day: float) -> str:
        if 6 <= time_of_day < 17:
            return "day"
        if 17 <= time_of_day < 20:
            return "sunset"
        if 4 <= time_of_day < 6:
            return "dawn"
        return "night"

    def _gradient(self, phase: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        if phase == "day":
            return self.day_top, self.day_bottom
        if phase == "sunset":
            return self.sunset_top, self.sunset_bottom
        if phase == "dawn":
            return self.sunset_bottom, self.day_bottom
        return self.night_top, self.night_bottom

    def draw(self, surface: pygame.Surface, time_of_day: float) -> None:
        w, h = surface.get_size()
        phase = self._phase(time_of_day)
        top, bottom = self._gradient(phase)
        for y in range(h):
            t = y / max(1, h - 1)
            col = color_lerp(top, bottom, t)
            pygame.draw.line(surface, col, (0, y), (w, y))

        # stylized sun/moon
        angle = (time_of_day / 24.0) * math.tau
        cx = int(w * 0.5 + math.cos(angle - math.pi / 2) * 260)
        cy = int(h * 0.72 + math.sin(angle - math.pi / 2) * 170)
        if phase == "night":
            pygame.draw.circle(surface, (230, 230, 255), (cx, cy), 18)
            pygame.draw.circle(surface, (28, 26, 64), (cx + 7, cy - 5), 16)
        else:
            pygame.draw.circle(surface, (255, 245, 170), (cx, cy), 20)
            glow = pygame.Surface((90, 90), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 220, 130, 65), (45, 45), 42)
            surface.blit(glow, (cx - 45, cy - 45))


@dataclass
class DamageNumber:
    x: float
    y: float
    text: str
    color: tuple[int, int, int]
    life: float = 0.85
    vy: float = -30.0


class DamageNumberSystem:
    def __init__(self) -> None:
        self.items: list[DamageNumber] = []

    def spawn(self, x: float, y: float, value: int, critical: bool = False) -> None:
        color = (255, 230, 120) if critical else (255, 170, 170)
        self.items.append(DamageNumber(x, y, str(value), color, life=1.2 if critical else 0.85))

    def update(self, dt: float) -> None:
        alive = []
        for n in self.items:
            n.life -= dt
            n.y += n.vy * dt
            n.vy -= 20 * dt
            if n.life > 0:
                alive.append(n)
        self.items = alive

    def draw(self, surface: pygame.Surface, camera, font: pygame.font.Font) -> None:
        for n in self.items:
            sx, sy = camera.world_to_screen(n.x, n.y)
            alpha = int(255 * min(1.0, n.life / 0.85))
            label = font.render(n.text, True, n.color)
            sprite = pygame.Surface((label.get_width(), label.get_height()), pygame.SRCALPHA)
            sprite.blit(label, (0, 0))
            sprite.set_alpha(alpha)
            surface.blit(sprite, (sx, sy))


class WeatherRenderer:
    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)
        self.clouds = [
            {
                "x": self.rng.randint(-200, 1000),
                "y": self.rng.randint(10, 170),
                "speed": self.rng.uniform(8, 25),
                "size": self.rng.randint(40, 90),
            }
            for _ in range(12)
        ]
        self.rain_drops = [
            {
                "x": self.rng.randint(0, 800),
                "y": self.rng.randint(-600, 600),
                "vy": self.rng.uniform(260, 520),
                "len": self.rng.randint(8, 16),
            }
            for _ in range(260)
        ]

    def update(self, dt: float, weather: str, screen_w: int, screen_h: int) -> None:
        for c in self.clouds:
            c["x"] += c["speed"] * dt
            if c["x"] > screen_w + 120:
                c["x"] = -150
                c["y"] = self.rng.randint(10, 170)
        if weather == "rain":
            for d in self.rain_drops:
                d["y"] += d["vy"] * dt
                d["x"] += 35 * dt
                if d["y"] > screen_h + 20:
                    d["y"] = -self.rng.randint(20, 300)
                    d["x"] = self.rng.randint(-20, screen_w + 20)

    def draw(self, surface: pygame.Surface, weather: str) -> None:
        # Clouds always visible
        for c in self.clouds:
            cloud = pygame.Surface((c["size"] * 2, c["size"]), pygame.SRCALPHA)
            pygame.draw.ellipse(cloud, (255, 255, 255, 55), (0, 8, c["size"], c["size"] - 16))
            pygame.draw.ellipse(cloud, (255, 255, 255, 80), (c["size"] // 2, 0, c["size"], c["size"] - 6))
            pygame.draw.ellipse(cloud, (255, 255, 255, 50), (c["size"], 10, c["size"], c["size"] - 18))
            surface.blit(cloud, (int(c["x"]), int(c["y"])))

        if weather == "rain":
            for d in self.rain_drops:
                pygame.draw.line(
                    surface,
                    (140, 180, 255),
                    (int(d["x"]), int(d["y"])),
                    (int(d["x"] - 4), int(d["y"] + d["len"])),
                    1,
                )


class AuraRenderer:
    def __init__(self) -> None:
        self.phase = 0.0

    def update(self, dt: float) -> None:
        self.phase += dt

    def draw_player_aura(self, surface: pygame.Surface, camera, player, cheat_mode: bool, time_slow: bool) -> None:
        px, py = player.center
        sx, sy = camera.world_to_screen(px, py)
        if not cheat_mode and not time_slow:
            return

        base = 22 + int((math.sin(self.phase * 6) + 1) * 3)
        color = (255, 225, 110) if cheat_mode else (150, 220, 255)
        for ring in range(3):
            radius = base + ring * 8
            alpha = max(25, 110 - ring * 30)
            aura = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(aura, (*color, alpha), (radius + 2, radius + 2), radius, 2)
            surface.blit(aura, (sx - radius - 2, sy - radius - 2))

        # small sparkle burst
        for i in range(8):
            a = self.phase * 3 + i * (math.tau / 8)
            rx = sx + math.cos(a) * (base + 12)
            ry = sy + math.sin(a) * (base + 12)
            pygame.draw.circle(surface, color, (int(rx), int(ry)), 2)


class RuneCircleRenderer:
    def __init__(self) -> None:
        self.t = 0.0

    def update(self, dt: float) -> None:
        self.t += dt

    def draw(self, surface: pygame.Surface, camera, x: float, y: float, active: bool) -> None:
        if not active:
            return
        sx, sy = camera.world_to_screen(x, y)
        radius = 28
        layer = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
        cx, cy = radius + 4, radius + 4
        pygame.draw.circle(layer, (190, 120, 255, 120), (cx, cy), radius, 2)
        pygame.draw.circle(layer, (130, 220, 255, 100), (cx, cy), radius - 8, 1)
        for i in range(6):
            a = self.t * 1.5 + i * (math.tau / 6)
            x1 = cx + math.cos(a) * (radius - 3)
            y1 = cy + math.sin(a) * (radius - 3)
            x2 = cx + math.cos(a + 0.25) * (radius - 12)
            y2 = cy + math.sin(a + 0.25) * (radius - 12)
            pygame.draw.line(layer, (220, 160, 255, 140), (x1, y1), (x2, y2), 2)
        surface.blit(layer, (sx - cx, sy - cy))


class ScreenShake:
    def __init__(self) -> None:
        self.time_left = 0.0
        self.intensity = 0.0

    def kick(self, intensity: float, duration: float = 0.16) -> None:
        self.time_left = max(self.time_left, duration)
        self.intensity = max(self.intensity, intensity)

    def update(self, dt: float) -> tuple[int, int]:
        if self.time_left <= 0:
            self.intensity = 0
            return 0, 0
        self.time_left -= dt
        fade = max(0.0, self.time_left / 0.16)
        amp = self.intensity * fade
        return random.randint(-int(amp), int(amp)), random.randint(-int(amp), int(amp))
