"""
travel.py - Travel System and Navigation for The Great Divide Trail

Handles all travel mechanics including movement, location tracking,
terrain effects, weather, and route navigation.

ENHANCEMENTS v2:
- Route choices at decision points
- Hidden location discovery via scouting
- River crossing integration
- Camp quality system integration
"""

import json
import random
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

# Import new systems (with fallback for standalone testing)
try:
    from route_system import RouteManager, RouteDecisionPoint, HiddenLocation, RouteOption
    from river_crossing import RiverCrossingManager, RiverCrossingPoint, RiverCondition, CrossingMethod
    from camp_system import CampManager, CampSite, CampType
    ENHANCED_SYSTEMS_AVAILABLE = True
except ImportError:
    ENHANCED_SYSTEMS_AVAILABLE = False
    print("Note: Enhanced travel systems not available")


# =============================================================================
# Constants
# =============================================================================

class Season(Enum):
    """Seasons affecting weather and travel."""
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"


class Weather(Enum):
    """Weather conditions."""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    HOT = "hot"
    COLD = "cold"
    SNOW = "snow"
    BLIZZARD = "blizzard"


# Weather effects on travel and party
WEATHER_EFFECTS = {
    Weather.CLEAR: {
        "speed_modifier": 0,
        "morale_modifier": 0,
        "health_risk": 0,
        "description": "Clear skies"
    },
    Weather.CLOUDY: {
        "speed_modifier": 0,
        "morale_modifier": 0,
        "health_risk": 0,
        "description": "Overcast skies"
    },
    Weather.RAIN: {
        "speed_modifier": -15,
        "morale_modifier": -5,
        "health_risk": 5,
        "description": "Steady rain"
    },
    Weather.STORM: {
        "speed_modifier": -30,
        "morale_modifier": -10,
        "health_risk": 15,
        "description": "Heavy storm"
    },
    Weather.HOT: {
        "speed_modifier": -10,
        "morale_modifier": -5,
        "health_risk": 10,
        "description": "Scorching heat"
    },
    Weather.COLD: {
        "speed_modifier": -10,
        "morale_modifier": -5,
        "health_risk": 10,
        "description": "Bitter cold"
    },
    Weather.SNOW: {
        "speed_modifier": -25,
        "morale_modifier": -5,
        "health_risk": 15,
        "description": "Snowfall"
    },
    Weather.BLIZZARD: {
        "speed_modifier": -50,
        "morale_modifier": -15,
        "health_risk": 30,
        "description": "Deadly blizzard"
    },
}

# Starting date
START_YEAR = 1840
START_MONTH = 4  # April
START_DAY = 1


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Location:
    """Represents a location on the trail."""
    id: str
    name: str
    region: str
    mile_marker: int
    terrain: str
    description: str
    is_landmark: bool = False
    is_settlement: bool = False
    is_destination: bool = False
    services: List[str] = field(default_factory=list)
    trade_goods: List[str] = field(default_factory=list)
    base_prices: Dict[str, float] = field(default_factory=dict)
    hazards: List[str] = field(default_factory=list)
    hunting_bonus: int = 0
    healing_bonus: int = 0
    travel_bonus: int = 0
    water_available: bool = False
    elevation: int = 0
    milestone: str = ""
    special_event: str = ""
    
    # NEW: Route and crossing flags
    has_route_choice: bool = False
    has_river_crossing: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Location':
        """Create Location from dictionary."""
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown"),
            region=data.get("region", ""),
            mile_marker=data.get("mile_marker", 0),
            terrain=data.get("terrain", "plains"),
            description=data.get("description", ""),
            is_landmark=data.get("is_landmark", False),
            is_settlement=data.get("is_settlement", False),
            is_destination=data.get("is_destination", False),
            services=data.get("services", []),
            trade_goods=data.get("trade_goods", []),
            base_prices=data.get("base_prices", {}),
            hazards=data.get("hazards", []),
            hunting_bonus=data.get("hunting_bonus", 0),
            healing_bonus=data.get("healing_bonus", 0),
            travel_bonus=data.get("travel_bonus", 0),
            water_available=data.get("water_available", False),
            elevation=data.get("elevation", 0),
            milestone=data.get("milestone", ""),
            special_event=data.get("special_event", ""),
            has_route_choice=data.get("has_route_choice", False),
            has_river_crossing=data.get("has_river_crossing", False),
        )


