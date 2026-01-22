"""
save_manager.py - Save/Load System for The Great Divide Trail

Handles game state serialization, save file management, and persistence.
Supports multiple save slots with metadata.
"""

import json
import os
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from gathering import GatheringManager, ForagingType, FishingMethod


# =============================================================================
# Constants
# =============================================================================

SAVE_VERSION = "1.0.0"
MAX_SAVE_SLOTS = 5
AUTOSAVE_SLOT = 0  # Slot 0 reserved for autosave

# Default save directory
DEFAULT_SAVE_DIR = os.path.join(os.path.expanduser("~"), ".great_divide_trail", "saves")


# =============================================================================
# Save Data Structure
# =============================================================================

def create_save_data(
    party,
    travel_manager,
    event_manager,
    hunting_manager,
    gathering_manager,
    difficulty: str = "normal"
) -> Dict:
    """
    Create a complete save data dictionary from game state.
    
    Args:
        party: Party object
        travel_manager: TravelManager object
        event_manager: EventManager object
        hunting_manager: HuntingManager object
        difficulty: Current difficulty setting
    
    Returns:
        Complete save data dictionary
    """
    return {
        "meta": {
            "version": SAVE_VERSION,
            "timestamp": datetime.now().isoformat(),
            "playtime_seconds": 0,  # Could track this if desired
        },
        "summary": {
            "party_name": party.name if party else "Unknown",
            "days_traveled": party.days_traveled if party else 0,
            "miles_traveled": travel_manager.miles_traveled if travel_manager else 0,
            "location": travel_manager.current_location.name if travel_manager else "Unknown",
            "alive_count": party.alive_count if party else 0,
            "total_members": party.size if party else 0,
            "difficulty": difficulty,
        },
        "game_state": {
            "difficulty": difficulty,
            "party": party.to_dict() if party else {},
            "travel": travel_manager.to_dict() if travel_manager else {},
            "events": event_manager.to_dict() if event_manager else {},
            "hunting": hunting_manager.to_dict() if hunting_manager else {},
            "gathering": gathering_manager.to_dict() if gathering_manager else {},
        }
    }


# =============================================================================
# Save Manager Class
# =============================================================================

