"""
game_loop.py - Main Game Loop for The Great Divide Trail

The central game loop that ties together all systems and handles
the primary gameplay flow.

ENHANCEMENTS v2:
- Fixed water refill at locations with water_available flag
- Added foraging system (berries, firewood, water)
- Added fishing system for rivers and lakes
- Added granular difficulty modifiers (event frequency, resource scarcity, healing rates)
- Added pace selection (slow/steady/normal/fast/grueling) affecting miles, health, morale
"""

import random
from typing import Dict, Optional, Callable
from enum import Enum

# Import game systems
from ui import (
    clear_screen, header, divider, status_display, message, narrative,
    event_display, party_summary, get_menu_choice, get_input, get_number,
    confirm, pause, title_screen, colorize, Colors, menu
)
from player import Player, Role, Condition, create_player, get_available_roles
from party import Party, create_default_party
from resources import ResourceManager, ResourceType
from travel import TravelManager, Weather, Season
from events import EventManager
from hunting import HuntingManager, HuntingStyle
from equipment import EquipmentManager
from save_manager import SaveManager, format_save_slot_display, AUTOSAVE_SLOT, MAX_SAVE_SLOTS


# =============================================================================
# Game States
# =============================================================================

class GameState(Enum):
    """Possible states of the game."""
    MAIN_MENU = "main_menu"
    NEW_GAME = "new_game"
    PLAYING = "playing"
    PAUSED = "paused"
    EVENT = "event"
    GAME_OVER = "game_over"
    VICTORY = "victory"
    QUIT = "quit"


# =============================================================================
# Difficulty Settings
# =============================================================================

DIFFICULTY_MODIFIERS = {
    "easy": {
        "event_frequency": 0.15,      # 15% base event chance
        "resource_consumption": 0.75,  # 25% less consumption
        "resource_decay": 0.5,         # 50% slower decay
        "healing_rate": 1.5,           # 50% faster healing
        "injury_chance": 0.7,          # 30% less injury chance
        "starting_supplies": 1.5,      # 50% more starting supplies
        "hunt_success": 1.2,           # 20% better hunting
        "trade_prices": 0.9,           # 10% cheaper prices
    },
    "normal": {
        "event_frequency": 0.25,
        "resource_consumption": 1.0,
        "resource_decay": 1.0,
        "healing_rate": 1.0,
        "injury_chance": 1.0,
        "starting_supplies": 1.0,
        "hunt_success": 1.0,
        "trade_prices": 1.0,
    },
    "hard": {
        "event_frequency": 0.35,       # 35% base event chance
        "resource_consumption": 1.3,   # 30% more consumption
        "resource_decay": 1.5,         # 50% faster decay
        "healing_rate": 0.7,           # 30% slower healing
        "injury_chance": 1.3,          # 30% more injury chance
        "starting_supplies": 0.7,      # 30% fewer starting supplies
        "hunt_success": 0.8,           # 20% worse hunting
        "trade_prices": 1.2,           # 20% more expensive
    },
}


# =============================================================================
# Pace Settings
# =============================================================================

class TravelPace(Enum):
    """Travel pace options."""
    SLOW = "slow"
    STEADY = "steady"
    NORMAL = "normal"
    FAST = "fast"
    GRUELING = "grueling"


PACE_MODIFIERS = {
    TravelPace.SLOW: {
        "speed": 0.7,           # 30% slower
        "health_effect": 5,     # +5 health per day
        "morale_effect": 3,     # +3 morale per day
        "injury_risk": 0.5,     # 50% less injury risk
        "description": "Slow and Careful - Lower injury risk, health recovery",
    },
    TravelPace.STEADY: {
        "speed": 0.85,          # 15% slower
        "health_effect": 2,     # +2 health per day
        "morale_effect": 1,     # +1 morale per day
        "injury_risk": 0.75,    # 25% less injury risk
        "description": "Steady Pace - Slight health recovery, reduced risk",
    },
    TravelPace.NORMAL: {
        "speed": 1.0,           # Normal speed
        "health_effect": 0,     # No change
        "morale_effect": 0,     # No change
        "injury_risk": 1.0,     # Normal risk
        "description": "Normal Pace - Balanced travel",
    },
    TravelPace.FAST: {
        "speed": 1.25,          # 25% faster
        "health_effect": -3,    # -3 health per day
        "morale_effect": -2,    # -2 morale per day
        "injury_risk": 1.3,     # 30% more injury risk
        "description": "Fast Pace - Cover more ground, increased fatigue",
    },
    TravelPace.GRUELING: {
        "speed": 1.5,           # 50% faster
        "health_effect": -8,    # -8 health per day
        "morale_effect": -5,    # -5 morale per day
        "injury_risk": 2.0,     # 100% more injury risk
        "description": "Grueling Pace - Maximum distance, severe exhaustion",
    },
}


# =============================================================================
# Foraging & Fishing Results
# =============================================================================

def forage_for_resources(location_terrain: str, party_skill: int, time_hours: int = 3) -> Dict:
    """
    Forage for berries, water, and firewood.
    
    Args:
        location_terrain: Current terrain type
        party_skill: Best foraging skill in party
        time_hours: Hours spent foraging
    
    Returns:
        Dict with results
    """
    results = {
        "berries_found": 0,
        "water_found": 0,
        "firewood_found": 0,
        "time_spent": time_hours,
        "success": False,
        "message": ""
    }
    
    # Terrain modifiers for foraging
    terrain_mods = {
        "forest": {"berries": 2.0, "water": 1.5, "wood": 2.0},
        "plains": {"berries": 1.0, "water": 0.5, "wood": 0.3},
        "mountains": {"berries": 0.8, "water": 1.2, "wood": 1.0},
        "desert": {"berries": 0.2, "water": 0.1, "wood": 0.2},
        "tundra": {"berries": 0.3, "water": 0.8, "wood": 0.4},
    }
    
    mods = terrain_mods.get(location_terrain, {"berries": 1.0, "water": 1.0, "wood": 1.0})
    
    # Skill affects yield (0-100 skill -> 0.5 to 1.5 multiplier)
    skill_mult = 0.5 + (party_skill / 100)
    
    # Base yields per hour
    base_berries = random.randint(2, 8) * time_hours
    base_water = random.randint(1, 4) * time_hours
    base_wood = random.randint(1, 3) * time_hours
    
    # Calculate final yields
    results["berries_found"] = int(base_berries * mods["berries"] * skill_mult)
    results["water_found"] = int(base_water * mods["water"] * skill_mult)
    results["firewood_found"] = int(base_wood * mods["wood"] * skill_mult)
    
    total_found = results["berries_found"] + results["water_found"] + results["firewood_found"]
    
    if total_found > 0:
        results["success"] = True
        items = []
        if results["berries_found"] > 0:
            items.append(f"{results['berries_found']} lbs of berries")
        if results["water_found"] > 0:
            items.append(f"{results['water_found']} gallons of water")
        if results["firewood_found"] > 0:
            items.append(f"{results['firewood_found']} bundles of firewood")
        results["message"] = f"Found: {', '.join(items)}"
    else:
        results["message"] = "Foraging expedition found nothing useful."
    
    return results


def fish_for_food(has_water: bool, party_skill: int, time_hours: int = 4) -> Dict:
    """
    Fish for food at rivers, lakes, or coastal areas.
    
    Args:
        has_water: Whether location has water available
        party_skill: Best fishing skill in party
        time_hours: Hours spent fishing
    
    Returns:
        Dict with results
    """
    results = {
        "fish_caught": 0,
        "time_spent": time_hours,
        "success": False,
        "message": ""
    }
    
    if not has_water:
        results["message"] = "No water nearby to fish in!"
        return results
    
    # Skill affects catch rate (0-100 skill -> 20% to 100% success per hour)
    success_chance = 0.2 + (party_skill / 125)
    
    # Try to catch fish for each hour
    for _ in range(time_hours):
        if random.random() < success_chance:
            # Caught something!
            catch_size = random.randint(3, 12)  # 3-12 lbs per fish
            results["fish_caught"] += catch_size
    
    if results["fish_caught"] > 0:
        results["success"] = True
        results["message"] = f"Caught {results['fish_caught']} lbs of fish!"
    else:
        results["message"] = "No luck fishing today. The fish weren't biting."
    
    return results


