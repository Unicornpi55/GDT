"""
events.py - Event System for The Great Divide Trail

Handles loading, triggering, and resolving random events during the journey.
Events are data-driven, loaded from events.json.
"""

import json
import random
from typing import Dict, List, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, field


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class EventOutcome:
    """Represents a possible outcome of an event choice."""
    chance: int  # Percentage chance (0-100)
    outcome_type: str  # success, partial, failure
    description: str
    effects: Dict = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EventOutcome':
        return cls(
            chance=data.get("chance", 50),
            outcome_type=data.get("type", "success"),
            description=data.get("description", ""),
            effects=data.get("effects", {}),
        )


@dataclass
class EventChoice:
    """Represents a choice the player can make during an event."""
    id: str
    text: str
    requirements: Dict = field(default_factory=dict)
    outcomes: List[EventOutcome] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EventChoice':
        outcomes = [EventOutcome.from_dict(o) for o in data.get("outcomes", [])]
        return cls(
            id=data.get("id", "unknown"),
            text=data.get("text", "Unknown choice"),
            requirements=data.get("requirements", {}),
            outcomes=outcomes,
        )
    
    def check_requirements(self, context: Dict) -> Tuple[bool, str]:
        """
        Check if requirements are met for this choice.
        
        Args:
            context: Dict with 'resources', 'skills', etc.
        
        Returns:
            Tuple of (requirements_met, reason_if_not)
        """
        if not self.requirements:
            return (True, "")
        
        # Check skill requirement
        if "skill" in self.requirements:
            skill_name = self.requirements["skill"]
            min_value = self.requirements.get("min_value", 0)
            actual_value = context.get("skills", {}).get(skill_name, 0)
            
            if actual_value < min_value:
                return (False, f"Requires {skill_name} skill of {min_value}+")
        
        # Check resource requirement
        if "resource" in self.requirements:
            resource_name = self.requirements["resource"]
            min_value = self.requirements.get("min_value", 0)
            actual_value = context.get("resources", {}).get(resource_name, 0)
            
            if actual_value < min_value:
                return (False, f"Requires {min_value}+ {resource_name}")
        
        return (True, "")
    
    def resolve(self) -> EventOutcome:
        """
        Resolve this choice by randomly selecting an outcome.
        
        Returns:
            Selected EventOutcome
        """
        if not self.outcomes:
            return EventOutcome(100, "success", "Nothing happens.", {})
        
        roll = random.randint(1, 100)
        cumulative = 0
        
        for outcome in self.outcomes:
            cumulative += outcome.chance
            if roll <= cumulative:
                return outcome
        
        # Fallback to last outcome
        return self.outcomes[-1]


@dataclass
class Event:
    """Represents a random event that can occur during the journey."""
    id: str
    name: str
    category: str
    description: str
    terrain: List[str] = field(default_factory=list)
    season: List[str] = field(default_factory=list)
    regions: List[str] = field(default_factory=list)
    weight: int = 10
    choices: List[EventChoice] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        choices = [EventChoice.from_dict(c) for c in data.get("choices", [])]
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown Event"),
            category=data.get("category", "misc"),
            description=data.get("description", ""),
            terrain=data.get("terrain", []),
            season=data.get("season", []),
            regions=data.get("regions", []),
            weight=data.get("weight", 10),
            choices=choices,
        )
    
    def matches_conditions(
        self, 
        terrain: str, 
        season: str, 
        region: str = ""
    ) -> bool:
        """
        Check if this event can trigger under current conditions.
        
        Args:
            terrain: Current terrain type
            season: Current season
            region: Current region (optional)
        
        Returns:
            True if event can trigger
        """
        # Check terrain (empty list means any terrain)
        if self.terrain and terrain not in self.terrain:
            return False
        
        # Check season (empty list means any season)
        if self.season and season not in self.season:
            return False
        
        # Check region (empty list means any region)
        if self.regions and region and region not in self.regions:
            return False
        
        return True
    
    def get_available_choices(self, context: Dict) -> List[Tuple[EventChoice, bool, str]]:
        """
        Get all choices with availability status.
        
        Args:
            context: Game context for checking requirements
        
        Returns:
            List of (choice, is_available, reason) tuples
        """
        result = []
        for choice in self.choices:
            available, reason = choice.check_requirements(context)
            result.append((choice, available, reason))
        return result


