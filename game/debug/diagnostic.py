#!/usr/bin/env python3
"""
diagnostic.py - Diagnostic script for The Great Divide Trail

Run this to diagnose autosave issues.
Usage: python diagnostic.py
"""

import sys
import os

# Add game directory to path
game_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, game_dir)

print("=" * 60)
print("THE GREAT DIVIDE TRAIL - DIAGNOSTIC TOOL")
print("=" * 60)
print()

# Test imports
print("Testing imports...")
try:
    from party import Party, create_default_party
    print("  ✓ party module OK")
except Exception as e:
    print(f"  ✗ party module ERROR: {e}")
    sys.exit(1)

try:
    from travel import TravelManager
    print("  ✓ travel module OK")
except Exception as e:
    print(f"  ✗ travel module ERROR: {e}")
    sys.exit(1)

try:
    from events import EventManager
    print("  ✓ events module OK")
except Exception as e:
    print(f"  ✗ events module ERROR: {e}")
    sys.exit(1)

try:
    from hunting import HuntingManager
    print("  ✓ hunting module OK")
except Exception as e:
    print(f"  ✗ hunting module ERROR: {e}")
    sys.exit(1)

try:
    from save_manager import SaveManager, create_save_data
    print("  ✓ save_manager module OK")
except Exception as e:
    print(f"  ✗ save_manager module ERROR: {e}")
    sys.exit(1)

print()
print("Creating test game objects...")

# Create objects
try:
    party = create_default_party()
    print(f"  ✓ Party created: {type(party).__name__}")
except Exception as e:
    print(f"  ✗ Party creation failed: {e}")
    sys.exit(1)

try:
    travel = TravelManager()
    print(f"  ✓ Travel created: {type(travel).__name__}")
except Exception as e:
    print(f"  ✗ Travel creation failed: {e}")
    sys.exit(1)

try:
    events = EventManager()
    print(f"  ✓ Events created: {type(events).__name__}")
except Exception as e:
    print(f"  ✗ Events creation failed: {e}")
    sys.exit(1)

try:
    hunting = HuntingManager()
    print(f"  ✓ Hunting created: {type(hunting).__name__}")
except Exception as e:
    print(f"  ✗ Hunting creation failed: {e}")
    sys.exit(1)

print()
print("Checking to_dict methods...")

# Check to_dict
try:
    party_dict = party.to_dict()
    print(f"  ✓ party.to_dict() works - returned {len(party_dict)} keys")
except Exception as e:
    print(f"  ✗ party.to_dict() failed: {e}")

try:
    travel_dict = travel.to_dict()
    print(f"  ✓ travel.to_dict() works - returned {len(travel_dict)} keys")
except Exception as e:
    print(f"  ✗ travel.to_dict() failed: {e}")

try:
    events_dict = events.to_dict()
    print(f"  ✓ events.to_dict() works - returned {len(events_dict)} keys")
except Exception as e:
    print(f"  ✗ events.to_dict() failed: {e}")

try:
    hunting_dict = hunting.to_dict()
    print(f"  ✓ hunting.to_dict() works - returned {len(hunting_dict)} keys")
except Exception as e:
    print(f"  ✗ hunting.to_dict() failed: {e}")

print()
print("Testing create_save_data...")

try:
    save_data = create_save_data(party, travel, events, hunting, "normal")
    print(f"  ✓ create_save_data() works")
    print(f"    - Save version: {save_data['meta']['version']}")
    print(f"    - Party name: {save_data['summary']['party_name']}")
    print(f"    - Difficulty: {save_data['game_state']['difficulty']}")
except Exception as e:
    print(f"  ✗ create_save_data() failed: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

print()
print("Testing SaveManager.autosave...")

try:
    sm = SaveManager()
    success, msg = sm.autosave(party, travel, events, hunting, "normal")
    if success:
        print(f"  ✓ Autosave succeeded: {msg}")
    else:
        print(f"  ✗ Autosave failed: {msg}")
except Exception as e:
    print(f"  ✗ Autosave raised exception: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

print()
print("=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
print()
print("If all tests passed above, the autosave issue is likely")
print("in the game_loop.py code, not the underlying modules.")
print()
print("If any tests failed, check the error messages above.")