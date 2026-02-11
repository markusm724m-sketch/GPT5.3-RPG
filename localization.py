"""Russian localization helpers for in-game UI and logs."""

from __future__ import annotations


ITEM_NAMES = {
    "wood": "Дерево",
    "ore": "Руда",
    "core": "Ядро",
    "gold": "Золото",
    "plank": "Доски",
    "house_kit": "Набор дома",
    "sword": "Меч",
    "magic_staff": "Посох",
    "cheat_fruit": "Чит-фрукт",
}

BIOME_NAMES = {
    "plains": "Равнины",
    "forest": "Лес",
    "mountains": "Горы",
    "village_ruins": "Руины деревни",
    "dungeon": "Подземелье",
}

WEATHER_NAMES = {
    "clear": "Ясно",
    "rain": "Дождь",
    "arcane_wind": "Чародейский ветер",
}

ROLE_NAMES = {
    "villager": "Житель",
    "merchant": "Торговец",
    "waifu": "Спутница",
    "spirit": "Дух",
    "wolf_ally": "Волк-союзник",
    "knight": "Рыцарь",
}

FACTION_NAMES = {
    "villagers": "Жители",
    "merchants": "Торговцы",
    "monster_clans": "Кланы монстров",
    "isekai_gods": "Боги исекая",
    "rival_heroes": "Герои-соперники",
}

SKILL_NAMES = {
    "blade_mastery": "Мастерство клинка",
    "arcane_flow": "Поток арканы",
    "dash_step": "Рывок",
    "summon_bond": "Связь призыва",
    "isekai_blessing": "Благословение исекая",
    "merchant_aura": "Аура торговца",
    "night_hunter": "Ночной охотник",
}

EVENT_TYPE_NAMES = {
    "raid": "Набег",
    "quest": "Квест",
    "world": "Мировое",
    "isekai": "Исекай",
}

ENTITY_NAMES = {
    "villager": "Житель",
    "merchant": "Торговец",
    "waifu": "Спутница",
    "slime": "Слизень",
    "goblin": "Гоблин",
    "wolf": "Волк",
    "dragon": "Дракон",
    "demon_lord": "Повелитель демонов",
    "spirit": "Дух",
    "wolf_ally": "Волк-союзник",
    "knight": "Рыцарь",
}

MOOD_NAMES = {
    "neutral": "спокойна",
    "happy": "счастлива",
    "inspired": "вдохновлена",
    "playful": "игрива",
}


def _fallback_name(key: str) -> str:
    return key.replace("_", " ").strip()


def localize_item(item_id: str) -> str:
    return ITEM_NAMES.get(item_id, _fallback_name(item_id))


def localize_biome(biome_id: str) -> str:
    return BIOME_NAMES.get(biome_id, _fallback_name(biome_id))


def localize_weather(weather_id: str) -> str:
    return WEATHER_NAMES.get(weather_id, _fallback_name(weather_id))


def localize_role(role_id: str) -> str:
    return ROLE_NAMES.get(role_id, _fallback_name(role_id))


def localize_faction(faction_id: str) -> str:
    return FACTION_NAMES.get(faction_id, _fallback_name(faction_id))


def localize_skill(skill_id: str) -> str:
    return SKILL_NAMES.get(skill_id, _fallback_name(skill_id))


def localize_event_type(event_type: str) -> str:
    return EVENT_TYPE_NAMES.get(event_type, _fallback_name(event_type))


def localize_entity(entity_type: str) -> str:
    return ENTITY_NAMES.get(entity_type, _fallback_name(entity_type))


def localize_mood(mood: str) -> str:
    return MOOD_NAMES.get(mood, _fallback_name(mood))