# =============================================================================
# Game Class
# =============================================================================

class Game:
    """
    Main game class that manages the game state and loop.
    """
    
    def __init__(self):
        """Initialize the game."""
        self.state = GameState.MAIN_MENU
        self.party: Optional[Party] = None
        self.travel: Optional[TravelManager] = None
        self.events: Optional[EventManager] = None
        self.hunting: Optional[HuntingManager] = None
        self.equipment: Optional[EquipmentManager] = None
        self.save_manager = SaveManager()
        
        # Game settings
        self.difficulty = "normal"
        self.current_pace = TravelPace.NORMAL
        self.auto_save = True
        
        # Current event being processed
        self.current_event = None
        
    # =========================================================================
    # Difficulty Helper
    # =========================================================================
    
    def get_difficulty_modifier(self, modifier_type: str) -> float:
        """
        Get a difficulty modifier value.
        
        Args:
            modifier_type: Type of modifier to get
        
        Returns:
            Modifier value
        """
        modifiers = DIFFICULTY_MODIFIERS.get(self.difficulty, DIFFICULTY_MODIFIERS["normal"])
        return modifiers.get(modifier_type, 1.0)
    
    # =========================================================================
    # Main Loop
    # =========================================================================
    
    def run(self):
        """Main game loop."""
        while self.state != GameState.QUIT:
            if self.state == GameState.MAIN_MENU:
                self._main_menu()
            elif self.state == GameState.NEW_GAME:
                self._new_game()
            elif self.state == GameState.PLAYING:
                self._game_turn()
            elif self.state == GameState.EVENT:
                self._handle_event()
            elif self.state == GameState.GAME_OVER:
                self._game_over()
            elif self.state == GameState.VICTORY:
                self._victory()
        
        print("\nThank you for playing The Great Divide Trail!")
    
    # =========================================================================
    # Main Menu
    # =========================================================================
    
    def _main_menu(self):
        """Display and handle main menu."""
        clear_screen()
        print(title_screen("THE GREAT DIVIDE TRAIL", "A Survival Journey - 1840"))
        
        # Build menu options dynamically
        options = []
        option_actions = []
        
        # Check for existing saves
        has_saves = self.save_manager.has_any_saves()
        
        if has_saves:
            options.append("Continue (Load Autosave)")
            option_actions.append("continue")
        
        options.extend([
            "New Game",
            "Quick Start (Default Party)",
        ])
        option_actions.extend(["new_game", "quick_start"])
        
        if has_saves:
            options.append("Load Game")
            option_actions.append("load_game")
        
        options.extend([
            "How to Play",
            "Quit"
        ])
        option_actions.extend(["help", "quit"])
        
        choice = get_menu_choice(options)
        action = option_actions[choice]
        
        if action == "continue":
            self._load_autosave()
        elif action == "new_game":
            self.state = GameState.NEW_GAME
        elif action == "quick_start":
            self._quick_start()
        elif action == "load_game":
            self._load_game_menu()
        elif action == "help":
            self._show_help()
        elif action == "quit":
            self.state = GameState.QUIT
    
    def _quick_start(self):
        """Start a new game with default settings."""
        self.party = create_default_party()
        self.travel = TravelManager()
        self.events = EventManager()
        self.hunting = HuntingManager()
        self.equipment = EquipmentManager()
        self.equipment.set_starting_equipment(
            party_size=self.party.size,
            difficulty=self.difficulty
        )
        
        # Apply difficulty modifiers to starting supplies
        supply_mult = self.get_difficulty_modifier("starting_supplies")
        if supply_mult != 1.0:
            for resource_type in [ResourceType.FOOD, ResourceType.WATER, ResourceType.AMMUNITION, 
                                 ResourceType.MEDICAL, ResourceType.CLOTHING]:
                current = self.party.resources.get_quantity(resource_type)
                self.party.resources.set_quantity(resource_type, current * supply_mult)
        
        # Generate initial weather
        self.travel.generate_weather()
        
        clear_screen()
        print(header("JOURNEY BEGINS"))
        print()
        print(narrative(
            "April 1, 1840. Your expedition sets out from Santa Fe, "
            "the ancient capital of New Mexico. Ahead lies 2,800 miles "
            "of wilderness - mountains, rivers, forests, and tundra. "
            "Your destination: the Russian settlement of Sitka in Alaska. "
            "May fortune favor the bold."
        ))
        print()
        print(f"Party: {self.party.name}")
        print(f"Members: {', '.join(m.name for m in self.party.members)}")
        print(f"Difficulty: {self.difficulty.title()}")
        print()
        pause()
        
        self.state = GameState.PLAYING
    
    def _show_help(self):
        """Display how to play information."""
        clear_screen()
        print(header("HOW TO PLAY"))
        print()
        print(narrative(
            "The Great Divide Trail is a survival game set in 1840. "
            "Lead your party from Santa Fe to Sitka, Alaska - a journey "
            "of nearly 3,000 miles through untamed wilderness."
        ))
        print()
        print("KEY CONCEPTS:")
        print("  • Manage your supplies: food, water, ammunition, medical supplies")
        print("  • Keep your party healthy and their morale high")
        print("  • Choose your travel pace wisely - faster = more exhaustion")
        print("  • Make wise choices during random events")
        print("  • Hunt for food, but don't waste ammunition")
        print("  • Forage for berries and firewood in forests")
        print("  • Fish at rivers and lakes for additional food")
        print("  • Refill water at rivers, lakes, and springs")
        print("  • Rest when injured or exhausted")
        print("  • Trade at settlements for supplies")
        print()
        print("TRAVEL PACE:")
        for pace in TravelPace:
            pace_info = PACE_MODIFIERS[pace]
            print(f"  • {pace.value.title()}: {pace_info['description']}")
        print()
        print("DIFFICULTY LEVELS:")
        print("  • Easy: More supplies, slower decay, better healing")
        print("  • Normal: Balanced experience")
        print("  • Hard: Fewer supplies, faster decay, more events")
        print()
        print("PARTY ROLES:")
        for role in get_available_roles():
            print(f"  • {role['name']}: {role['description']}")
        print()
        print("TIPS:")
        print("  • Start your journey in spring for the best weather")
        print("  • Don't travel during blizzards")
        print("  • Use slow pace when party is injured")
        print("  • Scout ahead to avoid hazards")
        print("  • Keep medical supplies for emergencies")
        print("  • Forage and fish to save ammunition")
        print()
        pause()
    
    # =========================================================================
    # Save/Load Methods
    # =========================================================================
    
    def _load_autosave(self):
        """Load the autosave and continue playing."""
        success, save_data, load_msg = self.save_manager.load_game(AUTOSAVE_SLOT)
        
        if not success:
            print(message(load_msg, "danger"))
            pause()
            return
        
        self._restore_from_save(save_data)
        
        print(message("Autosave loaded successfully!", "success"))
        pause()
        self.state = GameState.PLAYING
    
    def _load_game_menu(self):
        """Display load game menu."""
        while True:
            clear_screen()
            print(header("LOAD GAME"))
            print()
            
            slots = self.save_manager.get_save_slots()
            options = []
            valid_slots = []
            
            for slot_info in slots:
                display = format_save_slot_display(slot_info)
                options.append(display)
                if slot_info.get("exists") and not slot_info.get("corrupted"):
                    valid_slots.append(slot_info["slot"])
                else:
                    valid_slots.append(None)
            
            options.append("Back to Main Menu")
            
            print("Select a save to load:\n")
            choice = get_menu_choice(options)
            
            if choice == len(slots):  # Back
                return
            
            slot = valid_slots[choice]
            
            if slot is None:
                if slots[choice].get("corrupted"):
                    print(message("This save file is corrupted.", "danger"))
                else:
                    print(message("This slot is empty.", "warning"))
                pause()
                continue
            
            # Confirm load
            slot_info = slots[choice]
            print()
            print(f"Load {slot_info['summary'].get('party_name', 'Unknown')}?")
            print(f"  Location: {slot_info['summary'].get('location', 'Unknown')}")
            print(f"  Day: {slot_info['summary'].get('days_traveled', 0)}")
            
            if confirm("\nLoad this save? (y/n): "):
                success, save_data, msg = self.save_manager.load_game(slot)
                
                if success:
                    self._restore_from_save(save_data)
                    print(message("Game loaded successfully!", "success"))
                    pause()
                    self.state = GameState.PLAYING
                    return
                else:
                    print(message(msg, "danger"))
                    pause()
    
    def _save_game_menu(self):
        """Display save game menu."""
        while True:
            clear_screen()
            print(header("SAVE GAME"))
            print()
            
            slots = self.save_manager.get_save_slots()
            options = []
            
            # Skip autosave slot (index 0), start from slot 1
            for slot_info in slots[1:]:
                display = format_save_slot_display(slot_info)
                options.append(display)
            
            options.append("Back")
            
            print("Select a slot to save:\n")
            choice = get_menu_choice(options)
            
            if choice == len(slots) - 1:  # Back (accounting for skipped autosave)
                return
            
            slot = choice + 1  # Adjust for skipped autosave slot
            slot_info = slots[slot]
            
            # Confirm overwrite if slot has data
            if slot_info.get("exists"):
                print()
                print(f"This will overwrite: {slot_info['summary'].get('party_name', 'Unknown')}")
                if not confirm("Are you sure? (y/n): "):
                    continue
            
            # Save the game
            success, msg = self.save_manager.save_game(
                slot,
                self.party,
                self.travel,
                self.events,
                self.hunting,
                self.equipment,
                self.difficulty
            )
            
            if success:
                print(message(msg, "success"))
            else:
                print(message(msg, "danger"))
            
            pause()
            return
    
    def _restore_from_save(self, save_data: Dict):
        """
        Restore game state from save data.
        
        Args:
            save_data: Complete save data dictionary
        """
        try:
            restored = SaveManager.restore_game_state(save_data)
            
            self.party = restored["party"]
            self.travel = restored["travel"]
            self.events = restored["events"]
            self.hunting = restored["hunting"]
            self.difficulty = restored["difficulty"]
            
            # Restore pace if saved (default to normal if not)
            if "current_pace" in save_data.get("game_state", {}):
                pace_str = save_data["game_state"]["current_pace"]
                try:
                    self.current_pace = TravelPace(pace_str)
                except:
                    self.current_pace = TravelPace.NORMAL
            
            # Verify all objects were restored correctly
            if not self.party or not self.travel or not self.events or not self.hunting:
                print(message("Warning: Some game components failed to load", "warning"))
                # Re-initialize missing components
                if not self.travel:
                    self.travel = TravelManager()
                if not self.events:
                    self.events = EventManager()
                if not self.hunting:
                    self.hunting = HuntingManager()
            
            # Generate weather for current day if not already set
            if self.travel:
                self.travel.generate_weather()
        except Exception as e:
            print(message(f"Error restoring game state: {e}", "danger"))
            print(message("Some game features may not work correctly", "warning"))
            
            # Ensure minimum viable state
            if not self.travel:
                self.travel = TravelManager()
            if not self.events:
                self.events = EventManager()
            if not self.hunting:
                self.hunting = HuntingManager()
    
    def _do_autosave(self):
        """Perform an autosave if enabled."""
        if not self.auto_save:
            return
        
        # Defensive check: ensure all objects are valid before saving
        if not self.party or not self.travel or not self.events or not self.hunting:
            return
        
        # Check if any object is actually a string (shouldn't happen but defensive)
        if isinstance(self.party, str) or isinstance(self.travel, str) or \
           isinstance(self.events, str) or isinstance(self.hunting, str):
            return
        
        try:
            success, msg = self.save_manager.autosave(
                self.party,
                self.travel,
                self.events,
                self.hunting,
                self.equipment,
                self.difficulty
            )
            
            # Silent autosave - don't notify user unless there's an error
            if not success:
                print(message(f"Autosave failed: {msg}", "warning"))
        except Exception as e:
            # Silent failure for autosave
            pass
    
    # =========================================================================
    # New Game Setup
    # =========================================================================
    
    def _new_game(self):
        """Set up a new game with custom party."""
        clear_screen()
        print(header("CREATE YOUR EXPEDITION"))
        print()
        
        # Get expedition name
        party_name = get_input("Name your expedition", default="Pioneer Expedition")
        self.party = Party(name=party_name)
        
        # Select difficulty
        print("\nSelect difficulty:")
        difficulties = [
            "Easy (50% more supplies, slower decay, better healing)",
            "Normal (Balanced experience)",
            "Hard (30% fewer supplies, faster decay, more events)"
        ]
        diff_choice = get_menu_choice(difficulties)
        self.difficulty = ["easy", "normal", "hard"][diff_choice]
        
        # Get party size
        print()
        size = get_number("How many in your party?", min_val=1, max_val=5, default=4)
        
        # Get available roles
        roles = get_available_roles()
        role_names = [r["name"] for r in roles]
        
        # Create each member
        for i in range(size):
            clear_screen()
            print(header(f"PARTY MEMBER {i + 1} OF {size}"))
            print()
            
            name = get_input(f"Enter name")
            
            print("\nAvailable roles:")
            for j, role in enumerate(roles):
                print(f"  {j + 1}) {role['name']}: {role['description']}")
            
            role_idx = get_menu_choice(role_names, prompt="\nSelect role: ")
            role_name = role_names[role_idx]
            
            player = create_player(name, role_name)
            self.party.add_member(player)
            
            print(f"\n{colorize('✓', 'GREEN')} Added {player.name} as {player.role_name}")
            pause()
        
        # Set starting supplies with difficulty modifier
        supply_mult = self.get_difficulty_modifier("starting_supplies")
        self.party.resources.set_starting_supplies(
            party_size=self.party.size,
            difficulty="normal"  # Always use normal base, then multiply
        )
        
        # Apply difficulty multiplier
        if supply_mult != 1.0:
            for resource_type in [ResourceType.FOOD, ResourceType.WATER, ResourceType.AMMUNITION, 
                                 ResourceType.MEDICAL, ResourceType.CLOTHING]:
                current = self.party.resources.get_quantity(resource_type)
                self.party.resources.set_quantity(resource_type, current * supply_mult)
        
        # Initialize other systems
        self.travel = TravelManager()
        self.events = EventManager()
        self.hunting = HuntingManager()
        self.equipment = EquipmentManager()
        self.equipment.set_starting_equipment(
            party_size=self.party.size,
            difficulty=self.difficulty
)
        
        # Generate initial weather
        self.travel.generate_weather()
        
        # Show summary
        clear_screen()
        print(header("EXPEDITION READY"))
        print()
        print(f"Expedition: {self.party.name}")
        print(f"Difficulty: {self.difficulty.title()}")
        print(f"\nParty Members:")
        for member in self.party.members:
            print(f"  • {member.name} ({member.role_name})")
        print()
        print("Starting Supplies:")
        print(self.party.resources.get_full_display())
        print()
        
        if confirm("Begin your journey? (y/n): "):
            print()
            print(narrative(
                "April 1, 1840. With your supplies loaded and party assembled, "
                "you leave Santa Fe behind. The great Rocky Mountains beckon. "
                "The journey to Alaska begins."
            ))
            pause()
            self.state = GameState.PLAYING
        else:
            self.state = GameState.MAIN_MENU
    
    # =========================================================================
    # Main Game Turn
    # =========================================================================
    
    def _game_turn(self):
        """Execute one turn of the main game loop."""
        clear_screen()
        
        # Check for victory
        if self.travel.at_destination:
            self.state = GameState.VICTORY
            return
        
        # Check for game over
        if not self.party.is_party_alive():
            self.state = GameState.GAME_OVER
            return
        
        # Display status
        self._display_status()
        
        # Show main action menu
        options = [
            "Continue on the trail",
            "Rest",
            "Hunt for food",
            "Check equipment"
            "Repair Equipment"
            "Forage for supplies",
            "Check supplies",
            "Check party status",
            "Change rations",
            "Change travel pace",  # NEW
            "Scout ahead",
            "Game menu"
        ]
        
        # Add fishing option if at water location
        if self.travel.current_location.water_available:
            options.insert(4, "Fish for food")
        
        # Add water refill option if at water location
        if self.travel.current_location.water_available:
            options.insert(4, "Refill water")
        
        # Add trade option if at settlement
        if self.travel.current_location.is_settlement:
            options.insert(3, "Trade at settlement")
        
        choice = get_menu_choice(options, prompt="\nWhat do you want to do? ")
        
        # Handle choice
        if options[choice] == "Continue on the trail":
            self._travel()
        elif options[choice] == "Rest":
            self._rest()
        elif options[choice] == "Hunt for food":
            self._hunt()
        elif options[choice] == "Refill water":
            self._refill_water()
        elif options[choice] == "Fish for food":
            self._fish()
        elif options[choice] == "Forage for supplies":
            self._forage()
        elif options[choice] == "Trade at settlement":
            self._trade()
        elif options[choice] == "Check supplies":
            self._check_supplies()
        elif options[choice] == "Check party status":
            self._check_party()
        elif options[choice] == "Change rations":
            self._change_rations()
        elif options[choice] == "Change travel pace":
            self._change_pace()
        elif options[choice] == "Scout ahead":
            self._scout()
        elif options[choice] == "Game menu":
            self._game_menu()
        elif options[choice] == "Check equipment":
            self._check_equipment()
        elif options[choice] == "Repair equipment":
            self._repair_equipment()
    
    def _display_status(self):
        """Display current game status."""
        travel_status = self.travel.get_status_display()
        resource_display = self.party.resources.get_display_dict()
        
        print(status_display(
            location=travel_status["location"],
            weather=travel_status["weather"],
            date=travel_status["date"],
            resources=resource_display,
            party_status=self.party.get_party_status()
        ))

        broken = len(self.equipment.get_broken_items())
        if broken > 0:
            print(colorize(f"  ⚠ {broken} broken item(s)", "RED"))

        worn = len(self.equipment.get_worn_items(50))
        if worn > 0:
            print(colorize(f"  ⚠ {worn} worn item(s)", "YELLOW"))
        
        # Show distance info
        print(f"  Progress: {travel_status['progress']} ({travel_status['miles_traveled']} / "
              f"{travel_status['miles_traveled'] + travel_status['miles_remaining']} miles)")
        print(f"  Next: {travel_status['next_landmark']} ({travel_status['distance_to_next']} miles)")
        
        # Show current pace
        pace_info = PACE_MODIFIERS[self.current_pace]
        pace_color = "GREEN" if self.current_pace in [TravelPace.SLOW, TravelPace.STEADY] else \
                     "YELLOW" if self.current_pace == TravelPace.NORMAL else "RED"
        print(f"  Pace: {colorize(self.current_pace.value.title(), pace_color)} - {pace_info['description']}")
        
        # Show water available indicator
        if self.travel.current_location.water_available:
            print(colorize("  💧 Water source available here", "CYAN"))
        
        print()
    
    # =========================================================================
    # NEW Action: Change Pace
    # =========================================================================
    
    def _change_pace(self):
        """Change travel pace."""
        print()
        print(f"Current pace: {self.current_pace.value.title()}")
        print()
        
        options = []
        for pace in TravelPace:
            pace_info = PACE_MODIFIERS[pace]
            speed_pct = int((pace_info['speed'] - 1) * 100)
            speed_str = f"+{speed_pct}%" if speed_pct > 0 else f"{speed_pct}%" if speed_pct < 0 else "normal"
            options.append(f"{pace.value.title()} ({speed_str} speed) - {pace_info['description']}")
        
        choice = get_menu_choice(options, prompt="Select travel pace: ")
        
        pace_list = list(TravelPace)
        self.current_pace = pace_list[choice]
        
        pace_info = PACE_MODIFIERS[self.current_pace]
        print()
        print(message(f"Travel pace set to {self.current_pace.value.title()}", "info"))
        
        # Warn about extreme paces
        if self.current_pace == TravelPace.GRUELING:
            print(message("Warning: Grueling pace will severely exhaust your party!", "warning"))
        elif self.current_pace == TravelPace.FAST:
            print(message("Caution: Fast pace increases fatigue and injury risk.", "warning"))
        
        pause()
    
    # =========================================================================
    # Actions: Travel (Enhanced with Pace)
    # =========================================================================
    
    def _travel(self):
        """Handle travel action with pace modifiers."""
        # Check for dangerous conditions
        weather_effects = self.travel.get_weather_effects()
        
        if self.travel.current_weather == Weather.BLIZZARD:
            print(message("A blizzard is raging! Travel is extremely dangerous.", "danger"))
            if not confirm("Are you sure you want to travel? (y/n): "):
                return
        
        # Warn about grueling pace
        if self.current_pace == TravelPace.GRUELING:
            print(message("You're traveling at a GRUELING pace!", "warning"))
            if not confirm("This will severely exhaust your party. Continue? (y/n): "):
                return
        
        # Calculate travel distance with pace modifier
        party_mod = self.party.get_travel_speed_modifier()
        weather_mod = weather_effects["speed_modifier"]
        pace_mod = (PACE_MODIFIERS[self.current_pace]["speed"] - 1) * 100

        # Get equipment bonuses
        equipment_bonuses = self.equipment.get_party_bonuses()
        wagon_speed = equipment_bonuses.get("travel_speed", 0)
        cargo_capacity = equipment_bonuses.get("cargo_capacity", 0)
        
        # Add to speed calculation
        miles = self.travel.calculate_travel_distance(
            party_speed_modifier=party_mod + pace_mod + wagon_speed,
            weather_modifier=weather_mod
        )
        
        # Travel
        travel_result = self.travel.travel(miles)

        # Apply equipment wear
        usage = {
            EquipmentCategory.TRANSPORT: 1.0,  # Wagon always used
            EquipmentCategory.CAMPING: 1.0,     # Camp gear used daily
        }

        # Extra wear if traveling in harsh conditions
        if self.travel.current_weather in [Weather.STORM, Weather.BLIZZARD]:
            usage[EquipmentCategory.CAMPING] = 1.5

        equip_results = self.equipment.degrade_all(usage)

        # Display warnings
        for warning in equip_results["warnings"]:
            print(message(warning, "warning"))

        for broken in equip_results["broken"]:
            print(message(f"{broken} has broken!", "danger"))

        # Check critical equipment
        all_ok, issues = self.equipment.check_critical_equipment()
        if not all_ok:
            for issue in issues:
                print(message(issue, "danger"))
            # Optionally force repair or end game
        
        # Apply pace effects to party
        pace_info = PACE_MODIFIERS[self.current_pace]
        
        # Health effects from pace
        if pace_info["health_effect"] != 0:
            for member in self.party.alive_members:
                if pace_info["health_effect"] > 0:
                    member.heal(abs(pace_info["health_effect"]))
                else:
                    member.take_damage(abs(pace_info["health_effect"]))
        
        # Morale effects from pace
        if pace_info["morale_effect"] != 0:
            self.party.change_party_morale(pace_info["morale_effect"], f"{self.current_pace.value} pace")
        
        # Injury risk from pace
        if pace_info["injury_risk"] > 1.0 and random.random() < (pace_info["injury_risk"] - 1.0) * 0.3:
            # Someone got injured from exhaustion
            injured_member = random.choice(self.party.alive_members) if self.party.alive_members else None
            if injured_member:
                injured_member.add_condition(Condition.EXHAUSTED)
        
        # Process daily effects on party (with difficulty modifiers)
        terrain = self.travel.current_location.terrain
        weather = self.travel.current_weather.value
        weather_protection = self.equipment.get_total_bonus("weather_protection")
        daily_result = self.party.process_day(terrain=terrain, weather=weather)
        # Reduce weather damage
        if weather_protection > 0:
            # Reduce health damage from weather
            for member in self.party.alive_members:
                if weather_effects["health_risk"] > 0:
                    risk_reduction = weather_effects["health_risk"] * (weather_protection / 100)
                    # Apply reduced risk instead of full

        
        # Display results
        clear_screen()
        print(header("TRAVELING"))
        print()
        print(f"Traveling at {colorize(self.current_pace.value.title(), 'CYAN')} pace...")
        print(f"You traveled {travel_result['miles_traveled']} miles today.")
        print(f"Current location: {self.travel.current_location.name}")
        print()
        
        # Show pace effects
        if pace_info["health_effect"] != 0:
            effect_str = f"+{pace_info['health_effect']}" if pace_info['health_effect'] > 0 else str(pace_info['health_effect'])
            print(f"  Pace health effect: {effect_str} HP")
        if pace_info["morale_effect"] != 0:
            effect_str = f"+{pace_info['morale_effect']}" if pace_info['morale_effect'] > 0 else str(pace_info['morale_effect'])
            print(f"  Pace morale effect: {effect_str}")
        print()
        
        # Show locations reached
        for loc in travel_result["locations_reached"]:
            print(message(f"Reached {loc.name}", "success"))
            if loc.description:
                print(narrative(loc.description))
        
        # Show milestones
        for milestone in travel_result["milestones"]:
            print()
            print(colorize(f"★ {milestone}", "MAGENTA"))
        
        # Show daily results
        if daily_result["deaths"]:
            for name in daily_result["deaths"]:
                print()
                print(message(f"{name} has died.", "danger"))
        
        for warning in daily_result["warnings"]:
            print(message(warning, "warning"))
        
        # Check for random event (affected by difficulty)
        self._check_for_event()
        
        # Generate new weather for next day
        self.travel.generate_weather()
        
        # Autosave after travel
        self._do_autosave()
        
        print()
        pause()
    
    # =========================================================================
    # Actions: Rest (Enhanced with Difficulty)
    # =========================================================================
    
    def _rest(self):
        """Handle rest action with difficulty-modified healing."""
        print()
        days = get_number("How many days to rest?", min_val=1, max_val=7, default=1)
        
        # Apply difficulty modifier to healing
        healing_mult = self.get_difficulty_modifier("healing_rate")
        
        # Temporarily modify has_medic effect for healing
        result = self.party.rest(days=days)
        
        # Apply difficulty healing modifier
        if healing_mult != 1.0:
            for member in self.party.alive_members:
                current = member.health
                bonus_healing = int((current - member.health) * (healing_mult - 1.0))
                if bonus_healing > 0:
                    member.heal(bonus_healing)
                elif bonus_healing < 0:
                    member.take_damage(abs(bonus_healing))

        # In _rest() after healing:
        print("\nMaintaining equipment...")

        # Can do minor repairs while resting
        for item in self.equipment.get_worn_items(60):
            if random.random() < 0.3:  # 30% chance per day
                item.repair(
                    amount=20,
                    has_repair_kit=False,
                    mechanic_bonus=self.party.get_party_skill_bonus("repair")
                )
        
        clear_screen()
        print(header("RESTING"))
        print()
        print(f"Your party rested for {result['days_rested']} day(s).")
        
        if self.difficulty != "normal":
            diff_str = f"({self.difficulty} difficulty: {int((healing_mult - 1) * 100):+d}% healing)"
            print(f"  {diff_str}")
        print()
        
        if result["healing"]:
            print("Healing:")
            for heal in result["healing"]:
                print(f"  • {heal['name']} recovered {heal['amount']} health")
        
        if result["conditions_cleared"]:
            print("\nRecovered from:")
            for cleared in result["conditions_cleared"]:
                print(f"  • {cleared['name']}: {cleared['condition']}")
        
        print(f"\nMorale improved by {result['morale_boost']}")
        
        # Advance weather for rest days
        for _ in range(days):
            self.travel.generate_weather()
        
        # Autosave after rest
        self._do_autosave()
        
        print()
        pause()
    
    # (Continue in next part due to length...)
    # PART 2 - Copy this section and append it to game_loop_v2_pace_difficulty.py
