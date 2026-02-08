"""UI module: HUD, minimap, hotbar, notifications, pause and panels."""

from __future__ import annotations

import pygame


class UIManager:
    def __init__(self) -> None:
        self.show_inventory = False
        self.show_crafting = False
        self.paused = False
        self.show_event_panel = True
        self.show_progression = False
        self.notifications: list[dict] = []

    def notify(self, text: str, color: tuple[int, int, int] = (255, 230, 255), ttl: float = 4.0) -> None:
        self.notifications.append({"text": text, "ttl": ttl, "max": ttl, "color": color})
        self.notifications = self.notifications[-8:]

    def update(self, dt: float) -> None:
        alive = []
        for n in self.notifications:
            n["ttl"] -= dt
            if n["ttl"] > 0:
                alive.append(n)
        self.notifications = alive

    def draw_bars(self, surface: pygame.Surface, player, font: pygame.font.Font) -> None:
        pygame.draw.rect(surface, (30, 22, 44), (12, 12, 240, 64), border_radius=10)
        pygame.draw.rect(surface, (120, 80, 230), (12, 12, 240, 64), 2, border_radius=10)

        hp_ratio = player.hp / max(1, player.hp_max)
        mana_ratio = player.mana / max(1, player.mana_max)
        pygame.draw.rect(surface, (70, 20, 30), (22, 24, 190, 14), border_radius=6)
        pygame.draw.rect(surface, (220, 70, 95), (22, 24, int(190 * hp_ratio), 14), border_radius=6)

        pygame.draw.rect(surface, (20, 30, 70), (22, 45, 190, 14), border_radius=6)
        pygame.draw.rect(surface, (90, 150, 255), (22, 45, int(190 * mana_ratio), 14), border_radius=6)

        surface.blit(font.render(f"Lv {player.level}  EXP {player.exp}", True, (235, 235, 245)), (22, 61))
        surface.blit(font.render(f"Rep {player.reputation}", True, (255, 215, 135)), (155, 61))

    def draw_hotbar(self, surface: pygame.Surface, player, font: pygame.font.Font, screen_w: int, screen_h: int) -> None:
        total_w = 10 * 48 + 9 * 6
        start_x = (screen_w - total_w) // 2
        y = screen_h - 56
        for i in range(10):
            rect = pygame.Rect(start_x + i * 54, y, 48, 40)
            col = (100, 90, 180) if i == player.selected_hotbar else (42, 44, 70)
            pygame.draw.rect(surface, col, rect, border_radius=8)
            pygame.draw.rect(surface, (170, 140, 240), rect, 2, border_radius=8)
            item = player.hotbar[i]
            if item:
                surface.blit(font.render(item.get("id", "?")[:6], True, (245, 230, 140)), (rect.x + 4, rect.y + 10))
                surface.blit(font.render(str(item.get("count", 1)), True, (245, 245, 255)), (rect.right - 11, rect.bottom - 16))
            surface.blit(font.render(str((i + 1) % 10), True, (230, 230, 245)), (rect.x + 2, rect.y + 1))

    def draw_minimap(self, surface: pygame.Surface, player, world, font: pygame.font.Font, screen_w: int) -> None:
        mini = pygame.Rect(screen_w - 170, 12, 156, 156)
        pygame.draw.rect(surface, (20, 24, 34), mini, border_radius=10)
        pygame.draw.rect(surface, (110, 170, 240), mini, 2, border_radius=10)

        cx = int(player.x // 32)
        cy = int(player.y // 32)
        for oy in range(-20, 21):
            for ox in range(-20, 21):
                tx = cx + ox
                ty = cy + oy
                if (tx, ty) not in world.discovered_tiles:
                    continue
                px = mini.centerx + ox * 3
                py = mini.centery + oy * 3
                biome = world.biome_at(tx, ty)
                col = (80, 200, 90) if biome == "plains" else (50, 150, 65) if biome == "forest" else (130, 130, 140) if biome == "mountains" else (130, 85, 150)
                pygame.draw.rect(surface, col, (px, py, 3, 3))

        pygame.draw.circle(surface, (255, 220, 130), mini.center, 3)
        surface.blit(font.render(world.weather, True, (220, 220, 245)), (mini.x + 8, mini.bottom - 20))

    def draw_notifications(self, surface: pygame.Surface, font: pygame.font.Font, screen_w: int) -> None:
        base_y = 178
        for i, n in enumerate(reversed(self.notifications)):
            fade = n["ttl"] / n["max"]
            txt = n["text"]
            label = font.render(txt[:72], True, n["color"])
            box = pygame.Surface((label.get_width() + 18, 24), pygame.SRCALPHA)
            box.fill((40, 30, 70, int(170 * fade)))
            x = screen_w - box.get_width() - 12
            y = base_y + i * 28
            surface.blit(box, (x, y))
            surface.blit(label, (x + 9, y + 4))

    def draw_event_panel(self, surface: pygame.Surface, font: pygame.font.Font, events_system, y: int = 82) -> None:
        if not self.show_event_panel:
            return
        panel = pygame.Rect(10, y, 360, 160)
        pygame.draw.rect(surface, (28, 24, 44), panel, border_radius=10)
        pygame.draw.rect(surface, (210, 120, 255), panel, 2, border_radius=10)
        surface.blit(font.render("Active Procedural Events", True, (245, 220, 255)), (panel.x + 10, panel.y + 8))

        if not events_system.active_events:
            surface.blit(font.render("No active events. World is calm... for now.", True, (170, 170, 200)), (panel.x + 10, panel.y + 34))
            return

        for idx, e in enumerate(events_system.active_events[:4]):
            line = f"[{e.etype}] {e.title[:28]} ({int(e.timer)}s)"
            surface.blit(font.render(line, True, (240, 230, 245)), (panel.x + 10, panel.y + 34 + idx * 26))

    def draw_pause_overlay(self, surface: pygame.Surface, font_big: pygame.font.Font, screen_w: int, screen_h: int) -> None:
        if not self.paused:
            return
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((16, 12, 24, 170))
        surface.blit(overlay, (0, 0))
        txt = font_big.render("PAUSED", True, (250, 240, 255))
        surface.blit(txt, (screen_w // 2 - txt.get_width() // 2, screen_h // 2 - 30))

    def draw_progression_panel(self, surface: pygame.Surface, font: pygame.font.Font, progression, x: int = 20, y: int = 100) -> None:
        if not self.show_progression:
            return
        panel = pygame.Rect(x, y, 760, 460)
        pygame.draw.rect(surface, (20, 22, 40), panel, border_radius=12)
        pygame.draw.rect(surface, (150, 120, 250), panel, 2, border_radius=12)
        surface.blit(font.render("Progression / Factions / Companions", True, (240, 230, 255)), (x + 14, y + 10))

        surface.blit(font.render(f"Skill Points: {progression.skill_points}", True, (255, 230, 140)), (x + 16, y + 38))
        surface.blit(font.render(f"Gold: {progression.gold}", True, (255, 220, 130)), (x + 210, y + 38))

        sy = y + 70
        for idx, (sid, rank) in enumerate(progression.skill_ranks.items()):
            row = pygame.Rect(x + 16, sy + idx * 30, 350, 26)
            pygame.draw.rect(surface, (38, 40, 64), row, border_radius=6)
            pygame.draw.rect(surface, (80, 90, 140), row, 1, border_radius=6)
            surface.blit(font.render(f"{sid[:18]}  rank {rank}", True, (220, 225, 250)), (row.x + 8, row.y + 4))

        fx = x + 390
        surface.blit(font.render("Factions:", True, (220, 240, 255)), (fx, sy - 24))
        for i, (name, value) in enumerate(progression.factions.items()):
            col = (120, 230, 160) if value >= 0 else (255, 130, 130)
            surface.blit(font.render(f"{name}: {value}", True, col), (fx, sy + i * 24))

        cy = y + 270
        surface.blit(font.render("Companions:", True, (240, 220, 255)), (x + 16, cy))
        if not progression.companions:
            surface.blit(font.render("No companions yet. Press J/K/L to hire roles.", True, (170, 180, 220)), (x + 16, cy + 24))
        else:
            for i, c in enumerate(progression.companions[:8]):
                text = f"{c.name} ({c.role}) Lv{c.level} HP:{c.hp} Loyalty:{c.loyalty} Mood:{c.mood}"
                surface.blit(font.render(text[:65], True, (220, 230, 250)), (x + 16, cy + 24 + i * 24))
