"""
difficulty_settings.py - Difficulty and Pace Settings for The Great Divide Trail

Provides difficulty modifiers and travel pace options that affect gameplay.
"""

from enum import Enum
from typing import Dict
from dataclasses import dataclass


# =============================================================================
# Enums
# =============================================================================

class Difficulty(Enum):
    """Difficulty levels."""
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXTREME = "extreme"


class TravelPace(Enum):
    """Travel pace options."""
    SLOW = "slow"
    STEADY = "steady"
    FAST = "fast"
    GRUELING = "grueling"


# =============================================================================
# Difficulty Modifiers
# =============================================================================

DIFFICULTY_MODIFIERS = {
    Difficulty.EASY: {
        "name": "Easy",
        "description": "Forgiving journey with ample supplies",
        
        # Resource modifiers
        "starting_resources": 1.5,      # 50% more starting supplies
        "resource_decay": 0.7,          # 30% slower decay
        "consumption_rate": 0.85,       # 15% less consumption
        
        # Event modifiers
        "event_frequency": 0.6,         # 40% fewer random events
        "negative_event_chance": 0.7,   # 30% fewer bad outcomes
        
        # Healing and health
        "healing_rate": 1.3,            # 30% better healing
        "disease_severity": 0.7,        # 30% milder diseases
        "natural_recovery": 1.5,        # 50% faster natural recovery
        
        # Hunting and foraging
        "hunting_success": 1.2,         # 20% better hunting
        "hunting_yield": 1.3,           # 30% more food from hunts
        "foraging_yield": 1.3,          # 30% more from foraging
        "fishing_success": 1.2,         # 20% better fishing
        
        # Weather
        "weather_severity": 0.8,        # 20% milder weather effects
        "blizzard_chance": 0.5,         # 50% fewer blizzards
        
        # Trading
        "trade_prices": 0.85,           # 15% cheaper goods
    },
    
    Difficulty.NORMAL: {
        "name": "Normal",
        "description": "Balanced challenge for most players",
        
        "starting_resources": 1.0,
        "resource_decay": 1.0,
        "consumption_rate": 1.0,
        
        "event_frequency": 1.0,
        "negative_event_chance": 1.0,
        
        "healing_rate": 1.0,
        "disease_severity": 1.0,
        "natural_recovery": 1.0,
        
        "hunting_success": 1.0,
        "hunting_yield": 1.0,
        "foraging_yield": 1.0,
        "fishing_success": 1.0,
        
        "weather_severity": 1.0,
        "blizzard_chance": 1.0,
        
        "trade_prices": 1.0,
    },
    
    Difficulty.HARD: {
        "name": "Hard",
        "description": "Harsh wilderness tests your survival skills",
        
        "starting_resources": 0.7,      # 30% fewer starting supplies
        "resource_decay": 1.4,          # 40% faster decay
        "consumption_rate": 1.15,       # 15% more consumption
        
        "event_frequency": 1.4,         # 40% more random events
        "negative_event_chance": 1.3,   # 30% more bad outcomes
        
        "healing_rate": 0.8,            # 20% slower healing
        "disease_severity": 1.3,        # 30% worse diseases
        "natural_recovery": 0.7,        # 30% slower natural recovery
        
        "hunting_success": 0.85,        # 15% harder hunting
        "hunting_yield": 0.8,           # 20% less food from hunts
        "foraging_yield": 0.8,          # 20% less from foraging
        "fishing_success": 0.85,        # 15% harder fishing
        
        "weather_severity": 1.2,        # 20% worse weather effects
        "blizzard_chance": 1.5,         # 50% more blizzards
        
        "trade_prices": 1.25,           # 25% more expensive goods
    },
    
    Difficulty.EXTREME: {
        "name": "Extreme",
        "description": "Brutal survival - only for experts",
        
        "starting_resources": 0.5,      # 50% fewer starting supplies
        "resource_decay": 1.8,          # 80% faster decay
        "consumption_rate": 1.3,        # 30% more consumption
        
        "event_frequency": 1.8,         # 80% more random events
        "negative_event_chance": 1.5,   # 50% more bad outcomes
        
        "healing_rate": 0.6,            # 40% slower healing
        "disease_severity": 1.6,        # 60% worse diseases
        "natural_recovery": 0.5,        # 50% slower natural recovery
        
        "hunting_success": 0.7,         # 30% harder hunting
        "hunting_yield": 0.6,           # 40% less food from hunts
        "foraging_yield": 0.6,          # 40% less from foraging
        "fishing_success": 0.7,         # 30% harder fishing
        
        "weather_severity": 1.5,        # 50% worse weather effects
        "blizzard_chance": 2.0,         # 100% more blizzards
        
        "trade_prices": 1.5,            # 50% more expensive goods
    },
}