# This continues from line ~1250 where we left off with the _rest method

    # =========================================================================
    # Actions: Hunt, Forage, Fish, Refill (Same as before)
    # =========================================================================
    
    def _hunt(self):
        """Handle hunting action."""

        # Get best weapon
        weapon = self.equipment.get_weapon_for_hunting()
        
        if not weapon:
            print(message("No usable weapons for hunting!", "danger"))
            pause()
            return
        
        # Get weapon bonuses
        weapon_bonuses = weapon.get_effective_bonuses()
        hunting_bonus = weapon_bonuses.get("hunting", 0)
        accuracy_bonus = weapon_bonuses.get("accuracy", 0)
        
        # Display weapon info
        print(f"Weapon: {weapon.name}")
        print(f"Condition: {weapon.condition.value.title()}")
        print(f"Hunting bonus: +{hunting_bonus:.0f}")
        print()

        # Check for hunter
        hunter = self.party.get_best_for_skill("hunting")
        if not hunter:
            print(message("No one is able to hunt right now.", "warning"))
            pause()
            return
        
        # Check ammo
        ammo = self.party.resources.get_quantity(ResourceType.AMMUNITION)
        if ammo < 2:
            print(message("Not enough ammunition to hunt!", "warning"))
            pause()
            return
        
        # Show hunting forecast
        terrain = self.travel.current_location.terrain
        weather = self.travel.current_weather.value
        location_bonus = self.travel.current_location.hunting_bonus
        
        # Apply difficulty modifier to hunt success
        hunt_mult = self.get_difficulty_modifier("hunt_success")
        effective_skill = int(hunter.get_effective_skill("hunting") * hunt_mult + hunting_bonus)
        
        forecast = self.hunting.get_hunting_forecast(
            terrain=terrain,
            weather=weather,
            hunter_skill=effective_skill,
            hunting_bonus=hunter.get_skill_bonus("hunting"),
            location_bonus=location_bonus
        )
        
        print()
        print(f"Hunter: {hunter.name} ({hunter.role_name})")
        print(f"Hunting prospects: {forecast['prospects']}")
        if self.difficulty != "normal":
            print(f"  (Difficulty modifier: {int((hunt_mult - 1) * 100):+d}%)")
        print(f"Available game: {', '.join(forecast['available_game'][:4])}")
        print()
        
        # Select hunting style
        styles = self.hunting.get_style_descriptions()
        style_options = [f"{s['name']} - {s['description']}" for s in styles]
        style_options.append("Cancel")
        
        choice = get_menu_choice(style_options, prompt="Select hunting approach: ")
        
        if choice == len(styles):  # Cancel
            return
        
        style = [HuntingStyle.CONSERVATIVE, HuntingStyle.NORMAL, HuntingStyle.AGGRESSIVE][choice]
        
        # Execute hunt with difficulty modifier
        result = self.hunting.hunt(
            terrain=terrain,
            weather=weather,
            hunter_skill=effective_skill,
            hunting_bonus=hunter.get_skill_bonus("hunting"),
            ammo_available=int(ammo),
            style=style,
            location_bonus=location_bonus
        )
        
        # Degrade weapon after use
        intensity = 1.5 if style == HuntingStyle.AGGRESSIVE else 1.0
        weapon.degrade(intensity)

        print()
        print(f"{weapon.name} durability: {weapon.durability_percentage:.0f}%")

        clear_screen()
        print(header("HUNTING"))
        print()
        print(f"{hunter.name} goes hunting...")
        print()
        
        for detail in result.details:
            print(f"  {detail}")
        
        print()
        
        if result.success:
            print(message(result.message, "success"))
            self.party.resources.add(ResourceType.FOOD, result.food_gained)
            self.party.apply_morale_event("successful_hunt")
        else:
            print(message(result.message, "warning"))
            self.party.apply_morale_event("failed_hunt")
        
        # Use ammo
        self.party.resources.remove(ResourceType.AMMUNITION, result.ammo_used)
        
        # Handle injury (with difficulty modifier)
        if result.hunter_injured:
            injury_mult = self.get_difficulty_modifier("injury_chance")
            adjusted_damage = int(result.injury_damage * injury_mult)
            hunter.take_damage(adjusted_damage)
            hunter.add_condition(Condition.INJURED)
            print(message(f"{hunter.name} was injured! (-{adjusted_damage} health)", "danger"))
        
        # Autosave after hunt
        self._do_autosave()
        
        print()
        pause()
    
    def _refill_water(self):
        """Refill water at a water source (rivers, lakes, springs)."""
        location = self.travel.current_location
        
        if not location.water_available:
            print(message("There's no water source here.", "warning"))
            pause()
            return
        
        water_resource = self.party.resources.get(ResourceType.WATER)
        current_water = water_resource.quantity
        max_water = water_resource.max_capacity
        
        if current_water >= max_water:
            print(message("Your water containers are already full.", "info"))
            pause()
            return
        
        clear_screen()
        print(header("REFILLING WATER"))
        print()
        print(narrative(
            f"Your party gathers at the water source. The water appears clear and fresh."
        ))
        print()
        print(f"Current water: {int(current_water)} / {int(max_water)} gallons")
        print()
        
        if confirm("Refill all water containers? (y/n): "):
            # Fill to max capacity
            self.party.resources.set_quantity(ResourceType.WATER, max_water)
            water_gained = max_water - current_water
            
            print()
            print(message(f"Refilled {int(water_gained)} gallons of water!", "success"))
            print(f"Water now: {int(max_water)} / {int(max_water)} gallons")
            
            # Small morale boost
            self.party.change_party_morale(5, "found water")
            
            # Takes time but no full day
            print()
            print("(This took about an hour)")
        
        print()
        pause()
    
    def _fish(self):
        """Fish for food at rivers and lakes."""
        location = self.travel.current_location
        
        if not location.water_available:
            print(message("There's no water to fish in here.", "warning"))
            pause()
            return
        
        # Get best fishing skill (using hunting skill as proxy)
        fisher = self.party.get_best_for_skill("hunting")
        if not fisher or not fisher.can_work:
            print(message("No one is able to fish right now.", "warning"))
            pause()
            return
        
        clear_screen()
        print(header("FISHING"))
        print()
        print(f"Fisher: {fisher.name}")
        print()
        
        # Fishing time options
        options = [
            "Quick fishing (~2 hours)",
            "Half-day fishing (~4 hours)",
            "All-day fishing (~8 hours)",
            "Cancel"
        ]
        
        time_map = {0: 2, 1: 4, 2: 8}
        
        choice = get_menu_choice(options, prompt="How long to fish? ")
        
        if choice == 3:  # Cancel
            return
        
        time_hours = time_map[choice]
        
        # Execute fishing (affected by difficulty through hunt_success)
        hunt_mult = self.get_difficulty_modifier("hunt_success")
        effective_skill = int(fisher.get_effective_skill("hunting") * hunt_mult)
        
        result = fish_for_food(
            has_water=location.water_available,
            party_skill=effective_skill,
            time_hours=time_hours
        )
        
        print()
        print(f"Fishing for {time_hours} hours...")
        print()
        
        if result["success"]:
            print(message(result["message"], "success"))
            self.party.resources.add(ResourceType.FOOD, result["fish_caught"])
            
            # Morale boost for successful fishing
            self.party.change_party_morale(5, "successful fishing")
        else:
            print(message(result["message"], "warning"))
            # Small morale penalty for wasted time
            self.party.change_party_morale(-3, "failed fishing")
        
        print()
        print(f"Time spent: {time_hours} hours")
        
        # Autosave after fishing
        self._do_autosave()
        
        print()
        pause()
    
    def _forage(self):
        """Forage for berries, water, and firewood."""
        forager = self.party.get_best_for_skill("scouting")
        if not forager or not forager.can_work:
            print(message("No one is able to forage right now.", "warning"))
            pause()
            return
        
        clear_screen()
        print(header("FORAGING"))
        print()
        print(f"Forager: {forager.name}")
        print(f"Terrain: {self.travel.get_current_terrain().name}")
        print()
        
        # Foraging time options
        options = [
            "Quick foraging (~2 hours)",
            "Half-day foraging (~4 hours)",
            "Cancel"
        ]
        
        time_map = {0: 2, 1: 4}
        
        choice = get_menu_choice(options, prompt="How long to forage? ")
        
        if choice == 2:  # Cancel
            return
        
        time_hours = time_map[choice]
        
        # Execute foraging (affected by difficulty through hunt_success)
        hunt_mult = self.get_difficulty_modifier("hunt_success")
        effective_skill = int(forager.get_effective_skill("scouting") * hunt_mult)
        
        result = forage_for_resources(
            location_terrain=self.travel.current_location.terrain,
            party_skill=effective_skill,
            time_hours=time_hours
        )
        
        print()
        print(f"Foraging for {time_hours} hours...")
        print()
        
        if result["success"]:
            print(message(result["message"], "success"))
            
            # Add resources found
            if result["berries_found"] > 0:
                self.party.resources.add(ResourceType.FOOD, result["berries_found"])
            if result["water_found"] > 0:
                self.party.resources.add(ResourceType.WATER, result["water_found"])
            
            # Morale boost for successful foraging
            self.party.change_party_morale(3, "successful foraging")
        else:
            print(message(result["message"], "warning"))
            # Small morale penalty for wasted time
            self.party.change_party_morale(-2, "failed foraging")
        
        print()
        print(f"Time spent: {time_hours} hours")
        
        # Autosave after foraging
        self._do_autosave()
        
        print()
        pause()
    
    # =========================================================================
    # Actions: Trade (Enhanced with Difficulty Price Modifier)
    # =========================================================================
    
    def _trade(self):
        """Handle trading at a settlement with difficulty-adjusted prices."""
        location = self.travel.current_location
        
        if not location.is_settlement:
            print(message("There's no one to trade with here.", "warning"))
            pause()
            return
        
        clear_screen()
        print(header(f"TRADING AT {location.name.upper()}"))
        print()
        print(f"Available services: {', '.join(location.services)}")
        print(f"Your money: ${self.party.resources.get_quantity(ResourceType.MONEY):.0f}")
        
        # Show difficulty price modifier
        price_mult = self.get_difficulty_modifier("trade_prices")
        if price_mult != 1.0:
            price_pct = int((price_mult - 1) * 100)
            print(f"  ({self.difficulty.title()} difficulty: {price_pct:+d}% price modifier)")
        print()
        
        if not location.trade_goods:
            print("This settlement has no goods for trade.")
            pause()
            return
        
        # Show available goods with adjusted prices
        print("Goods available:")
        trade_options = []
        
        resource_map = {
            "food": ResourceType.FOOD,
            "water": ResourceType.WATER,
            "ammunition": ResourceType.AMMUNITION,
            "medical": ResourceType.MEDICAL,
            "clothing": ResourceType.CLOTHING,
            "tools": ResourceType.TOOLS,
        }
        
        for good in location.trade_goods:
            if good in location.base_prices:
                base_price = location.base_prices[good]
                adjusted_price = base_price * price_mult
                trade_options.append((good, adjusted_price))
                print(f"  • {good.title()}: ${adjusted_price:.2f} per unit")
        
        # In _trade(), add equipment options:
        print("\nEquipment for sale:")

        # Example items available at settlement
        available_equipment = [
            ("flintlock_rifle", EquipmentRarity.COMMON, 40),
            ("repair_kit", EquipmentRarity.COMMON, 20),
            ("canvas_tent", EquipmentRarity.COMMON, 25),
        ]

        for item_type, rarity, price in available_equipment:
            adjusted_price = price * price_mult
            print(f"  • {EQUIPMENT_TYPES[item_type]['name']}: ${adjusted_price:.2f}")

        # Add to menu options
        options.append("Buy equipment")

        # Handler:
        if user_wants_equipment:
            # Show equipment menu
            # Purchase and add to inventory
            new_item = self.equipment.add_equipment(item_type, rarity)
            print(message(f"Bought {new_item.name}!", "success"))
        
        print()
        
        while True:
            print("\nOptions:")
            options = [f"Buy {g.title()}" for g, p in trade_options]
            options.append("Done trading")
            
            choice = get_menu_choice(options)
            
            if choice == len(trade_options):
                break
            
            good, price = trade_options[choice]
            rt = resource_map.get(good)
            
            money = self.party.resources.get_quantity(ResourceType.MONEY)
            max_afford = int(money / price)
            
            if max_afford < 1:
                print(message("You can't afford any!", "warning"))
                continue
            
            print(f"\nYou can afford up to {max_afford} {good}.")
            amount = get_number(f"How much {good} to buy?", min_val=0, max_val=max_afford, default=0)
            
            if amount > 0:
                total_cost = amount * price
                self.party.resources.remove(ResourceType.MONEY, total_cost)
                self.party.resources.add(rt, amount)
                print(message(f"Bought {amount} {good} for ${total_cost:.2f}", "success"))
        
        self.party.apply_morale_event("found_supplies")
    
    # =========================================================================
    # Actions: Status Checks (Same as before)
    # =========================================================================
    
    def _check_supplies(self):
        """Display detailed supply information."""
        clear_screen()
        print(header("SUPPLIES"))
        print()
        print(self.party.resources.get_full_display())
        print()
        
        # Days of supplies
        days = self.party.resources.days_of_supplies(
            self.party.alive_count,
            rationing=self.party.current_rationing
        )
        print("Days of supplies remaining:")
        print(f"  Food: {days.get(ResourceType.FOOD, 0)} days")
        print(f"  Water: {days.get(ResourceType.WATER, 0)} days")
        print(f"\nCurrent rationing: {self.party.current_rationing.title()}")
        print(f"Current difficulty: {self.difficulty.title()}")
        print()
        pause()
    
    def _check_party(self):
        """Display detailed party status."""
        clear_screen()
        members_display = self.party.get_members_display()
        print(party_summary(members_display))
        
        # Show averages
        print(f"Average health: {self.party.average_health:.0f}")
        print(f"Average morale: {self.party.average_morale:.0f}")
        print()
        pause()
    
    def _change_rations(self):
        """Change rationing level."""
        print()
        print("Current rationing:", self.party.current_rationing.title())
        print()
        
        options = self.party.get_rationing_options()
        option_texts = [f"{o['level'].title()}: {o['description']}" for o in options]
        
        choice = get_menu_choice(option_texts, prompt="Select rationing level: ")
        
        level = options[choice]["level"]
        self.party.set_rationing(level)
        print(message(f"Rationing set to {level}", "info"))
        pause()
    
    def _scout(self):
        """Send a scout ahead."""
        scout = self.party.get_best_for_skill("scouting")
        
        if not scout or not scout.can_work:
            print(message("No one is available to scout.", "warning"))
            pause()
            return
        
        scout_skill = scout.get_effective_skill("scouting")
        result = self.travel.scout_ahead(scout_skill)
        
        clear_screen()
        print(header("SCOUTING REPORT"))
        print()
        print(f"Scout: {scout.name}")
        print(f"Scouted {result['distance_scouted']} miles ahead.")
        print()
        
        if result["locations_found"]:
            print("Locations ahead:")
            for loc in result["locations_found"]:
                settlement = " [Settlement]" if loc["is_settlement"] else ""
                print(f"  • {loc['name']} ({loc['distance']} miles){settlement}")
                if "hazards" in loc:
                    print(f"    ⚠ Hazards: {', '.join(loc['hazards'])}")
        else:
            print("No notable locations within scouting range.")
        
        if result["hazards_spotted"]:
            print(f"\nHazards spotted: {', '.join(set(result['hazards_spotted']))}")
        
        if result["weather_forecast"]:
            print(f"\nWeather forecast: {result['weather_forecast']}")
        
        if result["hunting_prospects"]:
            print(f"Hunting prospects: {result['hunting_prospects']}")
        
        print()
        pause()
    
    def _check_equipment(self):
        """Display equipment inventory."""
        clear_screen()
        print(header("EQUIPMENT"))
        print()
        
        # Show by category
        for category in EquipmentCategory:
            items = self.equipment.get_by_category(category)
            if items:
                print(f"\n{category.value.upper()}:")
                for item in items:
                    print(f"  {item}")
        
        print()
        
        # Show summary
        status = self.equipment.get_status_summary()
        print(f"Total items: {status['total_items']}")
        print(f"Broken: {colorize(str(status['broken']), 'RED') if status['broken'] > 0 else '0'}")
        print(f"Worn: {colorize(str(status['worn']), 'YELLOW') if status['worn'] > 0 else '0'}")
        
        print()
        print("ACTIVE BONUSES:")
        bonuses = self.equipment.get_party_bonuses()
        if bonuses:
            for bonus_type, value in sorted(bonuses.items()):
                print(f"  {bonus_type.replace('_', ' ').title()}: +{value:.1f}")
        else:
            print("  None")
        
        print()
        pause()
    
    def _repair_equipment(self):
        """Repair worn or broken equipment."""
        worn = self.equipment.get_worn_items(80)
        broken = self.equipment.get_broken_items()
        
        if not worn and not broken:
            print(message("All equipment is in good condition!", "success"))
            pause()
            return
        
        clear_screen()
        print(header("REPAIR EQUIPMENT"))
        print()
        
        # Check for repair materials
        has_kit = self.equipment.has_usable("repair_kit")
        tools = self.party.resources.get_quantity(ResourceType.TOOLS)
        
        print(f"Repair Kit: {'Yes' if has_kit else 'No'}")
        print(f"Tools: {int(tools)} kits")
        print()
        
        # Get mechanic
        mechanic = self.party.get_best_for_skill("repair")
        mechanic_bonus = mechanic.get_skill_bonus("repair") if mechanic else 0
        
        if mechanic:
            print(f"Mechanic: {mechanic.name} (+{mechanic_bonus} bonus)")
        print()
        
        # Show items needing repair
        print("Items needing repair:")
        all_items = broken + worn
        for i, item in enumerate(all_items, 1):
            print(f"  {i}) {item}")
        
        print()
        options = [f"Repair {item.name}" for item in all_items]
        options.extend(["Repair all", "Cancel"])
        
        choice = get_menu_choice(options)
        
        if choice == len(all_items) + 1:  # Cancel
            return
        elif choice == len(all_items):  # Repair all
            use_kit = has_kit and confirm("Use repair kit? (y/n): ")
            
            results = self.equipment.repair_all_worn(
                threshold=80,
                repair_amount=50,
                use_repair_kit=use_kit,
                mechanic_bonus=mechanic_bonus
            )
            
            print()
            print(f"Repaired: {len(results['repaired'])} items")
            print(f"Failed: {len(results['failed'])} items")
            
            if use_kit:
                # Degrade or consume repair kit
                for kit in self.equipment.equipment:
                    if kit.item_type == "repair_kit":
                        kit.degrade(len(results['repaired']))
                        break
        else:
            # Repair single item
            item = all_items[choice]
            use_kit = has_kit and confirm("Use repair kit? (y/n): ")
            
            result = self.equipment.repair_item(
                item,
                repair_amount=50,
                use_repair_kit=use_kit,
                mechanic_bonus=mechanic_bonus
            )
            
            print()
            if result["success"]:
                print(message(result["message"], "success"))
                print(f"New durability: {result['new_durability']:.0f}%")
                
                if use_kit:
                    for kit in self.equipment.equipment:
                        if kit.item_type == "repair_kit":
                            kit.degrade(1.0)
                            break
            else:
                print(message(result["message"], "danger"))
        
        pause()

    # =========================================================================
    # Events (Enhanced with Difficulty Event Frequency)
    # =========================================================================
    
    def _check_for_event(self):
        """Check if a random event should trigger (affected by difficulty)."""
        # Calculate event chance modifiers
        modifiers = {
            "scout_bonus": self.party.get_party_skill_bonus("scouting"),
        }
        
        # Higher danger in bad weather
        if self.travel.current_weather in [Weather.STORM, Weather.BLIZZARD]:
            modifiers["weather_danger"] = 30
        
        # Check terrain danger
        terrain = self.travel.current_location.terrain
        if terrain in ["mountains", "tundra"]:
            modifiers["terrain_danger"] = 20
        
        # Get difficulty-based event frequency
        base_chance = self.get_difficulty_modifier("event_frequency")
        
        if self.events.should_trigger_event(base_chance, modifiers):
            # Select and trigger event
            event = self.events.select_random_event(
                terrain=terrain,
                season=self.travel.date.season.value,
                region=self.travel.current_location.region
            )
            
            if event:
                self.current_event = event
                self.state = GameState.EVENT
    
    def _handle_event(self):
        """Handle a triggered event."""
        if not self.current_event:
            self.state = GameState.PLAYING
            return
        
        event = self.current_event
        context = EventManager.build_context(self.party, self.travel)
        
        # Display event
        clear_screen()
        choices_info = event.get_available_choices(context)
        choice_texts = []
        
        for choice, available, reason in choices_info:
            if available:
                choice_texts.append(choice.text)
            else:
                choice_texts.append(f"{choice.text} (unavailable: {reason})")
        
        print(event_display(event.name, event.description, choice_texts))
        
        # Get player choice
        valid_choices = [i for i, (_, available, _) in enumerate(choices_info) if available]
        
        while True:
            try:
                choice_input = input("\nYour choice: ").strip()
                choice_idx = int(choice_input) - 1
                
                if choice_idx in valid_choices:
                    break
                else:
                    print(colorize("That option is not available.", "YELLOW"))
            except ValueError:
                print(colorize("Please enter a number.", "YELLOW"))
        
        # Resolve choice
        result = self.events.resolve_choice(event, choice_idx, context)
        
        # Display outcome
        print()
        print(divider("─"))
        
        if result["outcome_type"] == "success":
            print(colorize(f"\n{result['outcome_description']}", "GREEN"))
        elif result["outcome_type"] == "partial":
            print(colorize(f"\n{result['outcome_description']}", "YELLOW"))
        else:
            print(colorize(f"\n{result['outcome_description']}", "RED"))
        
        # Apply effects (with difficulty modifiers for injury)
        if result["effects"]:
            # Modify injury effects based on difficulty
            if "health_damage" in result["effects"]:
                injury_mult = self.get_difficulty_modifier("injury_chance")
                result["effects"]["health_damage"] = int(result["effects"]["health_damage"] * injury_mult)
            
            effect_result = EventManager.apply_effects(
                result["effects"],
                self.party,
                self.travel
            )
            
            if effect_result["messages"]:
                print()
                for msg in effect_result["messages"]:
                    print(f"  • {msg}")
        
        print()
        pause()
        
        # Autosave after event
        self._do_autosave()
        
        self.current_event = None
        self.state = GameState.PLAYING
    
    # =========================================================================
    # Game Menu
    # =========================================================================
    
    def _game_menu(self):
        """Display in-game menu."""
        print()
        options = [
            "Return to game",
            "Save game",
            "Load game",
            "View statistics",
            f"Current pace: {self.current_pace.value.title()}",
            f"Current difficulty: {self.difficulty.title()}",
            "Toggle autosave (currently " + ("ON" if self.auto_save else "OFF") + ")",
            "Quit to main menu"
        ]
        
        choice = get_menu_choice(options, title="GAME MENU")
        
        if choice == 0:  # Return to game
            return
        elif choice == 1:  # Save game
            self._save_game_menu()
        elif choice == 2:  # Load game
            if confirm("Load a game? Unsaved progress will be lost. (y/n): "):
                self._load_game_menu()
        elif choice == 3:  # View statistics
            self._show_statistics()
        elif choice == 4:  # Show pace info
            pace_info = PACE_MODIFIERS[self.current_pace]
            print()
            print(f"Current pace: {self.current_pace.value.title()}")
            print(f"  {pace_info['description']}")
            print(f"  Speed: {int((pace_info['speed'] - 1) * 100):+d}%")
            print(f"  Health effect: {pace_info['health_effect']:+d} HP/day")
            print(f"  Morale effect: {pace_info['morale_effect']:+d}/day")
            pause()
        elif choice == 5:  # Show difficulty info
            diff_mods = DIFFICULTY_MODIFIERS[self.difficulty]
            print()
            print(f"Current difficulty: {self.difficulty.title()}")
            print(f"  Event frequency: {int(diff_mods['event_frequency'] * 100)}%")
            print(f"  Resource consumption: {int((diff_mods['resource_consumption'] - 1) * 100):+d}%")
            print(f"  Healing rate: {int((diff_mods['healing_rate'] - 1) * 100):+d}%")
            print(f"  Hunt success: {int((diff_mods['hunt_success'] - 1) * 100):+d}%")
            pause()
        elif choice == 6:  # Toggle autosave
            self.auto_save = not self.auto_save
            status = "enabled" if self.auto_save else "disabled"
            print(message(f"Autosave {status}.", "info"))
            pause()
        elif choice == 7:  # Quit to main menu
            if confirm("Return to main menu? Unsaved progress will be lost. (y/n): "):
                self.state = GameState.MAIN_MENU
    
    def _show_statistics(self):
        """Show game statistics."""
        clear_screen()
        print(header("JOURNEY STATISTICS"))
        print()
        
        print(f"Expedition: {self.party.name}")
        print(f"Difficulty: {self.difficulty.title()}")
        print(f"Days traveled: {self.party.days_traveled}")
        print(f"Miles traveled: {self.travel.miles_traveled}")
        print(f"Progress: {self.travel.progress_percentage:.1f}%")
        print(f"Current pace: {self.current_pace.value.title()}")
        print()
        
        print("Party:")
        print(f"  Living members: {self.party.alive_count}")
        print(f"  Deaths: {len(self.party.dead_members)}")
        print()
        
        if self.party.death_log:
            print("Fallen:")
            for death in self.party.death_log:
                print(f"  • {death['name']} ({death['role']}) - Day {death['day']}: {death['cause']}")
            print()
        
        hunting_stats = self.hunting.get_statistics()
        print("Hunting:")
        print(f"  Total hunts: {hunting_stats['total_hunts']}")
        print(f"  Success rate: {hunting_stats['success_rate']:.1f}%")
        print(f"  Food gained: {hunting_stats['total_food']} lbs")
        print()
        
        event_stats = self.events.get_statistics()
        print("Events:")
        print(f"  Total events: {event_stats['total_events']}")
        print(f"  Outcomes: {event_stats['by_outcome']}")
        print()
        
        pause()
    
    # =========================================================================
    # End States
    # =========================================================================
    
    def _game_over(self):
        """Handle game over state."""
        clear_screen()
        print(header("GAME OVER"))
        print()
        print(narrative(
            "The wilderness has claimed your expedition. "
            "Your party has perished, their dreams of reaching Alaska "
            "fading into the vast emptiness of the frontier."
        ))
        print()
        print(f"Difficulty: {self.difficulty.title()}")
        print(f"Days survived: {self.party.days_traveled}")
        print(f"Miles traveled: {self.travel.miles_traveled}")
        print(f"Final location: {self.travel.current_location.name}")
        print()
        
        if self.party.death_log:
            print("The fallen:")
            for death in self.party.death_log:
                print(f"  • {death['name']} - Day {death['day']}")
        
        print()
        pause()
        self.state = GameState.MAIN_MENU
    
    def _victory(self):
        """Handle victory state."""
        clear_screen()
        print(header("VICTORY!"))
        print()
        print(colorize("★ ★ ★ CONGRATULATIONS ★ ★ ★", "MAGENTA"))
        print()
        print(narrative(
            "Against all odds, your expedition has reached Sitka! "
            "The onion domes of the Russian Orthodox church rise above "
            "the harbor as your weary party enters the settlement. "
            "You have conquered the Great Divide Trail!"
        ))
        print()
        print(f"Difficulty: {colorize(self.difficulty.upper(), 'CYAN')}")
        print(f"Days to complete: {self.party.days_traveled}")
        print(f"Total distance: {self.travel.miles_traveled} miles")
        print(f"Survivors: {self.party.alive_count} of {self.party.size}")
        print()
        
        if self.party.alive_count == self.party.size:
            print(colorize("PERFECT JOURNEY - All party members survived!", "GREEN"))
        
        if self.difficulty == "hard":
            print(colorize("LEGENDARY - Completed on HARD difficulty!", "MAGENTA"))
        
        print()
        pause()
        self.state = GameState.MAIN_MENU


# =============================================================================
# Entry Point
# =============================================================================

def main():
    """Main entry point."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()