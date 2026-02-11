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


def _wrap_hour(value: float) -> float:
    return value % 24.0


class SkyRenderer:
    def __init__(self, seed: int = 0) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.stars = self._generate_stars()
        self.nebulae = self._generate_nebulae()

    def _phase(self, time_of_day: float) -> str:
        t = _wrap_hour(time_of_day)
        if 6 <= t < 17:
            return "day"
        if 17 <= t < 20:
            return "sunset"
        if 4 <= t < 6:
            return "dawn"
        return "night"

    def _sky_keys(self) -> list[tuple[float, tuple[int, int, int], tuple[int, int, int]]]:
        return [
            (0.0, (18, 24, 58), (32, 40, 76)),
            (4.5, (50, 70, 125), (100, 122, 170)),
            (6.5, (115, 176, 255), (227, 246, 255)),
            (16.5, (122, 180, 255), (235, 248, 255)),
            (18.3, (228, 122, 160), (255, 196, 136)),
            (20.5, (62, 54, 98), (84, 72, 122)),
            (24.0, (18, 24, 58), (32, 40, 76)),
        ]

    def _gradient(self, time_of_day: float) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        t = _wrap_hour(time_of_day)
        keys = self._sky_keys()
        for i in range(len(keys) - 1):
            t0, top0, bot0 = keys[i]
            t1, top1, bot1 = keys[i + 1]
            if t0 <= t <= t1:
                phase_t = (t - t0) / max(0.001, t1 - t0)
                return color_lerp(top0, top1, phase_t), color_lerp(bot0, bot1, phase_t)
        return keys[-1][1], keys[-1][2]

    def _generate_stars(self) -> list[dict[str, float]]:
        stars: list[dict[str, float]] = []
        for _ in range(180):
            stars.append(
                {
                    "x": self.rng.random(),
                    "y": self.rng.random() * 0.72,
                    "size": self.rng.choice([1.0, 1.0, 1.0, 1.5, 2.0]),
                    "twinkle": self.rng.uniform(0.8, 2.4),
                    "phase": self.rng.uniform(0.0, math.tau),
                    "base": self.rng.randint(165, 245),
                }
            )
        return stars

    def _generate_nebulae(self) -> list[dict[str, float]]:
        blobs: list[dict[str, float]] = []
        for _ in range(6):
            blobs.append(
                {
                    "x": self.rng.random(),
                    "y": self.rng.uniform(0.1, 0.58),
                    "r": self.rng.uniform(0.08, 0.18),
                    "phase": self.rng.uniform(0.0, math.tau),
                }
            )
        return blobs

    def _night_strength(self, time_of_day: float) -> float:
        t = _wrap_hour(time_of_day)
        if 6 <= t < 17:
            return 0.0
        if 4 <= t < 6:
            return (6 - t) / 2
        if 17 <= t < 20:
            return (t - 17) / 3
        return 1.0

    def draw(self, surface: pygame.Surface, time_of_day: float) -> None:
        w, h = surface.get_size()
        phase = self._phase(time_of_day)
        top, bottom = self._gradient(time_of_day)
        for y in range(h):
            t = y / max(1, h - 1)
            col = color_lerp(top, bottom, t)
            pygame.draw.line(surface, col, (0, y), (w, y))

        night = self._night_strength(time_of_day)
        if night > 0:
            nebula = pygame.Surface((w, h), pygame.SRCALPHA)
            for blob in self.nebulae:
                cx = int(blob["x"] * w + math.sin(time_of_day * 0.11 + blob["phase"]) * 22)
                cy = int(blob["y"] * h)
                radius = int(blob["r"] * min(w, h))
                alpha = int(42 * night)
                pygame.draw.circle(nebula, (115, 85, 190, alpha), (cx, cy), radius)
                pygame.draw.circle(nebula, (85, 128, 220, alpha // 2), (cx + radius // 3, cy), radius // 2)
            surface.blit(nebula, (0, 0))

            star_layer = pygame.Surface((w, h), pygame.SRCALPHA)
            for s in self.stars:
                twinkle = 0.45 + 0.55 * math.sin(time_of_day * s["twinkle"] + s["phase"])
                alpha = int(min(255, s["base"] * night * (0.65 + twinkle * 0.35)))
                sx = int(s["x"] * w)
                sy = int(s["y"] * h)
                radius = int(s["size"])
                pygame.draw.circle(star_layer, (235, 235, 255, alpha), (sx, sy), max(1, radius))
            surface.blit(star_layer, (0, 0))

        # Sun/moon trajectory.
        angle = ((_wrap_hour(time_of_day) - 6.0) / 24.0) * math.tau
        cx = int(w * 0.5 + math.cos(angle) * (w * 0.42))
        cy = int(h * 0.85 - math.sin(angle) * (h * 0.62))
        if phase == "night":
            moon_glow = pygame.Surface((160, 160), pygame.SRCALPHA)
            pygame.draw.circle(moon_glow, (170, 180, 255, 40), (80, 80), 68)
            pygame.draw.circle(moon_glow, (140, 160, 255, 28), (80, 80), 48)
            surface.blit(moon_glow, (cx - 80, cy - 80))
            pygame.draw.circle(surface, (242, 242, 255), (cx, cy), 16)
            pygame.draw.circle(surface, (38, 38, 74), (cx + 6, cy - 5), 14)
        else:
            sun_glow = pygame.Surface((220, 220), pygame.SRCALPHA)
            pygame.draw.circle(sun_glow, (255, 220, 132, 45), (110, 110), 96)
            pygame.draw.circle(sun_glow, (255, 190, 110, 32), (110, 110), 68)
            surface.blit(sun_glow, (cx - 110, cy - 110))
            pygame.draw.circle(surface, (255, 244, 182), (cx, cy), 20)
            pygame.draw.circle(surface, (255, 250, 210), (cx - 5, cy - 5), 7)

        # Subtle horizon haze for depth.
        haze = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(6):
            band_h = int(h * 0.08 + i * h * 0.035)
            alpha = 12 - i
            pygame.draw.rect(haze, (255, 210, 190, max(0, alpha)), (0, h - band_h, w, band_h))
        surface.blit(haze, (0, 0))


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
        self.wind_phase = self.rng.uniform(0, math.tau)
        self.clouds = [
            {
                "x": self.rng.uniform(-240, 1020),
                "y": self.rng.uniform(20, 220),
                "speed": self.rng.uniform(8, 30),
                "size": self.rng.randint(56, 128),
                "tone": self.rng.randint(208, 245),
                "phase": self.rng.uniform(0, math.tau),
            }
            for _ in range(14)
        ]
        self.rain_drops = [
            {
                "x": self.rng.uniform(0, 800),
                "y": self.rng.uniform(-600, 600),
                "vx": self.rng.uniform(-40, -20),
                "vy": self.rng.uniform(340, 620),
                "len": self.rng.randint(10, 18),
                "trail": [],
            }
            for _ in range(320)
        ]
        self.snow_flakes = [
            {
                "x": self.rng.uniform(0, 800),
                "y": self.rng.uniform(-600, 600),
                "vy": self.rng.uniform(38, 105),
                "size": self.rng.uniform(1.0, 2.8),
                "drift": self.rng.uniform(18, 45),
                "phase": self.rng.uniform(0, math.tau),
            }
            for _ in range(180)
        ]
        self.splashes: list[dict[str, float]] = []
        self.arcane_streaks: list[dict[str, float]] = []

    def update(self, dt: float, weather: str, screen_w: int, screen_h: int) -> None:
        self.wind_phase += dt * 0.9

        for c in self.clouds:
            drift = math.sin(self.wind_phase + c["phase"]) * 7
            c["x"] += (c["speed"] + drift) * dt
            if c["x"] > screen_w + 260:
                c["x"] = -280
                c["y"] = self.rng.uniform(20, 220)

        if weather == "rain":
            for d in self.rain_drops:
                d["trail"].append((d["x"], d["y"]))
                if len(d["trail"]) > 4:
                    d["trail"].pop(0)
                d["x"] += d["vx"] * dt
                d["y"] += d["vy"] * dt
                if d["y"] > screen_h + 15:
                    self.splashes.append(
                        {
                            "x": d["x"],
                            "y": screen_h - self.rng.uniform(4, 22),
                            "life": 0.22,
                            "max_life": 0.22,
                            "r": self.rng.uniform(3.0, 7.5),
                        }
                    )
                    d["y"] = -self.rng.uniform(20, 420)
                    d["x"] = self.rng.uniform(-30, screen_w + 30)
                    d["trail"].clear()
        else:
            for d in self.rain_drops:
                d["trail"].clear()

        if weather == "snow":
            for s in self.snow_flakes:
                s["y"] += s["vy"] * dt
                s["x"] += math.sin(self.wind_phase + s["phase"]) * s["drift"] * dt
                if s["y"] > screen_h + 8:
                    s["y"] = -self.rng.uniform(8, 220)
                    s["x"] = self.rng.uniform(-10, screen_w + 10)

        if weather == "arcane_wind":
            spawn_count = 2 + int(self.rng.random() < 0.3)
            for _ in range(spawn_count):
                if len(self.arcane_streaks) > 170:
                    break
                self.arcane_streaks.append(
                    {
                        "x": self.rng.uniform(-40, screen_w + 40),
                        "y": self.rng.uniform(-20, screen_h + 20),
                        "vx": self.rng.uniform(90, 220),
                        "vy": self.rng.uniform(-70, 70),
                        "life": self.rng.uniform(0.3, 0.7),
                        "max_life": 0.7,
                        "len": self.rng.uniform(14, 34),
                    }
                )

        alive_streaks = []
        for st in self.arcane_streaks:
            st["life"] -= dt
            st["x"] += st["vx"] * dt
            st["y"] += st["vy"] * dt
            if st["life"] > 0:
                alive_streaks.append(st)
        self.arcane_streaks = alive_streaks

        alive_splashes = []
        for sp in self.splashes:
            sp["life"] -= dt
            if sp["life"] > 0:
                alive_splashes.append(sp)
        self.splashes = alive_splashes

    def _draw_cloud(self, surface: pygame.Surface, cloud: dict[str, float]) -> None:
        size = int(cloud["size"])
        tone = int(cloud["tone"])
        cloud_surface = pygame.Surface((size * 2, size), pygame.SRCALPHA)
        pygame.draw.ellipse(cloud_surface, (tone, tone, tone, 36), (0, size // 4, size, size // 2))
        pygame.draw.ellipse(cloud_surface, (tone, tone, tone, 62), (size // 2, 0, size, int(size * 0.72)))
        pygame.draw.ellipse(
            cloud_surface,
            (tone, tone, tone, 48),
            (int(size * 1.05), int(size * 0.22), int(size * 0.86), int(size * 0.5)),
        )
        surface.blit(cloud_surface, (int(cloud["x"]), int(cloud["y"])))

    def draw(self, surface: pygame.Surface, weather: str) -> None:
        w, h = surface.get_size()

        for cloud in self.clouds:
            self._draw_cloud(surface, cloud)

        fx_layer = pygame.Surface((w, h), pygame.SRCALPHA)
        if weather == "rain":
            for d in self.rain_drops:
                trail = d["trail"]
                for i in range(1, len(trail)):
                    p0 = trail[i - 1]
                    p1 = trail[i]
                    alpha = int(25 + i * 16)
                    pygame.draw.line(
                        fx_layer,
                        (120, 170, 255, alpha),
                        (int(p0[0]), int(p0[1])),
                        (int(p1[0]), int(p1[1])),
                        1,
                    )
                pygame.draw.line(
                    fx_layer,
                    (170, 210, 255, 180),
                    (int(d["x"]), int(d["y"])),
                    (int(d["x"] + d["vx"] * 0.03), int(d["y"] + d["len"])),
                    1,
                )

            for sp in self.splashes:
                fade = max(0.0, sp["life"] / sp["max_life"])
                radius = sp["r"] * (1.0 + (1.0 - fade) * 1.2)
                alpha = int(130 * fade)
                pygame.draw.circle(fx_layer, (170, 210, 255, alpha), (int(sp["x"]), int(sp["y"])), int(radius), 1)

            rain_tint = pygame.Surface((w, h), pygame.SRCALPHA)
            rain_tint.fill((0, 18, 42, 22))
            surface.blit(rain_tint, (0, 0))

        if weather == "snow":
            for s in self.snow_flakes:
                sparkle = 0.75 + 0.25 * math.sin(self.wind_phase * 2 + s["phase"])
                alpha = int(140 + 90 * sparkle)
                pygame.draw.circle(fx_layer, (245, 248, 255, alpha), (int(s["x"]), int(s["y"])), max(1, int(s["size"])))

        if weather == "arcane_wind":
            for st in self.arcane_streaks:
                fade = max(0.0, st["life"] / st["max_life"])
                alpha = int(140 * fade)
                x1, y1 = int(st["x"]), int(st["y"])
                x2, y2 = int(st["x"] - st["len"]), int(st["y"] - st["len"] * 0.35)
                pygame.draw.line(fx_layer, (190, 120, 255, alpha), (x1, y1), (x2, y2), 2)
                pygame.draw.line(fx_layer, (120, 225, 255, alpha // 2), (x1, y1), (x2, y2), 1)

            arcane_tint = pygame.Surface((w, h), pygame.SRCALPHA)
            arcane_tint.fill((22, 0, 40, 22))
            surface.blit(arcane_tint, (0, 0))

        surface.blit(fx_layer, (0, 0))


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

        base = 24 + int((math.sin(self.phase * 6.5) + 1) * 3)
        color = (255, 225, 110) if cheat_mode else (150, 220, 255)

        glow = pygame.Surface((base * 4, base * 4), pygame.SRCALPHA)
        for i in range(4):
            radius = base + i * 12
            alpha = max(8, 34 - i * 6)
            pygame.draw.circle(glow, (*color, alpha), (base * 2, base * 2), radius)
        surface.blit(glow, (sx - base * 2, sy - base * 2))

        for ring in range(3):
            radius = base + ring * 8
            alpha = max(25, 115 - ring * 32)
            aura = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(aura, (*color, alpha), (radius + 2, radius + 2), radius, 2)
            surface.blit(aura, (sx - radius - 2, sy - radius - 2))

        for i in range(10):
            a = self.phase * 3.2 + i * (math.tau / 10)
            rx = sx + math.cos(a) * (base + 12)
            ry = sy + math.sin(a * 1.1) * (base + 12)
            pygame.draw.circle(surface, color, (int(rx), int(ry)), 2)


class RuneCircleRenderer:
    def __init__(self) -> None:
        self.t = 0.0
        self.particles: list[dict[str, float]] = []

    def update(self, dt: float) -> None:
        self.t += dt
        alive: list[dict[str, float]] = []
        for p in self.particles:
            p["life"] -= dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if p["life"] > 0:
                alive.append(p)
        self.particles = alive

    def draw(self, surface: pygame.Surface, camera, x: float, y: float, active: bool) -> None:
        if not active:
            return

        if random.random() < 0.35:
            angle = random.uniform(0, math.tau)
            speed = random.uniform(14, 36)
            self.particles.append(
                {
                    "x": x + math.cos(angle) * random.uniform(6, 28),
                    "y": y + math.sin(angle) * random.uniform(6, 28),
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "life": random.uniform(0.5, 0.9),
                    "max_life": 0.9,
                }
            )

        sx, sy = camera.world_to_screen(x, y)
        radius = 30 + int(math.sin(self.t * 2.2) * 4)
        layer = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
        cx, cy = radius + 5, radius + 5
        pygame.draw.circle(layer, (190, 120, 255, 128), (cx, cy), radius, 2)
        pygame.draw.circle(layer, (130, 220, 255, 105), (cx, cy), radius - 8, 1)
        pygame.draw.circle(layer, (255, 215, 255, 85), (cx, cy), radius - 15, 1)
        for i in range(8):
            a = self.t * 1.7 + i * (math.tau / 8)
            x1 = cx + math.cos(a) * (radius - 4)
            y1 = cy + math.sin(a) * (radius - 4)
            x2 = cx + math.cos(a + 0.36) * (radius - 14)
            y2 = cy + math.sin(a + 0.36) * (radius - 14)
            pygame.draw.line(layer, (220, 160, 255, 145), (x1, y1), (x2, y2), 2)

        for i in range(6):
            a = -self.t * 1.25 + i * (math.tau / 6)
            px = cx + math.cos(a) * (radius - 10)
            py = cy + math.sin(a) * (radius - 10)
            pygame.draw.circle(layer, (130, 230, 255, 150), (int(px), int(py)), 2)

        surface.blit(layer, (sx - cx, sy - cy))

        particles_layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for p in self.particles:
            px_s, py_s = camera.world_to_screen(p["x"], p["y"])
            max_life = max(0.001, float(p.get("max_life", 0.9)))
            alpha = int(max(0, min(255, 200 * (float(p.get("life", 0.0)) / max_life))))
            if alpha <= 0:
                continue
            pygame.draw.circle(particles_layer, (220, 160, 255, alpha), (int(px_s), int(py_s)), 2)
        surface.blit(particles_layer, (0, 0))


class PostProcessing:
    def __init__(self) -> None:
        self.vignette_strength = 0.33
        self.bloom_intensity = 0.28
        self._vignette_cache: dict[tuple[int, int, int], pygame.Surface] = {}

    def _get_vignette(self, size: tuple[int, int]) -> pygame.Surface:
        w, h = size
        strength = int(self.vignette_strength * 100)
        key = (w, h, strength)
        if key in self._vignette_cache:
            return self._vignette_cache[key]

        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        steps = 14
        max_inset = int(min(w, h) * 0.28)
        for i in range(steps):
            t = i / max(1, steps - 1)
            inset = int(max_inset * t)
            alpha = int((1.0 - t) ** 1.8 * (18 + strength // 7))
            rect = pygame.Rect(inset, inset, w - inset * 2, h - inset * 2)
            if rect.width <= 0 or rect.height <= 0:
                continue
            border = max(1, int(4 - t * 2))
            radius = max(4, int(min(rect.width, rect.height) * 0.16))
            pygame.draw.rect(mask, (0, 0, 0, alpha), rect, border, border_radius=radius)

        self._vignette_cache[key] = mask
        return mask

    def apply_vignette(self, surface: pygame.Surface) -> None:
        vignette = self._get_vignette(surface.get_size())
        surface.blit(vignette, (0, 0))

    def apply_bloom(self, surface: pygame.Surface) -> None:
        if self.bloom_intensity <= 0:
            return

        w, h = surface.get_size()
        small_w = max(1, w // 3)
        small_h = max(1, h // 3)
        mini = pygame.transform.smoothscale(surface, (small_w, small_h))
        mini.fill((110, 110, 110, 0), special_flags=pygame.BLEND_RGBA_SUB)

        blur_a = pygame.transform.smoothscale(mini, (max(1, w // 6), max(1, h // 6)))
        blur_b = pygame.transform.smoothscale(blur_a, (small_w, small_h))
        blur_full = pygame.transform.smoothscale(blur_b, (w, h))
        blur_full.set_alpha(int(255 * self.bloom_intensity))
        surface.blit(blur_full, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def apply_color_grading(self, surface: pygame.Surface, time_of_day: float = 12.0, weather: str = "clear") -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        t = _wrap_hour(time_of_day)

        if t < 6 or t > 19:
            overlay.fill((0, 18, 52, 28))
        elif 17 <= t <= 19:
            overlay.fill((34, 12, 0, 28))
        elif 6 <= t < 8:
            overlay.fill((18, 7, 0, 18))
        else:
            overlay.fill((8, 5, 0, 11))
        surface.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        if weather == "rain":
            cool = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            cool.fill((0, 10, 32, 24))
            surface.blit(cool, (0, 0))
        elif weather == "arcane_wind":
            arcane = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            arcane.fill((16, 0, 28, 20))
            surface.blit(arcane, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)


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
