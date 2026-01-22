"""
gathering.py - Foraging and Fishing System for The Great Divide Trail

Handles non-hunting resource gathering including:
- Foraging (berries, herbs, water)
- Fishing
- Firewood collection (future use)
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# Constants and Enums
# =============================================================================

class ForagingType(Enum):
    """Types of foraging activities."""
    BERRIES = "berries"
    HERBS = "herbs"
    WATER = "water"
    FIREWOOD = "firewood"


class FishingMethod(Enum):
    """Fishing methods available."""
    LINE = "line"          # Hand line fishing
    NET = "net"            # Net fishing (requires net)
    SPEAR = "spear"        # Spear fishing


# Foraging yields by terrain (in lbs for food, gallons for water)
FORAGING_YIELDS = {
    "desert": {
        ForagingType.BERRIES: (0, 2),      # Very poor
        ForagingType.HERBS: (0, 1),
        ForagingType.WATER: (0, 5),        # Very scarce
    },
    "plains": {
        ForagingType.BERRIES: (2, 8),
        ForagingType.HERBS: (1, 3),
        ForagingType.WATER: (5, 15),
    },
    "mountains": {
        ForagingType.BERRIES: (3, 10),
        ForagingType.HERBS: (2, 5),
        ForagingType.WATER: (10, 25),      # Mountain streams
    },
    "forest": {
        ForagingType.BERRIES: (5, 15),     # Best for berries
        ForagingType.HERBS: (3, 8),
        ForagingType.WATER: (10, 20),
    },
    "tundra": {
        ForagingType.BERRIES: (1, 4),
        ForagingType.HERBS: (0, 2),
        ForagingType.WATER: (5, 15),       # Can melt snow
    },
}

# Weather affects foraging success
WEATHER_FORAGING_MODIFIERS = {
    "clear": 1.2,
    "cloudy": 1.0,
    "rain": 0.8,
    "storm": 0.5,
    "hot": 0.9,
    "cold": 0.8,
    "snow": 0.6,
    "blizzard": 0.3,
}

# Season affects foraging (berries best in summer/fall)
SEASON_FORAGING_MODIFIERS = {
    "spring": {"berries": 0.5, "herbs": 1.2, "water": 1.0},
    "summer": {"berries": 1.5, "herbs": 1.0, "water": 0.9},
    "fall": {"berries": 1.2, "herbs": 0.8, "water": 1.0},
    "winter": {"berries": 0.1, "herbs": 0.2, "water": 1.1},  # Can melt snow
}

# Fishing yields (in lbs)
FISHING_YIELDS = {
    "line": (2, 10),      # Hand line - low but consistent
    "net": (10, 25),      # Net - best yield but requires equipment
    "spear": (5, 15),     # Spear - middle ground
}

# Time spent on activities (hours)
ACTIVITY_TIME = {
    "foraging": 3,
    "fishing": 4,
    "water_gathering": 1,
}


# =============================================================================
# Result Data Classes
# =============================================================================

@dataclass
class ForagingResult:
    """Results of a foraging expedition."""
    success: bool
    forage_type: ForagingType
    food_gained: int
    water_gained: int
    time_spent: int  # Hours
    message: str
    details: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "forage_type": self.forage_type.value,
            "food_gained": self.food_gained,
            "water_gained": self.water_gained,
            "time_spent": self.time_spent,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class FishingResult:
    """Results of a fishing expedition."""
    success: bool
    method: FishingMethod
    food_gained: int
    time_spent: int  # Hours
    equipment_broken: bool
    message: str
    details: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "method": self.method.value,
            "food_gained": self.food_gained,
            "time_spent": self.time_spent,
            "equipment_broken": self.equipment_broken,
            "message": self.message,
            "details": self.details,
        }


# =============================================================================
# Gathering Manager Class
# =============================================================================

class GatheringManager:
    """
    Manages foraging and fishing activities.
    """
    
    def __init__(self):
        """Initialize the gathering manager."""
        self.foraging_history: List[Dict] = []
        self.fishing_history: List[Dict] = []
    
    # =========================================================================
    # Foraging
    # =========================================================================
    
    def can_forage(self, terrain: str, forage_type: ForagingType) -> Tuple[bool, str]:
        """
        Check if foraging is possible in current conditions.
        
        Args:
            terrain: Current terrain type
            forage_type: Type of foraging
        
        Returns:
            Tuple of (can_forage, reason)
        """
        if terrain not in FORAGING_YIELDS:
            return (False, "Unknown terrain")
        
        yields = FORAGING_YIELDS[terrain].get(forage_type)
        if not yields or yields[1] == 0:
            return (False, f"No {forage_type.value} available in this terrain")
        
        return (True, "")
    
    def forage(
        self,
        terrain: str,
        weather: str,
        season: str,
        forage_type: ForagingType = ForagingType.BERRIES,
        forager_skill: int = 50,
        party_size: int = 1
    ) -> ForagingResult:
        """
        Execute a foraging expedition.
        
        Args:
            terrain: Current terrain type
            weather: Current weather condition
            season: Current season
            forage_type: What to forage for
            forager_skill: Effective foraging skill (0-100)
            party_size: Number of people foraging
        
        Returns:
            ForagingResult with outcomes
        """
        details = []
        
        # Check if foraging is possible
        can_forage, reason = self.can_forage(terrain, forage_type)
        if not can_forage:
            return ForagingResult(
                success=False,
                forage_type=forage_type,
                food_gained=0,
                water_gained=0,
                time_spent=1,
                message=reason,
                details=[reason]
            )
        
        # Get base yields
        base_yields = FORAGING_YIELDS[terrain][forage_type]
        
        # Calculate modifiers
        weather_mod = WEATHER_FORAGING_MODIFIERS.get(weather, 1.0)
        
        # Season modifier (only for food items)
        season_mods = SEASON_FORAGING_MODIFIERS.get(season, {})
        season_mod = season_mods.get(forage_type.value, 1.0)
        
        # Skill modifier (better foragers find more)
        skill_mod = 0.5 + (forager_skill / 100)
        
        # Party size helps (diminishing returns)
        party_mod = 1 + (party_size - 1) * 0.3
        
        # Calculate final yield
        total_mod = weather_mod * season_mod * skill_mod * party_mod
        
        min_yield, max_yield = base_yields
        base_amount = random.uniform(min_yield, max_yield)
        final_amount = int(base_amount * total_mod)
        
        # Success check (higher skill = more consistent yields)
        success_chance = 60 + forager_skill / 3  # 60-93% success
        success = random.randint(1, 100) <= success_chance
        
        if not success:
            final_amount = int(final_amount * 0.3)  # Partial yield on failure
        
        # Build results
        food_gained = 0
        water_gained = 0
        
        if forage_type == ForagingType.WATER:
            water_gained = final_amount
            details.append(f"Gathered {water_gained} gallons of water")
        else:
            food_gained = final_amount
            if forage_type == ForagingType.BERRIES:
                details.append(f"Gathered {food_gained} lbs of berries and edible plants")
            elif forage_type == ForagingType.HERBS:
                details.append(f"Gathered {food_gained} lbs of edible herbs and roots")
        
        # Message
        if success:
            if final_amount > base_yields[1] * 0.7:
                message = f"Excellent foraging! Found plenty of {forage_type.value}."
            else:
                message = f"Successfully foraged for {forage_type.value}."
        else:
            message = f"Foraging was difficult, but you found some {forage_type.value}."
        
        result = ForagingResult(
            success=success,
            forage_type=forage_type,
            food_gained=food_gained,
            water_gained=water_gained,
            time_spent=ACTIVITY_TIME["foraging"] if forage_type != ForagingType.WATER else ACTIVITY_TIME["water_gathering"],
            message=message,
            details=details
        )
        
        self._record_foraging(result)
        return result
    
    def get_foraging_prospects(
        self,
        terrain: str,
        season: str,
        weather: str
    ) -> Dict:
        """
        Get foraging prospects for current conditions.
        
        Args:
            terrain: Current terrain
            season: Current season
            weather: Current weather
        
        Returns:
            Dict with prospects for each forage type
        """
        prospects = {}
        
        for forage_type in ForagingType:
            can_forage, reason = self.can_forage(terrain, forage_type)
            
            if not can_forage:
                prospects[forage_type.value] = {
                    "available": False,
                    "reason": reason,
                    "rating": "impossible"
                }
                continue
            
            # Calculate rough yield potential
            base_yields = FORAGING_YIELDS[terrain][forage_type]
            weather_mod = WEATHER_FORAGING_MODIFIERS.get(weather, 1.0)
            season_mods = SEASON_FORAGING_MODIFIERS.get(season, {})
            season_mod = season_mods.get(forage_type.value, 1.0)
            
            total_mod = weather_mod * season_mod
            avg_yield = (base_yields[0] + base_yields[1]) / 2 * total_mod
            
            # Rate prospects
            if avg_yield >= 10:
                rating = "excellent"
            elif avg_yield >= 6:
                rating = "good"
            elif avg_yield >= 3:
                rating = "fair"
            else:
                rating = "poor"
            
            prospects[forage_type.value] = {
                "available": True,
                "rating": rating,
                "estimated_yield": f"{int(base_yields[0] * total_mod)}-{int(base_yields[1] * total_mod)}"
            }
        
        return prospects
    
    # =========================================================================
    # Fishing
    # =========================================================================
    
    def can_fish(self, water_available: bool, has_tools: bool, method: FishingMethod) -> Tuple[bool, str]:
        """
        Check if fishing is possible.
        
        Args:
            water_available: Is there water nearby?
            has_tools: Does party have tools?
            method: Fishing method to use
        
        Returns:
            Tuple of (can_fish, reason)
        """
        if not water_available:
            return (False, "No suitable water nearby for fishing")
        
        # Net requires tools
        if method == FishingMethod.NET and not has_tools:
            return (False, "Need tools/equipment to fish with a net")
        
        return (True, "")
    
    def fish(
        self,
        water_available: bool,
        method: FishingMethod = FishingMethod.LINE,
        fisher_skill: int = 50,
        has_tools: bool = True,
        weather: str = "clear"
    ) -> FishingResult:
        """
        Execute a fishing expedition.
        
        Args:
            water_available: Is water nearby?
            method: Fishing method
            fisher_skill: Effective fishing skill (0-100)
            has_tools: Does party have tools?
            weather: Current weather
        
        Returns:
            FishingResult with outcomes
        """
        details = []
        
        # Check if fishing is possible
        can_fish, reason = self.can_fish(water_available, has_tools, method)
        if not can_fish:
            return FishingResult(
                success=False,
                method=method,
                food_gained=0,
                time_spent=1,
                equipment_broken=False,
                message=reason,
                details=[reason]
            )
        
        details.append(f"Fishing with {method.value}...")
        
        # Get base yields
        base_yields = FISHING_YIELDS[method]
        
        # Weather affects fishing
        weather_mod = {
            "clear": 1.2,
            "cloudy": 1.1,
            "rain": 0.9,     # Fish bite less in rain
            "storm": 0.5,
            "hot": 1.0,
            "cold": 0.8,
            "snow": 0.7,
            "blizzard": 0.3,
        }.get(weather, 1.0)
        
        # Skill modifier
        skill_mod = 0.5 + (fisher_skill / 100)
        
        # Calculate yield
        total_mod = weather_mod * skill_mod
        base_amount = random.uniform(base_yields[0], base_yields[1])
        final_amount = int(base_amount * total_mod)
        
        # Success check
        base_success = {
            FishingMethod.LINE: 70,
            FishingMethod.NET: 85,
            FishingMethod.SPEAR: 60,
        }[method]
        
        success_chance = base_success + (fisher_skill / 5)
        success = random.randint(1, 100) <= success_chance
        
        if not success:
            final_amount = int(final_amount * 0.2)  # Small yield on failure
        
        # Check for equipment breakage (only for net)
        equipment_broken = False
        if method == FishingMethod.NET and random.random() < 0.1:  # 10% chance
            equipment_broken = True
            details.append("The fishing net was damaged!")
        
        # Build message
        if success:
            if final_amount > base_yields[1] * 0.8:
                message = f"Excellent catch! The fish are biting well."
            else:
                message = f"Successful fishing with {method.value}."
        else:
            message = f"The fish weren't biting today."
        
        details.append(f"Caught {final_amount} lbs of fish")
        
        result = FishingResult(
            success=success,
            method=method,
            food_gained=final_amount,
            time_spent=ACTIVITY_TIME["fishing"],
            equipment_broken=equipment_broken,
            message=message,
            details=details
        )
        
        self._record_fishing(result)
        return result
    
    def get_fishing_prospects(
        self,
        water_available: bool,
        weather: str
    ) -> Dict:
        """
        Get fishing prospects for current conditions.
        
        Args:
            water_available: Is water nearby?
            weather: Current weather
        
        Returns:
            Dict with fishing prospects
        """
        if not water_available:
            return {
                "available": False,
                "reason": "No suitable water nearby",
                "rating": "impossible"
            }
        
        weather_mod = {
            "clear": 1.2,
            "cloudy": 1.1,
            "rain": 0.9,
            "storm": 0.5,
            "hot": 1.0,
            "cold": 0.8,
            "snow": 0.7,
            "blizzard": 0.3,
        }.get(weather, 1.0)
        
        if weather_mod >= 1.1:
            rating = "excellent"
        elif weather_mod >= 0.9:
            rating = "good"
        elif weather_mod >= 0.6:
            rating = "fair"
        else:
            rating = "poor"
        
        return {
            "available": True,
            "rating": rating,
            "description": f"Fishing conditions are {rating}",
            "methods": {
                "line": "Always available, low yield",
                "spear": "Moderate yield, skill-based",
                "net": "Best yield, requires tools"
            }
        }
    
    # =========================================================================
    # History & Statistics
    # =========================================================================
    
    def _record_foraging(self, result: ForagingResult):
        """Record foraging in history."""
        self.foraging_history.append(result.to_dict())
    
    def _record_fishing(self, result: FishingResult):
        """Record fishing in history."""
        self.fishing_history.append(result.to_dict())
    
    def get_statistics(self) -> Dict:
        """Get gathering statistics."""
        forage_success = sum(1 for h in self.foraging_history if h["success"])
        fish_success = sum(1 for h in self.fishing_history if h["success"])
        
        total_foraged_food = sum(h["food_gained"] for h in self.foraging_history)
        total_foraged_water = sum(h["water_gained"] for h in self.foraging_history)
        total_fish = sum(h["food_gained"] for h in self.fishing_history)
        
        return {
            "foraging": {
                "total_attempts": len(self.foraging_history),
                "successful": forage_success,
                "success_rate": (forage_success / len(self.foraging_history) * 100) if self.foraging_history else 0,
                "food_gathered": total_foraged_food,
                "water_gathered": total_foraged_water,
            },
            "fishing": {
                "total_attempts": len(self.fishing_history),
                "successful": fish_success,
                "success_rate": (fish_success / len(self.fishing_history) * 100) if self.fishing_history else 0,
                "food_caught": total_fish,
            }
        }
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for saving."""
        return {
            "foraging_history": self.foraging_history,
            "fishing_history": self.fishing_history,
        }
    
    def load_state(self, data: Dict):
        """Load state from dictionary."""
        self.foraging_history = data.get("foraging_history", [])
        self.fishing_history = data.get("fishing_history", [])


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate gathering system functionality."""
    print("=" * 50)
    print("GATHERING SYSTEM DEMO")
    print("=" * 50)
    print()
    
    gm = GatheringManager()
    
    # Test foraging prospects
    print("Foraging prospects (forest, summer, clear):")
    prospects = gm.get_foraging_prospects("forest", "summer", "clear")
    for forage_type, info in prospects.items():
        if info["available"]:
            print(f"  {forage_type.title()}: {info['rating']} ({info['estimated_yield']})")
        else:
            print(f"  {forage_type.title()}: {info['reason']}")
    print()
    
    # Test foraging
    print("Foraging for berries in forest...")
    result = gm.forage(
        terrain="forest",
        weather="clear",
        season="summer",
        forage_type=ForagingType.BERRIES,
        forager_skill=60,
        party_size=3
    )
    print(f"  {result.message}")
    for detail in result.details:
        print(f"    {detail}")
    print()
    
    # Test water gathering
    print("Gathering water in mountains...")
    result = gm.forage(
        terrain="mountains",
        weather="clear",
        season="spring",
        forage_type=ForagingType.WATER,
        forager_skill=50,
        party_size=2
    )
    print(f"  {result.message}")
    for detail in result.details:
        print(f"    {detail}")
    print()
    
    # Test fishing prospects
    print("Fishing prospects (water available, clear weather):")
    fish_prospects = gm.get_fishing_prospects(water_available=True, weather="clear")
    print(f"  Rating: {fish_prospects['rating']}")
    print(f"  {fish_prospects['description']}")
    print()
    
    # Test fishing
    print("Fishing with hand line...")
    result = gm.fish(
        water_available=True,
        method=FishingMethod.LINE,
        fisher_skill=55,
        has_tools=True,
        weather="clear"
    )
    print(f"  {result.message}")
    for detail in result.details:
        print(f"    {detail}")
    print()
    
    # Simulate multiple activities
    print("Simulating 10 gathering activities...")
    for i in range(10):
        if random.random() < 0.6:
            # Forage
            terrain = random.choice(["forest", "plains", "mountains"])
            season = random.choice(["spring", "summer", "fall"])
            forage_type = random.choice([ForagingType.BERRIES, ForagingType.HERBS, ForagingType.WATER])
            result = gm.forage(terrain, "clear", season, forage_type, 50, 2)
            print(f"  {i+1}. Foraged {forage_type.value}: {result.food_gained + result.water_gained} gained")
        else:
            # Fish
            method = random.choice([FishingMethod.LINE, FishingMethod.SPEAR])
            result = gm.fish(True, method, 50, True, "clear")
            print(f"  {i+1}. Fished ({method.value}): {result.food_gained} lbs caught")
    print()
    
    # Statistics
    print("Gathering statistics:")
    stats = gm.get_statistics()
    print(f"  Foraging attempts: {stats['foraging']['total_attempts']}")
    print(f"  Foraging success rate: {stats['foraging']['success_rate']:.1f}%")
    print(f"  Total food foraged: {stats['foraging']['food_gathered']} lbs")
    print(f"  Total water gathered: {stats['foraging']['water_gathered']} gallons")
    print()
    print(f"  Fishing attempts: {stats['fishing']['total_attempts']}")
    print(f"  Fishing success rate: {stats['fishing']['success_rate']:.1f}%")
    print(f"  Total fish caught: {stats['fishing']['food_caught']} lbs")
    print()
    
    print("Demo complete!")


if __name__ == "__main__":
    demo()