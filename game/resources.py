"""
resources.py - Resource Management System for The Great Divide Trail

Handles all resource tracking, consumption, decay, and management
for the party's supplies during the journey.
"""

from typing import Dict, Optional, Tuple, List
from enum import Enum
from dataclasses import dataclass, field
import random


# =============================================================================
# Enums and Constants
# =============================================================================

class ResourceType(Enum):
    """Types of resources the party can carry."""
    FOOD = "food"
    WATER = "water"
    AMMUNITION = "ammunition"
    MEDICAL = "medical"
    CLOTHING = "clothing"
    TOOLS = "tools"
    MONEY = "money"


# Resource display names and units
RESOURCE_INFO = {
    ResourceType.FOOD: {"name": "Food", "unit": "lbs", "icon": "🍖"},
    ResourceType.WATER: {"name": "Water", "unit": "gallons", "icon": "💧"},
    ResourceType.AMMUNITION: {"name": "Ammunition", "unit": "rounds", "icon": "🔫"},
    ResourceType.MEDICAL: {"name": "Medical Supplies", "unit": "units", "icon": "💊"},
    ResourceType.CLOTHING: {"name": "Clothing", "unit": "sets", "icon": "🧥"},
    ResourceType.TOOLS: {"name": "Tools", "unit": "kits", "icon": "🔧"},
    ResourceType.MONEY: {"name": "Money", "unit": "dollars", "icon": "💰"},
}

# Daily consumption rates per person
DAILY_CONSUMPTION = {
    ResourceType.FOOD: 2,      # 2 lbs per person per day
    ResourceType.WATER: 1,     # 1 gallon per person per day
}

# Decay rates per day (percentage lost)
DECAY_RATES = {
    ResourceType.FOOD: 0.02,      # 2% food spoilage per day
    ResourceType.WATER: 0.01,     # 1% water loss per day (evaporation/spills)
    ResourceType.CLOTHING: 0.005, # 0.5% clothing degradation
}

# Weather multipliers for decay
WEATHER_DECAY_MULTIPLIERS = {
    "clear": 1.0,
    "cloudy": 1.0,
    "rain": 1.5,
    "storm": 2.0,
    "snow": 0.5,      # Cold preserves food
    "blizzard": 0.5,
    "hot": 2.5,       # Heat spoils food faster
    "cold": 0.5,
}

# Terrain effects on consumption
TERRAIN_CONSUMPTION_MULTIPLIERS = {
    "desert": {"water": 2.0, "food": 1.0},
    "plains": {"water": 1.0, "food": 1.0},
    "mountains": {"water": 1.0, "food": 1.5},  # More calories needed
    "forest": {"water": 0.8, "food": 1.0},     # Can find water
    "tundra": {"water": 0.5, "food": 1.5},     # Snow for water, more food needed
    "river": {"water": 0.5, "food": 1.0},
}


# =============================================================================
# Resource Class
# =============================================================================

