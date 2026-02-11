"""Crafting and inventory grid (10x5) with basic drag&drop UI."""

from __future__ import annotations

import pygame

from localization import localize_item


class CraftingSystem:
    def __init__(self) -> None:
        self.recipes = [
            {"name": "Доски", "in": {"wood": 2}, "out": ("plank", 1)},
            {"name": "Набор дома", "in": {"plank": 6}, "out": ("house_kit", 1)},
            {"name": "Меч", "in": {"ore": 3, "wood": 1}, "out": ("sword", 1)},
            {"name": "Посох мага", "in": {"ore": 4, "core": 1}, "out": ("magic_staff", 1)},
            {"name": "Чит-фрукт", "in": {"core": 3, "gold": 3}, "out": ("cheat_fruit", 1)},
        ]
        self.selected_recipe = 0
        self.drag_from: int | None = None
        self.drag_item: dict | None = None

    def _all_slots(self, player) -> list[dict]:
        return player.hotbar + player.inventory

    def count_item(self, player, item_id: str) -> int:
        total = 0
        for slot in self._all_slots(player):
            if slot.get("id") == item_id:
                total += slot.get("count", 0)
        return total

    def consume_item(self, player, item_id: str, count: int) -> bool:
        if self.count_item(player, item_id) < count:
            return False
        left = count
        for slot in self._all_slots(player):
            if slot.get("id") == item_id and left > 0:
                take = min(left, slot.get("count", 0))
                slot["count"] -= take
                left -= take
                if slot["count"] <= 0:
                    slot.clear()
        return True

    def can_craft(self, player, recipe: dict) -> bool:
        return all(self.count_item(player, item_id) >= req for item_id, req in recipe["in"].items())

    def craft_selected(self, player) -> bool:
        recipe = self.recipes[self.selected_recipe]
        if not self.can_craft(player, recipe):
            return False
        for item_id, req in recipe["in"].items():
            self.consume_item(player, item_id, req)
        out_id, out_count = recipe["out"]
        player.add_item(out_id, out_count)
        player.gain_exp(8)
        return True

    def _slot_rects(self, panel_x: int, panel_y: int) -> list[pygame.Rect]:
        # Inventory only (10x5)
        rects: list[pygame.Rect] = []
        for r in range(5):
            for c in range(10):
                rects.append(pygame.Rect(panel_x + 20 + c * 48, panel_y + 85 + r * 48, 42, 42))
        return rects

    def handle_event(self, event: pygame.event.Event, player, panel_x: int, panel_y: int) -> bool:
        rects = self._slot_rects(panel_x, panel_y)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(rects):
                if rect.collidepoint(event.pos):
                    slot = player.inventory[i]
                    if slot:
                        self.drag_from = i
                        self.drag_item = dict(slot)
                        slot.clear()
                        return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag_item is not None:
            placed = False
            for i, rect in enumerate(rects):
                if rect.collidepoint(event.pos):
                    target = player.inventory[i]
                    if not target:
                        target.update(self.drag_item)
                    elif target.get("id") == self.drag_item.get("id"):
                        target["count"] = target.get("count", 0) + self.drag_item.get("count", 0)
                    else:
                        tmp = dict(target)
                        target.clear()
                        target.update(self.drag_item)
                        self.drag_item = tmp
                    placed = True
                    break

            if not placed:
                if self.drag_from is not None and not player.inventory[self.drag_from]:
                    player.inventory[self.drag_from].update(self.drag_item)
                else:
                    for slot in player.inventory:
                        if not slot:
                            slot.update(self.drag_item)
                            break
            self.drag_from = None
            self.drag_item = None
            return True
        return False

    def draw(self, surface: pygame.Surface, player, font: pygame.font.Font, x: int, y: int, show_crafting: bool) -> None:
        panel = pygame.Rect(x, y, 520, 360)
        pygame.draw.rect(surface, (26, 28, 45), panel, border_radius=12)
        pygame.draw.rect(surface, (120, 100, 230), panel, 2, border_radius=12)
        surface.blit(font.render("Инвентарь 10x5", True, (230, 230, 250)), (x + 20, y + 15))

        rects = self._slot_rects(x, y)
        for i, rect in enumerate(rects):
            pygame.draw.rect(surface, (50, 55, 76), rect, border_radius=6)
            pygame.draw.rect(surface, (90, 95, 130), rect, 1, border_radius=6)
            slot = player.inventory[i]
            if slot:
                iid = slot.get("id", "?")
                cnt = slot.get("count", 1)
                surface.blit(font.render(localize_item(iid)[:8], True, (240, 230, 130)), (rect.x + 4, rect.y + 10))
                surface.blit(font.render(str(cnt), True, (240, 240, 245)), (rect.right - 12, rect.bottom - 18))

        if show_crafting:
            cx = x + 520 + 16
            pygame.draw.rect(surface, (26, 28, 45), (cx, y, 250, 360), border_radius=12)
            pygame.draw.rect(surface, (220, 120, 250), (cx, y, 250, 360), 2, border_radius=12)
            surface.blit(font.render("Крафт", True, (250, 220, 250)), (cx + 16, y + 12))
            for idx, recipe in enumerate(self.recipes):
                ry = y + 45 + idx * 56
                rr = pygame.Rect(cx + 12, ry, 226, 50)
                col = (80, 60, 120) if idx == self.selected_recipe else (44, 42, 67)
                pygame.draw.rect(surface, col, rr, border_radius=8)
                can = self.can_craft(player, recipe)
                txt = f"{recipe['name']} -> {localize_item(recipe['out'][0])}"
                surface.blit(font.render(txt[:28], True, (230, 245, 255) if can else (130, 130, 150)), (rr.x + 8, rr.y + 6))
                req = ", ".join(f"{localize_item(k)}:{v}" for k, v in recipe["in"].items())
                surface.blit(font.render(req[:30], True, (210, 190, 130)), (rr.x + 8, rr.y + 25))

        if self.drag_item:
            mx, my = pygame.mouse.get_pos()
            pygame.draw.rect(surface, (100, 80, 140), (mx - 18, my - 18, 36, 36), border_radius=6)
            surface.blit(font.render(localize_item(self.drag_item.get("id", "?"))[:6], True, (255, 255, 255)), (mx - 16, my - 6))
