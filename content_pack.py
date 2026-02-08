"""Large procedural content bank for quests, dialogues and anime flavor text."""

from __future__ import annotations

BIOME_THEMES = {
    "plains": {
        "adjectives": ["sunlit", "windy", "emerald", "gentle", "vast", "golden", "misty", "star-kissed", "sacred", "luminous"],
        "nouns": ["meadow", "field", "valley", "prairie", "ridge", "crossroad", "pasture", "camp", "hamlet", "gate"],
    },
    "forest": {
        "adjectives": ["verdant", "shadowed", "fae", "mossy", "thorned", "silent", "amber", "arcane", "twilit", "moonbound"],
        "nouns": ["thicket", "grove", "canopy", "trail", "clearing", "tree-ring", "copse", "sanctum", "shrine", "pool"],
    },
    "mountains": {
        "adjectives": ["frozen", "stormy", "granite", "high", "shattered", "howling", "ashen", "obsidian", "glacial", "thunder"],
        "nouns": ["peak", "pass", "cliff", "ridge", "summit", "cavern", "mine", "crag", "fort", "spire"],
    },
    "dungeon": {
        "adjectives": ["cursed", "forbidden", "forgotten", "abyssal", "eldritch", "violet", "haunted", "demonic", "void", "eternal"],
        "nouns": ["crypt", "labyrinth", "vault", "hall", "catacomb", "citadel", "pit", "gateway", "arena", "rift"],
    },
}

QUEST_OBJECTIVES = [
    "escort a caravan through monster roads",
    "rescue a trapped villager from slime caverns",
    "collect moon petals before dawn",
    "defeat rogue bandits near the broken gate",
    "recover a stolen heirloom blade",
    "investigate crimson lights in the ruin",
    "clear wolves from the orchard",
    "deliver mana crystals to a remote shrine",
    "protect a merchant camp at twilight",
    "hunt a corrupted treant",
    "gather ore for blacksmith apprentices",
    "repair ancient totems in the forest",
    "challenge a rival adventurer",
    "trace missing scouts by footprints",
    "seal an unstable portal",
    "rebuild the village watchtower",
    "capture a runaway mimic chest",
    "collect fireflies for alchemy",
    "guard lovers meeting under moonlight",
    "retrieve an artifact from a cursed hall",
    "rescue a cat from a demon roof",
    "reclaim a haunted windmill",
    "escort children to the next settlement",
    "map hidden dungeon corridors",
    "recover tax records from goblin raiders",
    "help a waifu bard gather song echoes",
    "purify a lake touched by shadow",
    "restore a broken teleport obelisk",
    "craft emergency medicine for refugees",
    "track a ghost caravan",
]

QUEST_REWARDS = [
    "gold chest",
    "core cluster",
    "artisan tool kit",
    "enchanted plank stack",
    "arcane sword blueprint",
    "isekai blessing token",
    "faction reputation",
    "merchant discount voucher",
    "dragon scale fragment",
    "mystic accessory",
    "training manual",
    "companion contract",
]

EVENT_INTROS = [
    "A trumpet of alarm echoes across the valley.",
    "The sky flashes and the wind tastes of mana.",
    "Villagers run in panic from the northern road.",
    "A mysterious letter arrives bearing your name.",
    "The earth trembles with a distant roar.",
    "An arcane sigil burns into the ground nearby.",
    "Merchants shout for guards at the city gate.",
    "A godlike whisper invades your thoughts.",
    "A rival hero posts a challenge notice.",
    "A wounded scout collapses at your campfire.",
    "Strange purple lightning splits the clouds.",
    "A caravan bell rings in desperate rhythm.",
]

NPC_DIALOGUES = {
    "villager": [
        "Thanks for helping us. We can finally sleep tonight.",
        "Monsters get bold after rain. Please be careful.",
        "If you build houses, more people will arrive.",
        "Some say this world is a game. You feel that too?",
        "I saw a star fall where the old ruins stand.",
        "Merchants pay better after you gain reputation.",
        "The rival hero is flashy, but your heart seems stronger.",
        "Our crops grow faster near your strange aura.",
        "Bandits took my ring. I still believe you'll get it back.",
        "I heard singing in the dungeon halls.",
    ],
    "merchant": [
        "Premium blades, premium prices, premium survival!",
        "Bring me cores and I can open special stock.",
        "Caravan routes are cursed this week.",
        "Your fame improves my profit. Keep it up.",
        "A demon lord bounty just doubled.",
        "Rain damages goods. Buy now before shortages.",
        "I can hire companions if you pay enough.",
        "Guild taxes are brutal this season.",
        "Found this amulet in meteor debris.",
        "Try selling crafted staffs; huge margin.",
    ],
    "waifu": [
        "Senpai, your aura is dazzling tonight.",
        "Let me support your quest chain.",
        "I can fight or manage your village, your choice.",
        "The moon makes your sword look legendary.",
        "I dreamt of a gate to your old world.",
        "Summon me when danger gets overwhelming.",
        "Your kindness is your strongest stat.",
        "Let's rebuild this village together.",
        "Teach me your time-slow trick someday.",
        "I wrote a song about your first battle.",
    ],
}

WORLD_FLAVOR_LINES = [
    "A distant bell rings three times, then silence.",
    "You notice glowing mushrooms near wet rocks.",
    "A fox watches from a hill before vanishing.",
    "The wind carries laughter from a ruined village.",
    "Ancient runes pulse softly in the dirt.",
    "A fallen star leaves a silver trail overhead.",
    "Drums echo far beyond the forest line.",
    "Clouds briefly form a dragon silhouette.",
    "The grass glitters like tiny gemstones.",
    "You hear distant chanting from the mountains.",
    "Shadows shift unnaturally near dungeon doors.",
    "A merchant banner flaps on an empty road.",
    "Rain smells like ozone and wildflowers.",
    "A raven drops a key and flies away.",
    "The moonlight paints your sword in blue.",
]
