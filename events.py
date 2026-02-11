"""Procedural events and quests system for emergent sandbox gameplay."""

from __future__ import annotations

import random
from dataclasses import dataclass

from content_pack import BIOME_THEMES, EVENT_INTROS, QUEST_OBJECTIVES, QUEST_REWARDS, WORLD_FLAVOR_LINES
from localization import localize_biome


@dataclass
class WorldEvent:
    eid: int
    etype: str
    title: str
    description: str
    biome: str
    difficulty: int
    reward: dict
    timer: float
    chain_tag: str = ""
    resolved: bool = False


class EventSystem:
    def __init__(self, seed: int = 1234) -> None:
        self.rng = random.Random(seed)
        self.active_events: list[WorldEvent] = []
        self.completed_events: list[str] = []
        self.next_event_id = 1
        self.game_minutes = 0.0
        self.next_event_in = self.rng.uniform(2.0, 10.0)
        self.next_flavor_in = self.rng.uniform(25.0, 55.0)

    def generate_biome_location(self, biome: str) -> str:
        theme = BIOME_THEMES.get(biome, BIOME_THEMES["plains"])
        adj = self.rng.choice(theme["adjectives"])
        noun = self.rng.choice(theme["nouns"])
        return f"{adj} {noun}"

    def _new_event(self, etype: str, title: str, desc: str, biome: str, difficulty: int, reward: dict, timer: float, chain_tag: str = "") -> WorldEvent:
        event = WorldEvent(
            eid=self.next_event_id,
            etype=etype,
            title=title,
            description=desc,
            biome=biome,
            difficulty=difficulty,
            reward=reward,
            timer=timer,
            chain_tag=chain_tag,
        )
        self.next_event_id += 1
        return event

    def _generate_template(self, biome: str, is_night: bool, player_level: int) -> WorldEvent:
        etype = self.rng.choice(
            [
                "raid",
                "quest",
                "world",
                "isekai",
                "quest",
                "world",
            ]
        )
        diff = max(1, player_level + self.rng.randint(-1, 3))
        timer = self.rng.uniform(50, 130)
        biome_name = localize_biome(biome)

        if etype == "raid":
            variant = self.rng.choice(["Набег бандитов", "Волна монстров", "Вторжение демонов"])
            reward = {"exp": 25 + diff * 8, "rep": 2 + diff // 2, "items": [("gold", 2 + diff)]}
            return self._new_event(
                "raid",
                f"{variant} у биома {biome_name}",
                f"Защити ближайших поселенцев от угрозы: {variant.lower()}.",
                biome,
                diff,
                reward,
                timer,
                chain_tag="defense",
            )

        if etype == "quest":
            variant = self.rng.choice(QUEST_OBJECTIVES)
            reward_name = self.rng.choice(QUEST_REWARDS)
            intro = self.rng.choice(EVENT_INTROS)
            location = self.generate_biome_location(biome)
            reward = {
                "exp": 35 + diff * 10,
                "rep": 3 + diff,
                "items": [(self.rng.choice(["ore", "core", "plank", "gold"]), 3 + diff)],
            }
            return self._new_event(
                "quest",
                f"Квест: {variant}",
                f"{intro} Локация: {location}. Возможная награда: {reward_name}.",
                biome,
                diff,
                reward,
                timer,
                chain_tag="questline",
            )

        if etype == "world":
            variant = self.rng.choice([
                "метеоритный дождь",
                "появились древние руины",
                "караван торговцев атакован",
            ])
            reward = {
                "exp": 20 + diff * 6,
                "rep": 1 + diff // 2,
                "items": [(self.rng.choice(["core", "ore", "gold"]), 2 + diff)],
            }
            return self._new_event(
                "world",
                f"Мировое событие: {variant}",
                f"Мир меняется: {variant}. Исследуй этот район.",
                biome,
                diff,
                reward,
                timer,
                chain_tag="worldshift",
            )

        twist = self.rng.choice([
            "на миг открылись врата в современный мир",
            "бог предлагает благословение или проклятие",
            "появился герой-соперник из исекая",
        ])
        reward = {"exp": 45 + diff * 7, "rep": self.rng.randint(-2, 5), "items": [("gold", 4 + diff)]}
        if is_night:
            reward["items"].append(("core", 1 + diff // 2))
        return self._new_event(
            "isekai",
            f"Поворот исекая: {twist}",
            "Реальность изгибается вокруг твоей судьбы. Выбери действие до конца таймера.",
            biome,
            diff,
            reward,
            timer,
            chain_tag="isekai",
        )

    def _apply_world_impact(self, event: WorldEvent, world, entities) -> str:
        if event.etype == "raid":
            if self.rng.random() < 0.5 and world.player_blocks:
                key = self.rng.choice(list(world.player_blocks.keys()))
                world.remove_player_block(*key)
                return "Набег повредил стену базы."
            from entities import BaseEntity

            for _ in range(min(5, 1 + event.difficulty // 2)):
                entities.entities.append(
                    BaseEntity(
                        self.rng.randint(-400, 400),
                        self.rng.randint(-400, 400),
                        self.rng.choice(["slime", "goblin", "wolf"]),
                        "monsters",
                        hp=28 + event.difficulty * 2,
                        speed=80 + event.difficulty * 2,
                        radius=11,
                    )
                )
            return "Силы монстров вошли в регион."

        if event.etype == "world" and "руин" in event.title.lower():
            tx = self.rng.randint(-30, 30)
            ty = self.rng.randint(-30, 30)
            for oy in range(-2, 3):
                for ox in range(-2, 3):
                    world.place_player_block(tx + ox, ty + oy, "wall")
            return "Древние руины сформировали таинственную структуру."

        if event.etype == "isekai" and "благослов" in event.title.lower():
            if self.rng.random() < 0.5:
                entities.faction_relations[("player", "villagers")] = entities.faction_relations.get(("player", "villagers"), 0) + 10
                return "Благословение усилило доверие жителей к тебе."
            entities.faction_relations[("player", "monsters")] = entities.faction_relations.get(("player", "monsters"), -80) - 10
            return "Проклятие сделало монстров более агрессивными."

        return "Мир незаметно изменился."

    def complete_event(self, event_id: int, player, world, entities) -> str | None:
        for event in self.active_events:
            if event.eid == event_id and not event.resolved:
                event.resolved = True
                player.gain_exp(event.reward.get("exp", 0))
                player.reputation += event.reward.get("rep", 0)
                for item_id, count in event.reward.get("items", []):
                    player.add_item(item_id, count)
                impact = self._apply_world_impact(event, world, entities)
                self.completed_events.append(event.title)

                # chain follow-up
                if event.chain_tag == "defense" and self.rng.random() < 0.55:
                    follow = self._new_event(
                        "quest",
                        "Просьба благодарной деревни",
                        "Жители просят сопроводить повозку с припасами по опасной дороге.",
                        event.biome,
                        max(1, event.difficulty),
                        {"exp": 45, "rep": 4, "items": [("gold", 6)]},
                        timer=90,
                        chain_tag="questline",
                    )
                    self.active_events.append(follow)
                    return f"Событие завершено: {event.title}. {impact} Открыто продолжение: {follow.title}."

                if event.chain_tag == "questline" and self.rng.random() < 0.45:
                    rival = self._new_event(
                        "isekai",
                        "Засада героя-соперника",
                        "Появляется соперник из исекая и бросает вызов твоей легенде.",
                        event.biome,
                        event.difficulty + 1,
                        {"exp": 65, "rep": 2, "items": [("core", 2), ("gold", 5)]},
                        timer=100,
                        chain_tag="isekai",
                    )
                    self.active_events.append(rival)
                    return f"Событие завершено: {event.title}. {impact} Цепная реакция: {rival.title}."

                return f"Событие завершено: {event.title}. {impact}"
        return None

    def update(self, dt: float, player, world, entities) -> list[dict]:
        logs: list[dict] = []
        # Compress real time -> game minutes (10 sec ~ 1 minute)
        self.game_minutes += dt / 10.0
        self.next_event_in -= dt / 60.0
        self.next_flavor_in -= dt

        biome = world.biome_at(int(player.x // 32), int(player.y // 32))
        trigger = self.next_event_in <= 0
        if world.is_night and self.rng.random() < 0.0009:
            trigger = True
        if player.level >= 4 and self.rng.random() < 0.0008:
            trigger = True

        if trigger and len(self.active_events) < 5:
            new_event = self._generate_template(biome, world.is_night, player.level)
            self.active_events.append(new_event)
            logs.append({"type": "event", "text": f"Новое событие: {new_event.title}"})
            self.next_event_in = self.rng.uniform(2.0, 10.0)

        if self.next_flavor_in <= 0:
            self.next_flavor_in = self.rng.uniform(25.0, 55.0)
            logs.append({"type": "flavor", "text": self.rng.choice(WORLD_FLAVOR_LINES)})

        keep: list[WorldEvent] = []
        for event in self.active_events:
            if event.resolved:
                continue
            event.timer -= dt
            auto_complete_chance = 0.0005 + player.level * 0.00008
            if event.timer <= 0:
                logs.append({"type": "event", "text": f"Провалено: {event.title}"})
                continue
            if self.rng.random() < auto_complete_chance:
                msg = self.complete_event(event.eid, player, world, entities)
                if msg:
                    logs.append({"type": "event", "text": msg})
            if not event.resolved:
                keep.append(event)
        self.active_events = keep
        return logs

    def to_dict(self) -> dict:
        return {
            "next_event_id": self.next_event_id,
            "game_minutes": self.game_minutes,
            "next_event_in": self.next_event_in,
            "next_flavor_in": self.next_flavor_in,
            "active_events": [
                {
                    "eid": e.eid,
                    "etype": e.etype,
                    "title": e.title,
                    "description": e.description,
                    "biome": e.biome,
                    "difficulty": e.difficulty,
                    "reward": e.reward,
                    "timer": e.timer,
                    "chain_tag": e.chain_tag,
                    "resolved": e.resolved,
                }
                for e in self.active_events
            ],
            "completed_events": self.completed_events[-50:],
        }

    def load_dict(self, data: dict) -> None:
        self.next_event_id = data.get("next_event_id", self.next_event_id)
        self.game_minutes = data.get("game_minutes", self.game_minutes)
        self.next_event_in = data.get("next_event_in", self.next_event_in)
        self.next_flavor_in = data.get("next_flavor_in", self.next_flavor_in)
        self.completed_events = data.get("completed_events", [])
        self.active_events = []
        for e in data.get("active_events", []):
            self.active_events.append(
                WorldEvent(
                    eid=e["eid"],
                    etype=e["etype"],
                    title=e["title"],
                    description=e["description"],
                    biome=e["biome"],
                    difficulty=e["difficulty"],
                    reward=e["reward"],
                    timer=e["timer"],
                    chain_tag=e.get("chain_tag", ""),
                    resolved=e.get("resolved", False),
                )
            )
