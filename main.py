"""Main entry point for anime-fantasy sandbox prototype (pygame only, procedural visuals)."""

from __future__ import annotations

import random

import pygame

from building import BuildingSystem
from combat import CombatSystem
from crafting import CraftingSystem
from entities import EntityManager
from events import EventSystem
from localization import localize_biome, localize_item, localize_role, localize_skill
from player import Player
from progression import ProgressionSystem
from ui import UIManager
from utils import Camera, ParticleSystem, load_json, save_json
from visuals import AuraRenderer, DamageNumberSystem, PostProcessing, RuneCircleRenderer, SkyRenderer, WeatherRenderer
from world import TILE_SIZE, World

WIDTH, HEIGHT = 800, 600
FPS = 60
SAVE_PATH = "savegame.json"


def save_game(player: Player, world: World, events: EventSystem, progression: ProgressionSystem) -> None:
    save_json(
        SAVE_PATH,
        {
            "player": player.to_dict(),
            "world": world.to_dict(),
            "events": events.to_dict(),
            "progression": progression.to_dict(),
        },
    )


def load_game(player: Player, world: World, events: EventSystem, progression: ProgressionSystem) -> bool:
    data = load_json(SAVE_PATH)
    if not data:
        return False
    player.load_dict(data.get("player", {}))
    world.load_dict(data.get("world", {}))
    events.load_dict(data.get("events", {}))
    progression.load_dict(data.get("progression", {}))
    return True


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Исекай-песочница")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 16)
    font_big = pygame.font.SysFont("consolas", 42, bold=True)

    world = World(seed=random.randint(1, 999999))
    player = Player()
    entities = EntityManager(world, seed=world.seed + 77)
    events_system = EventSystem(seed=world.seed + 1234)
    progression = ProgressionSystem()
    crafting = CraftingSystem()
    building = BuildingSystem()
    combat = CombatSystem()
    ui = UIManager()
    camera = Camera(WIDTH, HEIGHT)
    particles = ParticleSystem()
    sky = SkyRenderer(seed=world.seed + 17)
    weather_fx = WeatherRenderer(seed=world.seed + 543)
    aura_fx = AuraRenderer()
    rune_fx = RuneCircleRenderer()
    dmg_numbers = DamageNumberSystem()
    post_fx = PostProcessing()

    build_mode = False
    running = True
    time_acc = 0.0

    ui.notify("Добро пожаловать, странник исекая. Стань легендой.", (255, 215, 160), ttl=5)
    ui.notify("Управление: WASD/стрелки - движение, Space - прыжок, Shift - рывок, ЛКМ - удар, ПКМ - огненный шар", (210, 230, 255), ttl=6)

    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)
        time_acc += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    ui.paused = not ui.paused
                elif event.key == pygame.K_i:
                    ui.show_inventory = not ui.show_inventory
                elif event.key == pygame.K_c:
                    ui.show_crafting = not ui.show_crafting
                    ui.show_inventory = ui.show_crafting or ui.show_inventory
                elif event.key == pygame.K_b:
                    build_mode = not build_mode
                    ui.notify(f"Режим строительства: {'ВКЛ' if build_mode else 'ВЫКЛ'}", (180, 255, 210))
                elif event.key == pygame.K_TAB:
                    ui.show_event_panel = not ui.show_event_panel
                elif event.key == pygame.K_SPACE:
                    player.trigger_jump()
                elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    mods = progression.get_modifiers(world.is_night)
                    player.trigger_dash(cooldown_scale=max(0.5, 1.0 - mods["dash_cdr"]))
                elif event.key == pygame.K_f:
                    if player.cast_time_slow():
                        ui.notify("Замедление времени активировано", (160, 210, 255))
                elif event.key == pygame.K_e:
                    if player.use_cheat_fruit():
                        ui.notify("Чит-фрукт съеден! Пробуждена мощная аура.", (255, 235, 120), ttl=5)
                elif event.key == pygame.K_g:
                    if events_system.active_events:
                        message = events_system.complete_event(events_system.active_events[0].eid, player, world, entities)
                        if message:
                            ui.notify(message, (250, 220, 255), ttl=6)
                elif event.key == pygame.K_RETURN and ui.show_crafting:
                    if crafting.craft_selected(player):
                        ui.notify("Предмет создан!", (170, 255, 190))
                    else:
                        ui.notify("Не хватает ресурсов.", (255, 160, 160))
                elif event.key == pygame.K_UP and ui.show_crafting:
                    crafting.selected_recipe = (crafting.selected_recipe - 1) % len(crafting.recipes)
                elif event.key == pygame.K_DOWN and ui.show_crafting:
                    crafting.selected_recipe = (crafting.selected_recipe + 1) % len(crafting.recipes)
                elif event.key == pygame.K_F5:
                    save_game(player, world, events_system, progression)
                    ui.notify("Игра сохранена.", (180, 230, 255))
                elif event.key == pygame.K_F9:
                    if load_game(player, world, events_system, progression):
                        ui.notify("Игра загружена.", (180, 230, 255))
                    else:
                        ui.notify("Сохранение не найдено.", (255, 170, 170))
                elif event.key == pygame.K_p:
                    ui.show_progression = not ui.show_progression
                elif event.key == pygame.K_u:
                    for sid, rank in progression.skill_ranks.items():
                        if rank < 3 and progression.try_upgrade_skill(sid):
                            ui.notify(f"Навык улучшен: {localize_skill(sid)}", (210, 250, 180))
                            break
                elif event.key == pygame.K_j:
                    c = progression.hire_companion("villager")
                    if c:
                        ui.notify(f"Нанят спутник: {c.name} ({localize_role(c.role)})", (240, 220, 255))
                    else:
                        ui.notify("Недостаточно золота, чтобы нанять жителя.", (255, 170, 170))
                elif event.key == pygame.K_k:
                    c = progression.hire_companion("merchant")
                    if c:
                        ui.notify(f"Нанят спутник: {c.name} ({localize_role(c.role)})", (240, 220, 255))
                    else:
                        ui.notify("Недостаточно золота, чтобы нанять торговца.", (255, 170, 170))
                elif event.key == pygame.K_l:
                    c = progression.hire_companion("waifu")
                    if c:
                        ui.notify(f"Нанят спутник: {c.name} ({localize_role(c.role)})", (255, 205, 240))
                    else:
                        ui.notify("Недостаточно золота, чтобы нанять спутницу.", (255, 170, 170))
                elif event.key == pygame.K_r:
                    if player.mana >= 25:
                        player.mana -= 25
                        summon_type = random.choice(["spirit", "wolf_ally", "knight"])
                        ally = entities.summon_ally(player.x + random.randint(-35, 35), player.y + random.randint(-35, 35), summon_type)
                        particles.emit_burst(ally.x, ally.y, 18, (190, 200, 255), 90, 0.55)
                        ui.notify(f"Призван союзник: {localize_role(summon_type)}", (190, 220, 255))
                    else:
                        ui.notify("Недостаточно маны для призыва союзника.", (255, 160, 160))
                elif event.key == pygame.K_t:
                    slot = player.hotbar[player.selected_hotbar]
                    if slot:
                        sold = progression.sell_loot(slot.get("id", "wood"), 1)
                        item_name = localize_item(slot.get("id", "wood"))
                        slot["count"] -= 1
                        if slot["count"] <= 0:
                            slot.clear()
                        ui.notify(f"Продано: {item_name} за {sold} золота", (255, 225, 130))
                elif pygame.K_0 <= event.key <= pygame.K_9:
                    number = (event.key - pygame.K_1) % 10
                    player.selected_hotbar = number

            if ui.show_inventory:
                crafting.handle_event(event, player, panel_x=20, panel_y=100)

            if event.type == pygame.MOUSEBUTTONDOWN and not ui.paused and not ui.show_inventory:
                if build_mode:
                    tx, ty = building.world_tile_from_mouse(event.pos, camera)
                    if event.button == 1:
                        if building.place_block(player, world, tx, ty):
                            ui.notify("Блок стены установлен", (180, 240, 200))
                    elif event.button == 3:
                        if building.remove_block(player, world, tx, ty):
                            ui.notify("Блок стены убран", (240, 210, 170))
                else:
                    if event.button == 1:
                        mods = progression.get_modifiers(world.is_night)
                        msg = combat.melee_attack(player, entities, particles, dmg_numbers=dmg_numbers, melee_mult=mods["melee_mul"])
                        if msg:
                            ui.notify(msg["text"], (255, 220, 180))
                    elif event.button == 3:
                        mods = progression.get_modifiers(world.is_night)
                        if combat.cast_projectile(player, "fireball", particles, power_mult=mods["melee_mul"]):
                            ui.notify("Огненный шар!", (255, 190, 140))

        if not ui.paused:
            keys = pygame.key.get_pressed()
            player.handle_inputs(dt, keys, world)

            world.ensure_chunks_around(player.x, player.y, radius_chunks=2)
            world.reveal_around(player.x, player.y)

            world.update(dt)
            mods = progression.get_modifiers(world.is_night)
            player.update(dt, world, mana_regen_mult=mods["mana_regen_mul"])

            # progression hooks
            companion_logs = progression.tick_companions(dt, world.is_night)
            for text in companion_logs:
                ui.notify(text, (230, 220, 255))

            if world.weather == "rain" and random.random() < 0.7:
                rx = player.x + random.randint(-500, 500)
                ry = player.y - random.randint(250, 350)
                particles.emit_burst(rx, ry, 1, (130, 160, 255), 170, 0.7, gravity=260)

            # systems
            combat.update(dt)
            logs = entities.update(dt, player, events_system)
            logs.extend(combat.resolve_projectiles(entities, particles, player, dmg_numbers=dmg_numbers))
            logs.extend(events_system.update(dt, player, world, entities))
            settle = building.try_spawn_settler(player, entities, world)
            if settle:
                logs.append(settle)

            for log in logs:
                ltype = log.get("type")
                if ltype == "loot":
                    player.add_item(log["item"], 1)
                    levelups = player.gain_exp(log.get("exp", 5))
                    if levelups > 0:
                        for _ in range(levelups):
                            for lvl_msg in progression.on_level_up(player.level):
                                ui.notify(lvl_msg, (255, 230, 120))
                    particles.emit_burst(log["x"], log["y"], 7, (255, 230, 120), 80, 0.45)
                elif ltype in {"event", "dialogue", "combat", "settle", "flavor"}:
                    ui.notify(log.get("text", "..."), (245, 220, 255) if ltype == "event" else (230, 240, 255))

            particles.update(dt)
            aura_fx.update(dt)
            rune_fx.update(dt)
            dmg_numbers.update(dt)
            weather_fx.update(dt, world.weather, WIDTH, HEIGHT)
            ui.update(dt)

            # player death fallback
            if player.hp <= 0:
                player.hp = player.hp_max
                player.x, player.y = 180, 180
                ui.notify("Вы были повержены... но боги исекая вернули вас назад.", (255, 120, 140), ttl=5)

        camera.update(player.x + player.w / 2, player.y + player.h / 2)

        # Draw
        screen.fill((16, 14, 24))
        sky.draw(screen, world.time_of_day)
        world.draw(screen, camera, WIDTH, HEIGHT, focus_world=player.center)
        entities.draw(screen, camera)
        combat.draw(screen, camera)
        player.draw(screen, camera, time_acc)
        aura_fx.draw_player_aura(screen, camera, player, cheat_mode=player.cheat_mode, time_slow=player.time_slow > 0)
        rune_fx.draw(screen, camera, player.center[0], player.center[1], active=player.time_slow > 0)
        combat.draw_melee_arc(screen, camera, player)
        particles.draw(screen, camera)
        weather_fx.draw(screen, world.weather)
        dmg_numbers.draw(screen, camera, font)

        if build_mode and not ui.show_inventory:
            building.draw_preview(screen, camera, world, pygame.mouse.get_pos())

        # Apply post-processing
        post_fx.apply_bloom(screen)
        post_fx.apply_vignette(screen)
        post_fx.apply_color_grading(screen, world.time_of_day, world.weather)

        # UI layers
        ui.draw_bars(screen, player, font)
        ui.draw_minimap(screen, player, world, font, WIDTH)
        ui.draw_hotbar(screen, player, font, WIDTH, HEIGHT)
        ui.draw_event_panel(screen, font, events_system)
        ui.draw_notifications(screen, font, WIDTH)
        ui.draw_progression_panel(screen, font, progression)

        biome_name = localize_biome(world.biome_at(int(player.x // TILE_SIZE), int(player.y // TILE_SIZE)))
        info = f"Биом: {biome_name} | Время: {world.time_of_day:05.2f}"
        screen.blit(font.render(info, True, (235, 235, 245)), (10, HEIGHT - 24))
        screen.blit(font.render(f"Золото: {progression.gold} | Спутники: {len(progression.companions)}", True, (255, 225, 130)), (10, HEIGHT - 44))

        if ui.show_inventory:
            crafting.draw(screen, player, font, x=20, y=100, show_crafting=ui.show_crafting)

        ui.draw_pause_overlay(screen, font_big, WIDTH, HEIGHT)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
