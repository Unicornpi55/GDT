"""
party.py - Party Management for The Great Divide Trail

Combines player management and resource management into a unified
party system that handles the group's journey.
"""

from typing import List, Dict, Optional, Tuple, Generator
import random

from player import Player, Role, Condition, create_player, get_available_roles
from resources import ResourceManager, ResourceType, RESOURCE_INFO


# =============================================================================
# Constants
# =============================================================================

MIN_PARTY_SIZE = 1
MAX_PARTY_SIZE = 5

# Morale effects from various events
MORALE_EVENTS = {
    "death": -25,           # Party member death
    "successful_hunt": 10,  # Good hunt
    "failed_hunt": -5,      # Wasted time/ammo
    "rest_day": 15,         # Full rest
    "good_weather": 5,      # Nice day
    "bad_weather": -5,      # Storm/blizzard
    "found_supplies": 10,   # Found/traded supplies
    "low_food": -10,        # Running low on food
    "no_food": -20,         # Out of food
    "reached_landmark": 15, # Reached a major landmark
    "injury": -10,          # Party member injured
    "healed": 5,            # Party member recovered
}


# =============================================================================
# Party Class
# =============================================================================

class Party:
    """
    Manages the entire traveling party including members and resources.
    
    This is the main game state object that tracks:
    - All party members (Player objects)
    - All resources (ResourceManager)
    - Party-wide statistics and status
    """
    
    def __init__(self, name: str = "Expedition"):
        """
        Initialize a new party.
        
        Args:
            name: Name of the expedition/party
        """
        self.name = name
        self.members: List[Player] = []
        self.resources = ResourceManager()
        self.days_traveled = 0
        self.miles_traveled = 0
        self.current_rationing = "normal"  # filling, normal, meager, starving
        
        # Track deaths for the journey log
        self.death_log: List[Dict] = []
    
    # =========================================================================
    # Party Member Management
    # =========================================================================
    
    def add_member(self, player: Player) -> bool:
        """
        Add a member to the party.
        
        Args:
            player: Player object to add
        
        Returns:
            True if added, False if party is full
        """
        if len(self.members) >= MAX_PARTY_SIZE:
            return False
        
        self.members.append(player)
        return True
    
    def remove_member(self, player: Player) -> bool:
        """
        Remove a member from the party.
        
        Args:
            player: Player to remove
        
        Returns:
            True if removed, False if not found
        """
        if player in self.members:
            self.members.remove(player)
            return True
        return False
    
    def get_member_by_name(self, name: str) -> Optional[Player]:
        """Find a party member by name."""
        for member in self.members:
            if member.name.lower() == name.lower():
                return member
        return None
    
    def get_member_by_index(self, index: int) -> Optional[Player]:
        """Get a party member by index."""
        if 0 <= index < len(self.members):
            return self.members[index]
        return None
    
    @property
    def size(self) -> int:
        """Total number of party members (alive and dead)."""
        return len(self.members)
    
    @property
    def alive_members(self) -> List[Player]:
        """List of living party members."""
        return [m for m in self.members if m.is_alive]
    
    @property
    def dead_members(self) -> List[Player]:
        """List of deceased party members."""
        return [m for m in self.members if not m.is_alive]
    
    @property
    def alive_count(self) -> int:
        """Number of living party members."""
        return len(self.alive_members)
    
    @property
    def working_members(self) -> List[Player]:
        """List of members who can perform work (hunt, scout, etc.)."""
        return [m for m in self.members if m.is_alive and m.can_work]
    
    def iter_alive(self) -> Generator[Player, None, None]:
        """Iterate over living party members."""
        for member in self.members:
            if member.is_alive:
                yield member
    
    # =========================================================================
    # Role Queries
    # =========================================================================
    
    def has_role(self, role: Role) -> bool:
        """Check if any living member has a specific role."""
        for member in self.alive_members:
            if member.role == role:
                return True
        return False
    
    def get_members_with_role(self, role: Role) -> List[Player]:
        """Get all living members with a specific role."""
        return [m for m in self.alive_members if m.role == role]
    
    def get_best_for_skill(self, skill: str) -> Optional[Player]:
        """
        Get the best living party member for a skill.
        
        Args:
            skill: One of 'navigation', 'hunting', 'healing', 'scouting', 'repair'
        
        Returns:
            Player with highest effective skill, or None if no one available
        """
        best_member = None
        best_skill = -1
        
        for member in self.working_members:
            effective = member.get_effective_skill(skill)
            if effective > best_skill:
                best_skill = effective
                best_member = member
        
        return best_member
    
    def get_party_skill_bonus(self, skill: str) -> int:
        """
        Get the best skill bonus available in the party.
        
        Args:
            skill: The skill to check
        
        Returns:
            Highest bonus percentage among living members
        """
        best_bonus = 0
        for member in self.alive_members:
            bonus = member.get_skill_bonus(skill)
            if bonus > best_bonus:
                best_bonus = bonus
        return best_bonus
    
    # =========================================================================
    # Health & Morale
    # =========================================================================
    
    @property
    def average_health(self) -> float:
        """Calculate average health of living members."""
        alive = self.alive_members
        if not alive:
            return 0
        return sum(m.health for m in alive) / len(alive)
    
    @property
    def average_morale(self) -> float:
        """Calculate average morale of living members."""
        alive = self.alive_members
        if not alive:
            return 0
        return sum(m.morale for m in alive) / len(alive)
    
    @property
    def lowest_health_member(self) -> Optional[Player]:
        """Get the living member with lowest health."""
        alive = self.alive_members
        if not alive:
            return None
        return min(alive, key=lambda m: m.health)
    
    @property
    def lowest_morale_member(self) -> Optional[Player]:
        """Get the living member with lowest morale."""
        alive = self.alive_members
        if not alive:
            return None
        return min(alive, key=lambda m: m.morale)
    
    def change_party_morale(self, amount: int, reason: str = "") -> Dict:
        """
        Change morale for all living party members.
        
        Args:
            amount: Amount to change (positive or negative)
            reason: Reason for the change
        
        Returns:
            Dict with change details
        """
        results = {"affected": [], "reason": reason}
        
        for member in self.alive_members:
            old_morale = member.morale
            member.change_morale(amount)
            results["affected"].append({
                "name": member.name,
                "old": old_morale,
                "new": member.morale,
                "change": member.morale - old_morale,
            })
        
        return results
    
    def apply_morale_event(self, event_type: str) -> int:
        """
        Apply a morale event to the party.
        
        Args:
            event_type: Key from MORALE_EVENTS dict
        
        Returns:
            Morale change amount applied
        """
        amount = MORALE_EVENTS.get(event_type, 0)
        if amount != 0:
            self.change_party_morale(amount, event_type)
        return amount
    
    def heal_party(self, amount: int) -> Dict:
        """
        Heal all living party members.
        
        Args:
            amount: Base healing amount
        
        Returns:
            Dict with healing details
        """
        has_medic = self.has_role(Role.MEDIC)
        
        results = {"healed": [], "total": 0}
        
        for member in self.alive_members:
            healed = member.heal(amount, has_medic_bonus=has_medic)
            if healed > 0:
                results["healed"].append({"name": member.name, "amount": healed})
                results["total"] += healed
        
        return results
    
    def get_sick_members(self) -> List[Player]:
        """Get all living members with health conditions."""
        return [m for m in self.alive_members if not m.is_healthy]
    
    # =========================================================================
    # Travel
    # =========================================================================
    
    def get_travel_speed_modifier(self) -> int:
        """
        Calculate party travel speed modifier.
        
        Based on worst-condition member (party moves at slowest pace).
        
        Returns:
            Speed modifier as percentage
        """
        if not self.alive_members:
            return -100  # Can't travel with no one alive
        
        # Get worst modifier (most negative)
        worst = 0
        for member in self.alive_members:
            modifier = member.get_travel_speed_modifier()
            if modifier < worst:
                worst = modifier
        
        # Apply scout bonus to reduce penalty
        scout_bonus = self.get_party_skill_bonus("navigation")
        if scout_bonus > 0 and worst < 0:
            worst = int(worst * (1 - scout_bonus / 200))  # Reduce penalty by up to 50%
        
        return worst
    
    def calculate_daily_miles(self, base_miles: int, terrain_modifier: float = 1.0) -> int:
        """
        Calculate how many miles the party can travel in a day.
        
        Args:
            base_miles: Base miles per day for the terrain
            terrain_modifier: Multiplier based on terrain difficulty
        
        Returns:
            Miles that can be traveled
        """
        speed_modifier = self.get_travel_speed_modifier()
        effective_modifier = 1 + (speed_modifier / 100)
        
        miles = int(base_miles * terrain_modifier * effective_modifier)
        return max(1, miles)  # Always travel at least 1 mile
    
    # =========================================================================
    # Daily Processing
    # =========================================================================
    
    def process_day(self, terrain: str = "plains", weather: str = "clear") -> Dict:
        """
        Process all daily effects for the party.
        
        This is the main daily update function that handles:
        - Resource consumption
        - Resource decay
        - Health condition effects
        - Morale updates
        - Death checks
        
        Args:
            terrain: Current terrain type
            weather: Current weather condition
        
        Returns:
            Dict with all daily results
        """
        results = {
            "day": self.days_traveled + 1,
            "consumption": {},
            "decay": {},
            "member_updates": [],
            "deaths": [],
            "warnings": [],
            "events": [],
        }
        
        self.days_traveled += 1
        
        # 1. Consume daily resources
        if self.alive_count > 0:
            consumption = self.resources.consume_daily(
                party_size=self.alive_count,
                terrain=terrain,
                rationing=self.current_rationing
            )
            results["consumption"] = consumption
            results["warnings"].extend(consumption.get("warnings", []))
            
            # Check for starvation
            if ResourceType.FOOD in consumption.get("shortages", {}):
                self.apply_morale_event("no_food")
                results["events"].append("The party is starving!")
                # Apply starvation to all members
                for member in self.alive_members:
                    member.add_condition(Condition.STARVING)
            
            if ResourceType.WATER in consumption.get("shortages", {}):
                results["events"].append("The party is dehydrated!")
                for member in self.alive_members:
                    member.add_condition(Condition.DEHYDRATED)
        
        # 2. Apply resource decay
        decay = self.resources.apply_daily_decay(weather)
        results["decay"] = decay
        
        # 3. Process each member's daily update
        for member in self.members:
            if member.is_alive:
                update = member.daily_update()
                results["member_updates"].append({
                    "name": member.name,
                    "update": update
                })
                
                # Check for death
                if update.get("died"):
                    self._record_death(member, "conditions")
                    results["deaths"].append(member.name)
                    results["events"].append(f"{member.name} has died.")
                    self.apply_morale_event("death")
        
        # 4. Weather effects on morale
        if weather in ["storm", "blizzard"]:
            self.apply_morale_event("bad_weather")
            results["events"].append("The harsh weather dampens spirits.")
        elif weather == "clear" and random.random() < 0.3:
            self.apply_morale_event("good_weather")
        
        # 5. Low food warning morale hit
        food_days = self.resources.days_of_supplies(self.alive_count)
        if food_days.get(ResourceType.FOOD, 999) < 3 and food_days.get(ResourceType.FOOD, 999) > 0:
            self.apply_morale_event("low_food")
            results["warnings"].append("Food supplies are critically low!")
        
        return results
    
    def _record_death(self, member: Player, cause: str):
        """Record a death in the journey log."""
        self.death_log.append({
            "name": member.name,
            "role": member.role_name,
            "day": self.days_traveled,
            "cause": cause,
            "days_survived": member.days_survived,
        })
    
    # =========================================================================
    # Rest
    # =========================================================================
    
    def rest(self, days: int = 1) -> Dict:
        """
        Rest the party for a number of days.
        
        Args:
            days: Number of days to rest
        
        Returns:
            Dict with rest results
        """
        results = {
            "days_rested": days,
            "healing": [],
            "morale_boost": 0,
            "conditions_cleared": [],
        }
        
        for _ in range(days):
            self.days_traveled += 1
            
            # Heal party
            has_medic = self.has_role(Role.MEDIC)
            for member in self.alive_members:
                # Rest heals 5-15 HP
                heal_amount = random.randint(5, 15)
                healed = member.heal(heal_amount, has_medic_bonus=has_medic)
                
                if healed > 0:
                    results["healing"].append({"name": member.name, "amount": healed})
                
                # Chance to clear minor conditions
                for condition in member.conditions[:]:
                    if condition in [Condition.EXHAUSTED, Condition.INJURED]:
                        if random.random() < 0.3:  # 30% chance per day
                            member.remove_condition(condition)
                            results["conditions_cleared"].append({
                                "name": member.name,
                                "condition": condition.value
                            })
            
            # Morale boost from rest
            self.apply_morale_event("rest_day")
            results["morale_boost"] += MORALE_EVENTS["rest_day"]
            
            # Still consume resources while resting
            self.resources.consume_daily(
                party_size=self.alive_count,
                rationing=self.current_rationing
            )
        
        return results
    
    # =========================================================================
    # Rationing
    # =========================================================================
    
    def set_rationing(self, level: str) -> bool:
        """
        Set the party's rationing level.
        
        Args:
            level: 'filling', 'normal', 'meager', or 'starving'
        
        Returns:
            True if valid level, False otherwise
        """
        valid_levels = ["filling", "normal", "meager", "starving"]
        if level.lower() in valid_levels:
            self.current_rationing = level.lower()
            return True
        return False
    
    def get_rationing_options(self) -> List[Dict]:
        """Get rationing level options with descriptions."""
        return [
            {"level": "filling", "description": "Full rations (1.5x consumption, +5 morale/day)"},
            {"level": "normal", "description": "Normal rations (standard consumption)"},
            {"level": "meager", "description": "Reduced rations (0.5x consumption, -3 morale/day)"},
            {"level": "starving", "description": "Bare minimum (0.25x consumption, -8 morale/day, health risk)"},
        ]
    
    # =========================================================================
    # Status & Queries
    # =========================================================================
    
    def is_party_alive(self) -> bool:
        """Check if anyone in the party is still alive."""
        return self.alive_count > 0
    
    def get_party_status(self) -> str:
        """Get a summary status string for the party."""
        if not self.is_party_alive():
            return "All party members have perished"
        
        sick = len(self.get_sick_members())
        if sick > 0:
            return f"{self.alive_count} alive ({sick} sick/injured)"
        return f"{self.alive_count} alive, all healthy"
    
    def get_status_summary(self) -> Dict:
        """Get comprehensive status summary."""
        return {
            "name": self.name,
            "days_traveled": self.days_traveled,
            "miles_traveled": self.miles_traveled,
            "alive": self.alive_count,
            "dead": len(self.dead_members),
            "avg_health": round(self.average_health, 1),
            "avg_morale": round(self.average_morale, 1),
            "rationing": self.current_rationing,
            "resources": self.resources.get_display_dict(),
        }
    
    # =========================================================================
    # Display
    # =========================================================================
    
    def get_members_display(self) -> List[Dict]:
        """Get display data for all members."""
        return [m.get_display_dict() for m in self.members]
    
    def get_alive_members_display(self) -> List[Dict]:
        """Get display data for living members only."""
        return [m.get_display_dict() for m in self.alive_members]
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """Convert party to dictionary for saving."""
        return {
            "name": self.name,
            "members": [m.to_dict() for m in self.members],
            "resources": self.resources.to_dict(),
            "days_traveled": self.days_traveled,
            "miles_traveled": self.miles_traveled,
            "current_rationing": self.current_rationing,
            "death_log": self.death_log,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Party':
        """Create party from dictionary."""
        party = cls(name=data.get("name", "Expedition"))
        
        # Restore members
        for member_data in data.get("members", []):
            player = Player.from_dict(member_data)
            party.members.append(player)
        
        # Restore resources
        party.resources = ResourceManager.from_dict(data.get("resources", {}))
        
        party.days_traveled = data.get("days_traveled", 0)
        party.miles_traveled = data.get("miles_traveled", 0)
        party.current_rationing = data.get("current_rationing", "normal")
        party.death_log = data.get("death_log", [])
        
        return party


# =============================================================================
# Factory Functions
# =============================================================================

def create_party_interactive() -> Party:
    """
    Interactively create a new party (for use with UI).
    
    This is a helper that would be called by the game loop.
    Returns a configured Party object.
    """
    from ui import get_input, get_number, get_menu_choice, clear_screen, header
    
    clear_screen()
    print(header("CREATE YOUR EXPEDITION"))
    print()
    
    # Get expedition name
    party_name = get_input("Name your expedition", default="Walker Expedition")
    party = Party(name=party_name)
    
    # Get party size
    print()
    size = get_number("How many in your party?", min_val=MIN_PARTY_SIZE, max_val=MAX_PARTY_SIZE, default=4)
    
    # Get available roles
    roles = get_available_roles()
    role_names = [r["name"] for r in roles]
    
    # Create each member
    for i in range(size):
        print()
        print(f"--- Party Member {i + 1} of {size} ---")
        
        name = get_input(f"Enter name for member {i + 1}")
        
        print("\nAvailable roles:")
        for j, role in enumerate(roles):
            print(f"  {j + 1}) {role['name']}: {role['description']}")
        
        role_idx = get_menu_choice(role_names, prompt="Select role: ")
        role_name = role_names[role_idx]
        
        player = create_player(name, role_name)
        party.add_member(player)
        print(f"Added {player.name} as {player.role_name}")
    
    return party


def create_default_party() -> Party:
    """Create a default party for testing or quick start."""
    party = Party(name="Pioneer Expedition")
    
    # Add default members
    party.add_member(Player("John Walker", Role.TRAIL_LEADER))
    party.add_member(Player("Mary Walker", Role.MEDIC))
    party.add_member(Player("Thomas Grey", Role.HUNTER))
    party.add_member(Player("Sarah Grey", Role.SCOUT))
    
    # Set starting supplies
    party.resources.set_starting_supplies(party_size=4, difficulty="normal")
    
    return party


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate party management functionality."""
    print("=" * 50)
    print("PARTY MANAGEMENT DEMO")
    print("=" * 50)
    print()
    
    # Create default party
    party = create_default_party()
    
    print(f"Created party: {party.name}")
    print(f"Members: {party.size}")
    print()
    
    # Display members
    print("Party Members:")
    for member in party.members:
        print(f"  {member}")
    print()
    
    # Check roles
    print("Role checks:")
    print(f"  Has medic: {party.has_role(Role.MEDIC)}")
    print(f"  Has mechanic: {party.has_role(Role.MECHANIC)}")
    print(f"  Best hunter: {party.get_best_for_skill('hunting').name}")
    print(f"  Party hunting bonus: +{party.get_party_skill_bonus('hunting')}%")
    print()
    
    # Status
    print("Party Status:")
    print(f"  Average health: {party.average_health:.1f}")
    print(f"  Average morale: {party.average_morale:.1f}")
    print(f"  Status: {party.get_party_status()}")
    print()
    
    # Resources
    print("Resources:")
    print(party.resources.get_full_display())
    print()
    
    # Simulate some days
    print("Simulating 7 days of travel...")
    for day in range(7):
        results = party.process_day(terrain="mountains", weather="clear")
        
        if results["deaths"]:
            print(f"  Day {results['day']}: {', '.join(results['deaths'])} died!")
        if results["warnings"]:
            for warning in results["warnings"]:
                print(f"  Day {results['day']}: ⚠ {warning}")
    
    print()
    print("After 7 days:")
    print(f"  Days traveled: {party.days_traveled}")
    print(f"  Alive: {party.alive_count}")
    print(f"  Average health: {party.average_health:.1f}")
    print(f"  Average morale: {party.average_morale:.1f}")
    print()
    
    # Rest
    print("Resting for 2 days...")
    rest_results = party.rest(days=2)
    print(f"  Total healing: {sum(h['amount'] for h in rest_results['healing'])} HP")
    print(f"  Morale boost: +{rest_results['morale_boost']}")
    print()
    
    # Travel speed
    print("Travel calculations:")
    print(f"  Speed modifier: {party.get_travel_speed_modifier()}%")
    print(f"  Miles per day (base 15): {party.calculate_daily_miles(15)}")
    print()
    
    # Serialization
    print("Serialization test:")
    data = party.to_dict()
    restored = Party.from_dict(data)
    print(f"  Original party: {party.alive_count} alive")
    print(f"  Restored party: {restored.alive_count} alive")
    print(f"  Resources match: {party.resources.get_quantity(ResourceType.FOOD) == restored.resources.get_quantity(ResourceType.FOOD)}")
    print()
    
    print("Demo complete!")


if __name__ == "__main__":
    demo()