@dataclass
class Resource:
    """
    Represents a single resource type with quantity and quality tracking.
    
    Attributes:
        resource_type: The type of resource
        quantity: Current amount
        max_capacity: Maximum carrying capacity
        quality: Quality/condition (0-100, affects effectiveness)
    """
    resource_type: ResourceType
    quantity: float = 0
    max_capacity: float = 1000
    quality: float = 100  # 0-100, affects effectiveness
    
    @property
    def name(self) -> str:
        """Get display name."""
        return RESOURCE_INFO[self.resource_type]["name"]
    
    @property
    def unit(self) -> str:
        """Get unit of measurement."""
        return RESOURCE_INFO[self.resource_type]["unit"]
    
    @property
    def icon(self) -> str:
        """Get display icon."""
        return RESOURCE_INFO[self.resource_type]["icon"]
    
    @property
    def is_empty(self) -> bool:
        """Check if resource is depleted."""
        return self.quantity <= 0
    
    @property
    def is_full(self) -> bool:
        """Check if at max capacity."""
        return self.quantity >= self.max_capacity
    
    @property
    def percentage(self) -> float:
        """Get quantity as percentage of capacity."""
        if self.max_capacity <= 0:
            return 0
        return (self.quantity / self.max_capacity) * 100
    
    def add(self, amount: float) -> float:
        """
        Add to the resource quantity.
        
        Args:
            amount: Amount to add
        
        Returns:
            Actual amount added (may be less if at capacity)
        """
        if amount <= 0:
            return 0
        
        space_available = self.max_capacity - self.quantity
        actual_add = min(amount, space_available)
        self.quantity += actual_add
        
        return actual_add
    
    def remove(self, amount: float) -> float:
        """
        Remove from the resource quantity.
        
        Args:
            amount: Amount to remove
        
        Returns:
            Actual amount removed (may be less if not enough)
        """
        if amount <= 0:
            return 0
        
        actual_remove = min(amount, self.quantity)
        self.quantity -= actual_remove
        
        return actual_remove
    
    def apply_decay(self, rate_multiplier: float = 1.0) -> float:
        """
        Apply daily decay to the resource.
        
        Args:
            rate_multiplier: Multiplier for decay rate (weather, etc.)
        
        Returns:
            Amount lost to decay
        """
        base_rate = DECAY_RATES.get(self.resource_type, 0)
        if base_rate <= 0:
            return 0
        
        effective_rate = base_rate * rate_multiplier
        decay_amount = self.quantity * effective_rate
        
        self.quantity = max(0, self.quantity - decay_amount)
        
        # Quality also degrades slightly
        self.quality = max(0, self.quality - (effective_rate * 10))
        
        return decay_amount
    
    def display_string(self, show_icon: bool = False) -> str:
        """Get formatted display string."""
        icon = f"{self.icon} " if show_icon else ""
        return f"{icon}{self.name}: {int(self.quantity)} {self.unit}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for saving."""
        return {
            "type": self.resource_type.value,
            "quantity": self.quantity,
            "max_capacity": self.max_capacity,
            "quality": self.quality,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Resource':
        """Create from dictionary."""
        resource_type = ResourceType(data["type"])
        return cls(
            resource_type=resource_type,
            quantity=data.get("quantity", 0),
            max_capacity=data.get("max_capacity", 1000),
            quality=data.get("quality", 100),
        )


# =============================================================================
# ResourceManager Class
# =============================================================================

class ResourceManager:
    """
    Manages all resources for a party.
    
    Handles storage, consumption, decay, and tracking of all resource types.
    """
    
    def __init__(self):
        """Initialize resource manager with default capacities."""
        self.resources: Dict[ResourceType, Resource] = {}
        self._initialize_resources()
    
    def _initialize_resources(self):
        """Set up all resource types with default capacities."""
        default_capacities = {
            ResourceType.FOOD: 500,        # 500 lbs max
            ResourceType.WATER: 100,       # 100 gallons max
            ResourceType.AMMUNITION: 200,  # 200 rounds max
            ResourceType.MEDICAL: 50,      # 50 units max
            ResourceType.CLOTHING: 20,     # 20 sets max
            ResourceType.TOOLS: 10,        # 10 kits max
            ResourceType.MONEY: 10000,     # $10,000 max
        }
        
        for resource_type, capacity in default_capacities.items():
            self.resources[resource_type] = Resource(
                resource_type=resource_type,
                quantity=0,
                max_capacity=capacity
            )
    
    # =========================================================================
    # Basic Operations
    # =========================================================================
    
    def get(self, resource_type: ResourceType) -> Resource:
        """Get a resource object."""
        return self.resources.get(resource_type)
    
    def get_quantity(self, resource_type: ResourceType) -> float:
        """Get quantity of a resource."""
        resource = self.resources.get(resource_type)
        return resource.quantity if resource else 0
    
    def add(self, resource_type: ResourceType, amount: float) -> float:
        """Add to a resource."""
        resource = self.resources.get(resource_type)
        if resource:
            return resource.add(amount)
        return 0
    
    def remove(self, resource_type: ResourceType, amount: float) -> float:
        """Remove from a resource."""
        resource = self.resources.get(resource_type)
        if resource:
            return resource.remove(amount)
        return 0
    
    def has_enough(self, resource_type: ResourceType, amount: float) -> bool:
        """Check if there's enough of a resource."""
        return self.get_quantity(resource_type) >= amount
    
    def set_quantity(self, resource_type: ResourceType, amount: float):
        """Set a resource to a specific quantity."""
        resource = self.resources.get(resource_type)
        if resource:
            resource.quantity = max(0, min(amount, resource.max_capacity))
    
    # =========================================================================
    # Batch Operations
    # =========================================================================
    
    def add_multiple(self, resources: Dict[ResourceType, float]) -> Dict[ResourceType, float]:
        """
        Add multiple resources at once.
        
        Args:
            resources: Dict mapping resource type to amount
        
        Returns:
            Dict of actual amounts added
        """
        result = {}
        for resource_type, amount in resources.items():
            result[resource_type] = self.add(resource_type, amount)
        return result
    
    def remove_multiple(self, resources: Dict[ResourceType, float]) -> Tuple[bool, Dict[ResourceType, float]]:
        """
        Remove multiple resources at once.
        
        Args:
            resources: Dict mapping resource type to amount
        
        Returns:
            Tuple of (success, dict of actual amounts removed)
        """
        # First check if we have enough of everything
        for resource_type, amount in resources.items():
            if not self.has_enough(resource_type, amount):
                return (False, {})
        
        # Remove all
        result = {}
        for resource_type, amount in resources.items():
            result[resource_type] = self.remove(resource_type, amount)
        
        return (True, result)
    
    def set_starting_supplies(self, party_size: int, difficulty: str = "normal"):
        """
        Set initial supplies based on party size and difficulty.
        
        Args:
            party_size: Number of party members
            difficulty: 'easy', 'normal', or 'hard'
        """
        multipliers = {
            "easy": 1.5,
            "normal": 1.0,
            "hard": 0.7,
        }
        mult = multipliers.get(difficulty, 1.0)
        
        # Base supplies scale with party size
        base_supplies = {
            ResourceType.FOOD: 100 * party_size,
            ResourceType.WATER: 20 * party_size,
            ResourceType.AMMUNITION: 50,
            ResourceType.MEDICAL: 10,
            ResourceType.CLOTHING: party_size + 2,
            ResourceType.TOOLS: 3,
            ResourceType.MONEY: 200,
        }
        
        for resource_type, amount in base_supplies.items():
            self.set_quantity(resource_type, int(amount * mult))
    
    # =========================================================================
    # Consumption
    # =========================================================================
    
    def calculate_daily_consumption(
        self, 
        party_size: int, 
        terrain: str = "plains",
        rationing: str = "normal"
    ) -> Dict[ResourceType, float]:
        """
        Calculate daily resource consumption.
        
        Args:
            party_size: Number of living party members
            terrain: Current terrain type
            rationing: 'filling', 'normal', 'meager', or 'starving'
        
        Returns:
            Dict of resource type to consumption amount
        """
        ration_multipliers = {
            "filling": 1.5,
            "normal": 1.0,
            "meager": 0.5,
            "starving": 0.25,
        }
        ration_mult = ration_multipliers.get(rationing, 1.0)
        
        terrain_mults = TERRAIN_CONSUMPTION_MULTIPLIERS.get(terrain, {})
        
        consumption = {}
        
        for resource_type, base_rate in DAILY_CONSUMPTION.items():
            terrain_mult = terrain_mults.get(resource_type.value, 1.0)
            daily = base_rate * party_size * ration_mult * terrain_mult
            consumption[resource_type] = daily
        
        return consumption
    
    def consume_daily(
        self, 
        party_size: int, 
        terrain: str = "plains",
        rationing: str = "normal"
    ) -> Dict:
        """
        Consume daily resources and return results.
        
        Args:
            party_size: Number of living party members
            terrain: Current terrain type
            rationing: Ration level
        
        Returns:
            Dict with consumption results and any shortages
        """
        consumption = self.calculate_daily_consumption(party_size, terrain, rationing)
        
        results = {
            "consumed": {},
            "shortages": {},
            "warnings": [],
        }
        
        for resource_type, needed in consumption.items():
            available = self.get_quantity(resource_type)
            actual = self.remove(resource_type, needed)
            
            results["consumed"][resource_type] = actual
            
            if actual < needed:
                shortage = needed - actual
                results["shortages"][resource_type] = shortage
                results["warnings"].append(
                    f"Not enough {RESOURCE_INFO[resource_type]['name'].lower()}! "
                    f"Needed {needed:.1f}, had {available:.1f}"
                )
        
        # Check for low supplies
        for resource_type in [ResourceType.FOOD, ResourceType.WATER, ResourceType.AMMUNITION]:
            quantity = self.get_quantity(resource_type)
            resource = self.get(resource_type)
            if quantity > 0 and resource.percentage < 20:
                results["warnings"].append(
                    f"{resource.name} supplies are running low ({int(quantity)} {resource.unit} remaining)"
                )
        
        return results
    
    # =========================================================================
    # Decay
    # =========================================================================
    
    def apply_daily_decay(self, weather: str = "clear") -> Dict[ResourceType, float]:
        """
        Apply daily decay to all perishable resources.
        
        Args:
            weather: Current weather condition
        
        Returns:
            Dict of resource type to amount lost
        """
        weather_mult = WEATHER_DECAY_MULTIPLIERS.get(weather, 1.0)
        
        losses = {}
        for resource_type in DECAY_RATES.keys():
            resource = self.resources.get(resource_type)
            if resource and resource.quantity > 0:
                loss = resource.apply_decay(weather_mult)
                if loss > 0:
                    losses[resource_type] = loss
        
        return losses
    
    # =========================================================================
    # Status Checks
    # =========================================================================
    
    def get_status(self) -> Dict:
        """
        Get overall resource status.
        
        Returns:
            Dict with status information
        """
        status = {
            "critical": [],  # Resources at 0
            "low": [],       # Resources below 20%
            "adequate": [],  # Resources 20-50%
            "good": [],      # Resources above 50%
        }
        
        for resource_type, resource in self.resources.items():
            if resource.is_empty:
                status["critical"].append(resource_type)
            elif resource.percentage < 20:
                status["low"].append(resource_type)
            elif resource.percentage < 50:
                status["adequate"].append(resource_type)
            else:
                status["good"].append(resource_type)
        
        return status
    
    def days_of_supplies(self, party_size: int, rationing: str = "normal") -> Dict[ResourceType, int]:
        """
        Calculate how many days of supplies remain.
        
        Args:
            party_size: Number of party members
            rationing: Current rationing level
        
        Returns:
            Dict of resource type to days remaining
        """
        consumption = self.calculate_daily_consumption(party_size, rationing=rationing)
        
        days = {}
        for resource_type, daily in consumption.items():
            if daily > 0:
                quantity = self.get_quantity(resource_type)
                days[resource_type] = int(quantity / daily)
            else:
                days[resource_type] = 999  # Effectively unlimited
        
        return days
    
    # =========================================================================
    # Display
    # =========================================================================
    
    def get_display_dict(self) -> Dict[str, str]:
        """Get dictionary suitable for UI status display."""
        display = {}
        
        # Priority order for display
        priority = [
            ResourceType.FOOD,
            ResourceType.WATER,
            ResourceType.AMMUNITION,
            ResourceType.MEDICAL,
        ]
        
        for resource_type in priority:
            resource = self.resources.get(resource_type)
            if resource:
                display[resource.name] = f"{int(resource.quantity)} {resource.unit}"
        
        return display
    
    def get_full_display(self) -> str:
        """Get full resource display string."""
        lines = []
        for resource in self.resources.values():
            quality_str = f" (Quality: {int(resource.quality)}%)" if resource.quality < 100 else ""
            lines.append(f"  {resource.display_string()}{quality_str}")
        return "\n".join(lines)
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for saving."""
        return {
            "resources": {
                rt.value: r.to_dict() for rt, r in self.resources.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ResourceManager':
        """Create from dictionary."""
        manager = cls()
        
        for type_str, resource_data in data.get("resources", {}).items():
            resource = Resource.from_dict(resource_data)
            manager.resources[resource.resource_type] = resource
        
        return manager


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate resource system functionality."""
    print("=" * 50)
    print("RESOURCE SYSTEM DEMO")
    print("=" * 50)
    print()
    
    # Create resource manager
    rm = ResourceManager()
    
    # Set starting supplies for a party of 4
    rm.set_starting_supplies(party_size=4, difficulty="normal")
    
    print("Starting supplies (party of 4, normal difficulty):")
    print(rm.get_full_display())
    print()
    
    # Show days of supplies
    days = rm.days_of_supplies(party_size=4)
    print("Days of supplies remaining:")
    for resource_type, d in days.items():
        if d < 999:
            print(f"  {RESOURCE_INFO[resource_type]['name']}: {d} days")
    print()
    
    # Simulate daily consumption
    print("Simulating 5 days of travel...")
    for day in range(1, 6):
        results = rm.consume_daily(party_size=4, terrain="mountains", rationing="normal")
        decay = rm.apply_daily_decay(weather="clear")
        
        print(f"  Day {day}:")
        print(f"    Food consumed: {results['consumed'].get(ResourceType.FOOD, 0):.1f} lbs")
        print(f"    Water consumed: {results['consumed'].get(ResourceType.WATER, 0):.1f} gallons")
        if decay:
            print(f"    Decay losses: {sum(decay.values()):.1f}")
        for warning in results["warnings"]:
            print(f"    ⚠ {warning}")
    print()
    
    print("Supplies after 5 days:")
    print(rm.get_full_display())
    print()
    
    # Test hunting - add food
    print("Successful hunt! Adding 50 lbs of meat...")
    added = rm.add(ResourceType.FOOD, 50)
    print(f"  Added {added} lbs (capacity limit may apply)")
    print(f"  Food now: {rm.get_quantity(ResourceType.FOOD):.1f} lbs")
    print()
    
    # Test trading
    print("Trading: Buying supplies...")
    rm.add(ResourceType.MEDICAL, 5)
    rm.add(ResourceType.AMMUNITION, 20)
    rm.remove(ResourceType.MONEY, 50)
    print(f"  Medical: {rm.get_quantity(ResourceType.MEDICAL):.0f} units")
    print(f"  Ammo: {rm.get_quantity(ResourceType.AMMUNITION):.0f} rounds")
    print(f"  Money: ${rm.get_quantity(ResourceType.MONEY):.0f}")
    print()
    
    # Status check
    status = rm.get_status()
    print("Resource status:")
    if status["critical"]:
        print(f"  CRITICAL: {[RESOURCE_INFO[r]['name'] for r in status['critical']]}")
    if status["low"]:
        print(f"  LOW: {[RESOURCE_INFO[r]['name'] for r in status['low']]}")
    print()
    
    # Serialization test
    print("Serialization test:")
    data = rm.to_dict()
    restored = ResourceManager.from_dict(data)
    print(f"  Original food: {rm.get_quantity(ResourceType.FOOD):.1f}")
    print(f"  Restored food: {restored.get_quantity(ResourceType.FOOD):.1f}")
    print()
    
    print("Demo complete!")


if __name__ == "__main__":
    demo()