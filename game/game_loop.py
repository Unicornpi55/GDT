"""
game_loop.py - Main Game Loop for The Great Divide Trail

The central game loop that ties together all systems and handles
the primary gameplay flow.
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
        self.save_manager = SaveManager()
        
        # Game settings
        self.difficulty = "normal"
        self.auto_save = True
        
        # Current event being processed
        self.current_event = None
        
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
        print("  • Make wise choices during random events")
        print("  • Hunt for food, but don't waste ammunition")
        print("  • Rest when injured or exhausted")
        print("  • Trade at settlements for supplies")
        print()
        print("PARTY ROLES:")
        for role in get_available_roles():
            print(f"  • {role['name']}: {role['description']}")
        print()
        print("TIPS:")
        print("  • Start your journey in spring for the best weather")
        print("  • Don't travel during blizzards")
        print("  • Scout ahead to avoid hazards")
        print("  • Keep medical supplies for emergencies")
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
        restored = SaveManager.restore_game_state(save_data)
        
        self.party = restored["party"]
        self.travel = restored["travel"]
        self.events = restored["events"]
        self.hunting = restored["hunting"]
        self.difficulty = restored["difficulty"]
        
        # Generate weather for current day if not already set
        if self.travel:
            self.travel.generate_weather()
    
    def _do_autosave(self):
        """Perform an autosave if enabled."""
        if not self.auto_save:
            return
        
        success, msg = self.save_manager.autosave(
            self.party,
            self.travel,
            self.events,
            self.hunting,
            self.difficulty
        )
        
        # Silent autosave - don't notify user unless there's an error
        if not success:
            print(message(f"Autosave failed: {msg}", "warning"))
    
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
        difficulties = ["Easy (More supplies, lower event chance)",
                       "Normal (Balanced experience)",
                       "Hard (Fewer supplies, more dangers)"]
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
        
        # Set starting supplies
        self.party.resources.set_starting_supplies(
            party_size=self.party.size,
            difficulty=self.difficulty
        )
        
        # Initialize other systems
        self.travel = TravelManager()
        self.events = EventManager()
        self.hunting = HuntingManager()
        
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
            "Check supplies",
            "Check party status",
            "Change rations",
            "Scout ahead",
            "Game menu"
        ]
        
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
        elif options[choice] == "Trade at settlement":
            self._trade()
        elif options[choice] == "Check supplies":
            self._check_supplies()
        elif options[choice] == "Check party status":
            self._check_party()
        elif options[choice] == "Change rations":
            self._change_rations()
        elif options[choice] == "Scout ahead":
            self._scout()
        elif options[choice] == "Game menu":
            self._game_menu()
    
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
        
        # Show distance info
        print(f"  Progress: {travel_status['progress']} ({travel_status['miles_traveled']} / "
              f"{travel_status['miles_traveled'] + travel_status['miles_remaining']} miles)")
        print(f"  Next: {travel_status['next_landmark']} ({travel_status['distance_to_next']} miles)")
        print()
    
    # =========================================================================
    # Actions: Travel
    # =========================================================================
    
    def _travel(self):
        """Handle travel action."""
        # Check for dangerous conditions
        weather_effects = self.travel.get_weather_effects()
        
        if self.travel.current_weather == Weather.BLIZZARD:
            print(message("A blizzard is raging! Travel is extremely dangerous.", "danger"))
            if not confirm("Are you sure you want to travel? (y/n): "):
                return
        
        # Calculate travel distance
        party_mod = self.party.get_travel_speed_modifier()
        weather_mod = weather_effects["speed_modifier"]
        
        miles = self.travel.calculate_travel_distance(
            party_speed_modifier=party_mod,
            weather_modifier=weather_mod
        )
        
        # Travel
        travel_result = self.travel.travel(miles)
        
        # Process daily effects on party
        terrain = self.travel.current_location.terrain
        weather = self.travel.current_weather.value
        daily_result = self.party.process_day(terrain=terrain, weather=weather)
        
        # Display results
        clear_screen()
        print(header("TRAVELING"))
        print()
        print(f"You traveled {travel_result['miles_traveled']} miles today.")
        print(f"Current location: {self.travel.current_location.name}")
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
        
        # Check for random event
        self._check_for_event()
        
        # Generate new weather for next day
        self.travel.generate_weather()
        
        # Autosave after travel
        self._do_autosave()
        
        print()
        pause()
    
    # =========================================================================
    # Actions: Rest
    # =========================================================================
    
    def _rest(self):
        """Handle rest action."""
        print()
        days = get_number("How many days to rest?", min_val=1, max_val=7, default=1)
        
        result = self.party.rest(days=days)
        
        clear_screen()
        print(header("RESTING"))
        print()
        print(f"Your party rested for {result['days_rested']} day(s).")
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
    
    # =========================================================================
    # Actions: Hunt
    # =========================================================================
    
    def _hunt(self):
        """Handle hunting action."""
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
        
        forecast = self.hunting.get_hunting_forecast(
            terrain=terrain,
            weather=weather,
            hunter_skill=hunter.get_effective_skill("hunting"),
            hunting_bonus=hunter.get_skill_bonus("hunting"),
            location_bonus=location_bonus
        )
        
        print()
        print(f"Hunter: {hunter.name} ({hunter.role_name})")
        print(f"Hunting prospects: {forecast['prospects']}")
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
        
        # Execute hunt
        result = self.hunting.hunt(
            terrain=terrain,
            weather=weather,
            hunter_skill=hunter.get_effective_skill("hunting"),
            hunting_bonus=hunter.get_skill_bonus("hunting"),
            ammo_available=int(ammo),
            style=style,
            location_bonus=location_bonus
        )
        
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
        
        # Handle injury
        if result.hunter_injured:
            hunter.take_damage(result.injury_damage)
            hunter.add_condition(Condition.INJURED)
            print(message(f"{hunter.name} was injured! (-{result.injury_damage} health)", "danger"))
        
        # Autosave after hunt
        self._do_autosave()
        
        print()
        pause()
    
    # =========================================================================
    # Actions: Trade
    # =========================================================================
    
    def _trade(self):
        """Handle trading at a settlement."""
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
        print()
        
        if not location.trade_goods:
            print("This settlement has no goods for trade.")
            pause()
            return
        
        # Show available goods
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
                price = location.base_prices[good]
                trade_options.append((good, price))
                print(f"  • {good.title()}: ${price:.2f} per unit")
        
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
    # Actions: Status Checks
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
    
    # =========================================================================
    # Actions: Scout
    # =========================================================================
    
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
    
    # =========================================================================
    # Events
    # =========================================================================
    
    def _check_for_event(self):
        """Check if a random event should trigger."""
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
        
        # Should event trigger?
        base_chance = {"easy": 0.15, "normal": 0.25, "hard": 0.35}.get(self.difficulty, 0.25)
        
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
        
        # Apply effects
        if result["effects"]:
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
        elif choice == 4:  # Toggle autosave
            self.auto_save = not self.auto_save
            status = "enabled" if self.auto_save else "disabled"
            print(message(f"Autosave {status}.", "info"))
            pause()
        elif choice == 5:  # Quit to main menu
            if confirm("Return to main menu? Unsaved progress will be lost. (y/n): "):
                self.state = GameState.MAIN_MENU
    
    def _show_statistics(self):
        """Show game statistics."""
        clear_screen()
        print(header("JOURNEY STATISTICS"))
        print()
        
        print(f"Expedition: {self.party.name}")
        print(f"Days traveled: {self.party.days_traveled}")
        print(f"Miles traveled: {self.travel.miles_traveled}")
        print(f"Progress: {self.travel.progress_percentage:.1f}%")
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
        print(f"Days to complete: {self.party.days_traveled}")
        print(f"Total distance: {self.travel.miles_traveled} miles")
        print(f"Survivors: {self.party.alive_count} of {self.party.size}")
        print()
        
        if self.party.alive_count == self.party.size:
            print(colorize("PERFECT JOURNEY - All party members survived!", "GREEN"))
        
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