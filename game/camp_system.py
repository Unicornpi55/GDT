"""
camp_system.py - Camp Quality System for The Great Divide Trail

Handles camp setup and quality which affects:
- Rest effectiveness
- Healing rates
- Morale recovery
- Protection from weather
- Risk of night events
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# Enums and Constants
# =============================================================================

class CampType(Enum):
    """Types of camps that can be set up."""
    MINIMAL = "minimal"         # Quick stop, no real camp
    BASIC = "basic"             # Simple camp setup
    STANDARD = "standard"       # Normal camp with fire
    COMFORTABLE = "comfortable" # Well-organized camp
    FORTIFIED = "fortified"     # Defensive camp (uses more resources)


class CampFeature(Enum):
    """Features that can be added to a camp."""
    FIRE = "fire"               # Campfire (warmth, cooking, morale)
    SHELTER = "shelter"         # Tent/tarp setup
    WINDBREAK = "windbreak"     # Protection from wind
    WATCH = "watch"             # Night watch rotation
    PERIMETER = "perimeter"     # Defensive perimeter
    CACHE = "cache"             # Secure food storage (vs animals)


# Base camp quality by type (0-100)
CAMP_TYPE_BASE_QUALITY = {
    CampType.MINIMAL: 20,
    CampType.BASIC: 40,
    CampType.STANDARD: 60,
    CampType.COMFORTABLE: 80,
    CampType.FORTIFIED: 75,  # Less comfortable but safer
}

# Time to set up camp (hours)
CAMP_SETUP_TIME = {
    CampType.MINIMAL: 0.5,
    CampType.BASIC: 1,
    CampType.STANDARD: 2,
    CampType.COMFORTABLE: 3,
    CampType.FORTIFIED: 4,
}

# Resource usage per night
CAMP_RESOURCE_USAGE = {
    CampType.MINIMAL: {"food_mult": 1.0},
    CampType.BASIC: {"food_mult": 1.0},
    CampType.STANDARD: {"food_mult": 1.0, "tools_wear": 0.1},
    CampType.COMFORTABLE: {"food_mult": 1.1, "tools_wear": 0.15},
    CampType.FORTIFIED: {"food_mult": 1.0, "tools_wear": 0.2, "ammo_use": 0},
}

# Terrain camping modifiers
TERRAIN_CAMP_MODIFIERS = {
    "desert": {
        "quality_mod": -10,
        "shelter_difficulty": 20,  # Harder to find materials
        "fire_risk": 0,            # Low humidity = easier fire
        "animal_risk": 10,
        "description": "The open desert offers little shelter from sun or wind.",
    },
    "plains": {
        "quality_mod": 0,
        "shelter_difficulty": 10,
        "fire_risk": 10,  # Grass fires
        "animal_risk": 20,
        "description": "Flat grassland with good visibility but exposure to elements.",
    },
    "mountains": {
        "quality_mod": -15,
        "shelter_difficulty": 15,
        "fire_risk": 0,
        "animal_risk": 15,
        "description": "Rocky terrain makes for uncomfortable sleeping.",
    },
    "forest": {
        "quality_mod": 15,
        "shelter_difficulty": 0,  # Easy to find materials
        "fire_risk": 15,
        "animal_risk": 25,
        "description": "Trees provide shelter and firewood. Watch for wildlife.",
    },
    "tundra": {
        "quality_mod": -20,
        "shelter_difficulty": 25,
        "fire_risk": 0,
        "animal_risk": 10,
        "description": "Frozen ground and biting wind make camping harsh.",
    },
}

# Weather effects on camp quality
WEATHER_CAMP_MODIFIERS = {
    "clear": {"quality_mod": 10, "fire_difficulty": 0, "morale_mod": 5},
    "cloudy": {"quality_mod": 0, "fire_difficulty": 0, "morale_mod": 0},
    "rain": {"quality_mod": -20, "fire_difficulty": 30, "morale_mod": -10},
    "storm": {"quality_mod": -40, "fire_difficulty": 60, "morale_mod": -20},
    "hot": {"quality_mod": -10, "fire_difficulty": 0, "morale_mod": -5},
    "cold": {"quality_mod": -15, "fire_difficulty": 0, "morale_mod": -5},
    "snow": {"quality_mod": -25, "fire_difficulty": 20, "morale_mod": -10},
    "blizzard": {"quality_mod": -50, "fire_difficulty": 80, "morale_mod": -25},
}

# Feature bonuses
FEATURE_BONUSES = {
    CampFeature.FIRE: {
        "quality_bonus": 15,
        "healing_bonus": 10,
        "morale_bonus": 10,
        "cold_protection": 30,
        "animal_deterrent": 20,
    },
    CampFeature.SHELTER: {
        "quality_bonus": 20,
        "healing_bonus": 15,
        "weather_protection": 40,
        "morale_bonus": 5,
    },
    CampFeature.WINDBREAK: {
        "quality_bonus": 10,
        "cold_protection": 20,
        "weather_protection": 15,
    },
    CampFeature.WATCH: {
        "quality_bonus": 0,
        "animal_deterrent": 40,
        "ambush_protection": 50,
        "morale_bonus": 5,
    },
    CampFeature.PERIMETER: {
        "quality_bonus": 5,
        "animal_deterrent": 30,
        "ambush_protection": 30,
    },
    CampFeature.CACHE: {
        "quality_bonus": 5,
        "food_protection": 50,  # vs animal raids
    },
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class CampSite:
    """Represents a specific campsite with its properties."""
    terrain: str
    natural_shelter: int = 0       # 0-100, natural protection
    water_nearby: bool = False
    firewood_available: bool = True
    hazards: List[str] = field(default_factory=list)
    bonuses: Dict = field(default_factory=dict)
    
    @classmethod
    def from_location(cls, terrain: str, location_data: Dict = None) -> 'CampSite':
        """Create a campsite from location data."""
        data = location_data or {}
        
        # Generate natural shelter based on terrain
        shelter_ranges = {
            "desert": (0, 20),
            "plains": (0, 30),
            "mountains": (10, 60),  # Caves, overhangs
            "forest": (20, 70),
            "tundra": (0, 20),
        }
        min_s, max_s = shelter_ranges.get(terrain, (10, 40))
        natural_shelter = random.randint(min_s, max_s)
        
        # Firewood availability
        firewood = terrain in ["forest", "plains"]
        
        return cls(
            terrain=terrain,
            natural_shelter=natural_shelter,
            water_nearby=data.get("water_available", False),
            firewood_available=firewood,
            hazards=data.get("hazards", []),
            bonuses=data.get("camp_bonuses", {}),
        )


@dataclass
class Camp:
    """Represents an established camp."""
    camp_type: CampType
    site: CampSite
    features: List[CampFeature] = field(default_factory=list)
    quality: int = 50
    setup_time: float = 0
    
    @property
    def has_fire(self) -> bool:
        return CampFeature.FIRE in self.features
    
    @property
    def has_shelter(self) -> bool:
        return CampFeature.SHELTER in self.features
    
    @property
    def has_watch(self) -> bool:
        return CampFeature.WATCH in self.features


@dataclass
class RestResult:
    """Results of resting at a camp."""
    hours_rested: int
    health_recovered: int
    morale_change: int
    conditions_improved: List[str]
    events: List[str]
    resources_used: Dict
    quality_rating: str
    
    def to_dict(self) -> Dict:
        return {
            "hours_rested": self.hours_rested,
            "health_recovered": self.health_recovered,
            "morale_change": self.morale_change,
            "conditions_improved": self.conditions_improved,
            "events": self.events,
            "resources_used": self.resources_used,
            "quality_rating": self.quality_rating,
        }


# =============================================================================
# Camp Manager Class
# =============================================================================

class CampManager:
    """
    Manages camping and rest mechanics.
    """
    
    def __init__(self):
        """Initialize the camp manager."""
        self.current_camp: Optional[Camp] = None
        self.camp_history: List[Dict] = []
    
    # =========================================================================
    # Camp Setup
    # =========================================================================
    
    def scout_campsite(
        self, 
        terrain: str, 
        location_data: Dict = None,
        scout_skill: int = 50
    ) -> Tuple[CampSite, str]:
        """
        Scout for a good campsite.
        
        Args:
            terrain: Current terrain type
            location_data: Data from current location
            scout_skill: Party's scouting skill
        
        Returns:
            Tuple of (CampSite, description)
        """
        site = CampSite.from_location(terrain, location_data)
        
        # Skill bonus to natural shelter finding
        skill_bonus = int((scout_skill - 50) / 5)
        site.natural_shelter = min(100, max(0, site.natural_shelter + skill_bonus))
        
        # Build description
        terrain_info = TERRAIN_CAMP_MODIFIERS.get(terrain, {})
        desc = terrain_info.get("description", "A place to camp.")
        
        if site.natural_shelter > 60:
            desc += " You find an excellent sheltered spot."
        elif site.natural_shelter > 30:
            desc += " There's some natural protection here."
        else:
            desc += " The site is exposed to the elements."
        
        if site.water_nearby:
            desc += " Fresh water is nearby."
        
        if not site.firewood_available:
            desc += " Firewood will be hard to find."
        
        if site.hazards:
            desc += f" Potential hazards: {', '.join(site.hazards)}."
        
        return (site, desc)
    
    def get_camp_options(
        self, 
        site: CampSite, 
        has_tools: bool,
        party_size: int
    ) -> List[Tuple[CampType, bool, str, Dict]]:
        """
        Get available camp types for a site.
        
        Args:
            site: The campsite
            has_tools: Whether party has tools
            party_size: Number of party members
        
        Returns:
            List of (camp_type, available, reason, info) tuples
        """
        options = []
        
        for camp_type in CampType:
            available = True
            reason = ""
            
            # Check requirements
            if camp_type in [CampType.COMFORTABLE, CampType.FORTIFIED]:
                if not has_tools:
                    available = False
                    reason = "Requires tools"
            
            # Fortified needs enough people for watch
            if camp_type == CampType.FORTIFIED and party_size < 2:
                available = False
                reason = "Need 2+ people for watch rotation"
            
            info = {
                "name": camp_type.value.title(),
                "base_quality": CAMP_TYPE_BASE_QUALITY[camp_type],
                "setup_time": CAMP_SETUP_TIME[camp_type],
                "description": self._get_camp_type_description(camp_type),
            }
            
            options.append((camp_type, available, reason, info))
        
        return options
    
    def _get_camp_type_description(self, camp_type: CampType) -> str:
        """Get description for camp type."""
        descriptions = {
            CampType.MINIMAL: "A quick stop - barely a camp at all.",
            CampType.BASIC: "Simple bedrolls and a small fire if possible.",
            CampType.STANDARD: "A proper camp with fire and basic shelter.",
            CampType.COMFORTABLE: "Well-organized camp with good shelter and amenities.",
            CampType.FORTIFIED: "Defensive camp with perimeter and watch rotation.",
        }
        return descriptions.get(camp_type, "")
    
    def setup_camp(
        self,
        site: CampSite,
        camp_type: CampType,
        weather: str,
        has_tools: bool,
        party_skill: int = 50
    ) -> Tuple[Camp, List[str]]:
        """
        Set up camp at a site.
        
        Args:
            site: The campsite
            camp_type: Type of camp to set up
            weather: Current weather
            has_tools: Whether party has tools
            party_skill: Average party skill
        
        Returns:
            Tuple of (Camp, list of messages)
        """
        messages = []
        features = []
        
        # Determine which features are established
        weather_mods = WEATHER_CAMP_MODIFIERS.get(weather, {})
        fire_difficulty = weather_mods.get("fire_difficulty", 0)
        
        # Fire - attempt if firewood available
        if site.firewood_available and camp_type != CampType.MINIMAL:
            fire_success = random.randint(1, 100) > fire_difficulty
            if fire_success:
                features.append(CampFeature.FIRE)
                messages.append("A warm fire crackles to life.")
            else:
                messages.append("Unable to start a fire in these conditions.")
        
        # Shelter - based on camp type and tools
        if camp_type in [CampType.STANDARD, CampType.COMFORTABLE, CampType.FORTIFIED]:
            features.append(CampFeature.SHELTER)
            if site.natural_shelter > 50:
                messages.append("Natural shelter supplements your camp.")
        elif site.natural_shelter > 70:
            features.append(CampFeature.SHELTER)
            messages.append("Found excellent natural shelter.")
        
        # Windbreak - forests and some terrain
        if site.terrain == "forest" or site.natural_shelter > 40:
            features.append(CampFeature.WINDBREAK)
        
        # Watch - for fortified camps
        if camp_type == CampType.FORTIFIED:
            features.append(CampFeature.WATCH)
            features.append(CampFeature.PERIMETER)
            messages.append("Night watch rotation established.")
        
        # Cache - if tools and comfortable+ camp
        if has_tools and camp_type in [CampType.COMFORTABLE, CampType.FORTIFIED]:
            features.append(CampFeature.CACHE)
        
        # Calculate quality
        quality = self._calculate_camp_quality(
            camp_type, site, features, weather, party_skill
        )
        
        camp = Camp(
            camp_type=camp_type,
            site=site,
            features=features,
            quality=quality,
            setup_time=CAMP_SETUP_TIME[camp_type],
        )
        
        self.current_camp = camp
        
        # Quality message
        if quality >= 80:
            messages.append("An excellent camp - as good as it gets on the trail.")
        elif quality >= 60:
            messages.append("A comfortable camp for the night.")
        elif quality >= 40:
            messages.append("An adequate camp. It'll do.")
        elif quality >= 20:
            messages.append("A rough camp. Not much rest to be had here.")
        else:
            messages.append("Miserable conditions. This will be a long night.")
        
        return (camp, messages)
    
    def _calculate_camp_quality(
        self,
        camp_type: CampType,
        site: CampSite,
        features: List[CampFeature],
        weather: str,
        party_skill: int
    ) -> int:
        """Calculate overall camp quality."""
        # Base quality from camp type
        quality = CAMP_TYPE_BASE_QUALITY[camp_type]
        
        # Terrain modifier
        terrain_mods = TERRAIN_CAMP_MODIFIERS.get(site.terrain, {})
        quality += terrain_mods.get("quality_mod", 0)
        
        # Weather modifier
        weather_mods = WEATHER_CAMP_MODIFIERS.get(weather, {})
        quality += weather_mods.get("quality_mod", 0)
        
        # Natural shelter bonus
        quality += site.natural_shelter // 5
        
        # Feature bonuses
        for feature in features:
            bonuses = FEATURE_BONUSES.get(feature, {})
            quality += bonuses.get("quality_bonus", 0)
        
        # Skill bonus
        skill_bonus = (party_skill - 50) // 10
        quality += skill_bonus
        
        # Clamp to valid range
        return max(0, min(100, quality))
    
    # =========================================================================
    # Rest Mechanics
    # =========================================================================
    
    def rest_at_camp(
        self,
        camp: Camp,
        hours: int,
        weather: str,
        party_health: int,
        has_medic: bool = False
    ) -> RestResult:
        """
        Rest at the current camp.
        
        Args:
            camp: The established camp
            hours: Hours to rest
            weather: Current weather
            party_health: Average party health
            has_medic: Whether party has a medic
        
        Returns:
            RestResult with outcomes
        """
        events = []
        conditions_improved = []
        resources_used = {}
        
        # Base healing from rest (per hour)
        base_heal_per_hour = 1
        
        # Quality modifier (0.5x to 1.5x)
        quality_mult = 0.5 + (camp.quality / 100)
        
        # Feature bonuses
        heal_bonus = 0
        morale_bonus = 0
        
        for feature in camp.features:
            bonuses = FEATURE_BONUSES.get(feature, {})
            heal_bonus += bonuses.get("healing_bonus", 0)
            morale_bonus += bonuses.get("morale_bonus", 0)
        
        # Medic bonus
        if has_medic:
            heal_bonus += 20
        
        # Weather effects on morale
        weather_mods = WEATHER_CAMP_MODIFIERS.get(weather, {})
        morale_mod = weather_mods.get("morale_mod", 0)
        
        # Shelter protection from bad weather
        if CampFeature.SHELTER in camp.features:
            weather_protection = FEATURE_BONUSES[CampFeature.SHELTER]["weather_protection"]
            morale_mod = int(morale_mod * (1 - weather_protection / 100))
        
        # Calculate final values
        heal_rate = base_heal_per_hour * quality_mult * (1 + heal_bonus / 100)
        health_recovered = int(hours * heal_rate)
        
        morale_change = morale_bonus + morale_mod
        
        # Night events check (lower quality = more risk)
        event_chance = (100 - camp.quality) / 200  # 0-50% chance
        
        # Watch reduces event impact
        if CampFeature.WATCH in camp.features:
            event_chance *= 0.5
        
        if random.random() < event_chance:
            event = self._generate_camp_event(camp, weather)
            events.append(event["message"])
            health_recovered -= event.get("health_damage", 0)
            morale_change += event.get("morale_change", 0)
            resources_used.update(event.get("resources_lost", {}))
        
        # Chance to improve conditions based on rest quality
        if camp.quality >= 60:
            condition_improve_chance = 0.3
        elif camp.quality >= 40:
            condition_improve_chance = 0.15
        else:
            condition_improve_chance = 0.05
        
        if random.random() < condition_improve_chance:
            possible_conditions = ["exhausted", "minor injury"]
            improved = random.choice(possible_conditions)
            conditions_improved.append(improved)
        
        # Quality rating
        if camp.quality >= 80:
            quality_rating = "Excellent"
        elif camp.quality >= 60:
            quality_rating = "Good"
        elif camp.quality >= 40:
            quality_rating = "Fair"
        elif camp.quality >= 20:
            quality_rating = "Poor"
        else:
            quality_rating = "Terrible"
        
        result = RestResult(
            hours_rested=hours,
            health_recovered=max(0, health_recovered),
            morale_change=morale_change,
            conditions_improved=conditions_improved,
            events=events,
            resources_used=resources_used,
            quality_rating=quality_rating,
        )
        
        # Record in history
        self.camp_history.append({
            "camp_type": camp.camp_type.value,
            "quality": camp.quality,
            "terrain": camp.site.terrain,
            **result.to_dict()
        })
        
        return result
    
    def _generate_camp_event(self, camp: Camp, weather: str) -> Dict:
        """Generate a random camp event (usually negative)."""
        # Possible events based on camp features and terrain
        events = []
        
        # Animal raid - more likely without fire/cache
        if CampFeature.FIRE not in camp.features or CampFeature.CACHE not in camp.features:
            events.append({
                "type": "animal_raid",
                "message": "Animals got into the supplies during the night!",
                "resources_lost": {"food": random.randint(5, 15)},
                "morale_change": -5,
            })
        
        # Theft/ambush - more likely without watch
        if CampFeature.WATCH not in camp.features:
            events.append({
                "type": "disturbance",
                "message": "Strange noises kept the party awake.",
                "health_damage": 5,
                "morale_change": -8,
            })
        
        # Weather damage
        if weather in ["storm", "blizzard"] and CampFeature.SHELTER not in camp.features:
            events.append({
                "type": "weather_damage",
                "message": f"The {weather} damaged supplies!",
                "resources_lost": {"clothing": 1},
                "health_damage": 10,
                "morale_change": -10,
            })
        
        # Cold exposure
        if weather in ["cold", "snow", "blizzard"] and CampFeature.FIRE not in camp.features:
            events.append({
                "type": "cold_exposure",
                "message": "The bitter cold made for a miserable night.",
                "health_damage": 15,
                "morale_change": -15,
            })
        
        # Fire spread (rare, mostly in dry conditions)
        if CampFeature.FIRE in camp.features and camp.site.terrain in ["plains", "forest"]:
            if random.random() < 0.1:
                events.append({
                    "type": "fire_spread",
                    "message": "The campfire got out of control briefly!",
                    "resources_lost": {"food": random.randint(5, 10)},
                    "morale_change": -5,
                })
        
        if events:
            return random.choice(events)
        
        # Fallback minor event
        return {
            "type": "minor",
            "message": "Restless sleep due to uncomfortable conditions.",
            "morale_change": -3,
        }
    
    # =========================================================================
    # Quick Rest (No Camp Setup)
    # =========================================================================
    
    def quick_rest(
        self,
        terrain: str,
        weather: str,
        hours: int = 2
    ) -> RestResult:
        """
        Quick rest without setting up a proper camp.
        
        Args:
            terrain: Current terrain
            weather: Current weather
            hours: Hours to rest
        
        Returns:
            RestResult with minimal recovery
        """
        # Create minimal camp
        site = CampSite.from_location(terrain)
        camp = Camp(
            camp_type=CampType.MINIMAL,
            site=site,
            features=[],
            quality=15,
            setup_time=0,
        )
        
        return self.rest_at_camp(camp, hours, weather, 50, False)
    
    # =========================================================================
    # Statistics and Serialization
    # =========================================================================
    
    def get_statistics(self) -> Dict:
        """Get camping statistics."""
        if not self.camp_history:
            return {
                "total_camps": 0,
                "avg_quality": 0,
                "total_health_recovered": 0,
                "events_encountered": 0,
            }
        
        return {
            "total_camps": len(self.camp_history),
            "avg_quality": sum(c["quality"] for c in self.camp_history) / len(self.camp_history),
            "total_health_recovered": sum(c["health_recovered"] for c in self.camp_history),
            "events_encountered": sum(1 for c in self.camp_history if c["events"]),
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for saving."""
        return {
            "camp_history": self.camp_history,
        }
    
    def load_state(self, data: Dict):
        """Load state from dictionary."""
        self.camp_history = data.get("camp_history", [])


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate camp system functionality."""
    print("=" * 50)
    print("CAMP SYSTEM DEMO")
    print("=" * 50)
    print()
    
    cm = CampManager()
    
    # Scout a campsite
    print("Scouting campsite in forest terrain...")
    site, desc = cm.scout_campsite("forest", {"water_available": True}, scout_skill=60)
    print(f"  {desc}")
    print(f"  Natural shelter: {site.natural_shelter}%")
    print(f"  Water nearby: {site.water_nearby}")
    print(f"  Firewood: {site.firewood_available}")
    print()
    
    # Get camp options
    print("Available camp types:")
    options = cm.get_camp_options(site, has_tools=True, party_size=4)
    for camp_type, available, reason, info in options:
        status = "✓" if available else f"✗ ({reason})"
        print(f"  {info['name']}: Quality {info['base_quality']}, "
              f"Setup {info['setup_time']}h {status}")
        print(f"    {info['description']}")
    print()
    
    # Set up different camps and compare
    print("Testing camp quality in different conditions:")
    print("-" * 50)
    
    for camp_type in [CampType.BASIC, CampType.STANDARD, CampType.COMFORTABLE]:
        for weather in ["clear", "rain", "blizzard"]:
            camp, messages = cm.setup_camp(
                site=site,
                camp_type=camp_type,
                weather=weather,
                has_tools=True,
                party_skill=50
            )
            print(f"  {camp_type.value.title():12} + {weather:8}: Quality {camp.quality:3} | "
                  f"Features: {[f.value for f in camp.features]}")
    print()
    
    # Test resting
    print("Testing rest at a standard camp (clear weather):")
    camp, messages = cm.setup_camp(site, CampType.STANDARD, "clear", True, 60)
    for msg in messages:
        print(f"  {msg}")
    print()
    
    # Rest for 8 hours
    result = cm.rest_at_camp(camp, hours=8, weather="clear", party_health=70, has_medic=True)
    print(f"  Hours rested: {result.hours_rested}")
    print(f"  Health recovered: {result.health_recovered}")
    print(f"  Morale change: {result.morale_change:+d}")
    print(f"  Quality rating: {result.quality_rating}")
    if result.events:
        print(f"  Events: {result.events}")
    if result.conditions_improved:
        print(f"  Conditions improved: {result.conditions_improved}")
    print()
    
    # Test quick rest
    print("Testing quick rest (no camp setup):")
    quick_result = cm.quick_rest("mountains", "cold", 4)
    print(f"  Health recovered: {quick_result.health_recovered}")
    print(f"  Morale change: {quick_result.morale_change:+d}")
    print(f"  Quality rating: {quick_result.quality_rating}")
    print()
    
    # Statistics
    print("Camping statistics:")
    stats = cm.get_statistics()
    print(f"  Total camps: {stats['total_camps']}")
    print(f"  Avg quality: {stats['avg_quality']:.1f}")
    print(f"  Total health recovered: {stats['total_health_recovered']}")
    print()
    
    print("Demo complete!")


if __name__ == "__main__":
    demo()