@dataclass
class TerrainType:
    """Represents a terrain type with its properties."""
    id: str
    name: str
    base_miles_per_day: int
    description: str
    water_consumption_mult: float = 1.0
    food_consumption_mult: float = 1.0
    hunting_modifier: int = 0
    hazards: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, id: str, data: Dict) -> 'TerrainType':
        """Create TerrainType from dictionary."""
        return cls(
            id=id,
            name=data.get("name", id.title()),
            base_miles_per_day=data.get("base_miles_per_day", 15),
            description=data.get("description", ""),
            water_consumption_mult=data.get("water_consumption_mult", 1.0),
            food_consumption_mult=data.get("food_consumption_mult", 1.0),
            hunting_modifier=data.get("hunting_modifier", 0),
            hazards=data.get("hazards", []),
        )


@dataclass 
class GameDate:
    """Tracks the current game date."""
    year: int = START_YEAR
    month: int = START_MONTH
    day: int = START_DAY
    
    MONTH_NAMES = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    def advance(self, days: int = 1):
        """Advance the date by a number of days."""
        for _ in range(days):
            self.day += 1
            if self.day > self.DAYS_IN_MONTH[self.month - 1]:
                self.day = 1
                self.month += 1
                if self.month > 12:
                    self.month = 1
                    self.year += 1
    
    @property
    def season(self) -> Season:
        """Get the current season."""
        if self.month in [3, 4, 5]:
            return Season.SPRING
        elif self.month in [6, 7, 8]:
            return Season.SUMMER
        elif self.month in [9, 10, 11]:
            return Season.FALL
        else:
            return Season.WINTER
    
    @property
    def month_name(self) -> str:
        """Get the name of the current month."""
        return self.MONTH_NAMES[self.month - 1]
    
    def __str__(self) -> str:
        """Format as readable date string."""
        return f"{self.month_name} {self.day}, {self.year}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {"year": self.year, "month": self.month, "day": self.day}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GameDate':
        """Create from dictionary."""
        return cls(
            year=data.get("year", START_YEAR),
            month=data.get("month", START_MONTH),
            day=data.get("day", START_DAY)
        )


# =============================================================================
# Travel Manager Class
# =============================================================================

