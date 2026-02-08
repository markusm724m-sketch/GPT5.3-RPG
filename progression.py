"""Extended progression/economy/faction/companion systems for the sandbox prototype."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


SKILL_DEFS = {
    "blade_mastery": {
        "name": "Blade Mastery",
        "desc": "+15% melee damage per rank",
        "max_rank": 5,
        "cost": 1,
    },
    "arcane_flow": {
        "name": "Arcane Flow",
        "desc": "+10 mana regen per rank",
        "max_rank": 5,
        "cost": 1,
    },
    "dash_step": {
        "name": "Dash Step",
        "desc": "Lower dash cooldown",
        "max_rank": 3,
        "cost": 1,
    },
    "summon_bond": {
        "name": "Summon Bond",
        "desc": "Stronger minions and summon duration",
        "max_rank": 4,
        "cost": 2,
    },
    "isekai_blessing": {
        "name": "Isekai Blessing",
        "desc": "+HP/+Mana growth on level up",
        "max_rank": 3,
        "cost": 2,
    },
    "merchant_aura": {
        "name": "Merchant Aura",
        "desc": "Better trading rates",
        "max_rank": 3,
        "cost": 1,
    },
    "night_hunter": {
        "name": "Night Hunter",
        "desc": "Bonus damage and speed at night",
        "max_rank": 3,
        "cost": 2,
    },
}


@dataclass
class Companion:
    cid: int
    name: str
    role: str
    level: int = 1
    hp: int = 80
    loyalty: int = 40
    mood: str = "neutral"


@dataclass
class ProgressionSystem:
    skill_points: int = 0
    skill_ranks: dict[str, int] = field(default_factory=lambda: {k: 0 for k in SKILL_DEFS})
    factions: dict[str, int] = field(default_factory=lambda: {
        "villagers": 0,
        "merchants": 0,
        "monster_clans": -20,
        "isekai_gods": 0,
        "rival_heroes": -5,
    })
    gold: int = 25
    companions: list[Companion] = field(default_factory=list)
    next_companion_id: int = 1

    def on_level_up(self, new_level: int) -> list[str]:
        logs = []
        self.skill_points += 1
        if new_level % 3 == 0:
            self.gold += 20
            logs.append("Milestone reached: guild stipend +20 gold")
        return logs

    def try_upgrade_skill(self, skill_id: str) -> bool:
        if skill_id not in SKILL_DEFS:
            return False
        spec = SKILL_DEFS[skill_id]
        rank = self.skill_ranks.get(skill_id, 0)
        if rank >= spec["max_rank"]:
            return False
        if self.skill_points < spec["cost"]:
            return False
        self.skill_points -= spec["cost"]
        self.skill_ranks[skill_id] = rank + 1
        return True

    def relation_shift(self, faction: str, delta: int) -> None:
        if faction not in self.factions:
            self.factions[faction] = 0
        self.factions[faction] = max(-100, min(100, self.factions[faction] + delta))

    def hire_companion(self, role: str) -> Companion | None:
        base_cost = 30 if role == "villager" else 50 if role == "merchant" else 70
        discount = self.skill_ranks.get("merchant_aura", 0) * 0.08
        cost = int(base_cost * (1.0 - discount))
        if self.gold < cost:
            return None
        self.gold -= cost
        companion = Companion(
            cid=self.next_companion_id,
            name=random.choice(
                [
                    "Astra", "Nami", "Yuki", "Rin", "Sora", "Mika", "Luna",
                    "Kai", "Haru", "Eira", "Noa", "Ilya", "Selene", "Momo",
                ]
            ),
            role=role,
            level=1,
            hp=70 + random.randint(0, 25),
            loyalty=45 + random.randint(0, 20),
        )
        self.companions.append(companion)
        self.next_companion_id += 1
        return companion

    def tick_companions(self, dt: float, is_night: bool) -> list[str]:
        logs: list[str] = []
        for c in self.companions:
            if random.random() < 0.002 * dt * 60:
                c.loyalty = min(100, c.loyalty + 1)
            if is_night and c.role == "waifu" and random.random() < 0.001 * dt * 60:
                c.mood = random.choice(["happy", "inspired", "playful"])
                logs.append(f"{c.name} feels {c.mood} under the moonlight.")
        return logs

    def get_modifiers(self, is_night: bool) -> dict[str, float]:
        melee_mul = 1.0 + self.skill_ranks.get("blade_mastery", 0) * 0.15
        mana_regen = 1.0 + self.skill_ranks.get("arcane_flow", 0) * 0.18
        dash_cdr = self.skill_ranks.get("dash_step", 0) * 0.09
        summon_bonus = 1.0 + self.skill_ranks.get("summon_bond", 0) * 0.2
        growth_bonus = self.skill_ranks.get("isekai_blessing", 0)
        if is_night:
            melee_mul += self.skill_ranks.get("night_hunter", 0) * 0.1
        return {
            "melee_mul": melee_mul,
            "mana_regen_mul": mana_regen,
            "dash_cdr": dash_cdr,
            "summon_bonus": summon_bonus,
            "growth_bonus": growth_bonus,
        }

    def sell_loot(self, item_id: str, count: int = 1) -> int:
        price_table = {
            "wood": 1,
            "ore": 3,
            "core": 6,
            "gold": 10,
            "plank": 2,
            "sword": 16,
            "magic_staff": 28,
        }
        price = price_table.get(item_id, 1)
        bonus = 1.0 + self.skill_ranks.get("merchant_aura", 0) * 0.1
        total = int(price * count * bonus)
        self.gold += total
        self.relation_shift("merchants", 1)
        return total

    def to_dict(self) -> dict:
        return {
            "skill_points": self.skill_points,
            "skill_ranks": self.skill_ranks,
            "factions": self.factions,
            "gold": self.gold,
            "companions": [
                {
                    "cid": c.cid,
                    "name": c.name,
                    "role": c.role,
                    "level": c.level,
                    "hp": c.hp,
                    "loyalty": c.loyalty,
                    "mood": c.mood,
                }
                for c in self.companions
            ],
            "next_companion_id": self.next_companion_id,
        }

    def load_dict(self, data: dict) -> None:
        self.skill_points = data.get("skill_points", self.skill_points)
        self.skill_ranks.update(data.get("skill_ranks", {}))
        self.factions.update(data.get("factions", {}))
        self.gold = data.get("gold", self.gold)
        self.next_companion_id = data.get("next_companion_id", self.next_companion_id)
        self.companions = []
        for item in data.get("companions", []):
            self.companions.append(
                Companion(
                    cid=item.get("cid", 0),
                    name=item.get("name", "Companion"),
                    role=item.get("role", "villager"),
                    level=item.get("level", 1),
                    hp=item.get("hp", 80),
                    loyalty=item.get("loyalty", 40),
                    mood=item.get("mood", "neutral"),
                )
            )
