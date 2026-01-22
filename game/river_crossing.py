"""
river_crossing.py - River Crossing System for The Great Divide Trail

Dedicated mechanics for crossing rivers including:
- Ford (walk through)
- Caulk and float (waterproof wagon)
- Ferry (pay for transport)
- Wait for conditions to improve
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# Enums and Constants
# =============================================================================

class CrossingMethod(Enum):
    """Methods for crossing a river."""
    FORD = "ford"           # Walk/wade through
    CAULK = "caulk"         # Waterproof wagon and float
    FERRY = "ferry"         # Pay for ferry service
    BRIDGE = "bridge"       # Use a bridge (if available)
    WAIT = "wait"           # Wait for better conditions


class RiverCondition(Enum):
    """River water level conditions."""
    LOW = "low"             # Easy crossing
    NORMAL = "normal"       # Standard crossing
    HIGH = "high"           # Difficult crossing
    FLOOD = "flood"         # Extremely dangerous


class CrossingOutcome(Enum):
    """Possible outcomes of a crossing attempt."""
    SUCCESS = "success"           # Made it across safely
    PARTIAL_LOSS = "partial"      # Lost some supplies
    MAJOR_LOSS = "major"          # Lost significant supplies, possible injury
    DISASTER = "disaster"         # Deaths, massive losses
    CANCELLED = "cancelled"       # Crossing aborted


# Base success rates by method (modified by conditions)
BASE_SUCCESS_RATES = {
    CrossingMethod.FORD: 0.70,
    CrossingMethod.CAULK: 0.80,
    CrossingMethod.FERRY: 0.95,
    CrossingMethod.BRIDGE: 0.99,
    CrossingMethod.WAIT: 1.0,  # Always "succeeds" (no crossing)
}

# Condition modifiers (multiplier to success rate)
CONDITION_MODIFIERS = {
    RiverCondition.LOW: 1.3,
    RiverCondition.NORMAL: 1.0,
    RiverCondition.HIGH: 0.6,
    RiverCondition.FLOOD: 0.3,
}

# Weather modifiers
WEATHER_MODIFIERS = {
    "clear": 1.1,
    "cloudy": 1.0,
    "rain": 0.8,
    "storm": 0.5,
    "snow": 0.9,
    "blizzard": 0.6,
}

# Method costs and requirements
METHOD_INFO = {
    CrossingMethod.FORD: {
        "name": "Ford the River",
        "description": "Wade through the water. Fast but risky if water is high.",
        "time_hours": 2,
        "cost": 0,
        "requires_tools": False,
        "danger_base": 30,
    },
    CrossingMethod.CAULK: {
        "name": "Caulk and Float",
        "description": "Waterproof the wagon and float across. Requires tools and time.",
        "time_hours": 6,
        "cost": 0,
        "requires_tools": True,
        "danger_base": 20,
    },
    CrossingMethod.FERRY: {
        "name": "Take the Ferry",
        "description": "Pay for safe passage on a ferry. Safest but costs money.",
        "time_hours": 3,
        "cost": 25,  # Base cost
        "requires_tools": False,
        "danger_base": 5,
    },
    CrossingMethod.BRIDGE: {
        "name": "Cross the Bridge",
        "description": "Use an available bridge. Safest option when available.",
        "time_hours": 1,
        "cost": 5,  # Toll
        "requires_tools": False,
        "danger_base": 2,
    },
    CrossingMethod.WAIT: {
        "name": "Wait for Better Conditions",
        "description": "Camp and wait for the water level to drop. Uses supplies.",
        "time_hours": 0,
        "cost": 0,
        "requires_tools": False,
        "danger_base": 0,
    },
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class RiverCrossingPoint:
    """Represents a river crossing location."""
    id: str
    name: str
    river_name: str
    mile_marker: int
    description: str
    base_width: int              # River width in feet
    base_depth: int              # Average depth in feet
    current_strength: int        # 1-10 current strength
    has_ferry: bool = False
    has_bridge: bool = False
    ferry_cost: int = 25
    bridge_toll: int = 5
    
    # Seasonal effects
    spring_flood_chance: float = 0.4
    summer_low_chance: float = 0.3
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RiverCrossingPoint':
        """Create from dictionary."""
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown Crossing"),
            river_name=data.get("river_name", "Unknown River"),
            mile_marker=data.get("mile_marker", 0),
            description=data.get("description", ""),
            base_width=data.get("base_width", 100),
            base_depth=data.get("base_depth", 4),
            current_strength=data.get("current_strength", 5),
            has_ferry=data.get("has_ferry", False),
            has_bridge=data.get("has_bridge", False),
            ferry_cost=data.get("ferry_cost", 25),
            bridge_toll=data.get("bridge_toll", 5),
            spring_flood_chance=data.get("spring_flood_chance", 0.4),
            summer_low_chance=data.get("summer_low_chance", 0.3),
        )


@dataclass
class CrossingResult:
    """Results of a river crossing attempt."""
    success: bool
    outcome: CrossingOutcome
    method: CrossingMethod
    supplies_lost: Dict = field(default_factory=dict)
    injuries: List[str] = field(default_factory=list)
    deaths: List[str] = field(default_factory=list)
    time_spent: int = 0  # Hours
    money_spent: int = 0
    message: str = ""
    details: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "outcome": self.outcome.value,
            "method": self.method.value,
            "supplies_lost": self.supplies_lost,
            "injuries": self.injuries,
            "deaths": self.deaths,
            "time_spent": self.time_spent,
            "money_spent": self.money_spent,
            "message": self.message,
            "details": self.details,
        }


# =============================================================================
# River Crossing Manager
# =============================================================================

class RiverCrossingManager:
    """
    Manages river crossing mechanics.
    """
    
    def __init__(self):
        """Initialize the crossing manager."""
        self.crossing_points: List[RiverCrossingPoint] = []
        self.crossing_history: List[Dict] = []
        
        # Load default crossings
        self._load_default_crossings()
    
    def _load_default_crossings(self):
        """Load default river crossing points."""
        self.crossing_points = [
            RiverCrossingPoint.from_dict({
                "id": "rio_grande_1",
                "name": "Rio Grande Crossing",
                "river_name": "Rio Grande",
                "mile_marker": 120,
                "description": "The mighty Rio Grande flows wide and shallow here during dry months.",
                "base_width": 150,
                "base_depth": 3,
                "current_strength": 4,
                "has_ferry": True,
                "ferry_cost": 20,
                "spring_flood_chance": 0.5,
            }),
            RiverCrossingPoint.from_dict({
                "id": "arkansas_crossing",
                "name": "Arkansas River Ford",
                "river_name": "Arkansas River",
                "mile_marker": 280,
                "description": "A well-known ford on the Arkansas. The current can be treacherous.",
                "base_width": 200,
                "base_depth": 4,
                "current_strength": 6,
                "has_ferry": False,
                "spring_flood_chance": 0.6,
            }),
            RiverCrossingPoint.from_dict({
                "id": "blue_river_crossing",
                "name": "Blue River Crossing",
                "river_name": "Blue River",
                "mile_marker": 360,
                "description": "A mountain river fed by snowmelt. Cold and swift in spring.",
                "base_width": 80,
                "base_depth": 5,
                "current_strength": 7,
                "has_ferry": False,
                "spring_flood_chance": 0.7,
                "summer_low_chance": 0.2,
            }),
            RiverCrossingPoint.from_dict({
                "id": "green_river",
                "name": "Green River Ferry",
                "river_name": "Green River",
                "mile_marker": 650,
                "description": "The deep Green River. A ferry operates here in good weather.",
                "base_width": 300,
                "base_depth": 8,
                "current_strength": 5,
                "has_ferry": True,
                "ferry_cost": 35,
            }),
            RiverCrossingPoint.from_dict({
                "id": "snake_river",
                "name": "Snake River Crossing",
                "river_name": "Snake River",
                "mile_marker": 820,
                "description": "The Snake carves through a canyon here. Crossing is perilous.",
                "base_width": 250,
                "base_depth": 7,
                "current_strength": 8,
                "has_ferry": True,
                "ferry_cost": 40,
                "spring_flood_chance": 0.5,
            }),
            RiverCrossingPoint.from_dict({
                "id": "missouri_headwaters",
                "name": "Missouri Headwaters",
                "river_name": "Missouri River",
                "mile_marker": 1130,
                "description": "Where three rivers join to form the Missouri. Multiple channels to cross.",
                "base_width": 180,
                "base_depth": 4,
                "current_strength": 5,
                "has_ferry": False,
                "has_bridge": True,
                "bridge_toll": 8,
            }),
            RiverCrossingPoint.from_dict({
                "id": "flathead_river",
                "name": "Flathead River Crossing",
                "river_name": "Flathead River",
                "mile_marker": 1400,
                "description": "Crystal clear but deceptively deep. The Salish know safe fords.",
                "base_width": 120,
                "base_depth": 6,
                "current_strength": 6,
                "has_ferry": False,
                "summer_low_chance": 0.4,
            }),
            RiverCrossingPoint.from_dict({
                "id": "kootenai_crossing",
                "name": "Kootenai River Ford",
                "river_name": "Kootenai River",
                "mile_marker": 1520,
                "description": "A swift river marking the border of British territory.",
                "base_width": 140,
                "base_depth": 5,
                "current_strength": 7,
                "has_ferry": True,
                "ferry_cost": 30,
            }),
            RiverCrossingPoint.from_dict({
                "id": "peace_river",
                "name": "Peace River Crossing",
                "river_name": "Peace River",
                "mile_marker": 1920,
                "description": "The Peace flows slowly here, but the cold water is numbing.",
                "base_width": 220,
                "base_depth": 5,
                "current_strength": 4,
                "has_ferry": False,
            }),
            RiverCrossingPoint.from_dict({
                "id": "liard_river",
                "name": "Liard River Crossing",
                "river_name": "Liard River",
                "mile_marker": 2150,
                "description": "The Liard is dangerous - cold, fast, and unpredictable.",
                "base_width": 180,
                "base_depth": 6,
                "current_strength": 8,
                "has_ferry": False,
                "spring_flood_chance": 0.6,
            }),
        ]
    
    # =========================================================================
    # Condition Assessment
    # =========================================================================
    
    def get_river_condition(
        self, 
        crossing: RiverCrossingPoint, 
        season: str, 
        recent_weather: List[str]
    ) -> RiverCondition:
        """
        Determine current river condition based on season and weather.
        
        Args:
            crossing: The crossing point
            season: Current season
            recent_weather: List of recent weather conditions
        
        Returns:
            Current river condition
        """
        # Base condition by season
        if season == "spring":
            # Spring snowmelt = higher chance of flooding
            if random.random() < crossing.spring_flood_chance:
                base = RiverCondition.HIGH
            else:
                base = RiverCondition.NORMAL
        elif season == "summer":
            # Summer can be low water
            if random.random() < crossing.summer_low_chance:
                base = RiverCondition.LOW
            else:
                base = RiverCondition.NORMAL
        elif season == "fall":
            base = RiverCondition.NORMAL
        else:  # Winter
            base = RiverCondition.LOW  # Frozen or very low
        
        # Modify by recent weather
        rain_count = sum(1 for w in recent_weather if w in ["rain", "storm"])
        
        if rain_count >= 3:
            # Lots of rain = higher water
            if base == RiverCondition.NORMAL:
                return RiverCondition.HIGH
            elif base == RiverCondition.HIGH:
                return RiverCondition.FLOOD
        elif rain_count == 0 and season == "summer":
            # Dry spell = lower water
            if base == RiverCondition.NORMAL:
                return RiverCondition.LOW
        
        return base
    
    def assess_crossing(
        self, 
        crossing: RiverCrossingPoint, 
        condition: RiverCondition
    ) -> Dict:
        """
        Assess a crossing and provide information to the player.
        
        Args:
            crossing: The crossing point
            condition: Current river condition
        
        Returns:
            Assessment dictionary
        """
        # Adjust depth/width by condition
        depth_mults = {
            RiverCondition.LOW: 0.6,
            RiverCondition.NORMAL: 1.0,
            RiverCondition.HIGH: 1.5,
            RiverCondition.FLOOD: 2.0,
        }
        
        current_depth = int(crossing.base_depth * depth_mults[condition])
        current_width = int(crossing.base_width * (depth_mults[condition] * 0.7 + 0.3))
        
        # Danger assessment
        danger = crossing.current_strength * 5
        if condition == RiverCondition.HIGH:
            danger += 20
        elif condition == RiverCondition.FLOOD:
            danger += 50
        elif condition == RiverCondition.LOW:
            danger -= 15
        
        # Risk description
        if danger < 20:
            risk_level = "Low"
            risk_desc = "The crossing looks manageable."
        elif danger < 40:
            risk_level = "Moderate"
            risk_desc = "Exercise caution when crossing."
        elif danger < 60:
            risk_level = "High"
            risk_desc = "This crossing is dangerous."
        else:
            risk_level = "Extreme"
            risk_desc = "Crossing here would be foolhardy!"
        
        return {
            "name": crossing.name,
            "river": crossing.river_name,
            "condition": condition.value,
            "condition_desc": self._get_condition_description(condition),
            "current_depth_feet": current_depth,
            "current_width_feet": current_width,
            "current_strength": crossing.current_strength,
            "danger_rating": danger,
            "risk_level": risk_level,
            "risk_description": risk_desc,
            "has_ferry": crossing.has_ferry,
            "ferry_cost": crossing.ferry_cost if crossing.has_ferry else 0,
            "has_bridge": crossing.has_bridge,
            "bridge_toll": crossing.bridge_toll if crossing.has_bridge else 0,
        }
    
    def _get_condition_description(self, condition: RiverCondition) -> str:
        """Get descriptive text for river condition."""
        descriptions = {
            RiverCondition.LOW: "The water is low, exposing sandbars and rocks.",
            RiverCondition.NORMAL: "The river flows at its usual level.",
            RiverCondition.HIGH: "Recent rains have swollen the river. It runs swift and high.",
            RiverCondition.FLOOD: "The river is in flood! Brown water races past, carrying debris.",
        }
        return descriptions.get(condition, "")
    
    # =========================================================================
    # Crossing Methods
    # =========================================================================
    
    def get_available_methods(
        self, 
        crossing: RiverCrossingPoint, 
        condition: RiverCondition,
        has_tools: bool,
        money: int
    ) -> List[Tuple[CrossingMethod, bool, str, Dict]]:
        """
        Get available crossing methods with their availability.
        
        Args:
            crossing: The crossing point
            condition: Current condition
            has_tools: Whether party has tools
            money: Available money
        
        Returns:
            List of (method, available, reason, info) tuples
        """
        methods = []
        
        # Ford - always an option but may be inadvisable
        ford_available = True
        ford_reason = ""
        if condition == RiverCondition.FLOOD:
            ford_available = True  # Can attempt but very dangerous
            ford_reason = "EXTREMELY DANGEROUS in flood conditions!"
        methods.append((
            CrossingMethod.FORD,
            ford_available,
            ford_reason,
            METHOD_INFO[CrossingMethod.FORD]
        ))
        
        # Caulk and float - requires tools
        caulk_available = has_tools
        caulk_reason = "" if has_tools else "Requires tools"
        methods.append((
            CrossingMethod.CAULK,
            caulk_available,
            caulk_reason,
            METHOD_INFO[CrossingMethod.CAULK]
        ))
        
        # Ferry - if available and can afford
        if crossing.has_ferry:
            ferry_available = money >= crossing.ferry_cost
            ferry_reason = "" if ferry_available else f"Need ${crossing.ferry_cost}"
            # Ferry may not operate in flood
            if condition == RiverCondition.FLOOD:
                ferry_available = False
                ferry_reason = "Ferry not operating in flood conditions"
            methods.append((
                CrossingMethod.FERRY,
                ferry_available,
                ferry_reason,
                {**METHOD_INFO[CrossingMethod.FERRY], "cost": crossing.ferry_cost}
            ))
        
        # Bridge - if available
        if crossing.has_bridge:
            bridge_available = money >= crossing.bridge_toll
            bridge_reason = "" if bridge_available else f"Need ${crossing.bridge_toll} toll"
            methods.append((
                CrossingMethod.BRIDGE,
                bridge_available,
                bridge_reason,
                {**METHOD_INFO[CrossingMethod.BRIDGE], "cost": crossing.bridge_toll}
            ))
        
        # Wait - always available
        methods.append((
            CrossingMethod.WAIT,
            True,
            "",
            METHOD_INFO[CrossingMethod.WAIT]
        ))
        
        return methods
    
    def attempt_crossing(
        self,
        crossing: RiverCrossingPoint,
        method: CrossingMethod,
        condition: RiverCondition,
        weather: str,
        party_members: List[str],
        supplies: Dict,
        skill_bonus: int = 0
    ) -> CrossingResult:
        """
        Attempt to cross the river using the specified method.
        
        Args:
            crossing: The crossing point
            method: Chosen crossing method
            condition: Current river condition
            weather: Current weather
            party_members: List of party member names
            supplies: Dict of supply types to amounts
            skill_bonus: Bonus from navigation/scouting skill
        
        Returns:
            CrossingResult with outcomes
        """
        details = []
        
        # Handle waiting
        if method == CrossingMethod.WAIT:
            return CrossingResult(
                success=True,
                outcome=CrossingOutcome.CANCELLED,
                method=method,
                time_spent=0,
                message="You decide to wait for better conditions.",
                details=["The party makes camp by the river."]
            )
        
        # Calculate success chance
        base_rate = BASE_SUCCESS_RATES[method]
        condition_mod = CONDITION_MODIFIERS[condition]
        weather_mod = WEATHER_MODIFIERS.get(weather, 1.0)
        skill_mod = 1 + (skill_bonus / 200)  # Up to +50% from skill
        
        success_chance = base_rate * condition_mod * weather_mod * skill_mod
        success_chance = max(0.05, min(0.98, success_chance))  # 5-98% bounds
        
        details.append(f"Attempting to cross via {METHOD_INFO[method]['name'].lower()}...")
        details.append(f"River condition: {condition.value}")
        details.append(f"Estimated success: {int(success_chance * 100)}%")
        
        # Roll for outcome
        roll = random.random()
        
        method_info = METHOD_INFO[method]
        money_spent = method_info["cost"]
        if method == CrossingMethod.FERRY:
            money_spent = crossing.ferry_cost
        elif method == CrossingMethod.BRIDGE:
            money_spent = crossing.bridge_toll
        
        if roll < success_chance:
            # Success!
            return CrossingResult(
                success=True,
                outcome=CrossingOutcome.SUCCESS,
                method=method,
                time_spent=method_info["time_hours"],
                money_spent=money_spent,
                message=f"Successfully crossed the {crossing.river_name}!",
                details=details + ["The crossing went smoothly."]
            )
        
        # Failed crossing - determine severity
        failure_severity = random.random()
        danger_mod = method_info["danger_base"] / 100
        
        # Condition makes failures worse
        if condition == RiverCondition.HIGH:
            failure_severity *= 1.3
        elif condition == RiverCondition.FLOOD:
            failure_severity *= 2.0
        
        supplies_lost = {}
        injuries = []
        deaths = []
        
        if failure_severity < 0.5:
            # Minor loss
            outcome = CrossingOutcome.PARTIAL_LOSS
            
            # Lose some supplies
            for resource, amount in supplies.items():
                if random.random() < 0.3:
                    lost = int(amount * random.uniform(0.1, 0.3))
                    if lost > 0:
                        supplies_lost[resource] = lost
            
            message = f"The crossing was rough. Some supplies were lost to the {crossing.river_name}."
            details.append("Water rushed into the wagon. Some items were swept away.")
        
        elif failure_severity < 0.85:
            # Major loss
            outcome = CrossingOutcome.MAJOR_LOSS
            
            # Lose more supplies
            for resource, amount in supplies.items():
                if random.random() < 0.5:
                    lost = int(amount * random.uniform(0.2, 0.5))
                    if lost > 0:
                        supplies_lost[resource] = lost
            
            # Someone gets injured
            if party_members:
                injured = random.choice(party_members)
                injuries.append(injured)
            
            message = f"Disaster at the {crossing.river_name}! Supplies lost and someone was hurt."
            details.append("The wagon tipped in the current. Frantic moments of chaos followed.")
        
        else:
            # Disaster - possible death
            outcome = CrossingOutcome.DISASTER
            
            # Heavy supply loss
            for resource, amount in supplies.items():
                lost = int(amount * random.uniform(0.4, 0.7))
                if lost > 0:
                    supplies_lost[resource] = lost
            
            # Injury and possible death
            if party_members:
                injured = random.choice(party_members)
                injuries.append(injured)
                
                # Death chance based on conditions
                death_chance = 0.3 if condition == RiverCondition.FLOOD else 0.15
                if random.random() < death_chance:
                    victim = random.choice([m for m in party_members if m != injured] or party_members)
                    deaths.append(victim)
            
            message = f"Catastrophe! The {crossing.river_name} has claimed lives and supplies."
            details.append("The river's fury was merciless. Screams were swallowed by rushing water.")
        
        return CrossingResult(
            success=False,
            outcome=outcome,
            method=method,
            supplies_lost=supplies_lost,
            injuries=injuries,
            deaths=deaths,
            time_spent=method_info["time_hours"],
            money_spent=money_spent,
            message=message,
            details=details
        )
    
    def wait_for_conditions(self, days: int = 1) -> Tuple[bool, str]:
        """
        Wait for river conditions to potentially improve.
        
        Args:
            days: Number of days to wait
        
        Returns:
            Tuple of (conditions_improved, message)
        """
        # 30% chance per day for conditions to improve
        improvement_chance = 1 - (0.7 ** days)
        
        if random.random() < improvement_chance:
            return (True, f"After {days} day(s), the river level has dropped.")
        else:
            return (False, f"After {days} day(s), conditions remain the same.")
    
    # =========================================================================
    # Location Methods
    # =========================================================================
    
    def get_crossing_at_location(self, mile_marker: int, tolerance: int = 10) -> Optional[RiverCrossingPoint]:
        """
        Get a crossing point at or near the given mile marker.
        
        Args:
            mile_marker: Current position
            tolerance: How close to match
        
        Returns:
            RiverCrossingPoint if found, None otherwise
        """
        for crossing in self.crossing_points:
            if abs(crossing.mile_marker - mile_marker) <= tolerance:
                return crossing
        return None
    
    def get_upcoming_crossings(self, current_mile: int, range_miles: int = 100) -> List[RiverCrossingPoint]:
        """
        Get river crossings coming up on the trail.
        
        Args:
            current_mile: Current position
            range_miles: How far ahead to look
        
        Returns:
            List of upcoming crossings
        """
        upcoming = []
        for crossing in self.crossing_points:
            distance = crossing.mile_marker - current_mile
            if 0 < distance <= range_miles:
                upcoming.append(crossing)
        return sorted(upcoming, key=lambda x: x.mile_marker)
    
    # =========================================================================
    # Statistics and History
    # =========================================================================
    
    def record_crossing(self, result: CrossingResult, crossing_id: str):
        """Record a crossing attempt in history."""
        self.crossing_history.append({
            "crossing_id": crossing_id,
            **result.to_dict()
        })
    
    def get_statistics(self) -> Dict:
        """Get crossing statistics."""
        if not self.crossing_history:
            return {
                "total_crossings": 0,
                "successful": 0,
                "success_rate": 0,
                "deaths": 0,
                "supplies_lost": {},
            }
        
        successful = sum(1 for h in self.crossing_history if h["success"])
        deaths = sum(len(h.get("deaths", [])) for h in self.crossing_history)
        
        total_lost = {}
        for h in self.crossing_history:
            for resource, amount in h.get("supplies_lost", {}).items():
                total_lost[resource] = total_lost.get(resource, 0) + amount
        
        return {
            "total_crossings": len(self.crossing_history),
            "successful": successful,
            "success_rate": (successful / len(self.crossing_history)) * 100,
            "deaths": deaths,
            "supplies_lost": total_lost,
        }
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for saving."""
        return {
            "crossing_history": self.crossing_history,
        }
    
    def load_state(self, data: Dict):
        """Load state from dictionary."""
        self.crossing_history = data.get("crossing_history", [])


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate river crossing functionality."""
    print("=" * 50)
    print("RIVER CROSSING SYSTEM DEMO")
    print("=" * 50)
    print()
    
    rcm = RiverCrossingManager()
    
    # Show all crossings
    print(f"Loaded {len(rcm.crossing_points)} river crossings:")
    for crossing in rcm.crossing_points:
        ferry = " [Ferry]" if crossing.has_ferry else ""
        bridge = " [Bridge]" if crossing.has_bridge else ""
        print(f"  Mile {crossing.mile_marker}: {crossing.name}{ferry}{bridge}")
    print()
    
    # Test a specific crossing
    crossing = rcm.crossing_points[4]  # Snake River
    print(f"Testing crossing: {crossing.name}")
    print(f"  River: {crossing.river_name}")
    print(f"  Base depth: {crossing.base_depth} ft")
    print(f"  Current strength: {crossing.current_strength}/10")
    print()
    
    # Test different conditions
    for season in ["spring", "summer", "fall"]:
        recent_weather = ["clear", "rain", "clear"]
        condition = rcm.get_river_condition(crossing, season, recent_weather)
        assessment = rcm.assess_crossing(crossing, condition)
        
        print(f"  {season.title()}: {condition.value}")
        print(f"    Depth: {assessment['current_depth_feet']} ft")
        print(f"    Risk: {assessment['risk_level']}")
    print()
    
    # Test crossing methods
    condition = RiverCondition.HIGH
    print(f"Available methods ({condition.value} water):")
    methods = rcm.get_available_methods(crossing, condition, has_tools=True, money=50)
    for method, available, reason, info in methods:
        status = "✓" if available else f"✗ ({reason})"
        print(f"  {info['name']}: {status}")
        print(f"    {info['description']}")
    print()
    
    # Simulate some crossings
    print("Simulating 5 crossing attempts (ford, high water)...")
    party = ["John", "Mary", "Thomas", "Sarah"]
    supplies = {"food": 100, "ammunition": 30, "clothing": 5}
    
    for i in range(5):
        result = rcm.attempt_crossing(
            crossing=crossing,
            method=CrossingMethod.FORD,
            condition=RiverCondition.HIGH,
            weather="clear",
            party_members=party,
            supplies=supplies.copy(),
            skill_bonus=30
        )
        
        rcm.record_crossing(result, crossing.id)
        
        status = "✓" if result.success else "✗"
        losses = sum(result.supplies_lost.values())
        deaths = len(result.deaths)
        print(f"  {i+1}. [{status}] {result.outcome.value} - Lost: {losses} supplies, {deaths} deaths")
    print()
    
    # Statistics
    print("Crossing statistics:")
    stats = rcm.get_statistics()
    print(f"  Total crossings: {stats['total_crossings']}")
    print(f"  Success rate: {stats['success_rate']:.1f}%")
    print(f"  Total deaths: {stats['deaths']}")
    print(f"  Supplies lost: {stats['supplies_lost']}")
    print()
    
    print("Demo complete!")


if __name__ == "__main__":
    demo()