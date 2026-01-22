"""
route_system.py - Route Choices and Hidden Locations for The Great Divide Trail

Handles:
- Multiple route options at decision points
- Hidden/discoverable locations via scouting
- Shortcuts and alternate paths
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# Enums and Constants
# =============================================================================

class RouteType(Enum):
    """Types of routes available."""
    MAIN = "main"           # Standard route
    SHORTCUT = "shortcut"   # Faster but more dangerous
    SAFE = "safe"           # Longer but safer
    SCENIC = "scenic"       # Special encounters/discoveries
    HIDDEN = "hidden"       # Only discoverable via scouting


class HiddenLocationType(Enum):
    """Types of hidden locations."""
    CACHE = "cache"             # Supply cache
    CABIN = "cabin"             # Abandoned cabin (rest bonus)
    SHORTCUT = "shortcut"       # Secret path
    SPRING = "spring"           # Fresh water source
    HUNTING_GROUND = "hunting"  # Excellent hunting
    SHELTER = "shelter"         # Natural shelter
    GRAVE = "grave"             # Previous traveler's grave (supplies/warning)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class RouteOption:
    """Represents a possible route choice."""
    id: str
    name: str
    route_type: RouteType
    description: str
    distance: int                    # Miles for this route
    base_distance: int              # Miles for main route (for comparison)
    danger_level: int               # 0-100 danger rating
    terrain: str                    # Terrain type for this route
    requirements: Dict = field(default_factory=dict)  # Skill/resource requirements
    hazards: List[str] = field(default_factory=list)
    rewards: Dict = field(default_factory=dict)       # Potential rewards
    discovery_chance: float = 1.0   # Chance to discover (for hidden routes)
    
    @property
    def distance_difference(self) -> int:
        """Miles saved (positive) or added (negative) vs main route."""
        return self.base_distance - self.distance
    
    @property
    def is_shortcut(self) -> bool:
        """Check if this route saves distance."""
        return self.distance < self.base_distance
    
    def check_requirements(self, context: Dict) -> Tuple[bool, str]:
        """
        Check if requirements are met for this route.
        
        Args:
            context: Dict with 'skills', 'resources', 'party_size', etc.
        
        Returns:
            Tuple of (requirements_met, reason_if_not)
        """
        if not self.requirements:
            return (True, "")
        
        # Check skill requirements
        if "skill" in self.requirements:
            skill_name = self.requirements["skill"]
            min_value = self.requirements.get("min_value", 0)
            actual_value = context.get("skills", {}).get(skill_name, 0)
            
            if actual_value < min_value:
                return (False, f"Requires {skill_name} skill of {min_value}+")
        
        # Check resource requirements
        if "resource" in self.requirements:
            resource_name = self.requirements["resource"]
            min_value = self.requirements.get("min_amount", 0)
            actual_value = context.get("resources", {}).get(resource_name, 0)
            
            if actual_value < min_value:
                return (False, f"Requires {min_value}+ {resource_name}")
        
        # Check party health
        if "min_health" in self.requirements:
            min_health = self.requirements["min_health"]
            avg_health = context.get("avg_health", 100)
            
            if avg_health < min_health:
                return (False, f"Party too weak (need {min_health}+ avg health)")
        
        # Check weather
        if "weather_exclude" in self.requirements:
            current_weather = context.get("weather", "clear")
            if current_weather in self.requirements["weather_exclude"]:
                return (False, f"Route impassable in {current_weather} weather")
        
        return (True, "")
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RouteOption':
        """Create RouteOption from dictionary."""
        route_type = RouteType(data.get("route_type", "main"))
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown Route"),
            route_type=route_type,
            description=data.get("description", ""),
            distance=data.get("distance", 0),
            base_distance=data.get("base_distance", 0),
            danger_level=data.get("danger_level", 50),
            terrain=data.get("terrain", "plains"),
            requirements=data.get("requirements", {}),
            hazards=data.get("hazards", []),
            rewards=data.get("rewards", {}),
            discovery_chance=data.get("discovery_chance", 1.0),
        )


@dataclass
class HiddenLocation:
    """Represents a discoverable hidden location."""
    id: str
    name: str
    location_type: HiddenLocationType
    description: str
    mile_marker: int                 # Where it can be discovered
    discovery_range: int             # Miles from marker it can be found
    discovery_difficulty: int        # 0-100, higher = harder to find
    discovered: bool = False
    looted: bool = False             # For caches
    
    # Effects when discovered/used
    supplies: Dict = field(default_factory=dict)
    rest_bonus: int = 0              # Bonus healing when resting here
    morale_bonus: int = 0
    hunting_bonus: int = 0
    water_available: bool = False
    shelter_quality: int = 0         # 0-100
    
    # Story/flavor
    story_text: str = ""
    warning_text: str = ""           # For graves/danger signs
    
    def can_discover(self, current_mile: int, scout_skill: int) -> Tuple[bool, float]:
        """
        Check if this location can be discovered.
        
        Args:
            current_mile: Current position on trail
            scout_skill: Effective scouting skill (0-100)
        
        Returns:
            Tuple of (in_range, discovery_chance)
        """
        if self.discovered:
            return (True, 1.0)
        
        # Check if in range
        distance = abs(current_mile - self.mile_marker)
        if distance > self.discovery_range:
            return (False, 0.0)
        
        # Calculate discovery chance
        # Base chance modified by skill and difficulty
        base_chance = 0.3 + (scout_skill / 200)  # 30-80% base
        difficulty_mod = 1 - (self.discovery_difficulty / 200)  # 50-100%
        range_mod = 1 - (distance / self.discovery_range * 0.5)  # Closer = easier
        
        final_chance = base_chance * difficulty_mod * range_mod
        return (True, max(0.1, min(0.95, final_chance)))
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'HiddenLocation':
        """Create HiddenLocation from dictionary."""
        loc_type = HiddenLocationType(data.get("location_type", "cache"))
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown Location"),
            location_type=loc_type,
            description=data.get("description", ""),
            mile_marker=data.get("mile_marker", 0),
            discovery_range=data.get("discovery_range", 20),
            discovery_difficulty=data.get("discovery_difficulty", 50),
            discovered=data.get("discovered", False),
            looted=data.get("looted", False),
            supplies=data.get("supplies", {}),
            rest_bonus=data.get("rest_bonus", 0),
            morale_bonus=data.get("morale_bonus", 0),
            hunting_bonus=data.get("hunting_bonus", 0),
            water_available=data.get("water_available", False),
            shelter_quality=data.get("shelter_quality", 0),
            story_text=data.get("story_text", ""),
            warning_text=data.get("warning_text", ""),
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for saving."""
        return {
            "id": self.id,
            "name": self.name,
            "location_type": self.location_type.value,
            "description": self.description,
            "mile_marker": self.mile_marker,
            "discovery_range": self.discovery_range,
            "discovery_difficulty": self.discovery_difficulty,
            "discovered": self.discovered,
            "looted": self.looted,
            "supplies": self.supplies,
            "rest_bonus": self.rest_bonus,
            "morale_bonus": self.morale_bonus,
            "hunting_bonus": self.hunting_bonus,
            "water_available": self.water_available,
            "shelter_quality": self.shelter_quality,
            "story_text": self.story_text,
            "warning_text": self.warning_text,
        }