class SaveManager:
    """
    Manages save files for the game.
    
    Handles:
    - Creating and loading save files
    - Managing multiple save slots
    - Autosave functionality
    - Save file validation
    """
    
    def __init__(self, save_dir: str = None):
        """
        Initialize the save manager.
        
        Args:
            save_dir: Directory for save files (default: ~/.great_divide_trail/saves)
        """
        self.save_dir = save_dir or DEFAULT_SAVE_DIR
        self._ensure_save_directory()
    
    def _ensure_save_directory(self):
        """Create save directory if it doesn't exist."""
        try:
            os.makedirs(self.save_dir, exist_ok=True)
        except OSError as e:
            print(f"Warning: Could not create save directory: {e}")
    
    def _get_save_path(self, slot: int) -> str:
        """Get the file path for a save slot."""
        if slot == AUTOSAVE_SLOT:
            filename = "autosave.json"
        else:
            filename = f"save_slot_{slot}.json"
        return os.path.join(self.save_dir, filename)
    
    # =========================================================================
    # Save Operations
    # =========================================================================
    
    def save_game(
        self,
        slot: int,
        party,
        travel_manager,
        event_manager,
        hunting_manager,
        difficulty: str = "normal"
    ) -> Tuple[bool, str]:
        """
        Save the current game state to a slot.
        
        Args:
            slot: Save slot number (0 = autosave, 1-5 = manual)
            party: Party object
            travel_manager: TravelManager object
            event_manager: EventManager object
            hunting_manager: HuntingManager object
            difficulty: Current difficulty setting
        
        Returns:
            Tuple of (success, message)
        """
        if slot < 0 or slot > MAX_SAVE_SLOTS:
            return (False, f"Invalid save slot: {slot}")
        
        try:
            save_data = create_save_data(
                party, travel_manager, event_manager, hunting_manager, difficulty
            )
            
            save_path = self._get_save_path(slot)
            
            # Write to temporary file first, then rename (atomic operation)
            temp_path = save_path + ".tmp"
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            # Rename temp file to actual save file
            if os.path.exists(save_path):
                os.remove(save_path)
            os.rename(temp_path, save_path)
            
            slot_name = "Autosave" if slot == AUTOSAVE_SLOT else f"Slot {slot}"
            return (True, f"Game saved to {slot_name}")
        
        except OSError as e:
            return (False, f"Failed to save game: {e}")
        except Exception as e:
            return (False, f"Unexpected error saving game: {e}")
    
    def autosave(
        self,
        party,
        travel_manager,
        event_manager,
        hunting_manager,
        difficulty: str = "normal"
    ) -> Tuple[bool, str]:
        """
        Perform an autosave.
        
        Args:
            Same as save_game
        
        Returns:
            Tuple of (success, message)
        """
        return self.save_game(
            AUTOSAVE_SLOT,
            party, travel_manager, event_manager, hunting_manager, difficulty
        )
    
    # =========================================================================
    # Load Operations
    # =========================================================================
    
    def load_game(self, slot: int) -> Tuple[bool, Dict, str]:
        """
        Load a game from a save slot.
        
        Args:
            slot: Save slot number
        
        Returns:
            Tuple of (success, save_data, message)
        """
        if slot < 0 or slot > MAX_SAVE_SLOTS:
            return (False, {}, f"Invalid save slot: {slot}")
        
        save_path = self._get_save_path(slot)
        
        if not os.path.exists(save_path):
            slot_name = "Autosave" if slot == AUTOSAVE_SLOT else f"Slot {slot}"
            return (False, {}, f"No save found in {slot_name}")
        
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # Validate save data
            is_valid, validation_msg = self._validate_save_data(save_data)
            if not is_valid:
                return (False, {}, f"Invalid save file: {validation_msg}")
            
            return (True, save_data, "Game loaded successfully")
        
        except json.JSONDecodeError as e:
            return (False, {}, f"Corrupted save file: {e}")
        except OSError as e:
            return (False, {}, f"Failed to load save: {e}")
        except Exception as e:
            return (False, {}, f"Unexpected error loading save: {e}")
    
    def _validate_save_data(self, save_data: Dict) -> Tuple[bool, str]:
        """
        Validate save data structure.
        
        Args:
            save_data: Loaded save data dictionary
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required top-level keys
        required_keys = ["meta", "summary", "game_state"]
        for key in required_keys:
            if key not in save_data:
                return (False, f"Missing required key: {key}")
        
        # Check version compatibility
        save_version = save_data.get("meta", {}).get("version", "0.0.0")
        if not self._is_version_compatible(save_version):
            return (False, f"Incompatible save version: {save_version}")
        
        # Check game state has required components
        game_state = save_data.get("game_state", {})
        state_keys = ["party", "travel"]
        for key in state_keys:
            if key not in game_state:
                return (False, f"Missing game state component: {key}")
        
        return (True, "")
    
    def _is_version_compatible(self, save_version: str) -> bool:
        """
        Check if a save version is compatible with current version.
        
        Args:
            save_version: Version string from save file
        
        Returns:
            True if compatible
        """
        # For now, accept any 1.x.x version
        try:
            major = int(save_version.split(".")[0])
            current_major = int(SAVE_VERSION.split(".")[0])
            return major == current_major
        except (ValueError, IndexError):
            return False
    
    # =========================================================================
    # Save Slot Management
    # =========================================================================
    
    def get_save_slots(self) -> List[Dict]:
        """
        Get information about all save slots.
        
        Returns:
            List of save slot info dictionaries
        """
        slots = []
        
        # Autosave slot
        slots.append(self._get_slot_info(AUTOSAVE_SLOT, "Autosave"))
        
        # Manual save slots
        for slot in range(1, MAX_SAVE_SLOTS + 1):
            slots.append(self._get_slot_info(slot, f"Save Slot {slot}"))
        
        return slots
    
    def _get_slot_info(self, slot: int, name: str) -> Dict:
        """
        Get information about a specific save slot.
        
        Args:
            slot: Slot number
            name: Display name for the slot
        
        Returns:
            Dictionary with slot information
        """
        save_path = self._get_save_path(slot)
        
        info = {
            "slot": slot,
            "name": name,
            "exists": False,
            "path": save_path,
        }
        
        if os.path.exists(save_path):
            try:
                with open(save_path, 'r', encoding='utf-8') as f:
                    save_data = json.load(f)
                
                info["exists"] = True
                info["summary"] = save_data.get("summary", {})
                info["timestamp"] = save_data.get("meta", {}).get("timestamp", "Unknown")
                
                # Parse timestamp for display
                try:
                    dt = datetime.fromisoformat(info["timestamp"])
                    info["date_display"] = dt.strftime("%b %d, %Y %I:%M %p")
                except:
                    info["date_display"] = info["timestamp"]
            
            except (json.JSONDecodeError, OSError):
                info["exists"] = True
                info["corrupted"] = True
                info["summary"] = {"party_name": "[Corrupted Save]"}
        
        return info
    
    def delete_save(self, slot: int) -> Tuple[bool, str]:
        """
        Delete a save file.
        
        Args:
            slot: Slot number to delete
        
        Returns:
            Tuple of (success, message)
        """
        if slot < 0 or slot > MAX_SAVE_SLOTS:
            return (False, f"Invalid save slot: {slot}")
        
        save_path = self._get_save_path(slot)
        
        if not os.path.exists(save_path):
            return (False, "No save file to delete")
        
        try:
            os.remove(save_path)
            slot_name = "Autosave" if slot == AUTOSAVE_SLOT else f"Slot {slot}"
            return (True, f"Deleted {slot_name}")
        except OSError as e:
            return (False, f"Failed to delete save: {e}")
    
    def has_any_saves(self) -> bool:
        """Check if any save files exist."""
        for slot in range(MAX_SAVE_SLOTS + 1):
            if os.path.exists(self._get_save_path(slot)):
                return True
        return False
    
    # =========================================================================
    # Game State Restoration
    # =========================================================================
    
    @staticmethod
    def restore_game_state(save_data: Dict) -> Dict:
        """
        Restore game objects from save data.
        
        Args:
            save_data: Complete save data dictionary
        
        Returns:
            Dictionary with restored game objects
        """
        from party import Party
        from travel import TravelManager
        from events import EventManager
        from hunting import HuntingManager
        
        game_state = save_data.get("game_state", {})
        
        # Restore party
        party = None
        if "party" in game_state and game_state["party"]:
            party = Party.from_dict(game_state["party"])
        
        # Restore travel manager
        travel = TravelManager()
        if "travel" in game_state:
            travel.load_state(game_state["travel"])
        
        # Restore event manager
        events = EventManager()
        if "events" in game_state:
            events.load_state(game_state["events"])
        
        # Restore hunting manager
        hunting = HuntingManager()
        if "hunting" in game_state:
            hunting.load_state(game_state["hunting"])

        # Restore gathering manager
        gathering = GatheringManager()
        if "gathering" in game_state:
            gathering.load_state(game_state["gathering"])
        
        # Get difficulty
        difficulty = game_state.get("difficulty", "normal")
        
        return {
            "party": party,
            "travel": travel,
            "events": events,
            "hunting": hunting,
            "gathering": gathering,
            "difficulty": difficulty,
        }


# =============================================================================
# Utility Functions
# =============================================================================

def format_save_slot_display(slot_info: Dict) -> str:
    """
    Format a save slot for display.
    
    Args:
        slot_info: Slot info dictionary from get_save_slots()
    
    Returns:
        Formatted string for display
    """
    if not slot_info.get("exists"):
        return f"{slot_info['name']}: [Empty]"
    
    if slot_info.get("corrupted"):
        return f"{slot_info['name']}: [Corrupted]"
    
    summary = slot_info.get("summary", {})
    date = slot_info.get("date_display", "Unknown date")
    
    party_name = summary.get("party_name", "Unknown")
    location = summary.get("location", "Unknown")
    days = summary.get("days_traveled", 0)
    alive = summary.get("alive_count", 0)
    total = summary.get("total_members", 0)
    
    return (f"{slot_info['name']}: {party_name} - Day {days}, {location} "
            f"({alive}/{total} alive) - {date}")


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate save system functionality."""
    print("=" * 50)
    print("SAVE SYSTEM DEMO")
    print("=" * 50)
    print()
    
    # Create save manager with test directory
    test_dir = os.path.join(os.path.dirname(__file__), "test_saves")
    sm = SaveManager(save_dir=test_dir)
    
    print(f"Save directory: {sm.save_dir}")
    print()
    
    # Create mock game objects for testing
    from party import create_default_party
    from travel import TravelManager
    from events import EventManager
    from hunting import HuntingManager
    
    party = create_default_party()
    travel = TravelManager()
    events = EventManager()
    hunting = HuntingManager()
    
    # Simulate some game progress
    party.days_traveled = 15
    travel.miles_traveled = 180
    travel.current_location_index = 3
    
    print("Mock game state created:")
    print(f"  Party: {party.name}")
    print(f"  Days: {party.days_traveled}")
    print(f"  Miles: {travel.miles_traveled}")
    print()
    
    # Test saving
    print("Testing save to slot 1...")
    success, message = sm.save_game(1, party, travel, events, hunting, "normal")
    print(f"  Result: {message}")
    print()
    
    # Test autosave
    print("Testing autosave...")
    success, message = sm.autosave(party, travel, events, hunting, "normal")
    print(f"  Result: {message}")
    print()
    
    # List save slots
    print("Save slots:")
    slots = sm.get_save_slots()
    for slot in slots:
        print(f"  {format_save_slot_display(slot)}")
    print()
    
    # Test loading
    print("Testing load from slot 1...")
    success, save_data, message = sm.load_game(1)
    print(f"  Result: {message}")
    
    if success:
        print(f"  Loaded party: {save_data['summary']['party_name']}")
        print(f"  Loaded days: {save_data['summary']['days_traveled']}")
        
        # Test state restoration
        print("\nRestoring game state...")
        restored = SaveManager.restore_game_state(save_data)
        print(f"  Restored party: {restored['party'].name}")
        print(f"  Restored days: {restored['party'].days_traveled}")
        print(f"  Restored miles: {restored['travel'].miles_traveled}")
    print()
    
    # Test loading non-existent slot
    print("Testing load from empty slot 5...")
    success, _, message = sm.load_game(5)
    print(f"  Result: {message}")
    print()
    
    # Clean up test saves
    print("Cleaning up test saves...")
    for slot in range(MAX_SAVE_SLOTS + 1):
        sm.delete_save(slot)
    
    # Remove test directory
    try:
        os.rmdir(test_dir)
        print("  Test directory removed.")
    except:
        pass
    
    print()
    print("Demo complete!")


if __name__ == "__main__":
    demo()