"""
hunting.py - Hunting System for The Great Divide Trail

Handles all hunting mechanics including success calculations,
food yield, ammunition consumption, and hunting risks.
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# Constants and Enums
# =============================================================================

class HuntingStyle(Enum):
    """Different approaches to hunting."""
    CONSERVATIVE = "conservative"  # Low risk, low reward
    NORMAL = "normal"              # Balanced approach
    AGGRESSIVE = "aggressive"      # High risk, high reward


class GameAnimal(Enum):
    """Types of game that can be hunted."""
    RABBIT = "rabbit"
    DEER = "deer"
    ELK = "elk"
    BISON = "bison"
    BEAR = "bear"
    MOOSE = "moose"
    MOUNTAIN_GOAT = "mountain_goat"
    WATERFOWL = "waterfowl"


# Animal data: food yield, difficulty, ammo cost, danger level
ANIMAL_DATA = {
    GameAnimal.RABBIT: {
        "name": "Rabbit",
        "food_yield": (5, 10),      # Min, max pounds
        "difficulty": 20,           # Base difficulty to hit
        "ammo_cost": (1, 2),        # Min, max ammo used
        "danger": 0,                # Chance of injury
        "terrain": ["plains", "forest", "mountains", "desert"],
    },
    GameAnimal.WATERFOWL: {
        "name": "Waterfowl",
        "food_yield": (8, 15),
        "difficulty": 35,
        "ammo_cost": (2, 4),
        "danger": 0,
        "terrain": ["plains", "forest"],
    },
    GameAnimal.DEER: {
        "name": "Deer",
        "food_yield": (30, 50),
        "difficulty": 40,
        "ammo_cost": (2, 4),
        "danger": 5,
        "terrain": ["forest", "plains", "mountains"],
    },
    GameAnimal.ELK: {
        "name": "Elk",
        "food_yield": (100, 150),
        "difficulty": 50,
        "ammo_cost": (3, 6),
        "danger": 10,
        "terrain": ["forest", "mountains"],
    },
    GameAnimal.MOUNTAIN_GOAT: {
        "name": "Mountain Goat",
        "food_yield": (40, 60),
        "difficulty": 60,
        "ammo_cost": (2, 5),
        "danger": 15,  # Dangerous terrain
        "terrain": ["mountains", "tundra"],
    },
    GameAnimal.BISON: {
        "name": "Bison",
        "food_yield": (200, 400),
        "difficulty": 55,
        "ammo_cost": (4, 8),
        "danger": 20,
        "terrain": ["plains"],
    },
    GameAnimal.MOOSE: {
        "name": "Moose",
        "food_yield": (150, 250),
        "difficulty": 50,
        "ammo_cost": (3, 6),
        "danger": 25,  # Moose are dangerous!
        "terrain": ["forest", "tundra"],
    },
    GameAnimal.BEAR: {
        "name": "Bear",
        "food_yield": (150, 200),
        "difficulty": 65,
        "ammo_cost": (5, 10),
        "danger": 40,  # Very dangerous
        "terrain": ["forest", "mountains"],
    },
}

# Terrain hunting modifiers
TERRAIN_HUNTING_MODS = {
    "desert": -30,      # Very hard to find game
    "plains": 10,       # Good hunting
    "mountains": -10,   # Harder terrain
    "forest": 20,       # Best hunting
    "tundra": -20,      # Sparse game
}

# Weather hunting modifiers  
WEATHER_HUNTING_MODS = {
    "clear": 10,
    "cloudy": 5,
    "rain": -15,
    "storm": -40,
    "hot": -10,
    "cold": -5,
    "snow": -25,
    "blizzard": -50,  # Essentially impossible
}

# Hunting style modifiers
STYLE_MODIFIERS = {
    HuntingStyle.CONSERVATIVE: {
        "success_mod": -10,
        "yield_mod": 0.7,
        "ammo_mod": 0.6,
        "danger_mod": 0.3,
        "time_hours": 2,
    },
    HuntingStyle.NORMAL: {
        "success_mod": 0,
        "yield_mod": 1.0,
        "ammo_mod": 1.0,
        "danger_mod": 1.0,
        "time_hours": 4,
    },
    HuntingStyle.AGGRESSIVE: {
        "success_mod": 15,
        "yield_mod": 1.3,
        "ammo_mod": 1.5,
        "danger_mod": 2.0,
        "time_hours": 6,
    },
}


# =============================================================================
# Hunting Result Data Class
# =============================================================================

@dataclass
class HuntingResult:
    """Results of a hunting expedition."""
    success: bool
    animal: Optional[GameAnimal]
    food_gained: int
    ammo_used: int
    hunter_injured: bool
    injury_damage: int
    time_spent: int  # Hours
    message: str
    details: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "animal": self.animal.value if self.animal else None,
            "food_gained": self.food_gained,
            "ammo_used": self.ammo_used,
            "hunter_injured": self.hunter_injured,
            "injury_damage": self.injury_damage,
            "time_spent": self.time_spent,
            "message": self.message,
            "details": self.details,
        }


# =============================================================================
# Hunting Manager Class
# =============================================================================

class HuntingManager:
    """
    Manages all hunting-related game mechanics.
    """
    
    def __init__(self):
        """Initialize the hunting manager."""
        self.hunting_history: List[Dict] = []
    
    # =========================================================================
    # Animal Selection
    # =========================================================================
    
    def get_available_animals(self, terrain: str) -> List[GameAnimal]:
        """
        Get animals available in the current terrain.
        
        Args:
            terrain: Current terrain type
        
        Returns:
            List of available GameAnimal types
        """
        available = []
        for animal, data in ANIMAL_DATA.items():
            if terrain in data["terrain"]:
                available.append(animal)
        return available
    
    def select_target_animal(
        self, 
        terrain: str, 
        hunter_skill: int = 50,
        prefer_safe: bool = False
    ) -> Optional[GameAnimal]:
        """
        Select which animal the hunter encounters.
        
        Higher skill hunters encounter better game.
        
        Args:
            terrain: Current terrain type
            hunter_skill: Hunter's effective skill
            prefer_safe: If True, prefer less dangerous animals
        
        Returns:
            Selected animal or None if no game found
        """
        available = self.get_available_animals(terrain)
        if not available:
            return None
        
        # Weight animals by skill level
        weights = []
        for animal in available:
            data = ANIMAL_DATA[animal]
            
            # Base weight inversely proportional to difficulty
            weight = max(10, 100 - data["difficulty"])
            
            # Skill bonus - better hunters find better game
            if hunter_skill > 50:
                skill_bonus = (hunter_skill - 50) / 50
                weight += data["food_yield"][1] * skill_bonus * 0.1
            
            # Safety preference
            if prefer_safe and data["danger"] > 20:
                weight *= 0.3
            
            weights.append(max(1, int(weight)))
        
        # Weighted random selection
        total = sum(weights)
        roll = random.randint(1, total)
        
        cumulative = 0
        for animal, weight in zip(available, weights):
            cumulative += weight
            if roll <= cumulative:
                return animal
        
        return available[0]
    
    # =========================================================================
    # Hunting Execution
    # =========================================================================
    
    def calculate_success_chance(
        self,
        animal: GameAnimal,
        hunter_skill: int,
        terrain: str,
        weather: str,
        style: HuntingStyle
    ) -> int:
        """
        Calculate the chance of a successful hunt.
        
        Args:
            animal: Target animal
            hunter_skill: Hunter's effective skill (0-100)
            terrain: Current terrain
            weather: Current weather
            style: Hunting approach
        
        Returns:
            Success chance as percentage (0-100)
        """
        animal_data = ANIMAL_DATA[animal]
        style_data = STYLE_MODIFIERS[style]
        
        # Base chance from skill vs difficulty
        base_chance = hunter_skill - animal_data["difficulty"] + 50
        
        # Apply modifiers
        terrain_mod = TERRAIN_HUNTING_MODS.get(terrain, 0)
        weather_mod = WEATHER_HUNTING_MODS.get(weather, 0)
        style_mod = style_data["success_mod"]
        
        total_chance = base_chance + terrain_mod + weather_mod + style_mod
        
        # Clamp to reasonable range
        return max(5, min(95, total_chance))
    
    def hunt(
        self,
        terrain: str,
        weather: str,
        hunter_skill: int = 50,
        hunting_bonus: int = 0,
        ammo_available: int = 100,
        style: HuntingStyle = HuntingStyle.NORMAL,
        location_bonus: int = 0,
        equipment_bonus: int = 0,
        **kwargs
    ) -> HuntingResult:
        
        effective_skill = hunter_skill + hunting_bonus + location_bonus + equipment_bonus

        """
        Execute a hunting expedition.
        
        Args:
            terrain: Current terrain type
            weather: Current weather condition
            hunter_skill: Hunter's base skill (0-100)
            hunting_bonus: Role bonus from Hunter class
            ammo_available: Ammunition available
            style: Hunting approach
            location_bonus: Bonus from current location
        
        Returns:
            HuntingResult with all outcomes
        """
        details = []
        
        # Apply bonuses to effective skill
        effective_skill = hunter_skill + hunting_bonus + location_bonus
        effective_skill = max(10, min(100, effective_skill))
        
        style_data = STYLE_MODIFIERS[style]
        
        # Check if we have enough ammo
        min_ammo_needed = 2
        if ammo_available < min_ammo_needed:
            return HuntingResult(
                success=False,
                animal=None,
                food_gained=0,
                ammo_used=0,
                hunter_injured=False,
                injury_damage=0,
                time_spent=1,
                message="Not enough ammunition to hunt!",
                details=["You need at least 2 rounds of ammunition."]
            )
        
        # Select target animal
        animal = self.select_target_animal(
            terrain, 
            effective_skill,
            prefer_safe=(style == HuntingStyle.CONSERVATIVE)
        )
        
        if not animal:
            return HuntingResult(
                success=False,
                animal=None,
                food_gained=0,
                ammo_used=0,
                hunter_injured=False,
                injury_damage=0,
                time_spent=style_data["time_hours"],
                message="No game could be found in this area.",
                details=[f"The {terrain} terrain offers little in the way of wildlife."]
            )
        
        animal_data = ANIMAL_DATA[animal]
        details.append(f"Tracking {animal_data['name'].lower()}...")
        
        # Calculate success chance
        success_chance = self.calculate_success_chance(
            animal, effective_skill, terrain, weather, style
        )
        details.append(f"Estimated success chance: {success_chance}%")
        
        # Calculate ammo usage
        base_ammo = random.randint(*animal_data["ammo_cost"])
        ammo_used = int(base_ammo * style_data["ammo_mod"])
        ammo_used = min(ammo_used, ammo_available)
        
        # Roll for success
        roll = random.randint(1, 100)
        success = roll <= success_chance
        
        # Calculate danger/injury
        danger_chance = animal_data["danger"] * style_data["danger_mod"]
        injury_roll = random.randint(1, 100)
        hunter_injured = injury_roll <= danger_chance
        injury_damage = 0
        
        if hunter_injured:
            # Injury severity based on animal
            if animal in [GameAnimal.BEAR, GameAnimal.MOOSE, GameAnimal.BISON]:
                injury_damage = random.randint(20, 40)
            elif animal in [GameAnimal.ELK, GameAnimal.MOUNTAIN_GOAT]:
                injury_damage = random.randint(10, 25)
            else:
                injury_damage = random.randint(5, 15)
        
        # Calculate results
        if success:
            base_yield = random.randint(*animal_data["food_yield"])
            food_gained = int(base_yield * style_data["yield_mod"])
            
            if hunter_injured:
                message = f"Brought down a {animal_data['name'].lower()}, but the hunter was injured in the process!"
                details.append(f"The {animal_data['name'].lower()} fought back before going down.")
                details.append(f"Hunter took {injury_damage} damage.")
            else:
                message = f"Successfully hunted a {animal_data['name'].lower()}!"
            
            details.append(f"Gained {food_gained} lbs of meat.")
            details.append(f"Used {ammo_used} ammunition.")
            
        else:
            food_gained = 0
            
            if hunter_injured:
                message = f"The hunt failed, and the hunter was injured!"
                details.append(f"The {animal_data['name'].lower()} attacked during the failed hunt.")
                details.append(f"Hunter took {injury_damage} damage.")
            else:
                # Various failure messages
                failure_messages = [
                    f"The {animal_data['name'].lower()} escaped.",
                    "The shot went wide.",
                    f"Lost track of the {animal_data['name'].lower()} in the brush.",
                    "The hunt was unsuccessful.",
                ]
                message = random.choice(failure_messages)
            
            details.append(f"Wasted {ammo_used} ammunition.")
        
        # Record hunt
        result = HuntingResult(
            success=success,
            animal=animal,
            food_gained=food_gained,
            ammo_used=ammo_used,
            hunter_injured=hunter_injured,
            injury_damage=injury_damage,
            time_spent=style_data["time_hours"],
            message=message,
            details=details
        )
        
        self._record_hunt(result)
        
        return result
    
    def _record_hunt(self, result: HuntingResult):
        """Record hunt in history."""
        self.hunting_history.append(result.to_dict())
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_hunting_forecast(
        self,
        terrain: str,
        weather: str,
        hunter_skill: int = 50,
        hunting_bonus: int = 0,
        location_bonus: int = 0
    ) -> Dict:
        """
        Get a forecast of hunting conditions.
        
        Args:
            terrain: Current terrain
            weather: Current weather
            hunter_skill: Hunter's skill
            hunting_bonus: Role bonus
            location_bonus: Location bonus
        
        Returns:
            Dict with hunting prospects
        """
        effective_skill = hunter_skill + hunting_bonus + location_bonus
        
        terrain_mod = TERRAIN_HUNTING_MODS.get(terrain, 0)
        weather_mod = WEATHER_HUNTING_MODS.get(weather, 0)
        
        combined_mod = terrain_mod + weather_mod + location_bonus
        
        if combined_mod >= 20:
            prospects = "Excellent"
            description = "Game is plentiful and conditions are ideal."
        elif combined_mod >= 5:
            prospects = "Good"
            description = "Decent hunting conditions."
        elif combined_mod >= -10:
            prospects = "Fair"
            description = "Game is scarce but huntable."
        elif combined_mod >= -25:
            prospects = "Poor"
            description = "Difficult conditions for hunting."
        else:
            prospects = "Terrible"
            description = "Hunting would be nearly impossible."
        
        available = self.get_available_animals(terrain)
        
        return {
            "prospects": prospects,
            "description": description,
            "terrain_modifier": terrain_mod,
            "weather_modifier": weather_mod,
            "location_bonus": location_bonus,
            "effective_skill": effective_skill,
            "available_game": [ANIMAL_DATA[a]["name"] for a in available],
        }
    
    def get_style_descriptions(self) -> List[Dict]:
        """Get descriptions of hunting styles for UI."""
        return [
            {
                "style": HuntingStyle.CONSERVATIVE.value,
                "name": "Conservative Hunt",
                "description": "Take your time, use less ammo, lower risk but smaller yield",
                "time": "~2 hours",
                "risk": "Low",
            },
            {
                "style": HuntingStyle.NORMAL.value,
                "name": "Normal Hunt", 
                "description": "Balanced approach with moderate risk and reward",
                "time": "~4 hours",
                "risk": "Medium",
            },
            {
                "style": HuntingStyle.AGGRESSIVE.value,
                "name": "Aggressive Hunt",
                "description": "Go for big game, use more ammo, higher risk but bigger yield",
                "time": "~6 hours", 
                "risk": "High",
            },
        ]
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    def get_statistics(self) -> Dict:
        """Get hunting statistics."""
        if not self.hunting_history:
            return {
                "total_hunts": 0,
                "successful_hunts": 0,
                "success_rate": 0,
                "total_food": 0,
                "total_ammo": 0,
                "injuries": 0,
            }
        
        successful = [h for h in self.hunting_history if h["success"]]
        
        return {
            "total_hunts": len(self.hunting_history),
            "successful_hunts": len(successful),
            "success_rate": len(successful) / len(self.hunting_history) * 100,
            "total_food": sum(h["food_gained"] for h in self.hunting_history),
            "total_ammo": sum(h["ammo_used"] for h in self.hunting_history),
            "injuries": sum(1 for h in self.hunting_history if h["hunter_injured"]),
        }
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for saving."""
        return {
            "hunting_history": self.hunting_history,
        }
    
    def load_state(self, data: Dict):
        """Load state from dictionary."""
        self.hunting_history = data.get("hunting_history", [])


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate hunting system functionality."""
    print("=" * 50)
    print("HUNTING SYSTEM DEMO")
    print("=" * 50)
    print()
    
    hm = HuntingManager()
    
    # Show available game by terrain
    print("Available game by terrain:")
    for terrain in ["plains", "forest", "mountains", "desert", "tundra"]:
        animals = hm.get_available_animals(terrain)
        names = [ANIMAL_DATA[a]["name"] for a in animals]
        print(f"  {terrain.title()}: {', '.join(names)}")
    print()
    
    # Show hunting styles
    print("Hunting styles:")
    for style_info in hm.get_style_descriptions():
        print(f"  {style_info['name']}")
        print(f"    {style_info['description']}")
        print(f"    Time: {style_info['time']}, Risk: {style_info['risk']}")
    print()
    
    # Get hunting forecast
    print("Hunting forecast (forest, clear weather, skill 60):")
    forecast = hm.get_hunting_forecast("forest", "clear", 60, hunting_bonus=30)
    print(f"  Prospects: {forecast['prospects']}")
    print(f"  {forecast['description']}")
    print(f"  Available game: {', '.join(forecast['available_game'])}")
    print()
    
    # Simulate several hunts
    print("Simulating 10 hunts...")
    terrains = ["forest", "plains", "mountains"]
    weathers = ["clear", "cloudy", "rain"]
    styles = [HuntingStyle.CONSERVATIVE, HuntingStyle.NORMAL, HuntingStyle.AGGRESSIVE]
    
    for i in range(10):
        terrain = random.choice(terrains)
        weather = random.choice(weathers)
        style = random.choice(styles)
        
        result = hm.hunt(
            terrain=terrain,
            weather=weather,
            hunter_skill=55,
            hunting_bonus=30,
            ammo_available=50,
            style=style
        )
        
        status = "✓" if result.success else "✗"
        injury = " (INJURED!)" if result.hunter_injured else ""
        print(f"  {i+1}. [{status}] {terrain}/{weather}/{style.value}: "
              f"{result.food_gained} lbs, {result.ammo_used} ammo{injury}")
    print()
    
    # Show statistics
    print("Hunting statistics:")
    stats = hm.get_statistics()
    print(f"  Total hunts: {stats['total_hunts']}")
    print(f"  Successful: {stats['successful_hunts']} ({stats['success_rate']:.1f}%)")
    print(f"  Total food gained: {stats['total_food']} lbs")
    print(f"  Total ammo used: {stats['total_ammo']}")
    print(f"  Injuries: {stats['injuries']}")
    print()
    
    # Test edge cases
    print("Edge case tests:")
    
    # No ammo
    result = hm.hunt("forest", "clear", ammo_available=1)
    print(f"  No ammo: {result.message}")
    
    # Bad conditions
    result = hm.hunt("desert", "blizzard", hunter_skill=20, ammo_available=50)
    print(f"  Desert blizzard: {result.message}")
    
    print()
    print("Demo complete!")


if __name__ == "__main__":
    demo()