@dataclass
class RouteDecisionPoint:
    """A point where players must choose between routes."""
    id: str
    name: str
    mile_marker: int
    description: str
    routes: List[RouteOption] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RouteDecisionPoint':
        """Create from dictionary."""
        routes = [RouteOption.from_dict(r) for r in data.get("routes", [])]
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown Junction"),
            mile_marker=data.get("mile_marker", 0),
            description=data.get("description", ""),
            routes=routes,
        )


# =============================================================================
# Route Manager Class
# =============================================================================

class RouteManager:
    """
    Manages route choices and hidden location discovery.
    """
    
    def __init__(self):
        """Initialize the route manager."""
        self.decision_points: List[RouteDecisionPoint] = []
        self.hidden_locations: List[HiddenLocation] = []
        self.current_route: Optional[RouteOption] = None
        self.route_history: List[Dict] = []
        self.discoveries: List[str] = []  # IDs of discovered locations
        
        # Load default data
        self._load_default_data()
    
    def _load_default_data(self):
        """Load default route decision points and hidden locations."""
        # Route decision points
        self.decision_points = [
            RouteDecisionPoint.from_dict({
                "id": "gore_pass_junction",
                "name": "Gore Pass Junction",
                "mile_marker": 400,
                "description": "The trail splits here. Gore Pass offers a direct but treacherous mountain crossing. The river valley route is longer but safer.",
                "routes": [
                    {
                        "id": "gore_pass_direct",
                        "name": "Gore Pass (Direct)",
                        "route_type": "shortcut",
                        "description": "A steep mountain pass at 9,500 feet. Saves time but risks avalanches and altitude sickness.",
                        "distance": 50,
                        "base_distance": 80,
                        "danger_level": 70,
                        "terrain": "mountains",
                        "hazards": ["avalanche", "altitude", "injury"],
                        "requirements": {"min_health": 50},
                        "rewards": {"morale": 10},
                    },
                    {
                        "id": "river_valley_route",
                        "name": "River Valley Route",
                        "route_type": "safe",
                        "description": "Follow the river valley around the mountains. Longer but with good water and hunting.",
                        "distance": 80,
                        "base_distance": 80,
                        "danger_level": 30,
                        "terrain": "forest",
                        "hazards": ["river_crossing"],
                        "rewards": {"hunting_bonus": 15, "water": True},
                    },
                ]
            }),
            RouteDecisionPoint.from_dict({
                "id": "wind_river_crossing",
                "name": "Wind River Crossing",
                "mile_marker": 830,
                "description": "The Wind River blocks your path. You must choose how to proceed.",
                "routes": [
                    {
                        "id": "wind_river_ford",
                        "name": "Ford at Shallow Point",
                        "route_type": "main",
                        "description": "A known fording point. Risky when water is high.",
                        "distance": 20,
                        "base_distance": 20,
                        "danger_level": 50,
                        "terrain": "plains",
                        "hazards": ["river_crossing"],
                    },
                    {
                        "id": "wind_river_north",
                        "name": "Northern Bridge Route",
                        "route_type": "safe",
                        "description": "A longer route to a makeshift bridge. Safer but adds distance.",
                        "distance": 45,
                        "base_distance": 20,
                        "danger_level": 20,
                        "terrain": "plains",
                        "rewards": {},
                    },
                    {
                        "id": "wind_river_canyon",
                        "name": "Canyon Shortcut",
                        "route_type": "hidden",
                        "description": "A treacherous canyon path known only to experienced scouts.",
                        "distance": 15,
                        "base_distance": 20,
                        "danger_level": 80,
                        "terrain": "mountains",
                        "hazards": ["injury", "rockslide"],
                        "requirements": {"skill": "scouting", "min_value": 40},
                        "discovery_chance": 0.4,
                    },
                ]
            }),
            RouteDecisionPoint.from_dict({
                "id": "marias_pass_choice",
                "name": "Marias Pass Approach",
                "mile_marker": 1320,
                "description": "Marias Pass lies ahead, but there are different approaches through Blackfoot territory.",
                "routes": [
                    {
                        "id": "marias_direct",
                        "name": "Direct Through Pass",
                        "route_type": "main",
                        "description": "The most direct route, but exposed to potential encounters.",
                        "distance": 60,
                        "base_distance": 60,
                        "danger_level": 60,
                        "terrain": "mountains",
                        "hazards": ["ambush", "wildlife", "avalanche"],
                    },
                    {
                        "id": "marias_south",
                        "name": "Southern Forest Route",
                        "route_type": "safe",
                        "description": "Skirt the mountains through dense forest. More cover, less exposure.",
                        "distance": 90,
                        "base_distance": 60,
                        "danger_level": 35,
                        "terrain": "forest",
                        "hazards": ["wildlife"],
                        "rewards": {"hunting_bonus": 20},
                    },
                    {
                        "id": "marias_ridge",
                        "name": "High Ridge Trail",
                        "route_type": "shortcut",
                        "description": "A grueling climb along the ridgeline. Shorter but exhausting.",
                        "distance": 45,
                        "base_distance": 60,
                        "danger_level": 75,
                        "terrain": "mountains",
                        "hazards": ["altitude", "injury", "cold"],
                        "requirements": {"min_health": 60},
                    },
                ]
            }),
            RouteDecisionPoint.from_dict({
                "id": "chilkoot_approach",
                "name": "Chilkoot Pass Approach",
                "mile_marker": 2480,
                "description": "The final mountain barrier. The Chilkoot awaits, but Tlingit guides speak of alternatives.",
                "routes": [
                    {
                        "id": "chilkoot_main",
                        "name": "Chilkoot Pass",
                        "route_type": "main",
                        "description": "The traditional route over the pass. Well-traveled but steep.",
                        "distance": 40,
                        "base_distance": 40,
                        "danger_level": 55,
                        "terrain": "mountains",
                        "hazards": ["avalanche", "cold", "altitude"],
                    },
                    {
                        "id": "chilkoot_white",
                        "name": "White Pass Route",
                        "route_type": "safe",
                        "description": "A lower, longer route. Less steep but more exposed to weather.",
                        "distance": 65,
                        "base_distance": 40,
                        "danger_level": 40,
                        "terrain": "mountains",
                        "hazards": ["cold"],
                        "requirements": {"weather_exclude": ["blizzard"]},
                    },
                    {
                        "id": "chilkoot_tlingit",
                        "name": "Tlingit Secret Path",
                        "route_type": "hidden",
                        "description": "An ancient path known to the Tlingit. Must befriend local guides.",
                        "distance": 35,
                        "base_distance": 40,
                        "danger_level": 30,
                        "terrain": "forest",
                        "requirements": {"resource": "money", "min_amount": 50},
                        "rewards": {"morale": 20},
                        "discovery_chance": 0.3,
                    },
                ]
            }),
        ]
        
        # Hidden locations
        self.hidden_locations = [
            HiddenLocation.from_dict({
                "id": "trapper_cache_1",
                "name": "Old Trapper's Cache",
                "location_type": "cache",
                "description": "A weathered cache box hidden beneath a distinctive rock formation.",
                "mile_marker": 250,
                "discovery_range": 30,
                "discovery_difficulty": 40,
                "supplies": {"food": 30, "ammunition": 15, "medical": 2},
                "story_text": "The cache bears the mark 'J.B. 1835'. Whoever left this never returned for it.",
            }),
            HiddenLocation.from_dict({
                "id": "abandoned_cabin_1",
                "name": "Abandoned Homestead",
                "location_type": "cabin",
                "description": "A small cabin, half-collapsed but still offering shelter.",
                "mile_marker": 450,
                "discovery_range": 25,
                "discovery_difficulty": 30,
                "rest_bonus": 25,
                "morale_bonus": 10,
                "shelter_quality": 60,
                "supplies": {"food": 10, "tools": 1},
                "story_text": "The cabin's former occupants left in haste. A journal speaks of harsh winters and dwindling supplies.",
            }),
            HiddenLocation.from_dict({
                "id": "hidden_spring_1",
                "name": "Crystal Spring",
                "location_type": "spring",
                "description": "A pristine spring bubbling from the rocks, surrounded by lush vegetation.",
                "mile_marker": 620,
                "discovery_range": 15,
                "discovery_difficulty": 50,
                "water_available": True,
                "rest_bonus": 15,
                "morale_bonus": 15,
                "story_text": "The water is ice-cold and refreshing. Native symbols carved nearby suggest this is a sacred place.",
            }),
            HiddenLocation.from_dict({
                "id": "hunting_valley",
                "name": "Hidden Valley",
                "location_type": "hunting",
                "description": "A sheltered valley teeming with game, hidden from the main trail.",
                "mile_marker": 900,
                "discovery_range": 20,
                "discovery_difficulty": 55,
                "hunting_bonus": 40,
                "water_available": True,
                "morale_bonus": 10,
                "story_text": "Deer and elk graze peacefully. This valley has been untouched by hunters for years.",
            }),
            HiddenLocation.from_dict({
                "id": "traveler_grave",
                "name": "Pioneer's Grave",
                "location_type": "grave",
                "description": "A wooden cross marks a lonely grave beside the trail.",
                "mile_marker": 1100,
                "discovery_range": 10,
                "discovery_difficulty": 20,
                "supplies": {"ammunition": 8, "clothing": 1},
                "morale_bonus": -5,
                "story_text": "The marker reads: 'Thomas Whitfield, died of fever, June 1838. May he find peace.'",
                "warning_text": "A note tucked in the rocks warns of bad water at the river bend ahead.",
            }),
            HiddenLocation.from_dict({
                "id": "rock_shelter",
                "name": "Ancient Rock Shelter",
                "location_type": "shelter",
                "description": "A natural overhang that has sheltered travelers for centuries.",
                "mile_marker": 1550,
                "discovery_range": 20,
                "discovery_difficulty": 45,
                "rest_bonus": 20,
                "shelter_quality": 75,
                "story_text": "Charcoal drawings on the walls depict hunts from long ago. The shelter is dry and windproof.",
            }),
            HiddenLocation.from_dict({
                "id": "miner_cache",
                "name": "Miner's Hidden Cache",
                "location_type": "cache",
                "description": "A carefully concealed stash, marked only by three stacked stones.",
                "mile_marker": 1250,
                "discovery_range": 15,
                "discovery_difficulty": 65,
                "supplies": {"money": 40, "tools": 1, "medical": 3},
                "story_text": "Gold dust and supplies hidden by a prospector. A map shows their intended route - they headed into the mountains and never emerged.",
            }),
            HiddenLocation.from_dict({
                "id": "hot_springs",
                "name": "Hidden Hot Springs",
                "location_type": "spring",
                "description": "Natural hot springs in a secluded grotto.",
                "mile_marker": 1800,
                "discovery_range": 25,
                "discovery_difficulty": 50,
                "water_available": True,
                "rest_bonus": 35,
                "morale_bonus": 25,
                "shelter_quality": 40,
                "story_text": "The warm mineral water soothes aching muscles. Steam rises into the cold air.",
            }),
            HiddenLocation.from_dict({
                "id": "native_shortcut",
                "name": "Ancient Trail Marker",
                "location_type": "shortcut",
                "description": "Weathered stone cairns mark an old native trail through the wilderness.",
                "mile_marker": 2100,
                "discovery_range": 30,
                "discovery_difficulty": 60,
                "story_text": "Following the cairns reveals a path that cuts through seemingly impassable terrain.",
            }),
            HiddenLocation.from_dict({
                "id": "abandoned_camp_supplies",
                "name": "Abandoned Expedition Camp",
                "location_type": "cache",
                "description": "The remnants of a previous expedition, hastily abandoned.",
                "mile_marker": 2350,
                "discovery_range": 20,
                "discovery_difficulty": 35,
                "supplies": {"food": 45, "ammunition": 20, "clothing": 2, "medical": 4},
                "shelter_quality": 30,
                "story_text": "Frozen tents and scattered supplies tell of a harsh winter. You find useful items among the wreckage.",
                "warning_text": "Signs suggest the party was attacked - by what, you cannot tell.",
            }),
        ]
    
    # =========================================================================
    # Route Decision Methods
    # =========================================================================
    
    def get_decision_point(self, mile_marker: int, tolerance: int = 10) -> Optional[RouteDecisionPoint]:
        """
        Check if there's a route decision point at the current location.
        
        Args:
            mile_marker: Current position on trail
            tolerance: How close to the decision point to trigger
        
        Returns:
            RouteDecisionPoint if found, None otherwise
        """
        for point in self.decision_points:
            if abs(point.mile_marker - mile_marker) <= tolerance:
                return point
        return None
    
    def get_available_routes(
        self, 
        decision_point: RouteDecisionPoint, 
        context: Dict,
        scout_skill: int = 50
    ) -> List[Tuple[RouteOption, bool, str]]:
        """
        Get available routes at a decision point.
        
        Args:
            decision_point: The decision point
            context: Game context for requirement checking
            scout_skill: Party's scouting skill
        
        Returns:
            List of (route, is_available, reason) tuples
        """
        available = []
        
        for route in decision_point.routes:
            # Hidden routes need to be discovered
            if route.route_type == RouteType.HIDDEN:
                # Check if already discovered
                if f"route_{route.id}" not in self.discoveries:
                    # Roll for discovery based on scout skill
                    discovery_roll = random.random()
                    discovery_threshold = route.discovery_chance * (scout_skill / 100 + 0.5)
                    
                    if discovery_roll > discovery_threshold:
                        continue  # Route not discovered
                    else:
                        self.discoveries.append(f"route_{route.id}")
            
            # Check requirements
            meets_req, reason = route.check_requirements(context)
            available.append((route, meets_req, reason))
        
        return available
    
    def select_route(self, route: RouteOption) -> Dict:
        """
        Select a route and record the choice.
        
        Args:
            route: The chosen route
        
        Returns:
            Dict with route details for travel
        """
        self.current_route = route
        self.route_history.append({
            "route_id": route.id,
            "route_name": route.name,
            "distance": route.distance,
            "terrain": route.terrain,
        })
        
        return {
            "distance": route.distance,
            "terrain": route.terrain,
            "hazards": route.hazards,
            "danger_level": route.danger_level,
            "rewards": route.rewards,
        }
    
    # =========================================================================
    # Hidden Location Methods
    # =========================================================================
    
    def scout_for_hidden(
        self, 
        current_mile: int, 
        scout_skill: int,
        scout_range: int = 30
    ) -> List[HiddenLocation]:
        """
        Scout for hidden locations near current position.
        
        Args:
            current_mile: Current position on trail
            scout_skill: Effective scouting skill
            scout_range: How far ahead to scout
        
        Returns:
            List of newly discovered locations
        """
        discovered = []
        
        for location in self.hidden_locations:
            # Skip already discovered
            if location.discovered:
                continue
            
            # Check if in scouting range
            in_range, chance = location.can_discover(current_mile, scout_skill)
            
            if in_range and random.random() < chance:
                location.discovered = True
                self.discoveries.append(location.id)
                discovered.append(location)
        
        return discovered
    
    def get_discovered_locations(self, current_mile: int, range_miles: int = 50) -> List[HiddenLocation]:
        """
        Get all discovered hidden locations within range.
        
        Args:
            current_mile: Current position
            range_miles: How far ahead to look
        
        Returns:
            List of discovered locations within range
        """
        nearby = []
        
        for location in self.hidden_locations:
            if not location.discovered:
                continue
            
            distance = location.mile_marker - current_mile
            if 0 <= distance <= range_miles:
                nearby.append(location)
        
        return sorted(nearby, key=lambda x: x.mile_marker)
    
    def visit_hidden_location(self, location: HiddenLocation) -> Dict:
        """
        Visit a hidden location and collect rewards.
        
        Args:
            location: The location to visit
        
        Returns:
            Dict with visit results
        """
        results = {
            "location": location.name,
            "type": location.location_type.value,
            "supplies_found": {},
            "rest_bonus": location.rest_bonus,
            "hunting_bonus": location.hunting_bonus,
            "morale_bonus": location.morale_bonus,
            "water_available": location.water_available,
            "shelter_quality": location.shelter_quality,
            "story": location.story_text,
            "warning": location.warning_text,
            "already_looted": False,
        }
        
        # Check if supplies already taken
        if location.location_type == HiddenLocationType.CACHE:
            if location.looted:
                results["already_looted"] = True
            else:
                results["supplies_found"] = location.supplies
                location.looted = True
        else:
            # Non-cache locations always provide their bonuses
            results["supplies_found"] = location.supplies
        
        return results
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """Convert state to dictionary for saving."""
        return {
            "discoveries": self.discoveries,
            "route_history": self.route_history,
            "current_route": self.current_route.id if self.current_route else None,
            "hidden_locations": [loc.to_dict() for loc in self.hidden_locations],
        }
    
    def load_state(self, data: Dict):
        """Load state from dictionary."""
        self.discoveries = data.get("discoveries", [])
        self.route_history = data.get("route_history", [])
        
        # Restore hidden location states
        saved_locations = {loc["id"]: loc for loc in data.get("hidden_locations", [])}
        for location in self.hidden_locations:
            if location.id in saved_locations:
                saved = saved_locations[location.id]
                location.discovered = saved.get("discovered", False)
                location.looted = saved.get("looted", False)


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate route system functionality."""
    print("=" * 50)
    print("ROUTE SYSTEM DEMO")
    print("=" * 50)
    print()
    
    rm = RouteManager()
    
    # Show decision points
    print(f"Loaded {len(rm.decision_points)} route decision points:")
    for point in rm.decision_points:
        print(f"  Mile {point.mile_marker}: {point.name} ({len(point.routes)} routes)")
    print()
    
    # Show hidden locations
    print(f"Loaded {len(rm.hidden_locations)} hidden locations:")
    for loc in rm.hidden_locations:
        print(f"  Mile {loc.mile_marker}: {loc.name} ({loc.location_type.value})")
    print()
    
    # Test route decision
    print("Testing route decision at Gore Pass (mile 400)...")
    decision = rm.get_decision_point(405)
    if decision:
        print(f"  Found: {decision.name}")
        print(f"  {decision.description}")
        print()
        
        # Mock context
        context = {
            "skills": {"scouting": 50},
            "resources": {"money": 100},
            "avg_health": 70,
            "weather": "clear",
        }
        
        routes = rm.get_available_routes(decision, context, scout_skill=60)
        print("  Available routes:")
        for route, available, reason in routes:
            status = "✓" if available else f"✗ ({reason})"
            distance_diff = route.distance_difference
            diff_str = f"({distance_diff:+d} miles)" if distance_diff != 0 else ""
            print(f"    {route.name}: {route.distance} miles {diff_str} - Danger: {route.danger_level}% {status}")
    print()
    
    # Test scouting for hidden locations
    print("Testing scout for hidden locations at mile 450...")
    discovered = rm.scout_for_hidden(450, scout_skill=70)
    print(f"  Discovered {len(discovered)} new locations")
    for loc in discovered:
        print(f"    - {loc.name}: {loc.description[:50]}...")
    print()
    
    # Test visiting a location
    if discovered:
        print(f"Visiting {discovered[0].name}...")
        result = rm.visit_hidden_location(discovered[0])
        print(f"  Story: {result['story'][:60]}...")
        if result['supplies_found']:
            print(f"  Supplies found: {result['supplies_found']}")
        if result['rest_bonus']:
            print(f"  Rest bonus: +{result['rest_bonus']}%")
    print()
    
    # Test serialization
    print("Testing serialization...")
    data = rm.to_dict()
    print(f"  Saved {len(data['discoveries'])} discoveries")
    
    rm2 = RouteManager()
    rm2.load_state(data)
    print(f"  Restored {len(rm2.discoveries)} discoveries")
    print()
    
    print("Demo complete!")


if __name__ == "__main__":
    demo()