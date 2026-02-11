"""Real-time combat: melee arc, projectiles and anime-like particles."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame


@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    damage: int
    kind: str


class CombatSystem:
    def __init__(self) -> None:
        self.projectiles: list[Projectile] = []
        self.attack_cooldown = 0.0
        self.cast_cooldown = 0.0

    def update(self, dt: float) -> None:
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        if self.cast_cooldown > 0:
            self.cast_cooldown -= dt
        alive: list[Projectile] = []
        for p in self.projectiles:
            p.life -= dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            if p.life > 0:
                alive.append(p)
        self.projectiles = alive

    def melee_attack(self, player, entities, particles, dmg_numbers=None, melee_mult: float = 1.0) -> dict | None:
        if self.attack_cooldown > 0:
            return None
        self.attack_cooldown = 0.3
        px, py = player.center
        hit = 0
        for ent in entities.entities:
            if ent.hp <= 0 or ent.faction == "villagers":
                continue
            dx = ent.x - px
            dy = ent.y - py
            dist = math.hypot(dx, dy)
            if dist > 58:
                continue
            if dist > 0:
                dot = (dx / dist) * player.facing.x + (dy / dist) * player.facing.y
                if dot < 0.2:
                    continue
            crit = (player.level >= 5 and pygame.time.get_ticks() % 7 == 0)
            base_damage = 16 + player.level * 2 + (8 if player.cheat_mode else 0)
            damage = int(base_damage * melee_mult * (1.65 if crit else 1.0))
            dead = entities.damage_entity(ent, damage)
            hit += 1
            if dmg_numbers is not None:
                dmg_numbers.spawn(ent.x, ent.y - 10, damage, critical=crit)
            particles.emit_burst(ent.x, ent.y, 13, (250, 70, 90), 85, 0.45, gravity=20)
            particles.emit_burst(ent.x, ent.y, 9, (255, 220, 120), 70, 0.35)
            if dead:
                player.gain_exp(20)
        if hit > 0:
            return {"type": "combat", "text": f"Удар в ближнем бою поразил целей: {hit}."}
        return None

    def cast_projectile(self, player, kind: str, particles, power_mult: float = 1.0) -> bool:
        if self.cast_cooldown > 0:
            return False
        mana_cost = 12 if kind == "fireball" else 10
        if player.mana < mana_cost:
            return False
        player.mana -= mana_cost
        self.cast_cooldown = 0.25
        px, py = player.center
        speed = 320 if kind == "fireball" else 360
        vx = player.facing.x * speed
        vy = player.facing.y * speed
        damage = int((22 + player.level * 2 + (10 if player.cheat_mode else 0)) * power_mult)
        self.projectiles.append(Projectile(px, py, vx, vy, 1.8, damage, kind))
        particles.emit_burst(px, py, 7, (255, 140, 70) if kind == "fireball" else (120, 220, 255), 65, 0.3)
        return True

    def resolve_projectiles(self, entities, particles, player, dmg_numbers=None) -> list[dict]:
        logs: list[dict] = []
        kept: list[Projectile] = []
        for p in self.projectiles:
            collided = False
            for ent in entities.entities:
                if ent.hp <= 0 or ent.faction == "villagers":
                    continue
                if (ent.x - p.x) ** 2 + (ent.y - p.y) ** 2 <= (ent.radius + 6) ** 2:
                    dead = entities.damage_entity(ent, p.damage)
                    if dmg_numbers is not None:
                        dmg_numbers.spawn(ent.x, ent.y - 8, p.damage, critical=p.damage >= 40)
                    c = (255, 140, 70) if p.kind == "fireball" else (150, 220, 255)
                    particles.emit_burst(p.x, p.y, 16, c, 100, 0.42)
                    if dead:
                        player.gain_exp(28)
                    collided = True
                    break
            if not collided:
                kept.append(p)
            else:
                spell = "Огненный шар" if p.kind == "fireball" else p.kind.replace("_", " ").title()
                logs.append({"type": "combat", "text": f"{spell} взорвался!"})
        self.projectiles = kept
        return logs

    def draw(self, surface: pygame.Surface, camera) -> None:
        for p in self.projectiles:
            sx, sy = camera.world_to_screen(p.x, p.y)
            if p.kind == "fireball":
                pygame.draw.circle(surface, (255, 170, 70), (int(sx), int(sy)), 6)
                pygame.draw.circle(surface, (255, 230, 120), (int(sx), int(sy)), 3)
            else:
                pygame.draw.polygon(surface, (150, 230, 255), [(sx, sy - 6), (sx + 5, sy + 4), (sx - 5, sy + 4)])

    def draw_melee_arc(self, surface: pygame.Surface, camera, player) -> None:
        # Cosmetic sword arc around player
        if self.attack_cooldown > 0.2:
            return
        px, py = player.center
        sx, sy = camera.world_to_screen(px, py)
        endx = sx + int(player.facing.x * 28)
        endy = sy + int(player.facing.y * 28)
        left = (endx - int(player.facing.y * 8), endy + int(player.facing.x * 8))
        right = (endx + int(player.facing.y * 8), endy - int(player.facing.x * 8))
        pygame.draw.polygon(surface, (230, 230, 255), [(sx, sy), left, right])
