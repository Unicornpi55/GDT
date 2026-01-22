"""
player.py - Individual Party Member Class for The Great Divide Trail

Defines the Player class representing a single party member with
health, morale, skills, and conditions.
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum
import random


# =============================================================================
# Enums and Constants
# =============================================================================

class Role(Enum):
    """Available party member roles with their specializations."""
    TRAVELER = "Traveler"          # Default, no bonus
    TRAIL_LEADER = "Trail Leader"  # Better navigation, fewer wrong turns
    HUNTER = "Hunter"              # Increased food yield
    MEDIC = "Medic"                # Reduced disease mortality
    SCOUT = "Scout"                # Earlier warning of events
    MECHANIC = "Mechanic"          # Faster equipment repair


class Condition(Enum):
    """Health conditions that can affect party members."""
    HEALTHY = "Healthy"
    INJURED = "Injured"
    HYPOTHERMIA = "Hypothermia"
    DYSENTERY = "Dysentery"
    SCURVY = "Scurvy"
    FROSTBITE = "Frostbite"
    INFECTION = "Infection"
    EXHAUSTED = "Exhausted"
    STARVING = "Starving"
    DEHYDRATED = "Dehydrated"


# Role bonuses - multipliers or flat bonuses for various actions
ROLE_BONUSES = {
    Role.TRAVELER: {
        "navigation": 0,
        "hunting": 0,
        "healing": 0,
        "scouting": 0,
        "repair": 0,
    },
    Role.TRAIL_LEADER: {
        "navigation": 25,      # +25% better navigation
        "hunting": 0,
        "healing": 0,
        "scouting": 10,
        "repair": 0,
    },
    Role.HUNTER: {
        "navigation": 0,
        "hunting": 30,         # +30% food yield
        "healing": 0,
        "scouting": 5,
        "repair": 0,
    },
    Role.MEDIC: {
        "navigation": 0,
        "hunting": 0,
        "healing": 35,         # +35% healing effectiveness
        "scouting": 0,
        "repair": 0,
    },
    Role.SCOUT: {
        "navigation": 15,
        "hunting": 10,
        "healing": 0,
        "scouting": 40,        # +40% event warning
        "repair": 0,
    },
    Role.MECHANIC: {
        "navigation": 0,
        "hunting": 0,
        "healing": 0,
        "scouting": 0,
        "repair": 40,          # +40% repair speed
    },
}

# Condition effects on the player
CONDITION_EFFECTS = {
    Condition.HEALTHY: {
        "health_drain": 0,
        "morale_drain": 0,
        "travel_speed": 0,
        "can_work": True,
    },
    Condition.INJURED: {
        "health_drain": 2,      # Loses 2 health per day
        "morale_drain": 3,
        "travel_speed": -15,    # 15% slower travel
        "can_work": True,
    },
    Condition.HYPOTHERMIA: {
        "health_drain": 5,
        "morale_drain": 5,
        "travel_speed": -25,
        "can_work": False,
    },
    Condition.DYSENTERY: {
        "health_drain": 4,
        "morale_drain": 4,
        "travel_speed": -20,
        "can_work": False,
    },
    Condition.SCURVY: {
        "health_drain": 2,
        "morale_drain": 3,
        "travel_speed": -10,
        "can_work": True,
    },
    Condition.FROSTBITE: {
        "health_drain": 3,
        "morale_drain": 4,
        "travel_speed": -15,
        "can_work": True,
    },
    Condition.INFECTION: {
        "health_drain": 6,
        "morale_drain": 5,
        "travel_speed": -20,
        "can_work": False,
    },
    Condition.EXHAUSTED: {
        "health_drain": 1,
        "morale_drain": 5,
        "travel_speed": -20,
        "can_work": True,
    },
    Condition.STARVING: {
        "health_drain": 5,
        "morale_drain": 8,
        "travel_speed": -25,
        "can_work": False,
    },
    Condition.DEHYDRATED: {
        "health_drain": 6,
        "morale_drain": 6,
        "travel_speed": -30,
        "can_work": False,
    },
}


# =============================================================================
# Player Class
# =============================================================================

class Player:
    """
    Represents a single party member on the trail.
    
    Attributes:
        name: The character's name
        role: Their role/specialization (affects bonuses)
        health: Current health (0-100, 0 = dead)
        max_health: Maximum health
        morale: Current morale (0-100)
        conditions: List of current health conditions
        days_survived: Number of days this character has survived
    """
    
    def __init__(
        self,
        name: str,
        role: Role = Role.TRAVELER,
        health: int = 100,
        morale: int = 75
    ):
        """
        Initialize a new party member.
        
        Args:
            name: Character name
            role: Character role (default: Traveler)
            health: Starting health (default: 100)
            morale: Starting morale (default: 75)
        """
        self.name = name
        self.role = role
        self.health = health
        self.max_health = 100
        self.morale = morale
        self.conditions: List[Condition] = []
        self.days_survived = 0
        self._is_alive = True
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def is_alive(self) -> bool:
        """Check if the player is still alive."""
        return self._is_alive and self.health > 0
    
    @property
    def is_healthy(self) -> bool:
        """Check if the player has no negative conditions."""
        return len(self.conditions) == 0
    
    @property
    def can_work(self) -> bool:
        """Check if the player can perform work actions (hunt, scout, etc.)."""
        if not self.is_alive:
            return False
        
        for condition in self.conditions:
            if not CONDITION_EFFECTS[condition]["can_work"]:
                return False
        
        return True
    
    @property
    def role_name(self) -> str:
        """Get the display name of the player's role."""
        return self.role.value
    
    @property
    def condition_names(self) -> List[str]:
        """Get list of condition names as strings."""
        if not self.conditions:
            return ["Healthy"]
        return [c.value for c in self.conditions]
    
    # =========================================================================
    # Skill Bonuses
    # =========================================================================
    
    def get_skill_bonus(self, skill: str) -> int:
        """
        Get the bonus for a specific skill based on role.
        
        Args:
            skill: One of 'navigation', 'hunting', 'healing', 'scouting', 'repair'
        
        Returns:
            Bonus percentage (0-100)
        """
        bonuses = ROLE_BONUSES.get(self.role, ROLE_BONUSES[Role.TRAVELER])
        return bonuses.get(skill, 0)
    
    def get_effective_skill(self, skill: str, base_value: int = 50) -> int:
        """
        Calculate effective skill value including bonuses and penalties.
        
        Args:
            skill: The skill to calculate
            base_value: Base skill value before modifiers
        
        Returns:
            Effective skill value
        """
        bonus = self.get_skill_bonus(skill)
        
        # Apply health penalty (low health reduces effectiveness)
        health_modifier = self.health / 100
        
        # Apply morale penalty (low morale reduces effectiveness)
        morale_modifier = 0.5 + (self.morale / 200)  # Range: 0.5 to 1.0
        
        effective = base_value * (1 + bonus / 100) * health_modifier * morale_modifier
        
        return int(effective)
    
    # =========================================================================
    # Health Management
    # =========================================================================
    
    def take_damage(self, amount: int, source: str = "unknown") -> Tuple[int, bool]:
        """
        Apply damage to the player.
        
        Args:
            amount: Amount of damage to take
            source: Description of damage source
        
        Returns:
            Tuple of (actual damage taken, whether player died)
        """
        if not self.is_alive:
            return (0, True)
        
        actual_damage = min(amount, self.health)
        self.health -= actual_damage
        
        died = False
        if self.health <= 0:
            self.health = 0
            self._is_alive = False
            died = True
        
        return (actual_damage, died)
    
    def heal(self, amount: int, has_medic_bonus: bool = False) -> int:
        """
        Heal the player.
        
        Args:
            amount: Base amount to heal
            has_medic_bonus: Whether a medic is providing the healing
        
        Returns:
            Actual amount healed
        """
        if not self.is_alive:
            return 0
        
        # Apply medic bonus if applicable
        if has_medic_bonus:
            amount = int(amount * 1.35)
        
        old_health = self.health
        self.health = min(self.max_health, self.health + amount)
        
        return self.health - old_health
    
    def add_condition(self, condition: Condition) -> bool:
        """
        Add a health condition to the player.
        
        Args:
            condition: The condition to add
        
        Returns:
            True if condition was added, False if already present
        """
        if condition not in self.conditions and condition != Condition.HEALTHY:
            self.conditions.append(condition)
            return True
        return False
    
    def remove_condition(self, condition: Condition) -> bool:
        """
        Remove a health condition from the player.
        
        Args:
            condition: The condition to remove
        
        Returns:
            True if condition was removed, False if not present
        """
        if condition in self.conditions:
            self.conditions.remove(condition)
            return True
        return False
    
    def has_condition(self, condition: Condition) -> bool:
        """Check if player has a specific condition."""
        return condition in self.conditions
    
    # =========================================================================
    # Morale Management
    # =========================================================================
    
    def change_morale(self, amount: int) -> int:
        """
        Change the player's morale.
        
        Args:
            amount: Amount to change (positive or negative)
        
        Returns:
            New morale value
        """
        self.morale = max(0, min(100, self.morale + amount))
        return self.morale
    
    def boost_morale(self, amount: int) -> int:
        """Increase morale (convenience method)."""
        return self.change_morale(abs(amount))
    
    def reduce_morale(self, amount: int) -> int:
        """Decrease morale (convenience method)."""
        return self.change_morale(-abs(amount))
    
    # =========================================================================
    # Daily Update
    # =========================================================================
    
    def daily_update(self) -> Dict:
        """
        Process daily effects on the player.
        
        Called once per game day to apply condition effects,
        natural recovery, etc.
        
        Returns:
            Dict containing update results
        """
        results = {
            "health_change": 0,
            "morale_change": 0,
            "conditions_worsened": [],
            "conditions_improved": [],
            "died": False,
        }
        
        if not self.is_alive:
            return results
        
        self.days_survived += 1
        
        # Apply condition effects
        total_health_drain = 0
        total_morale_drain = 0
        
        for condition in self.conditions:
            effects = CONDITION_EFFECTS[condition]
            total_health_drain += effects["health_drain"]
            total_morale_drain += effects["morale_drain"]
        
        # Apply health drain
        if total_health_drain > 0:
            damage, died = self.take_damage(total_health_drain, "conditions")
            results["health_change"] -= damage
            results["died"] = died
        
        # Apply morale drain
        if total_morale_drain > 0:
            self.reduce_morale(total_morale_drain)
            results["morale_change"] -= total_morale_drain
        
        # Natural morale recovery if healthy and morale is low
        if self.is_healthy and self.morale < 50:
            recovery = random.randint(1, 3)
            self.boost_morale(recovery)
            results["morale_change"] += recovery
        
        # Random chance for conditions to worsen or improve
        for condition in self.conditions[:]:  # Copy list to allow modification
            # 10% chance to worsen (add infection if injured)
            if condition == Condition.INJURED and random.random() < 0.10:
                if self.add_condition(Condition.INFECTION):
                    results["conditions_worsened"].append(Condition.INFECTION)
            
            # 5% natural recovery chance (except for serious conditions)
            if condition in [Condition.EXHAUSTED, Condition.INJURED]:
                if random.random() < 0.05:
                    self.remove_condition(condition)
                    results["conditions_improved"].append(condition)
        
        return results
    
    # =========================================================================
    # Travel Speed
    # =========================================================================
    
    def get_travel_speed_modifier(self) -> int:
        """
        Calculate travel speed modifier based on conditions.
        
        Returns:
            Speed modifier as percentage (negative = slower)
        """
        modifier = 0
        
        for condition in self.conditions:
            modifier += CONDITION_EFFECTS[condition]["travel_speed"]
        
        # Health-based modifier
        if self.health < 30:
            modifier -= 20
        elif self.health < 50:
            modifier -= 10
        
        return modifier
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """Convert player to dictionary for saving."""
        return {
            "name": self.name,
            "role": self.role.value,
            "health": self.health,
            "max_health": self.max_health,
            "morale": self.morale,
            "conditions": [c.value for c in self.conditions],
            "days_survived": self.days_survived,
            "is_alive": self._is_alive,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Player':
        """Create player from dictionary (loading)."""
        # Find role enum from string
        role = Role.TRAVELER
        for r in Role:
            if r.value == data.get("role"):
                role = r
                break
        
        player = cls(
            name=data["name"],
            role=role,
            health=data.get("health", 100),
            morale=data.get("morale", 75)
        )
        
        player.max_health = data.get("max_health", 100)
        player.days_survived = data.get("days_survived", 0)
        player._is_alive = data.get("is_alive", True)
        
        # Restore conditions
        for cond_name in data.get("conditions", []):
            for c in Condition:
                if c.value == cond_name:
                    player.conditions.append(c)
                    break
        
        return player
    
    # =========================================================================
    # Display
    # =========================================================================
    
    def __str__(self) -> str:
        """String representation of the player."""
        status = "DEAD" if not self.is_alive else f"HP:{self.health} M:{self.morale}"
        conditions = ", ".join(self.condition_names) if self.conditions else "Healthy"
        return f"{self.name} ({self.role_name}) - {status} [{conditions}]"
    
    def __repr__(self) -> str:
        return f"Player(name='{self.name}', role={self.role}, health={self.health}, alive={self.is_alive})"
    
    def get_display_dict(self) -> Dict:
        """Get dictionary suitable for UI display functions."""
        return {
            "name": self.name,
            "role": self.role_name,
            "health": self.health,
            "morale": self.morale,
            "conditions": self.condition_names if self.conditions else [],
        }


# =============================================================================
# Factory Functions
# =============================================================================

def create_player(name: str, role_name: str = "Traveler") -> Player:
    """
    Create a player with role specified by string name.
    
    Args:
        name: Player name
        role_name: Role name as string (e.g., "Hunter", "Medic")
    
    Returns:
        New Player instance
    """
    role = Role.TRAVELER
    for r in Role:
        if r.value.lower() == role_name.lower():
            role = r
            break
    
    return Player(name=name, role=role)


def get_available_roles() -> List[Dict[str, str]]:
    """
    Get list of available roles with descriptions.
    
    Returns:
        List of dicts with 'name' and 'description' keys
    """
    descriptions = {
        Role.TRAVELER: "No special bonuses",
        Role.TRAIL_LEADER: "Better navigation, fewer wrong turns",
        Role.HUNTER: "Increased food yield when hunting",
        Role.MEDIC: "Reduced disease mortality, better healing",
        Role.SCOUT: "Earlier warning of dangers and events",
        Role.MECHANIC: "Faster equipment and wagon repair",
    }
    
    return [
        {"name": role.value, "description": descriptions[role]}
        for role in Role
    ]


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate player functionality."""
    print("=" * 50)
    print("PLAYER CLASS DEMO")
    print("=" * 50)
    print()
    
    # Create some players
    leader = Player("John Walker", Role.TRAIL_LEADER)
    hunter = Player("Thomas Grey", Role.HUNTER, health=80, morale=60)
    medic = Player("Mary Walker", Role.MEDIC)
    
    print("Created players:")
    print(f"  {leader}")
    print(f"  {hunter}")
    print(f"  {medic}")
    print()
    
    # Show role bonuses
    print("Skill bonuses:")
    print(f"  {leader.name} navigation bonus: +{leader.get_skill_bonus('navigation')}%")
    print(f"  {hunter.name} hunting bonus: +{hunter.get_skill_bonus('hunting')}%")
    print(f"  {medic.name} healing bonus: +{medic.get_skill_bonus('healing')}%")
    print()
    
    # Add conditions
    print("Adding conditions...")
    hunter.add_condition(Condition.INJURED)
    hunter.add_condition(Condition.EXHAUSTED)
    print(f"  {hunter}")
    print(f"  Can work: {hunter.can_work}")
    print(f"  Travel speed modifier: {hunter.get_travel_speed_modifier()}%")
    print()
    
    # Simulate damage and healing
    print("Combat simulation:")
    damage, died = hunter.take_damage(25, "wolf attack")
    print(f"  {hunter.name} took {damage} damage from wolf attack")
    print(f"  Health now: {hunter.health}")
    
    healed = hunter.heal(15, has_medic_bonus=True)
    print(f"  Medic healed {healed} HP (with bonus)")
    print(f"  Health now: {hunter.health}")
    print()
    
    # Daily update
    print("Processing daily update...")
    results = hunter.daily_update()
    print(f"  Health change: {results['health_change']}")
    print(f"  Morale change: {results['morale_change']}")
    print(f"  {hunter}")
    print()
    
    # Serialization
    print("Serialization test:")
    data = hunter.to_dict()
    print(f"  Saved: {data}")
    
    restored = Player.from_dict(data)
    print(f"  Restored: {restored}")
    print()
    
    # Available roles
    print("Available roles:")
    for role_info in get_available_roles():
        print(f"  {role_info['name']}: {role_info['description']}")
    
    print()
    print("Demo complete!")


if __name__ == "__main__":
    demo()