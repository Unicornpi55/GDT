"""
equipment.py - Equipment and Inventory System for The Great Divide Trail

Handles individual equipment items with durability tracking, repair mechanics,
and integration with hunting, camping, and travel systems.
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import random


# =============================================================================
# Enums and Constants
# =============================================================================

class EquipmentCategory(Enum):
    """Categories of equipment."""
    WEAPON = "weapon"
    CAMPING = "camping"
    COOKING = "cooking"
    TOOLS = "tools"
    CLOTHING = "clothing"
    TRANSPORT = "transport"


class EquipmentRarity(Enum):
    """Rarity/quality tiers."""
    POOR = "poor"
    COMMON = "common"
    QUALITY = "quality"
    EXCELLENT = "excellent"


class EquipmentCondition(Enum):
    """Condition states based on durability."""
    BROKEN = "broken"          # 0% durability
    POOR = "poor"              # 1-25%
    WORN = "worn"              # 26-50%
    GOOD = "good"              # 51-75%
    EXCELLENT = "excellent"    # 76-100%


# Equipment definitions with base stats
EQUIPMENT_TYPES = {
    # Weapons
    "flintlock_rifle": {
        "name": "Flintlock Rifle",
        "category": EquipmentCategory.WEAPON,
        "description": "Standard hunting rifle, reliable but requires maintenance",
        "base_durability": 100,
        "degradation_rate": 2,      # Loses 2 durability per use
        "bonuses": {"hunting": 15, "accuracy": 10},
        "base_value": 40,
        "weight": 9,
        "repair_difficulty": 40,
    },
    "kentucky_rifle": {
        "name": "Kentucky Long Rifle",
        "category": EquipmentCategory.WEAPON,
        "description": "High-quality rifle with excellent accuracy",
        "base_durability": 120,
        "degradation_rate": 1.5,
        "bonuses": {"hunting": 25, "accuracy": 20},
        "base_value": 75,
        "weight": 8,
        "repair_difficulty": 50,
    },
    "smoothbore_musket": {
        "name": "Smoothbore Musket",
        "category": EquipmentCategory.WEAPON,
        "description": "Cheap but inaccurate military surplus",
        "base_durability": 80,
        "degradation_rate": 3,
        "bonuses": {"hunting": 5, "accuracy": -5},
        "base_value": 20,
        "weight": 10,
        "repair_difficulty": 30,
    },
    "bow": {
        "name": "Hunting Bow",
        "category": EquipmentCategory.WEAPON,
        "description": "Silent hunting weapon, no ammunition needed",
        "base_durability": 60,
        "degradation_rate": 1,
        "bonuses": {"hunting": 10, "stealth": 20},
        "base_value": 15,
        "weight": 3,
        "repair_difficulty": 25,
        "no_ammo_required": True,
    },
    
    # Camping Gear
    "canvas_tent": {
        "name": "Canvas Tent",
        "category": EquipmentCategory.CAMPING,
        "description": "Sturdy tent, protects from weather",
        "base_durability": 100,
        "degradation_rate": 0.5,    # Slow wear
        "bonuses": {"weather_protection": 50, "morale": 5},
        "base_value": 25,
        "weight": 15,
        "repair_difficulty": 20,
        "capacity": 4,  # Number of people
    },
    "leather_tent": {
        "name": "Leather Tent",
        "category": EquipmentCategory.CAMPING,
        "description": "Durable leather tent, excellent protection",
        "base_durability": 150,
        "degradation_rate": 0.3,
        "bonuses": {"weather_protection": 70, "morale": 10},
        "base_value": 50,
        "weight": 20,
        "repair_difficulty": 35,
        "capacity": 6,
    },
    "bedroll": {
        "name": "Bedroll",
        "category": EquipmentCategory.CAMPING,
        "description": "Simple sleeping gear",
        "base_durability": 80,
        "degradation_rate": 0.3,
        "bonuses": {"rest_quality": 10},
        "base_value": 5,
        "weight": 3,
        "repair_difficulty": 10,
    },
    
    # Cooking Equipment
    "iron_pot": {
        "name": "Iron Cooking Pot",
        "category": EquipmentCategory.COOKING,
        "description": "Essential for preparing meals",
        "base_durability": 200,
        "degradation_rate": 0.2,
        "bonuses": {"food_quality": 15, "morale": 5},
        "base_value": 10,
        "weight": 8,
        "repair_difficulty": 40,
    },
    "dutch_oven": {
        "name": "Dutch Oven",
        "category": EquipmentCategory.COOKING,
        "description": "Versatile cast iron cookware",
        "base_durability": 250,
        "degradation_rate": 0.1,
        "bonuses": {"food_quality": 25, "morale": 10},
        "base_value": 20,
        "weight": 12,
        "repair_difficulty": 50,
    },
    "tin_cups": {
        "name": "Tin Cups",
        "category": EquipmentCategory.COOKING,
        "description": "Set of drinking cups",
        "base_durability": 100,
        "degradation_rate": 0.1,
        "bonuses": {"morale": 3},
        "base_value": 3,
        "weight": 2,
        "repair_difficulty": 15,
    },
    
    # Tools
    "repair_kit": {
        "name": "Repair Kit",
        "category": EquipmentCategory.TOOLS,
        "description": "Tools and materials for repairs",
        "base_durability": 100,
        "degradation_rate": 1,      # Consumed when used
        "bonuses": {"repair_bonus": 30},
        "base_value": 20,
        "weight": 5,
        "repair_difficulty": 0,     # Can't repair itself
        "consumable": True,
    },
    "axe": {
        "name": "Woodcutter's Axe",
        "category": EquipmentCategory.TOOLS,
        "description": "Essential for firewood and construction",
        "base_durability": 150,
        "degradation_rate": 0.5,
        "bonuses": {"wood_gathering": 50, "construction": 20},
        "base_value": 12,
        "weight": 6,
        "repair_difficulty": 30,
    },
    "shovel": {
        "name": "Shovel",
        "category": EquipmentCategory.TOOLS,
        "description": "Digging and excavation",
        "base_durability": 120,
        "degradation_rate": 0.4,
        "bonuses": {"excavation": 40},
        "base_value": 8,
        "weight": 7,
        "repair_difficulty": 25,
    },
    "rope": {
        "name": "Hemp Rope (50ft)",
        "category": EquipmentCategory.TOOLS,
        "description": "Multipurpose rope for climbing and hauling",
        "base_durability": 80,
        "degradation_rate": 0.3,
        "bonuses": {"climbing": 30, "hauling": 20},
        "base_value": 5,
        "weight": 4,
        "repair_difficulty": 20,
    },
    
    # Clothing/Armor
    "leather_coat": {
        "name": "Leather Coat",
        "category": EquipmentCategory.CLOTHING,
        "description": "Durable coat, protects from cold and injury",
        "base_durability": 100,
        "degradation_rate": 0.4,
        "bonuses": {"cold_resistance": 25, "injury_resistance": 10},
        "base_value": 15,
        "weight": 5,
        "repair_difficulty": 25,
    },
    "wool_blanket": {
        "name": "Wool Blanket",
        "category": EquipmentCategory.CLOTHING,
        "description": "Warm blanket for cold nights",
        "base_durability": 80,
        "degradation_rate": 0.2,
        "bonuses": {"cold_resistance": 15, "rest_quality": 10},
        "base_value": 8,
        "weight": 3,
        "repair_difficulty": 15,
    },
    "fur_hat": {
        "name": "Fur Hat",
        "category": EquipmentCategory.CLOTHING,
        "description": "Keeps head warm in freezing weather",
        "base_durability": 60,
        "degradation_rate": 0.2,
        "bonuses": {"cold_resistance": 10},
        "base_value": 5,
        "weight": 1,
        "repair_difficulty": 10,
    },
    
    # Transport
    "wagon": {
        "name": "Covered Wagon",
        "category": EquipmentCategory.TRANSPORT,
        "description": "Main transport for supplies",
        "base_durability": 200,
        "degradation_rate": 0.8,
        "bonuses": {"cargo_capacity": 500, "travel_speed": -5},
        "base_value": 100,
        "weight": 0,  # Not carried, is the vehicle
        "repair_difficulty": 60,
        "critical": True,  # Cannot continue without it
    },
    "pack_horse": {
        "name": "Pack Horse",
        "category": EquipmentCategory.TRANSPORT,
        "description": "Carries additional supplies",
        "base_durability": 100,  # Horse health
        "degradation_rate": 0.1,
        "bonuses": {"cargo_capacity": 200, "travel_speed": 5},
        "base_value": 50,
        "weight": 0,
        "repair_difficulty": 0,  # Heals naturally
        "living": True,
    },
}

# Rarity modifiers
RARITY_MODIFIERS = {
    EquipmentRarity.POOR: {
        "durability_mult": 0.6,
        "bonus_mult": 0.7,
        "value_mult": 0.5,
        "degradation_mult": 1.5,
    },
    EquipmentRarity.COMMON: {
        "durability_mult": 1.0,
        "bonus_mult": 1.0,
        "value_mult": 1.0,
        "degradation_mult": 1.0,
    },
    EquipmentRarity.QUALITY: {
        "durability_mult": 1.3,
        "bonus_mult": 1.2,
        "value_mult": 1.5,
        "degradation_mult": 0.8,
    },
    EquipmentRarity.EXCELLENT: {
        "durability_mult": 1.6,
        "bonus_mult": 1.5,
        "value_mult": 2.5,
        "degradation_mult": 0.6,
    },
}


# =============================================================================
# Equipment Item Class
# =============================================================================

@dataclass
class EquipmentItem:
    """Represents a single equipment item with durability."""
    
    item_type: str
    rarity: EquipmentRarity = EquipmentRarity.COMMON
    current_durability: float = 100
    max_durability: float = 100
    is_equipped: bool = True
    times_repaired: int = 0
    
    def __post_init__(self):
        """Initialize with proper max durability based on type and rarity."""
        if self.item_type not in EQUIPMENT_TYPES:
            raise ValueError(f"Unknown equipment type: {self.item_type}")
        
        base_data = EQUIPMENT_TYPES[self.item_type]
        rarity_mods = RARITY_MODIFIERS[self.rarity]
        
        self.max_durability = base_data["base_durability"] * rarity_mods["durability_mult"]
        
        # If current durability wasn't set, start at max
        if self.current_durability == 100:
            self.current_durability = self.max_durability
    
    @property
    def data(self) -> Dict:
        """Get base equipment data."""
        return EQUIPMENT_TYPES[self.item_type]
    
    @property
    def name(self) -> str:
        """Get display name."""
        base_name = self.data["name"]
        if self.rarity != EquipmentRarity.COMMON:
            return f"{self.rarity.value.title()} {base_name}"
        return base_name
    
    @property
    def durability_percentage(self) -> float:
        """Get durability as percentage."""
        if self.max_durability <= 0:
            return 0
        return (self.current_durability / self.max_durability) * 100
    
    @property
    def condition(self) -> EquipmentCondition:
        """Get condition based on durability."""
        pct = self.durability_percentage
        if pct <= 0:
            return EquipmentCondition.BROKEN
        elif pct <= 25:
            return EquipmentCondition.POOR
        elif pct <= 50:
            return EquipmentCondition.WORN
        elif pct <= 75:
            return EquipmentCondition.GOOD
        else:
            return EquipmentCondition.EXCELLENT
    
    @property
    def is_broken(self) -> bool:
        """Check if item is broken."""
        return self.current_durability <= 0
    
    @property
    def is_usable(self) -> bool:
        """Check if item can be used."""
        return self.current_durability > 0 and self.is_equipped
    
    def get_effective_bonuses(self) -> Dict[str, float]:
        """Get bonuses adjusted for condition and rarity."""
        if self.is_broken:
            return {}
        
        base_bonuses = self.data.get("bonuses", {})
        rarity_mult = RARITY_MODIFIERS[self.rarity]["bonus_mult"]
        
        # Condition penalty (broken = 0%, poor = 50%, worn = 70%, good = 85%, excellent = 100%)
        condition_mult = {
            EquipmentCondition.BROKEN: 0.0,
            EquipmentCondition.POOR: 0.5,
            EquipmentCondition.WORN: 0.7,
            EquipmentCondition.GOOD: 0.85,
            EquipmentCondition.EXCELLENT: 1.0,
        }[self.condition]
        
        effective = {}
        for bonus_type, value in base_bonuses.items():
            effective[bonus_type] = value * rarity_mult * condition_mult
        
        return effective
    
    def degrade(self, usage_intensity: float = 1.0) -> float:
        """
        Apply durability loss from use.
        
        Args:
            usage_intensity: Multiplier for degradation (1.0 = normal use)
        
        Returns:
            Durability lost
        """
        if self.is_broken:
            return 0
        
        base_rate = self.data["degradation_rate"]
        rarity_mult = RARITY_MODIFIERS[self.rarity]["degradation_mult"]
        
        # Items degrade faster as they get more worn
        wear_penalty = 1.0
        if self.durability_percentage < 50:
            wear_penalty = 1.2
        if self.durability_percentage < 25:
            wear_penalty = 1.5
        
        loss = base_rate * rarity_mult * usage_intensity * wear_penalty
        
        old_durability = self.current_durability
        self.current_durability = max(0, self.current_durability - loss)
        
        return old_durability - self.current_durability
    
    def repair(self, amount: float, has_repair_kit: bool = False, mechanic_bonus: int = 0) -> Tuple[float, bool]:
        """
        Repair the item.
        
        Args:
            amount: Base repair amount
            has_repair_kit: Whether a repair kit is being used
            mechanic_bonus: Bonus from mechanic role
        
        Returns:
            Tuple of (amount_repaired, success)
        """
        if self.current_durability >= self.max_durability:
            return (0, False)
        
        # Calculate repair difficulty
        difficulty = self.data["repair_difficulty"]
        skill = 50 + mechanic_bonus + (30 if has_repair_kit else 0)
        
        # Success chance
        success_chance = min(95, max(10, skill - difficulty + 50))
        success = random.randint(1, 100) <= success_chance
        
        if not success:
            # Failed repair might cause damage
            if random.random() < 0.1:  # 10% chance
                damage = random.randint(5, 15)
                self.current_durability = max(0, self.current_durability - damage)
                return (-damage, False)
            return (0, False)
        
        # Successful repair
        repair_mult = 1.0
        if has_repair_kit:
            repair_mult *= 1.5
        
        # Quality degrades with repeated repairs
        quality_penalty = 1.0 - (self.times_repaired * 0.05)
        quality_penalty = max(0.5, quality_penalty)
        
        actual_repair = amount * repair_mult * quality_penalty
        
        old_durability = self.current_durability
        self.current_durability = min(self.max_durability, self.current_durability + actual_repair)
        
        self.times_repaired += 1
        
        return (self.current_durability - old_durability, True)
    
    def get_value(self) -> int:
        """Calculate current value based on condition."""
        base_value = self.data["base_value"]
        rarity_mult = RARITY_MODIFIERS[self.rarity]["value_mult"]
        
        # Value decreases with wear
        condition_mult = self.durability_percentage / 100
        
        return int(base_value * rarity_mult * condition_mult)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for saving."""
        return {
            "item_type": self.item_type,
            "rarity": self.rarity.value,
            "current_durability": self.current_durability,
            "max_durability": self.max_durability,
            "is_equipped": self.is_equipped,
            "times_repaired": self.times_repaired,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EquipmentItem':
        """Create from dictionary."""
        rarity = EquipmentRarity(data.get("rarity", "common"))
        return cls(
            item_type=data["item_type"],
            rarity=rarity,
            current_durability=data.get("current_durability", 100),
            max_durability=data.get("max_durability", 100),
            is_equipped=data.get("is_equipped", True),
            times_repaired=data.get("times_repaired", 0),
        )
    
    def __str__(self) -> str:
        """String representation."""
        condition_icon = {
            EquipmentCondition.BROKEN: "✗",
            EquipmentCondition.POOR: "▼",
            EquipmentCondition.WORN: "▽",
            EquipmentCondition.GOOD: "○",
            EquipmentCondition.EXCELLENT: "●",
        }[self.condition]
        
        return f"{condition_icon} {self.name} [{self.durability_percentage:.0f}%] ({self.condition.value})"


# =============================================================================
# Equipment Manager Class
# =============================================================================

class EquipmentManager:
    """
    Manages all equipment for the party.
    """
    
    def __init__(self):
        """Initialize equipment manager."""
        self.equipment: List[EquipmentItem] = []
        self.auto_equip_best = True
    
    # =========================================================================
    # Adding/Removing Equipment
    # =========================================================================
    
    def add_equipment(self, item_type: str, rarity: EquipmentRarity = EquipmentRarity.COMMON) -> EquipmentItem:
        """
        Add a new equipment item.
        
        Args:
            item_type: Type of equipment
            rarity: Quality/rarity tier
        
        Returns:
            The created EquipmentItem
        """
        item = EquipmentItem(item_type=item_type, rarity=rarity)
        self.equipment.append(item)
        
        if self.auto_equip_best:
            self._auto_equip_category(item.data["category"])
        
        return item
    
    def remove_equipment(self, item: EquipmentItem) -> bool:
        """
        Remove an equipment item.
        
        Args:
            item: Item to remove
        
        Returns:
            True if removed
        """
        if item in self.equipment:
            self.equipment.remove(item)
            return True
        return False
    
    def _auto_equip_category(self, category: EquipmentCategory):
        """Automatically equip best items in a category."""
        items = [e for e in self.equipment if e.data["category"] == category]
        
        if not items:
            return
        
        # Sort by effective value (durability + bonuses)
        items.sort(key=lambda x: x.durability_percentage + sum(x.get_effective_bonuses().values()), reverse=True)
        
        # Equip best, unequip others
        for i, item in enumerate(items):
            item.is_equipped = (i == 0)
    
    # =========================================================================
    # Queries
    # =========================================================================
    
    def get_equipped(self, category: EquipmentCategory = None) -> List[EquipmentItem]:
        """Get all equipped items, optionally filtered by category."""
        equipped = [e for e in self.equipment if e.is_equipped and e.is_usable]
        
        if category:
            equipped = [e for e in equipped if e.data["category"] == category]
        
        return equipped
    
    def get_by_category(self, category: EquipmentCategory) -> List[EquipmentItem]:
        """Get all items in a category."""
        return [e for e in self.equipment if e.data["category"] == category]
    
    def get_broken_items(self) -> List[EquipmentItem]:
        """Get all broken items."""
        return [e for e in self.equipment if e.is_broken]
    
    def get_worn_items(self, threshold: float = 50.0) -> List[EquipmentItem]:
        """Get items below durability threshold."""
        return [e for e in self.equipment if 0 < e.durability_percentage < threshold]
    
    def has_usable(self, item_type: str) -> bool:
        """Check if party has a usable item of a type."""
        for item in self.equipment:
            if item.item_type == item_type and item.is_usable:
                return True
        return False
    
    def get_best_weapon(self) -> Optional[EquipmentItem]:
        """Get the best usable weapon."""
        weapons = [e for e in self.equipment if e.data["category"] == EquipmentCategory.WEAPON and e.is_usable]
        
        if not weapons:
            return None
        
        # Sort by hunting bonus
        weapons.sort(key=lambda x: x.get_effective_bonuses().get("hunting", 0), reverse=True)
        return weapons[0]
    
    # =========================================================================
    # Bonus Calculations
    # =========================================================================
    
    def get_total_bonus(self, bonus_type: str) -> float:
        """Get total bonus of a type from all equipped items."""
        total = 0
        for item in self.get_equipped():
            bonuses = item.get_effective_bonuses()
            total += bonuses.get(bonus_type, 0)
        return total
    
    def get_party_bonuses(self) -> Dict[str, float]:
        """Get all active bonuses."""
        bonuses = {}
        
        for item in self.get_equipped():
            for bonus_type, value in item.get_effective_bonuses().items():
                bonuses[bonus_type] = bonuses.get(bonus_type, 0) + value
        
        return bonuses
    
    # =========================================================================
    # Maintenance
    # =========================================================================
    
    def degrade_all(self, usage_dict: Dict[EquipmentCategory, float] = None) -> Dict:
        """
        Apply daily wear to all equipped items.
        
        Args:
            usage_dict: Dict mapping category to usage intensity
        
        Returns:
            Dict with degradation results
        """
        if usage_dict is None:
            usage_dict = {}
        
        results = {
            "degraded": [],
            "broken": [],
            "warnings": [],
        }
        
        for item in self.get_equipped():
            category = item.data["category"]
            intensity = usage_dict.get(category, 1.0)
            
            old_condition = item.condition
            loss = item.degrade(intensity)
            
            if loss > 0:
                results["degraded"].append({
                    "item": item.name,
                    "loss": loss,
                    "new_durability": item.durability_percentage,
                })
                
                # Check if condition changed
                if item.condition != old_condition:
                    if item.is_broken:
                        results["broken"].append(item.name)
                    elif item.condition == EquipmentCondition.POOR:
                        results["warnings"].append(f"{item.name} is in poor condition!")
                    elif item.condition == EquipmentCondition.WORN:
                        results["warnings"].append(f"{item.name} is getting worn.")
        
        return results
    
    def repair_item(self, item: EquipmentItem, repair_amount: float = 50, 
                   use_repair_kit: bool = False, mechanic_bonus: int = 0) -> Dict:
        """
        Repair a specific item.
        
        Args:
            item: Item to repair
            repair_amount: Base repair amount
            use_repair_kit: Whether to use a repair kit
            mechanic_bonus: Bonus from mechanic role
        
        Returns:
            Dict with repair results
        """
        repaired, success = item.repair(repair_amount, use_repair_kit, mechanic_bonus)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully repaired {item.name}",
                "amount": repaired,
                "new_durability": item.durability_percentage,
                "used_kit": use_repair_kit,
            }
        else:
            if repaired < 0:
                return {
                    "success": False,
                    "message": f"Repair failed and damaged {item.name}!",
                    "amount": repaired,
                    "new_durability": item.durability_percentage,
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to repair {item.name}",
                    "amount": 0,
                    "new_durability": item.durability_percentage,
                }
    
    def repair_all_worn(self, threshold: float = 75.0, **repair_kwargs) -> Dict:
        """
        Attempt to repair all items below threshold.
        
        Args:
            threshold: Repair items below this durability %
            **repair_kwargs: Passed to repair_item
        
        Returns:
            Dict with results
        """
        results = {
            "repaired": [],
            "failed": [],
            "skipped": [],
        }
        
        for item in self.equipment:
            if item.is_broken or item.durability_percentage < threshold:
                result = self.repair_item(item, **repair_kwargs)
                
                if result["success"]:
                    results["repaired"].append(result)
                else:
                    results["failed"].append(result)
            else:
                results["skipped"].append(item.name)
        
        return results
    
    # =========================================================================
    # Special Checks
    # =========================================================================
    
    def check_critical_equipment(self) -> Tuple[bool, List[str]]:
        """
        Check if critical equipment is functional.
        
        Returns:
            Tuple of (all_ok, list of critical issues)
        """
        issues = []
        
        for item in self.equipment:
            if item.data.get("critical", False) and item.is_broken:
                issues.append(f"CRITICAL: {item.name} is broken!")
        
        return (len(issues) == 0, issues)
    
    def get_weapon_for_hunting(self) -> Optional[EquipmentItem]:
        """Get best weapon for hunting, considering ammo requirements."""
        weapons = self.get_equipped(EquipmentCategory.WEAPON)
        
        if not weapons:
            return None
        
        # Prefer weapons with hunting bonus
        weapons.sort(key=lambda x: x.get_effective_bonuses().get("hunting", 0), reverse=True)
        return weapons[0]
    
    # =========================================================================
    # Display
    # =========================================================================
    
    def get_inventory_display(self, category: EquipmentCategory = None) -> str:
        """Get formatted inventory display."""
        items = self.equipment if category is None else self.get_by_category(category)
        
        if not items:
            return "No equipment"
        
        lines = []
        for item in sorted(items, key=lambda x: (x.data["category"].value, -x.durability_percentage)):
            equipped = "[E] " if item.is_equipped else "    "
            lines.append(f"{equipped}{item}")
        
        return "\n".join(lines)
    
    def get_status_summary(self) -> Dict:
        """Get equipment status summary."""
        return {
            "total_items": len(self.equipment),
            "equipped": len(self.get_equipped()),
            "broken": len(self.get_broken_items()),
            "worn": len(self.get_worn_items(50)),
            "excellent": len([e for e in self.equipment if e.condition == EquipmentCondition.EXCELLENT]),
        }
    
    # =========================================================================
    # Starting Equipment
    # =========================================================================
    
    def set_starting_equipment(self, party_size: int, difficulty: str = "normal"):
        """
        Set up starting equipment based on party size and difficulty.
        
        Args:
            party_size: Number of party members
            difficulty: 'easy', 'normal', or 'hard'
        """
        self.equipment.clear()
        
        # Rarity distributions by difficulty
        weapon_rarity = {
            "easy": EquipmentRarity.QUALITY,
            "normal": EquipmentRarity.COMMON,
            "hard": EquipmentRarity.POOR,
        }.get(difficulty, EquipmentRarity.COMMON)
        
        # Essential equipment
        self.add_equipment("wagon", EquipmentRarity.COMMON)
        self.add_equipment("canvas_tent", weapon_rarity)
        self.add_equipment("iron_pot", EquipmentRarity.COMMON)
        
        # Weapons (at least 1 per party)
        for _ in range(max(1, party_size // 2)):
            self.add_equipment("flintlock_rifle", weapon_rarity)
        
        # Tools
        self.add_equipment("repair_kit", EquipmentRarity.COMMON)
        self.add_equipment("axe", EquipmentRarity.COMMON)
        self.add_equipment("rope", EquipmentRarity.COMMON)
        
        # Personal items
        for _ in range(party_size):
            self.add_equipment("bedroll", EquipmentRarity.COMMON)
            self.add_equipment("wool_blanket", EquipmentRarity.COMMON)
        
        # Extra gear for easy mode
        if difficulty == "easy":
            self.add_equipment("dutch_oven", EquipmentRarity.QUALITY)
            self.add_equipment("pack_horse", EquipmentRarity.COMMON)
            self.add_equipment("repair_kit", EquipmentRarity.QUALITY)
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for saving."""
        return {
            "equipment": [item.to_dict() for item in self.equipment],
            "auto_equip_best": self.auto_equip_best,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EquipmentManager':
        """Create from dictionary."""
        manager = cls()
        manager.auto_equip_best = data.get("auto_equip_best", True)
        
        for item_data in data.get("equipment", []):
            item = EquipmentItem.from_dict(item_data)
            manager.equipment.append(item)
        
        return manager


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate equipment system."""
    print("=" * 60)
    print("EQUIPMENT & INVENTORY SYSTEM DEMO")
    print("=" * 60)
    print()
    
    # Create equipment manager
    em = EquipmentManager()
    
    # Set starting equipment
    em.set_starting_equipment(party_size=4, difficulty="normal")
    
    print("STARTING EQUIPMENT (Party of 4):")
    print(em.get_inventory_display())
    print()
    
    # Show bonuses
    print("ACTIVE BONUSES:")
    bonuses = em.get_party_bonuses()
    for bonus_type, value in sorted(bonuses.items()):
        print(f"  {bonus_type}: +{value:.1f}")
    print()
    
    # Simulate use
    print("Simulating 10 days of travel...")
    for day in range(10):
        # Use weapons for hunting every 3 days
        usage = {}
        if day % 3 == 0:
            usage[EquipmentCategory.WEAPON] = 1.5  # Intense hunting
            print(f"  Day {day + 1}: Hunting")
        
        # Always use camping gear
        usage[EquipmentCategory.CAMPING] = 1.0
        
        results = em.degrade_all(usage)
        
        if results["broken"]:
            print(f"  Day {day + 1}: BROKEN - {', '.join(results['broken'])}")
        
        for warning in results["warnings"]:
            print(f"  Day {day + 1}: ⚠ {warning}")
    
    print()
    print("AFTER 10 DAYS:")
    print(em.get_inventory_display())
    print()
    
    # Repair worn items
    print("Attempting repairs (with mechanic bonus +40)...")
    repair_results = em.repair_all_worn(
        threshold=80.0,
        repair_amount=50,
        use_repair_kit=True,
        mechanic_bonus=40
    )
    
    print(f"  Repaired: {len(repair_results['repaired'])} items")
    print(f"  Failed: {len(repair_results['failed'])} items")
    
    for result in repair_results["repaired"][:3]:
        print(f"    ✓ {result['message']} (+{result['amount']:.1f} durability)")
    print()
    
    # Show final status
    print("FINAL EQUIPMENT STATUS:")
    status = em.get_status_summary()
    print(f"  Total items: {status['total_items']}")
    print(f"  Equipped: {status['equipped']}")
    print(f"  Broken: {status['broken']}")
    print(f"  Worn: {status['worn']}")
    print(f"  Excellent: {status['excellent']}")
    print()
    
    # Test different rarities
    print("RARITY COMPARISON (Flintlock Rifles):")
    for rarity in EquipmentRarity:
        rifle = EquipmentItem("flintlock_rifle", rarity)
        bonuses = rifle.get_effective_bonuses()
        print(f"  {rarity.value.title()}: {rifle.max_durability:.0f} durability, "
              f"+{bonuses.get('hunting', 0):.1f} hunting, ${rifle.get_value()}")
    print()
    
    # Test critical equipment check
    print("CRITICAL EQUIPMENT CHECK:")
    all_ok, issues = em.check_critical_equipment()
    if all_ok:
        print("  ✓ All critical equipment functional")
    else:
        for issue in issues:
            print(f"  ✗ {issue}")
    print()
    
    # Serialization test
    print("SERIALIZATION TEST:")
    saved = em.to_dict()
    print(f"  Saved {len(saved['equipment'])} items")
    
    restored = EquipmentManager.from_dict(saved)
    print(f"  Restored {len(restored.equipment)} items")
    print(f"  First item: {restored.equipment[0]}")
    print()
    
    print("Demo complete!")


if __name__ == "__main__":
    demo()