class TravelManager:
    """
    Manages all travel-related game mechanics.
    
    Handles:
    - Location tracking and navigation
    - Distance/mile tracking
    - Weather generation
    - Terrain effects
    - Route progression
    - Route choices (NEW)
    - River crossings (NEW)
    - Camp quality (NEW)
    """
    
    def __init__(self, data_path: str = None):
        """
        Initialize the travel manager.
        
        Args:
            data_path: Path to locations.json file
        """
        self.locations: List[Location] = []
        self.terrain_types: Dict[str, TerrainType] = {}
        self.weather_patterns: Dict[str, Dict[str, int]] = {}
        self.regions: List[Dict] = []
        
        self.current_location_index: int = 0
        self.miles_traveled: int = 0
        self.total_distance: int = 2800
        
        self.current_weather: Weather = Weather.CLEAR
        self.date: GameDate = GameDate()
        
        # Weather history for river conditions
        self.recent_weather: List[str] = []
        self.max_weather_history = 5
        
        # NEW: Enhanced systems
        if ENHANCED_SYSTEMS_AVAILABLE:
            self.route_manager = RouteManager()
            self.river_manager = RiverCrossingManager()
            self.camp_manager = CampManager()
        else:
            self.route_manager = None
            self.river_manager = None
            self.camp_manager = None
        
        # Track active route (when traveling a chosen route)
        self.active_route: Optional[Dict] = None
        self.route_miles_remaining: int = 0
        
        # Load data
        if data_path:
            self.load_data(data_path)
        else:
            # Try default path
            default_path = Path(__file__).parent / "data" / "locations.json"
            if default_path.exists():
                self.load_data(str(default_path))
            else:
                self._create_default_data()
    
    def load_data(self, filepath: str):
        """Load location data from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load metadata
            meta = data.get("meta", {})
            self.total_distance = meta.get("total_distance", 2800)
            
            # Load regions
            self.regions = data.get("regions", [])
            
            # Load locations
            self.locations = []
            for loc_data in data.get("locations", []):
                self.locations.append(Location.from_dict(loc_data))
            
            # Sort locations by mile marker
            self.locations.sort(key=lambda x: x.mile_marker)
            
            # Load terrain types
            self.terrain_types = {}
            for terrain_id, terrain_data in data.get("terrain_types", {}).items():
                self.terrain_types[terrain_id] = TerrainType.from_dict(terrain_id, terrain_data)
            
            # Load weather patterns
            self.weather_patterns = data.get("weather_patterns", {})
            
        except FileNotFoundError:
            print(f"Warning: Could not find {filepath}, using defaults")
            self._create_default_data()
        except json.JSONDecodeError as e:
            print(f"Warning: Error parsing {filepath}: {e}")
            self._create_default_data()
    
    def _create_default_data(self):
        """Create minimal default data if file loading fails."""
        self.locations = [
            Location(id="start", name="Starting Point", region="start", 
                    mile_marker=0, terrain="plains", description="The beginning."),
            Location(id="end", name="Destination", region="end",
                    mile_marker=2800, terrain="forest", description="The end.",
                    is_destination=True),
        ]
        self.terrain_types = {
            "plains": TerrainType("plains", "Plains", 20, "Open grassland"),
            "mountains": TerrainType("mountains", "Mountains", 10, "Rugged terrain"),
            "forest": TerrainType("forest", "Forest", 12, "Dense woodland"),
            "desert": TerrainType("desert", "Desert", 18, "Arid wasteland"),
            "tundra": TerrainType("tundra", "Tundra", 14, "Frozen wilderness"),
        }
    
    # =========================================================================
    # Location Management
    # =========================================================================
    
    @property
    def current_location(self) -> Location:
        """Get the current location."""
        if 0 <= self.current_location_index < len(self.locations):
            return self.locations[self.current_location_index]
        return self.locations[0]
    
    @property
    def next_location(self) -> Optional[Location]:
        """Get the next location on the trail."""
        next_idx = self.current_location_index + 1
        if next_idx < len(self.locations):
            return self.locations[next_idx]
        return None
    
    @property
    def distance_to_next(self) -> int:
        """Get distance to the next location."""
        if self.next_location:
            return self.next_location.mile_marker - self.miles_traveled
        return 0
    
    @property
    def progress_percentage(self) -> float:
        """Get journey progress as percentage."""
        if self.total_distance <= 0:
            return 100.0
        return (self.miles_traveled / self.total_distance) * 100
    
    @property
    def at_destination(self) -> bool:
        """Check if party has reached the final destination."""
        return self.current_location.is_destination
    
    def get_current_terrain(self) -> TerrainType:
        """Get the current terrain type."""
        # If on active route, use route terrain
        if self.active_route:
            terrain_id = self.active_route.get("terrain", self.current_location.terrain)
        else:
            terrain_id = self.current_location.terrain
        return self.terrain_types.get(terrain_id, 
            TerrainType("unknown", "Unknown", 15, "Unknown terrain"))
    
    def get_current_region(self) -> Optional[Dict]:
        """Get the current region info."""
        region_id = self.current_location.region
        for region in self.regions:
            if region.get("id") == region_id:
                return region
        return None
    
    def get_nearby_landmarks(self, miles_ahead: int = 100) -> List[Location]:
        """Get landmarks within a certain distance ahead."""
        landmarks = []
        for loc in self.locations:
            if loc.mile_marker > self.miles_traveled and \
               loc.mile_marker <= self.miles_traveled + miles_ahead and \
               loc.is_landmark:
                landmarks.append(loc)
        return landmarks
    
    # =========================================================================
    # Route Choice System (NEW)
    # =========================================================================
    
    def check_for_route_choice(self) -> Optional[RouteDecisionPoint]:
        """
        Check if there's a route decision point at current location.
        
        Returns:
            RouteDecisionPoint if found, None otherwise
        """
        if not self.route_manager:
            return None
        
        return self.route_manager.get_decision_point(self.miles_traveled, tolerance=15)
    
    def get_route_options(self, decision_point: RouteDecisionPoint, context: Dict) -> List:
        """
        Get available routes at a decision point.
        
        Args:
            decision_point: The decision point
            context: Game context (skills, resources, etc.)
        
        Returns:
            List of (route, available, reason) tuples
        """
        if not self.route_manager:
            return []
        
        scout_skill = context.get("skills", {}).get("scouting", 50)
        return self.route_manager.get_available_routes(decision_point, context, scout_skill)
    
    def select_route(self, route: RouteOption) -> Dict:
        """
        Select a route and begin traveling it.
        
        Args:
            route: The chosen route
        
        Returns:
            Dict with route details
        """
        if not self.route_manager:
            return {}
        
        route_info = self.route_manager.select_route(route)
        
        # Set active route
        self.active_route = {
            "id": route.id,
            "name": route.name,
            "terrain": route.terrain,
            "distance": route.distance,
            "hazards": route.hazards,
            "danger_level": route.danger_level,
            "rewards": route.rewards,
        }
        self.route_miles_remaining = route.distance
        
        return route_info
    
    def clear_active_route(self):
        """Clear the active route when completed."""
        self.active_route = None
        self.route_miles_remaining = 0
    
    # =========================================================================
    # River Crossing System (NEW)
    # =========================================================================
    
    def check_for_river_crossing(self) -> Optional[RiverCrossingPoint]:
        """
        Check if there's a river crossing at current location.
        
        Returns:
            RiverCrossingPoint if found, None otherwise
        """
        if not self.river_manager:
            return None
        
        return self.river_manager.get_crossing_at_location(self.miles_traveled, tolerance=15)
    
    def get_river_condition(self, crossing: RiverCrossingPoint) -> RiverCondition:
        """
        Get current river conditions.
        
        Args:
            crossing: The crossing point
        
        Returns:
            Current RiverCondition
        """
        if not self.river_manager:
            return RiverCondition.NORMAL
        
        return self.river_manager.get_river_condition(
            crossing, 
            self.date.season.value,
            self.recent_weather
        )
    
    def assess_river_crossing(self, crossing: RiverCrossingPoint, condition: RiverCondition) -> Dict:
        """
        Assess a river crossing.
        
        Args:
            crossing: The crossing point
            condition: Current condition
        
        Returns:
            Assessment dictionary
        """
        if not self.river_manager:
            return {}
        
        return self.river_manager.assess_crossing(crossing, condition)
    
    def get_crossing_methods(
        self, 
        crossing: RiverCrossingPoint, 
        condition: RiverCondition,
        has_tools: bool,
        money: int
    ) -> List:
        """Get available crossing methods."""
        if not self.river_manager:
            return []
        
        return self.river_manager.get_available_methods(crossing, condition, has_tools, money)
    
    def attempt_river_crossing(
        self,
        crossing: RiverCrossingPoint,
        method: CrossingMethod,
        condition: RiverCondition,
        party_members: List[str],
        supplies: Dict,
        skill_bonus: int = 0
    ):
        """
        Attempt to cross a river.
        
        Returns:
            CrossingResult
        """
        if not self.river_manager:
            return None
        
        result = self.river_manager.attempt_crossing(
            crossing=crossing,
            method=method,
            condition=condition,
            weather=self.current_weather.value,
            party_members=party_members,
            supplies=supplies,
            skill_bonus=skill_bonus
        )
        
        # Record the crossing
        self.river_manager.record_crossing(result, crossing.id)
        
        return result
    
    def get_upcoming_crossings(self, range_miles: int = 100) -> List[RiverCrossingPoint]:
        """Get river crossings coming up on the trail."""
        if not self.river_manager:
            return []
        
        return self.river_manager.get_upcoming_crossings(self.miles_traveled, range_miles)
    
    # =========================================================================
    # Hidden Location Discovery (NEW)
    # =========================================================================
    
    def scout_for_hidden_locations(self, scout_skill: int, scout_range: int = 30) -> List[HiddenLocation]:
        """
        Scout for hidden locations.
        
        Args:
            scout_skill: Effective scouting skill
            scout_range: How far to scout
        
        Returns:
            List of newly discovered locations
        """
        if not self.route_manager:
            return []
        
        return self.route_manager.scout_for_hidden(self.miles_traveled, scout_skill, scout_range)
    
    def get_discovered_hidden_locations(self, range_miles: int = 50) -> List[HiddenLocation]:
        """Get discovered hidden locations within range."""
        if not self.route_manager:
            return []
        
        return self.route_manager.get_discovered_locations(self.miles_traveled, range_miles)
    
    def visit_hidden_location(self, location: HiddenLocation) -> Dict:
        """Visit a hidden location and get rewards."""
        if not self.route_manager:
            return {}
        
        return self.route_manager.visit_hidden_location(location)
    
    # =========================================================================
    # Camp System (NEW)
    # =========================================================================
    
    def scout_campsite(self, scout_skill: int = 50) -> Tuple[CampSite, str]:
        """Scout for a campsite at current location."""
        if not self.camp_manager:
            return None, "Camp system not available."
        
        location_data = {
            "water_available": self.current_location.water_available,
            "hazards": self.current_location.hazards,
        }
        
        return self.camp_manager.scout_campsite(
            terrain=self.current_location.terrain,
            location_data=location_data,
            scout_skill=scout_skill
        )
    
    def get_camp_options(self, site: CampSite, has_tools: bool, party_size: int) -> List:
        """Get available camp types for a site."""
        if not self.camp_manager:
            return []
        
        return self.camp_manager.get_camp_options(site, has_tools, party_size)
    
    def setup_camp(self, site: CampSite, camp_type: CampType, has_tools: bool, party_skill: int = 50):
        """Set up camp at a site."""
        if not self.camp_manager:
            return None, []
        
        return self.camp_manager.setup_camp(
            site=site,
            camp_type=camp_type,
            weather=self.current_weather.value,
            has_tools=has_tools,
            party_skill=party_skill
        )
    
    def rest_at_camp(self, camp, hours: int, party_health: int, has_medic: bool = False):
        """Rest at the current camp."""
        if not self.camp_manager:
            return None
        
        return self.camp_manager.rest_at_camp(
            camp=camp,
            hours=hours,
            weather=self.current_weather.value,
            party_health=party_health,
            has_medic=has_medic
        )
    
    # =========================================================================
    # Travel Actions
    # =========================================================================
    
    def calculate_travel_distance(
        self, 
        party_speed_modifier: int = 0,
        weather_modifier: int = 0,
        forced_pace: str = "normal"
    ) -> int:
        """
        Calculate how far the party can travel in a day.
        
        Args:
            party_speed_modifier: Modifier from party conditions
            weather_modifier: Modifier from current weather
            forced_pace: 'slow', 'normal', 'fast', or 'grueling'
        
        Returns:
            Miles that can be traveled
        """
        terrain = self.get_current_terrain()
        base_miles = terrain.base_miles_per_day
        
        # Location-specific bonus
        location_bonus = self.current_location.travel_bonus
        
        # Route-specific modifier
        route_modifier = 0
        if self.active_route:
            # Dangerous routes might slow travel
            danger = self.active_route.get("danger_level", 50)
            if danger > 60:
                route_modifier = -10
        
        # Pace modifiers
        pace_modifiers = {
            "slow": -30,      # Careful travel
            "normal": 0,
            "fast": 20,       # Pushed pace
            "grueling": 40,   # Exhausting pace
        }
        pace_mod = pace_modifiers.get(forced_pace, 0)
        
        # Calculate total modifier
        total_modifier = party_speed_modifier + weather_modifier + location_bonus + pace_mod + route_modifier
        effective_modifier = 1 + (total_modifier / 100)
        
        # Calculate final distance
        miles = int(base_miles * effective_modifier)
        
        # Minimum 1 mile, maximum 2x base
        return max(1, min(miles, base_miles * 2))
    
    def travel(self, miles: int) -> Dict:
        """
        Move the party forward on the trail.
        
        Args:
            miles: Number of miles to travel
        
        Returns:
            Dict with travel results
        """
        results = {
            "miles_traveled": 0,
            "locations_reached": [],
            "milestones": [],
            "hazards_encountered": [],
            "at_destination": False,
            "route_completed": False,
            "river_crossing_ahead": None,
            "route_choice_ahead": None,
        }
        
        start_miles = self.miles_traveled
        target_miles = self.miles_traveled + miles
        
        # If on active route, track progress
        if self.active_route:
            self.route_miles_remaining -= miles
            if self.route_miles_remaining <= 0:
                results["route_completed"] = True
                # Apply route rewards
                if self.active_route.get("rewards"):
                    results["route_rewards"] = self.active_route["rewards"]
                self.clear_active_route()
        
        # Check for locations passed along the way
        for loc in self.locations:
            if loc.mile_marker > start_miles and loc.mile_marker <= target_miles:
                results["locations_reached"].append(loc)
                
                if loc.milestone:
                    results["milestones"].append(loc.milestone)
                
                if loc.hazards:
                    results["hazards_encountered"].extend(loc.hazards)
                
                # Update current location index
                self.current_location_index = self.locations.index(loc)
        
        # Update miles traveled
        self.miles_traveled = min(target_miles, self.total_distance)
        results["miles_traveled"] = self.miles_traveled - start_miles
        
        # Check if reached destination
        if self.at_destination:
            results["at_destination"] = True
        
        # Check for upcoming challenges
        if self.river_manager:
            crossing = self.check_for_river_crossing()
            if crossing:
                results["river_crossing_ahead"] = crossing
        
        if self.route_manager:
            route_point = self.check_for_route_choice()
            if route_point:
                results["route_choice_ahead"] = route_point
        
        # Advance date
        self.date.advance(1)
        
        return results
    
    # =========================================================================
    # Weather System
    # =========================================================================
    
    def generate_weather(self) -> Weather:
        """
        Generate weather for the current day based on season and location.
        
        Returns:
            Weather enum value
        """
        season = self.date.season.value
        terrain = self.current_location.terrain
        
        # Get base weather probabilities for season
        base_probs = self.weather_patterns.get(season, {
            "clear": 40, "cloudy": 30, "rain": 20, "storm": 10
        })
        
        # Adjust for terrain
        adjusted_probs = dict(base_probs)
        
        if terrain == "mountains":
            adjusted_probs["storm"] = adjusted_probs.get("storm", 10) + 10
            if self.current_location.elevation > 8000:
                adjusted_probs["snow"] = adjusted_probs.get("snow", 0) + 15
        
        elif terrain == "desert":
            adjusted_probs["hot"] = adjusted_probs.get("hot", 0) + 20
            adjusted_probs["rain"] = max(0, adjusted_probs.get("rain", 0) - 15)
        
        elif terrain == "tundra":
            adjusted_probs["cold"] = adjusted_probs.get("cold", 0) + 20
            adjusted_probs["snow"] = adjusted_probs.get("snow", 0) + 15
            adjusted_probs["blizzard"] = adjusted_probs.get("blizzard", 0) + 5
        
        # Convert to cumulative probabilities
        total = sum(adjusted_probs.values())
        roll = random.randint(1, total)
        
        cumulative = 0
        for weather_name, prob in adjusted_probs.items():
            cumulative += prob
            if roll <= cumulative:
                try:
                    self.current_weather = Weather(weather_name)
                except ValueError:
                    self.current_weather = Weather.CLEAR
                break
        else:
            self.current_weather = Weather.CLEAR
        
        # Track weather history for river conditions
        self.recent_weather.append(self.current_weather.value)
        if len(self.recent_weather) > self.max_weather_history:
            self.recent_weather.pop(0)
        
        return self.current_weather
    
    def get_weather_effects(self) -> Dict:
        """Get the effects of the current weather."""
        return WEATHER_EFFECTS.get(self.current_weather, WEATHER_EFFECTS[Weather.CLEAR])
    
    @property
    def weather_description(self) -> str:
        """Get a description of the current weather."""
        effects = self.get_weather_effects()
        return effects.get("description", "Unknown conditions")
    
    # =========================================================================
    # Hazards
    # =========================================================================
    
    def check_hazards(self) -> List[Dict]:
        """
        Check for hazards at current location/weather.
        
        Returns:
            List of hazard events that triggered
        """
        hazards = []
        
        # Location hazards
        loc_hazards = list(self.current_location.hazards)
        
        # Active route hazards
        if self.active_route:
            loc_hazards.extend(self.active_route.get("hazards", []))
        
        # Weather hazards
        if self.current_weather == Weather.BLIZZARD:
            loc_hazards.extend(["hypothermia", "lost"])
        elif self.current_weather == Weather.STORM:
            loc_hazards.append("injury")
        
        # Terrain hazards
        terrain = self.get_current_terrain()
        loc_hazards.extend(terrain.hazards)
        
        # Roll for each hazard
        for hazard in set(loc_hazards):
            chance = self._get_hazard_chance(hazard)
            if random.random() < chance:
                hazards.append({
                    "type": hazard,
                    "severity": self._get_hazard_severity(hazard),
                    "description": self._get_hazard_description(hazard),
                })
        
        return hazards
    
    def _get_hazard_chance(self, hazard: str) -> float:
        """Get the base chance for a hazard to trigger."""
        chances = {
            "avalanche": 0.05,
            "injury": 0.08,
            "altitude": 0.10,
            "wildlife": 0.12,
            "river_crossing": 0.15,
            "dehydration": 0.10,
            "heat": 0.08,
            "cold": 0.10,
            "frostbite": 0.08,
            "hypothermia": 0.06,
            "ambush": 0.05,
            "geothermal": 0.03,
            "crevasse": 0.04,
            "lost": 0.10,
            "rockslide": 0.06,
        }
        return chances.get(hazard, 0.05)
    
    def _get_hazard_severity(self, hazard: str) -> str:
        """Determine severity of a hazard event."""
        roll = random.random()
        if roll < 0.6:
            return "minor"
        elif roll < 0.9:
            return "moderate"
        else:
            return "severe"
    
    def _get_hazard_description(self, hazard: str) -> str:
        """Get a description for a hazard."""
        descriptions = {
            "avalanche": "An avalanche thunders down the mountainside!",
            "injury": "Someone takes a bad fall on the rough terrain.",
            "altitude": "The thin mountain air makes breathing difficult.",
            "wildlife": "Wild animals threaten the party!",
            "river_crossing": "The river crossing proves treacherous.",
            "dehydration": "The relentless sun saps everyone's strength.",
            "heat": "The oppressive heat takes its toll.",
            "cold": "The bitter cold seeps into everyone's bones.",
            "frostbite": "The freezing temperatures cause frostbite.",
            "hypothermia": "The deadly cold threatens to claim lives.",
            "ambush": "Hostile figures appear on the trail!",
            "geothermal": "Scalding water erupts from the ground!",
            "crevasse": "A hidden crevasse nearly swallows a party member!",
            "lost": "The party becomes disoriented and loses the trail.",
            "rockslide": "Rocks tumble down the slope!",
        }
        return descriptions.get(hazard, f"A {hazard} hazard occurs!")
    
    # =========================================================================
    # Scouting (Enhanced)
    # =========================================================================
    
    def scout_ahead(self, scout_skill: int = 50) -> Dict:
        """
        Scout ahead on the trail.
        
        Args:
            scout_skill: Effective scouting skill (0-100)
        
        Returns:
            Dict with scouting results
        """
        results = {
            "distance_scouted": 0,
            "locations_found": [],
            "hazards_spotted": [],
            "weather_forecast": None,
            "hunting_prospects": None,
            "hidden_locations_found": [],
            "river_crossings_ahead": [],
            "route_choices_ahead": [],
        }
        
        # Scout distance based on skill and terrain
        base_distance = 20
        skill_bonus = scout_skill / 100
        results["distance_scouted"] = int(base_distance * (1 + skill_bonus))
        
        # Find locations ahead
        scout_range = self.miles_traveled + results["distance_scouted"]
        for loc in self.locations:
            if loc.mile_marker > self.miles_traveled and loc.mile_marker <= scout_range:
                loc_info = {
                    "name": loc.name,
                    "distance": loc.mile_marker - self.miles_traveled,
                    "terrain": loc.terrain,
                    "is_settlement": loc.is_settlement,
                    "water_available": loc.water_available,
                }
                
                # Spot hazards with skill check
                if loc.hazards and random.random() < skill_bonus:
                    loc_info["hazards"] = loc.hazards
                    results["hazards_spotted"].extend(loc.hazards)
                
                results["locations_found"].append(loc_info)
        
        # Weather forecast (skill-based accuracy)
        if random.random() < skill_bonus:
            # Store current weather
            old_weather = self.current_weather
            # Generate next day's weather
            next_weather = self.generate_weather()
            results["weather_forecast"] = next_weather.value
            # Restore current weather
            self.current_weather = old_weather
            if self.recent_weather:
                self.recent_weather.pop()
        
        # Hunting prospects
        terrain = self.get_current_terrain()
        base_hunting = 50 + terrain.hunting_modifier + self.current_location.hunting_bonus
        if random.random() < skill_bonus:
            if base_hunting >= 60:
                results["hunting_prospects"] = "excellent"
            elif base_hunting >= 40:
                results["hunting_prospects"] = "good"
            elif base_hunting >= 20:
                results["hunting_prospects"] = "fair"
            else:
                results["hunting_prospects"] = "poor"
        
        # NEW: Scout for hidden locations
        if self.route_manager:
            discovered = self.scout_for_hidden_locations(scout_skill, results["distance_scouted"])
            results["hidden_locations_found"] = [
                {"name": loc.name, "type": loc.location_type.value, "mile": loc.mile_marker}
                for loc in discovered
            ]
        
        # NEW: Check for river crossings ahead
        if self.river_manager:
            crossings = self.get_upcoming_crossings(results["distance_scouted"])
            results["river_crossings_ahead"] = [
                {"name": c.name, "river": c.river_name, "distance": c.mile_marker - self.miles_traveled}
                for c in crossings
            ]
        
        # NEW: Check for route choices ahead
        if self.route_manager:
            for point in self.route_manager.decision_points:
                distance = point.mile_marker - self.miles_traveled
                if 0 < distance <= results["distance_scouted"]:
                    results["route_choices_ahead"].append({
                        "name": point.name,
                        "distance": distance,
                        "routes": len(point.routes),
                    })
        
        return results
    
    # =========================================================================
    # Status Display
    # =========================================================================
    
    def get_status_display(self) -> Dict:
        """Get status info for UI display."""
        status = {
            "location": self.current_location.name,
            "region": self.current_location.region.replace("_", " ").title(),
            "terrain": self.get_current_terrain().name,
            "weather": self.weather_description,
            "date": str(self.date),
            "season": self.date.season.value.title(),
            "miles_traveled": self.miles_traveled,
            "miles_remaining": self.total_distance - self.miles_traveled,
            "progress": f"{self.progress_percentage:.1f}%",
            "next_landmark": self.next_location.name if self.next_location else "Destination",
            "distance_to_next": self.distance_to_next,
        }
        
        # Add active route info
        if self.active_route:
            status["active_route"] = self.active_route["name"]
            status["route_miles_remaining"] = self.route_miles_remaining
        
        return status
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """Convert travel state to dictionary for saving."""
        data = {
            "current_location_index": self.current_location_index,
            "miles_traveled": self.miles_traveled,
            "current_weather": self.current_weather.value,
            "date": self.date.to_dict(),
            "recent_weather": self.recent_weather,
            "active_route": self.active_route,
            "route_miles_remaining": self.route_miles_remaining,
        }
        
        # Save enhanced system states
        if self.route_manager:
            data["route_manager"] = self.route_manager.to_dict()
        if self.river_manager:
            data["river_manager"] = self.river_manager.to_dict()
        if self.camp_manager:
            data["camp_manager"] = self.camp_manager.to_dict()
        
        return data
    
    def load_state(self, data: Dict):
        """Load travel state from dictionary."""
        self.current_location_index = data.get("current_location_index", 0)
        self.miles_traveled = data.get("miles_traveled", 0)
        
        weather_str = data.get("current_weather", "clear")
        try:
            self.current_weather = Weather(weather_str)
        except ValueError:
            self.current_weather = Weather.CLEAR
        
        if "date" in data:
            self.date = GameDate.from_dict(data["date"])
        
        self.recent_weather = data.get("recent_weather", [])
        self.active_route = data.get("active_route")
        self.route_miles_remaining = data.get("route_miles_remaining", 0)
        
        # Load enhanced system states
        if self.route_manager and "route_manager" in data:
            self.route_manager.load_state(data["route_manager"])
        if self.river_manager and "river_manager" in data:
            self.river_manager.load_state(data["river_manager"])
        if self.camp_manager and "camp_manager" in data:
            self.camp_manager.load_state(data["camp_manager"])


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate travel system functionality."""
    print("=" * 50)
    print("TRAVEL SYSTEM DEMO (Enhanced)")
    print("=" * 50)
    print()
    
    # Initialize travel manager
    tm = TravelManager()
    
    print(f"Loaded {len(tm.locations)} locations")
    print(f"Total journey distance: {tm.total_distance} miles")
    print(f"Enhanced systems available: {ENHANCED_SYSTEMS_AVAILABLE}")
    print()
    
    # Show starting status
    print("Starting Status:")
    status = tm.get_status_display()
    for key, value in status.items():
        print(f"  {key}: {value}")
    print()
    
    # Test scouting with new features
    print("Enhanced Scouting (skill 70):")
    scout_results = tm.scout_ahead(scout_skill=70)
    print(f"  Distance scouted: {scout_results['distance_scouted']} miles")
    print(f"  Locations found: {len(scout_results['locations_found'])}")
    
    if scout_results.get('hidden_locations_found'):
        print(f"  Hidden locations discovered: {len(scout_results['hidden_locations_found'])}")
        for loc in scout_results['hidden_locations_found']:
            print(f"    - {loc['name']} ({loc['type']}) at mile {loc['mile']}")
    
    if scout_results.get('river_crossings_ahead'):
        print(f"  River crossings ahead: {len(scout_results['river_crossings_ahead'])}")
        for crossing in scout_results['river_crossings_ahead']:
            print(f"    - {crossing['name']} ({crossing['river']}) in {crossing['distance']} miles")
    
    if scout_results.get('route_choices_ahead'):
        print(f"  Route choices ahead: {len(scout_results['route_choices_ahead'])}")
        for choice in scout_results['route_choices_ahead']:
            print(f"    - {choice['name']} ({choice['routes']} options) in {choice['distance']} miles")
    print()
    
    # Test route choice
    if ENHANCED_SYSTEMS_AVAILABLE and tm.route_manager:
        print("Testing route decision point...")
        tm.miles_traveled = 395  # Near Gore Pass Junction
        decision = tm.check_for_route_choice()
        if decision:
            print(f"  Found: {decision.name}")
            print(f"  Description: {decision.description[:80]}...")
            
            context = {"skills": {"scouting": 60}, "avg_health": 70, "weather": "clear"}
            routes = tm.get_route_options(decision, context)
            print(f"  Available routes:")
            for route, available, reason in routes:
                status_str = "✓" if available else f"✗ ({reason})"
                print(f"    - {route.name}: {route.distance} mi, danger {route.danger_level}% {status_str}")
    print()
    
    # Test river crossing
    if ENHANCED_SYSTEMS_AVAILABLE and tm.river_manager:
        print("Testing river crossing...")
        tm.miles_traveled = 280  # Near Arkansas River
        crossing = tm.check_for_river_crossing()
        if crossing:
            condition = tm.get_river_condition(crossing)
            assessment = tm.assess_river_crossing(crossing, condition)
            print(f"  Crossing: {assessment['name']}")
            print(f"  River: {assessment['river']}")
            print(f"  Condition: {assessment['condition']} - {assessment['condition_desc']}")
            print(f"  Risk: {assessment['risk_level']} ({assessment['risk_description']})")
    print()
    
    print("Demo complete!")


if __name__ == "__main__":
    demo()