# =============================================================================
# Travel Pace Settings
# =============================================================================

PACE_SETTINGS = {
    TravelPace.SLOW: {
        "name": "Slow and Careful",
        "description": "Cautious travel - safer but slower progress",
        "icon": "🐢",
        
        # Travel effects
        "speed_modifier": -30,          # 30% slower travel
        "miles_per_day_mult": 0.7,      # 70% of normal miles
        
        # Health effects
        "health_drain_per_day": 0,      # No health loss
        "morale_change_per_day": 2,     # +2 morale per day (relaxed pace)
        "exhaustion_chance": 0.0,       # No risk of exhaustion
        
        # Other effects
        "injury_chance_mult": 0.6,      # 40% less injury risk
        "hunting_time_available": 1.3,  # 30% more time for hunting/foraging
        "scouting_bonus": 5,            # Better scouting (+5)
    },
    
    TravelPace.STEADY: {
        "name": "Steady Pace",
        "description": "Normal, sustainable travel pace",
        "icon": "👣",
        
        "speed_modifier": 0,
        "miles_per_day_mult": 1.0,
        
        "health_drain_per_day": 0,
        "morale_change_per_day": 0,
        "exhaustion_chance": 0.0,
        
        "injury_chance_mult": 1.0,
        "hunting_time_available": 1.0,
        "scouting_bonus": 0,
    },
    
    TravelPace.FAST: {
        "name": "Fast Pace",
        "description": "Pushed pace - good progress but tiring",
        "icon": "🏃",
        
        "speed_modifier": 20,           # 20% faster travel
        "miles_per_day_mult": 1.3,      # 130% of normal miles
        
        "health_drain_per_day": 2,      # -2 health per day
        "morale_change_per_day": -3,    # -3 morale per day (tiring)
        "exhaustion_chance": 0.15,      # 15% chance of exhaustion
        
        "injury_chance_mult": 1.3,      # 30% more injury risk
        "hunting_time_available": 0.7,  # 30% less time for hunting/foraging
        "scouting_bonus": -5,           # Worse scouting (-5)
    },
    
    TravelPace.GRUELING: {
        "name": "Grueling Pace",
        "description": "Maximum speed - dangerous and exhausting",
        "icon": "💨",
        
        "speed_modifier": 40,           # 40% faster travel
        "miles_per_day_mult": 1.6,      # 160% of normal miles
        
        "health_drain_per_day": 5,      # -5 health per day
        "morale_change_per_day": -8,    # -8 morale per day (brutal)
        "exhaustion_chance": 0.35,      # 35% chance of exhaustion
        
        "injury_chance_mult": 1.8,      # 80% more injury risk
        "hunting_time_available": 0.4,  # 60% less time for hunting/foraging
        "scouting_bonus": -10,          # Much worse scouting (-10)
    },
}


# =============================================================================
# Helper Classes
# =============================================================================