# =============================================================================
# Event Manager Class
# =============================================================================

class EventManager:
    """
    Manages the event system including loading, triggering, and processing.
    """
    
    def __init__(self, data_path: str = None):
        """
        Initialize the event manager.
        
        Args:
            data_path: Path to events.json file
        """
        self.events: List[Event] = []
        self.categories: List[str] = []
        self.event_history: List[Dict] = []
        
        # Event cooldowns (prevent same event twice in a row)
        self.recent_events: List[str] = []
        self.cooldown_count = 3  # Events can't repeat within this many events
        
        # Load data
        if data_path:
            self.load_data(data_path)
        else:
            default_path = Path(__file__).parent / "data" / "events.json"
            if default_path.exists():
                self.load_data(str(default_path))
    
    def load_data(self, filepath: str):
        """Load event data from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.categories = data.get("event_categories", [])
            
            self.events = []
            for event_data in data.get("events", []):
                self.events.append(Event.from_dict(event_data))
            
        except FileNotFoundError:
            print(f"Warning: Could not find {filepath}")
            self._create_default_events()
        except json.JSONDecodeError as e:
            print(f"Warning: Error parsing {filepath}: {e}")
            self._create_default_events()
    
    def _create_default_events(self):
        """Create minimal default events if loading fails."""
        self.events = [
            Event(
                id="nothing",
                name="Uneventful Day",
                category="misc",
                description="The day passes without incident.",
                choices=[
                    EventChoice(
                        id="continue",
                        text="Continue on",
                        outcomes=[EventOutcome(100, "success", "You continue your journey.", {})]
                    )
                ]
            )
        ]
    
    # =========================================================================
    # Event Selection
    # =========================================================================
    
    def get_eligible_events(
        self, 
        terrain: str, 
        season: str, 
        region: str = "",
        category: str = None
    ) -> List[Event]:
        """
        Get all events eligible to trigger under current conditions.
        
        Args:
            terrain: Current terrain type
            season: Current season
            region: Current region
            category: Optional category filter
        
        Returns:
            List of eligible events
        """
        eligible = []
        
        for event in self.events:
            # Skip recently triggered events
            if event.id in self.recent_events:
                continue
            
            # Check conditions
            if not event.matches_conditions(terrain, season, region):
                continue
            
            # Check category filter
            if category and event.category != category:
                continue
            
            eligible.append(event)
        
        return eligible
    
    def select_random_event(
        self, 
        terrain: str, 
        season: str, 
        region: str = "",
        category: str = None
    ) -> Optional[Event]:
        """
        Select a random event based on weights and conditions.
        
        Args:
            terrain: Current terrain type
            season: Current season  
            region: Current region
            category: Optional category filter
        
        Returns:
            Selected event or None if no eligible events
        """
        eligible = self.get_eligible_events(terrain, season, region, category)
        
        if not eligible:
            return None
        
        # Weighted random selection
        total_weight = sum(e.weight for e in eligible)
        roll = random.randint(1, total_weight)
        
        cumulative = 0
        for event in eligible:
            cumulative += event.weight
            if roll <= cumulative:
                return event
        
        return eligible[-1]
    
    def should_trigger_event(
        self, 
        base_chance: float = 0.25,
        modifiers: Dict[str, float] = None
    ) -> bool:
        """
        Determine if an event should trigger this turn.
        
        Args:
            base_chance: Base probability (0.0 to 1.0)
            modifiers: Dict of modifier name to value
        
        Returns:
            True if event should trigger
        """
        chance = base_chance
        
        if modifiers:
            # Apply modifiers
            for name, value in modifiers.items():
                if name == "scout_bonus":
                    # Good scouting reduces bad event chance
                    chance *= (1 - value / 200)
                elif name == "terrain_danger":
                    # Dangerous terrain increases event chance
                    chance *= (1 + value / 100)
                elif name == "weather_danger":
                    # Bad weather increases event chance
                    chance *= (1 + value / 100)
        
        return random.random() < chance
    
    # =========================================================================
    # Event Resolution
    # =========================================================================
    
    def resolve_choice(
        self, 
        event: Event, 
        choice_index: int, 
        context: Dict
    ) -> Dict:
        """
        Resolve a player's choice for an event.
        
        Args:
            event: The event being resolved
            choice_index: Index of chosen option
            context: Game context for requirements checking
        
        Returns:
            Dict with resolution results
        """
        if choice_index < 0 or choice_index >= len(event.choices):
            return {"error": "Invalid choice index"}
        
        choice = event.choices[choice_index]
        
        # Check requirements
        available, reason = choice.check_requirements(context)
        if not available:
            return {"error": f"Cannot select this choice: {reason}"}
        
        # Resolve outcome
        outcome = choice.resolve()
        
        # Record in history
        self._record_event(event, choice, outcome)
        
        # Update cooldown
        self._update_cooldown(event.id)
        
        return {
            "event_id": event.id,
            "event_name": event.name,
            "choice_id": choice.id,
            "choice_text": choice.text,
            "outcome_type": outcome.outcome_type,
            "outcome_description": outcome.description,
            "effects": outcome.effects,
        }
    
    def _record_event(self, event: Event, choice: EventChoice, outcome: EventOutcome):
        """Record event in history."""
        self.event_history.append({
            "event_id": event.id,
            "event_name": event.name,
            "choice_id": choice.id,
            "outcome_type": outcome.outcome_type,
        })
    
    def _update_cooldown(self, event_id: str):
        """Update the recent events cooldown list."""
        self.recent_events.append(event_id)
        if len(self.recent_events) > self.cooldown_count:
            self.recent_events.pop(0)
    
    # =========================================================================
    # Effect Application
    # =========================================================================
    
    @staticmethod
    def apply_effects(effects: Dict, party, travel_manager=None) -> Dict:
        """
        Apply event effects to the game state.
        
        Args:
            effects: Dict of effect name to value
            party: Party object to modify
            travel_manager: Optional TravelManager for travel effects
        
        Returns:
            Dict describing what was applied
        """
        results = {
            "applied": [],
            "messages": [],
        }
        
        # Resource effects
        resource_mapping = {
            "food_gained": ("food", "add"),
            "food_lost": ("food", "remove"),
            "water_gained": ("water", "add"),
            "water_lost": ("water", "remove"),
            "ammo_gained": ("ammunition", "add"),
            "ammo_lost": ("ammunition", "remove"),
            "medical_gained": ("medical", "add"),
            "medical_lost": ("medical", "remove"),
            "money_gained": ("money", "add"),
            "money_lost": ("money", "remove"),
            "clothing_gained": ("clothing", "add"),
            "clothing_lost": ("clothing", "remove"),
            "tools_lost": ("tools", "remove"),
        }
        
        for effect_name, (resource, action) in resource_mapping.items():
            if effect_name in effects:
                amount = effects[effect_name]
                if party and hasattr(party, 'resources'):
                    from resources import ResourceType
                    try:
                        rt = ResourceType(resource)
                        if action == "add":
                            party.resources.add(rt, amount)
                            results["messages"].append(f"Gained {amount} {resource}")
                        else:
                            party.resources.remove(rt, amount)
                            results["messages"].append(f"Lost {amount} {resource}")
                        results["applied"].append(effect_name)
                    except (ValueError, KeyError):
                        pass
        
        # Health effects
        if "health_damage" in effects:
            damage = effects["health_damage"]
            if party:
                # Apply to random party member or all
                for member in party.alive_members:
                    member.take_damage(damage // len(party.alive_members))
                results["messages"].append(f"Party took {damage} damage")
                results["applied"].append("health_damage")
        
        if "health_healed" in effects:
            heal = effects["health_healed"]
            if party:
                party.heal_party(heal)
                results["messages"].append(f"Party healed {heal} HP")
                results["applied"].append("health_healed")
        
        # Morale effects
        if "morale" in effects:
            change = effects["morale"]
            if party:
                party.change_party_morale(change)
                if change > 0:
                    results["messages"].append(f"Morale increased by {change}")
                elif change < 0:
                    results["messages"].append(f"Morale decreased by {abs(change)}")
                results["applied"].append("morale")
        
        # Condition effects
        if "condition" in effects:
            condition_name = effects["condition"]
            condition_chance = effects.get("condition_chance", 100)
            
            if random.randint(1, 100) <= condition_chance:
                if party:
                    from player import Condition
                    try:
                        cond = Condition(condition_name.upper()) if hasattr(Condition, condition_name.upper()) else None
                        if cond is None:
                            # Try to find by value
                            for c in Condition:
                                if c.value.lower() == condition_name.lower():
                                    cond = c
                                    break
                        
                        if cond:
                            # Apply to random party member
                            target = random.choice(party.alive_members) if party.alive_members else None
                            if target:
                                target.add_condition(cond)
                                results["messages"].append(f"{target.name} contracted {cond.value}")
                                results["applied"].append("condition")
                    except:
                        pass
        
        # Time effects
        if "days_lost" in effects:
            days = effects["days_lost"]
            if travel_manager:
                for _ in range(int(days)):
                    travel_manager.date.advance(1)
            results["messages"].append(f"Lost {days} day(s)")
            results["applied"].append("days_lost")
        
        if "miles_bonus" in effects:
            results["miles_bonus"] = effects["miles_bonus"]
            results["messages"].append(f"Travel bonus: {effects['miles_bonus']} miles")
            results["applied"].append("miles_bonus")
        
        # Scouting bonus
        if "scouting_bonus" in effects:
            results["scouting_bonus"] = effects["scouting_bonus"]
            results["messages"].append(f"Scouting improved for upcoming travel")
            results["applied"].append("scouting_bonus")
        
        return results
    
    # =========================================================================
    # Context Building
    # =========================================================================
    
    @staticmethod
    def build_context(party, travel_manager=None) -> Dict:
        """
        Build context dict for requirement checking.
        
        Args:
            party: Party object
            travel_manager: Optional TravelManager
        
        Returns:
            Context dict with resources and skills
        """
        context = {
            "resources": {},
            "skills": {},
        }
        
        if party:
            # Get resource quantities
            if hasattr(party, 'resources'):
                from resources import ResourceType
                context["resources"] = {
                    "food": party.resources.get_quantity(ResourceType.FOOD),
                    "water": party.resources.get_quantity(ResourceType.WATER),
                    "ammunition": party.resources.get_quantity(ResourceType.AMMUNITION),
                    "medical": party.resources.get_quantity(ResourceType.MEDICAL),
                    "money": party.resources.get_quantity(ResourceType.MONEY),
                    "tools": party.resources.get_quantity(ResourceType.TOOLS),
                    "clothing": party.resources.get_quantity(ResourceType.CLOTHING),
                }
            
            # Get party skill bonuses
            if hasattr(party, 'get_party_skill_bonus'):
                context["skills"] = {
                    "navigation": party.get_party_skill_bonus("navigation"),
                    "hunting": party.get_party_skill_bonus("hunting"),
                    "healing": party.get_party_skill_bonus("healing"),
                    "scouting": party.get_party_skill_bonus("scouting"),
                    "repair": party.get_party_skill_bonus("repair"),
                }
        
        return context
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """Convert state to dictionary for saving."""
        return {
            "event_history": self.event_history,
            "recent_events": self.recent_events,
        }
    
    def load_state(self, data: Dict):
        """Load state from dictionary."""
        self.event_history = data.get("event_history", [])
        self.recent_events = data.get("recent_events", [])
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    def get_statistics(self) -> Dict:
        """Get statistics about events encountered."""
        stats = {
            "total_events": len(self.event_history),
            "by_outcome": {"success": 0, "partial": 0, "failure": 0},
            "by_category": {},
        }
        
        for record in self.event_history:
            outcome = record.get("outcome_type", "unknown")
            if outcome in stats["by_outcome"]:
                stats["by_outcome"][outcome] += 1
        
        return stats


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate event system functionality."""
    print("=" * 50)
    print("EVENT SYSTEM DEMO")
    print("=" * 50)
    print()
    
    # Initialize event manager
    em = EventManager()
    
    print(f"Loaded {len(em.events)} events")
    print(f"Categories: {em.categories}")
    print()
    
    # Show some events
    print("Sample events:")
    for event in em.events[:3]:
        print(f"\n  [{event.category}] {event.name}")
        print(f"  Terrain: {event.terrain}")
        print(f"  Season: {event.season}")
        print(f"  Weight: {event.weight}")
        print(f"  Choices: {len(event.choices)}")
    print()
    
    # Test event selection
    print("Testing event selection for mountains in winter...")
    eligible = em.get_eligible_events("mountains", "winter")
    print(f"  Eligible events: {len(eligible)}")
    for e in eligible[:5]:
        print(f"    - {e.name} (weight: {e.weight})")
    print()
    
    # Select random event
    print("Selecting random event...")
    event = em.select_random_event("mountains", "winter")
    if event:
        print(f"\n  Selected: {event.name}")
        print(f"  {event.description}")
        print("\n  Choices:")
        
        # Build mock context
        mock_context = {
            "resources": {
                "food": 100,
                "ammunition": 30,
                "medical": 5,
                "money": 50,
                "tools": 2,
            },
            "skills": {
                "scouting": 40,
                "hunting": 30,
                "navigation": 25,
            }
        }
        
        for i, (choice, available, reason) in enumerate(event.get_available_choices(mock_context)):
            status = "✓" if available else f"✗ ({reason})"
            print(f"    {i + 1}) {choice.text} {status}")
        
        # Resolve first available choice
        print("\n  Resolving first available choice...")
        for i, (choice, available, _) in enumerate(event.get_available_choices(mock_context)):
            if available:
                result = em.resolve_choice(event, i, mock_context)
                print(f"\n  Choice: {result['choice_text']}")
                print(f"  Outcome: {result['outcome_type'].upper()}")
                print(f"  {result['outcome_description']}")
                print(f"  Effects: {result['effects']}")
                break
    print()
    
    # Test event triggering probability
    print("Testing event trigger probability (1000 samples, 25% base)...")
    triggers = sum(1 for _ in range(1000) if em.should_trigger_event(0.25))
    print(f"  Triggered: {triggers}/1000 ({triggers/10:.1f}%)")
    
    # With modifiers
    modifiers = {"scout_bonus": 40, "terrain_danger": 20}
    triggers_mod = sum(1 for _ in range(1000) if em.should_trigger_event(0.25, modifiers))
    print(f"  With scout bonus and terrain danger: {triggers_mod}/1000 ({triggers_mod/10:.1f}%)")
    print()
    
    # Statistics
    print("Event statistics:")
    stats = em.get_statistics()
    print(f"  Total events: {stats['total_events']}")
    print(f"  By outcome: {stats['by_outcome']}")
    print()
    
    print("Demo complete!")


if __name__ == "__main__":
    demo()