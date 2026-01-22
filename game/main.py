#!/usr/bin/env python3
"""
The Great Divide Trail
======================
A terminal-based survival, resource-management, and narrative simulation game.

Set in 1840, lead your party from Santa Fe, New Mexico to Sitka, Alaska
along the spine of the Rocky Mountains. Manage supplies, make difficult
choices, and survive the 2,800-mile journey through untamed wilderness.

Inspired by The Oregon Trail and historical exploration narratives.

Usage:
    python main.py

Author: Great Divide Trail Project
Version: 1.0.0 (MVP)
"""

import sys
import os


def check_requirements():
    """Check that all required modules are available."""
    required_modules = [
        "ui",
        "player", 
        "party",
        "resources",
        "travel",
        "events",
        "hunting",
        "game_loop",
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError as e:
            missing.append(f"{module}: {e}")
    
    if missing:
        print("Error: Missing required modules:")
        for m in missing:
            print(f"  • {m}")
        print("\nMake sure all game files are in the same directory.")
        return False
    
    return True


def check_data_files():
    """Check that data files exist."""
    data_path = os.path.join(os.path.dirname(__file__), "data")
    
    required_files = [
        "locations.json",
        "events.json",
    ]
    
    missing = []
    for filename in required_files:
        filepath = os.path.join(data_path, filename)
        if not os.path.exists(filepath):
            missing.append(filepath)
    
    if missing:
        print("Warning: Missing data files:")
        for f in missing:
            print(f"  • {f}")
        print("\nThe game may not function correctly.")
        return False
    
    return True


def main():
    """Main entry point for the game."""
    # Add the game directory to path if needed
    game_dir = os.path.dirname(os.path.abspath(__file__))
    if game_dir not in sys.path:
        sys.path.insert(0, game_dir)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check data files (warning only)
    check_data_files()
    
    # Import and run the game
    try:
        from game_loop import Game
        
        game = Game()
        game.run()
        
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("\nIf this persists, please check that all game files are present.")
        
        # In debug mode, show full traceback
        if os.environ.get("DEBUG"):
            import traceback
            traceback.print_exc()
        
        sys.exit(1)


if __name__ == "__main__":
    main()