@dataclass
class GameSettings:
    """Container for current game difficulty and pace settings."""
    difficulty: Difficulty = Difficulty.NORMAL
    pace: TravelPace = TravelPace.STEADY
    
    def get_difficulty_modifier(self, key: str) -> float:
        """Get a difficulty modifier value."""
        return DIFFICULTY_MODIFIERS[self.difficulty].get(key, 1.0)
    
    def get_pace_setting(self, key: str) -> float:
        """Get a pace setting value."""
        return PACE_SETTINGS[self.pace].get(key, 0)
    
    def apply_difficulty_to_value(self, base_value: float, modifier_key: str) -> float:
        """Apply difficulty modifier to a base value."""
        modifier = self.get_difficulty_modifier(modifier_key)
        return base_value * modifier
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for saving."""
        return {
            "difficulty": self.difficulty.value,
            "pace": self.pace.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GameSettings':
        """Create from dictionary."""
        diff_str = data.get("difficulty", "normal")
        pace_str = data.get("pace", "steady")
        
        # Find matching enums
        difficulty = Difficulty.NORMAL
        for d in Difficulty:
            if d.value == diff_str:
                difficulty = d
                break
        
        pace = TravelPace.STEADY
        for p in TravelPace:
            if p.value == pace_str:
                pace = p
                break
        
        return cls(difficulty=difficulty, pace=pace)


# =============================================================================
# UI Helper Functions
# =============================================================================

def get_difficulty_descriptions() -> list:
    """Get list of difficulty options for UI display."""
    options = []
    for diff in Difficulty:
        mods = DIFFICULTY_MODIFIERS[diff]
        options.append({
            "value": diff,
            "name": mods["name"],
            "description": mods["description"],
        })
    return options


def get_pace_descriptions() -> list:
    """Get list of pace options for UI display."""
    options = []
    for pace in TravelPace:
        settings = PACE_SETTINGS[pace]
        
        # Build effects summary
        effects = []
        if settings["miles_per_day_mult"] != 1.0:
            pct = int((settings["miles_per_day_mult"] - 1.0) * 100)
            if pct > 0:
                effects.append(f"+{pct}% miles")
            else:
                effects.append(f"{pct}% miles")
        
        if settings["health_drain_per_day"] != 0:
            effects.append(f"{settings['health_drain_per_day']:+d} health/day")
        
        if settings["morale_change_per_day"] != 0:
            effects.append(f"{settings['morale_change_per_day']:+d} morale/day")
        
        effects_str = ", ".join(effects) if effects else "No penalties"
        
        options.append({
            "value": pace,
            "name": settings["name"],
            "icon": settings["icon"],
            "description": settings["description"],
            "effects": effects_str,
        })
    return options


def format_pace_display(pace: TravelPace) -> str:
    """Format pace for status display."""
    settings = PACE_SETTINGS[pace]
    return f"{settings['icon']} {settings['name']}"


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate difficulty and pace settings."""
    print("=" * 50)
    print("DIFFICULTY & PACE SETTINGS DEMO")
    print("=" * 50)
    print()
    
    # Show difficulties
    print("DIFFICULTY LEVELS:")
    for diff_info in get_difficulty_descriptions():
        print(f"\n  {diff_info['name'].upper()}")
        print(f"  {diff_info['description']}")
        
        mods = DIFFICULTY_MODIFIERS[diff_info['value']]
        print(f"  Starting supplies: {mods['starting_resources']*100:.0f}%")
        print(f"  Resource decay: {mods['resource_decay']*100:.0f}%")
        print(f"  Hunting success: {mods['hunting_success']*100:.0f}%")
        print(f"  Event frequency: {mods['event_frequency']*100:.0f}%")
    
    print()
    print("=" * 50)
    print()
    
    # Show paces
    print("TRAVEL PACE OPTIONS:")
    for pace_info in get_pace_descriptions():
        print(f"\n  {pace_info['icon']} {pace_info['name'].upper()}")
        print(f"  {pace_info['description']}")
        print(f"  Effects: {pace_info['effects']}")
    
    print()
    print("=" * 50)
    print()
    
    # Test GameSettings
    print("TESTING GameSettings CLASS:")
    settings = GameSettings(Difficulty.HARD, TravelPace.FAST)
    
    print(f"  Difficulty: {settings.difficulty.value}")
    print(f"  Pace: {settings.pace.value}")
    print()
    
    # Apply some modifiers
    base_supplies = 100
    modified = settings.apply_difficulty_to_value(base_supplies, "starting_resources")
    print(f"  Base supplies: {base_supplies}")
    print(f"  Hard difficulty: {modified}")
    print()
    
    # Get pace effects
    health_drain = settings.get_pace_setting("health_drain_per_day")
    miles_mult = settings.get_pace_setting("miles_per_day_mult")
    print(f"  Fast pace health drain: {health_drain} per day")
    print(f"  Fast pace miles multiplier: {miles_mult}x")
    print()
    
    # Serialization
    print("SERIALIZATION TEST:")
    data = settings.to_dict()
    print(f"  Saved: {data}")
    
    restored = GameSettings.from_dict(data)
    print(f"  Restored difficulty: {restored.difficulty.value}")
    print(f"  Restored pace: {restored.pace.value}")
    print()
    
    print("Demo complete!")


if __name__ == "__main__":
    demo()