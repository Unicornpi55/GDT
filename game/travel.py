"""
travel.py - Travel System and Navigation for The Great Divide Trail

Handles all travel mechanics including movement, location tracking,
terrain effects, weather, and route navigation.
"""

import json
import random
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


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
        
        # Load data
        if data_path:
            self.load_data(data_path)
        else:
            # Try default path
            default_path = Path(__file__).parent / "data" / "locations.json"
            if default_path.exists():
                self.load_data(str(default_path))
    
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
        
        # Pace modifiers
        pace_modifiers = {
            "slow": -30,      # Careful travel
            "normal": 0,
            "fast": 20,       # Pushed pace
            "grueling": 40,   # Exhausting pace
        }
        pace_mod = pace_modifiers.get(forced_pace, 0)
        
        # Calculate total modifier
        total_modifier = party_speed_modifier + weather_modifier + location_bonus + pace_mod
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
        }
        
        start_miles = self.miles_traveled
        target_miles = self.miles_traveled + miles
        
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
            # Mountains: more storms, snow at high elevation
            adjusted_probs["storm"] = adjusted_probs.get("storm", 10) + 10
            if self.current_location.elevation > 8000:
                adjusted_probs["snow"] = adjusted_probs.get("snow", 0) + 15
        
        elif terrain == "desert":
            # Desert: more hot weather, less rain
            adjusted_probs["hot"] = adjusted_probs.get("hot", 0) + 20
            adjusted_probs["rain"] = max(0, adjusted_probs.get("rain", 0) - 15)
        
        elif terrain == "tundra":
            # Tundra: more cold/snow
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
                return self.current_weather
        
        self.current_weather = Weather.CLEAR
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
        loc_hazards = self.current_location.hazards
        
        # Weather hazards
        if self.current_weather == Weather.BLIZZARD:
            loc_hazards = loc_hazards + ["hypothermia", "lost"]
        elif self.current_weather == Weather.STORM:
            loc_hazards = loc_hazards + ["injury"]
        
        # Terrain hazards
        terrain = self.get_current_terrain()
        loc_hazards = loc_hazards + terrain.hazards
        
        # Roll for each hazard
        for hazard in set(loc_hazards):  # Remove duplicates
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
        }
        return descriptions.get(hazard, f"A {hazard} hazard occurs!")
    
    # =========================================================================
    # Scouting
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
                }
                
                # Spot hazards with skill check
                if loc.hazards and random.random() < skill_bonus:
                    loc_info["hazards"] = loc.hazards
                    results["hazards_spotted"].extend(loc.hazards)
                
                results["locations_found"].append(loc_info)
        
        # Weather forecast (skill-based accuracy)
        if random.random() < skill_bonus:
            # Peek at next day's weather
            next_weather = self.generate_weather()
            results["weather_forecast"] = next_weather.value
            # Reset weather for today
            self.generate_weather()
        
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
        
        return results
    
    # =========================================================================
    # Status Display
    # =========================================================================
    
    def get_status_display(self) -> Dict:
        """Get status info for UI display."""
        return {
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
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """Convert travel state to dictionary for saving."""
        return {
            "current_location_index": self.current_location_index,
            "miles_traveled": self.miles_traveled,
            "current_weather": self.current_weather.value,
            "date": self.date.to_dict(),
        }
    
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


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate travel system functionality."""
    print("=" * 50)
    print("TRAVEL SYSTEM DEMO")
    print("=" * 50)
    print()
    
    # Initialize travel manager
    tm = TravelManager()
    
    print(f"Loaded {len(tm.locations)} locations")
    print(f"Total journey distance: {tm.total_distance} miles")
    print()
    
    # Show starting status
    print("Starting Status:")
    status = tm.get_status_display()
    for key, value in status.items():
        print(f"  {key}: {value}")
    print()
    
    # Show current location details
    loc = tm.current_location
    print(f"Current Location: {loc.name}")
    print(f"  Description: {loc.description}")
    print(f"  Terrain: {loc.terrain}")
    print(f"  Services: {loc.services}")
    print()
    
    # Generate weather
    print("Generating weather for the journey...")
    for _ in range(5):
        weather = tm.generate_weather()
        effects = tm.get_weather_effects()
        print(f"  Day {tm.date}: {weather.value} - {effects['description']}")
        tm.date.advance(1)
    print()
    
    # Reset date for travel simulation
    tm.date = GameDate()
    
    # Simulate travel
    print("Simulating 10 days of travel...")
    for day in range(10):
        tm.generate_weather()
        weather_effects = tm.get_weather_effects()
        
        # Calculate travel distance
        miles = tm.calculate_travel_distance(
            party_speed_modifier=0,
            weather_modifier=weather_effects["speed_modifier"]
        )
        
        # Travel
        results = tm.travel(miles)
        
        print(f"  Day {day + 1}: Traveled {results['miles_traveled']} miles " +
              f"({tm.current_weather.value})")
        
        if results["locations_reached"]:
            for reached in results["locations_reached"]:
                print(f"    → Reached {reached.name}")
        
        if results["milestones"]:
            for ms in results["milestones"]:
                print(f"    ★ {ms}")
        
        # Check hazards
        hazards = tm.check_hazards()
        for hazard in hazards:
            print(f"    ⚠ HAZARD: {hazard['description']} ({hazard['severity']})")
        
        if results["at_destination"]:
            print("\n  *** DESTINATION REACHED! ***")
            break
    
    print()
    print(f"Final position: Mile {tm.miles_traveled}")
    print(f"Progress: {tm.progress_percentage:.1f}%")
    print()
    
    # Test scouting
    print("Scouting ahead (skill 70)...")
    scout_results = tm.scout_ahead(scout_skill=70)
    print(f"  Distance scouted: {scout_results['distance_scouted']} miles")
    print(f"  Locations found: {len(scout_results['locations_found'])}")
    for loc_info in scout_results["locations_found"]:
        print(f"    - {loc_info['name']} ({loc_info['distance']} miles)")
    if scout_results["hazards_spotted"]:
        print(f"  Hazards spotted: {scout_results['hazards_spotted']}")
    if scout_results["weather_forecast"]:
        print(f"  Weather forecast: {scout_results['weather_forecast']}")
    if scout_results["hunting_prospects"]:
        print(f"  Hunting prospects: {scout_results['hunting_prospects']}")
    print()
    
    # Serialization test
    print("Serialization test:")
    saved = tm.to_dict()
    print(f"  Saved state: {saved}")
    
    tm2 = TravelManager()
    tm2.load_state(saved)
    print(f"  Restored miles: {tm2.miles_traveled}")
    print()
    
    print("Demo complete!")


if __name__ == "__main__":
    demo()