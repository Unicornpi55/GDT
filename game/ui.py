"""
ui.py - Terminal UI utilities for The Great Divide Trail

Provides consistent formatting, display functions, and input handling
for the terminal-based game interface.
"""

import os
import sys
from typing import List, Dict, Optional, Any

# =============================================================================
# ANSI Color Codes (Optional - can be disabled)
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    ENABLED = True  # Set to False to disable all colors
    
    # Basic colors
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Foreground colors
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    
    @classmethod
    def disable(cls):
        """Disable all color output."""
        cls.ENABLED = False
    
    @classmethod
    def enable(cls):
        """Enable color output."""
        cls.ENABLED = True
    
    @classmethod
    def get(cls, color_name: str) -> str:
        """Get a color code, returning empty string if colors disabled."""
        if not cls.ENABLED:
            return ""
        return getattr(cls, color_name, "")


def colorize(text: str, color: str) -> str:
    """Apply color to text if colors are enabled."""
    if not Colors.ENABLED:
        return text
    color_code = getattr(Colors, color.upper(), "")
    return f"{color_code}{text}{Colors.RESET}"


# =============================================================================
# Screen Utilities
# =============================================================================

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_terminal_width() -> int:
    """Get the current terminal width, defaulting to 80."""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


# =============================================================================
# Dividers and Formatting
# =============================================================================

DIVIDER_CHAR = "─"
DIVIDER_DOUBLE = "═"
DIVIDER_WIDTH = 50


def divider(char: str = DIVIDER_CHAR, width: int = DIVIDER_WIDTH) -> str:
    """Create a horizontal divider line."""
    return char * width


def header(text: str, char: str = DIVIDER_CHAR, width: int = DIVIDER_WIDTH) -> str:
    """Create a centered header with dividers above and below."""
    lines = [
        divider(char, width),
        text.center(width),
        divider(char, width)
    ]
    return "\n".join(lines)


def box(text: str, width: int = DIVIDER_WIDTH, padding: int = 1) -> str:
    """Create a box around text."""
    lines = text.split("\n")
    inner_width = width - 4  # Account for borders and spaces
    
    result = ["┌" + "─" * (width - 2) + "┐"]
    
    # Add padding lines at top
    for _ in range(padding):
        result.append("│" + " " * (width - 2) + "│")
    
    # Add content lines
    for line in lines:
        # Truncate or pad line to fit
        if len(line) > inner_width:
            line = line[:inner_width - 3] + "..."
        padded = f" {line}".ljust(width - 2)
        result.append(f"│{padded}│")
    
    # Add padding lines at bottom
    for _ in range(padding):
        result.append("│" + " " * (width - 2) + "│")
    
    result.append("└" + "─" * (width - 2) + "┘")
    
    return "\n".join(result)


def title_screen(title: str, subtitle: str = "") -> str:
    """Create a game title screen."""
    width = DIVIDER_WIDTH
    lines = [
        "",
        divider(DIVIDER_DOUBLE, width),
        "",
        title.center(width),
        "",
    ]
    if subtitle:
        lines.append(subtitle.center(width))
        lines.append("")
    lines.append(divider(DIVIDER_DOUBLE, width))
    lines.append("")
    
    return "\n".join(lines)


# =============================================================================
# Status Display
# =============================================================================

def status_bar(items: Dict[str, Any], width: int = DIVIDER_WIDTH) -> str:
    """
    Create a status bar showing key-value pairs.
    
    Example:
        status_bar({"Food": "120 lbs", "Ammo": 38, "Morale": "Low"})
    """
    parts = [f"{k}: {v}" for k, v in items.items()]
    return " | ".join(parts)


def status_display(
    location: str,
    weather: str,
    date: str,
    resources: Dict[str, Any],
    party_status: str = ""
) -> str:
    """
    Create the main game status display.
    
    Returns a formatted status block showing current game state.
    """
    lines = [
        divider(),
        f"  Location: {location}",
        f"  Date: {date}  |  Weather: {weather}",
        divider("─", DIVIDER_WIDTH),
    ]
    
    # Resource line
    resource_parts = [f"{k}: {v}" for k, v in resources.items()]
    lines.append("  " + " | ".join(resource_parts))
    
    if party_status:
        lines.append(f"  Party: {party_status}")
    
    lines.append(divider())
    
    return "\n".join(lines)


def health_bar(current: int, maximum: int, width: int = 20, 
               filled_char: str = "█", empty_char: str = "░") -> str:
    """
    Create a text-based health/progress bar.
    
    Example: [████████░░░░░░░░░░░░] 40/100
    """
    if maximum <= 0:
        return f"[{empty_char * width}] 0/0"
    
    ratio = max(0, min(1, current / maximum))
    filled = int(width * ratio)
    empty = width - filled
    
    bar = f"[{filled_char * filled}{empty_char * empty}]"
    return f"{bar} {current}/{maximum}"


def morale_indicator(morale: int) -> str:
    """Convert morale value to descriptive text with optional color."""
    if morale >= 80:
        text = "Excellent"
        color = "GREEN"
    elif morale >= 60:
        text = "Good"
        color = "GREEN"
    elif morale >= 40:
        text = "Fair"
        color = "YELLOW"
    elif morale >= 20:
        text = "Low"
        color = "YELLOW"
    else:
        text = "Critical"
        color = "RED"
    
    return colorize(text, color)


def health_indicator(health: int) -> str:
    """Convert health value to descriptive text with optional color."""
    if health >= 80:
        text = "Healthy"
        color = "GREEN"
    elif health >= 60:
        text = "Good"
        color = "GREEN"
    elif health >= 40:
        text = "Fair"
        color = "YELLOW"
    elif health >= 20:
        text = "Poor"
        color = "RED"
    else:
        text = "Critical"
        color = "RED"
    
    return colorize(text, color)


# =============================================================================
# Menu System
# =============================================================================

def menu(options: List[str], title: str = "", prompt: str = "Choose an option: ") -> str:
    """
    Display a numbered menu and return the formatted string.
    
    Args:
        options: List of menu option strings
        title: Optional title above the menu
        prompt: The input prompt text
    
    Returns:
        Formatted menu string
    """
    lines = []
    
    if title:
        lines.append(title)
        lines.append("")
    
    for i, option in enumerate(options, 1):
        lines.append(f"  {i}) {option}")
    
    lines.append("")
    lines.append(prompt)
    
    return "\n".join(lines)


def get_menu_choice(options: List[str], title: str = "", 
                    prompt: str = "Choose an option: ") -> int:
    """
    Display a menu and get validated user input.
    
    Args:
        options: List of menu option strings
        title: Optional title above the menu
        prompt: The input prompt text
    
    Returns:
        Selected option index (0-based)
    """
    while True:
        print(menu(options, title, ""))
        try:
            choice = input(prompt).strip()
            
            # Handle empty input
            if not choice:
                print(colorize("Please enter a number.", "YELLOW"))
                continue
            
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(options):
                return choice_num - 1  # Return 0-based index
            else:
                print(colorize(f"Please choose a number between 1 and {len(options)}.", "YELLOW"))
        
        except ValueError:
            print(colorize("Invalid input. Please enter a number.", "YELLOW"))


def confirm(prompt: str = "Are you sure? (y/n): ") -> bool:
    """Get yes/no confirmation from user."""
    while True:
        response = input(prompt).strip().lower()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            print(colorize("Please enter 'y' or 'n'.", "YELLOW"))


def get_input(prompt: str, default: str = "", allow_empty: bool = False) -> str:
    """
    Get text input from user with optional default value.
    
    Args:
        prompt: The input prompt
        default: Default value if user enters nothing
        allow_empty: Whether to allow empty input
    
    Returns:
        User input string
    """
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    while True:
        response = input(full_prompt).strip()
        
        if not response:
            if default:
                return default
            elif allow_empty:
                return ""
            else:
                print(colorize("Input cannot be empty.", "YELLOW"))
                continue
        
        return response


def get_number(prompt: str, min_val: int = None, max_val: int = None, 
               default: int = None) -> int:
    """
    Get a number from user with optional bounds and default.
    
    Args:
        prompt: The input prompt
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        default: Default value if user enters nothing
    
    Returns:
        User input as integer
    """
    bounds = ""
    if min_val is not None and max_val is not None:
        bounds = f" ({min_val}-{max_val})"
    elif min_val is not None:
        bounds = f" (min: {min_val})"
    elif max_val is not None:
        bounds = f" (max: {max_val})"
    
    if default is not None:
        full_prompt = f"{prompt}{bounds} [{default}]: "
    else:
        full_prompt = f"{prompt}{bounds}: "
    
    while True:
        response = input(full_prompt).strip()
        
        if not response and default is not None:
            return default
        
        try:
            value = int(response)
            
            if min_val is not None and value < min_val:
                print(colorize(f"Value must be at least {min_val}.", "YELLOW"))
                continue
            
            if max_val is not None and value > max_val:
                print(colorize(f"Value must be at most {max_val}.", "YELLOW"))
                continue
            
            return value
        
        except ValueError:
            print(colorize("Please enter a valid number.", "YELLOW"))


# =============================================================================
# Message Display
# =============================================================================

def message(text: str, msg_type: str = "info") -> str:
    """
    Format a game message with appropriate styling.
    
    Args:
        text: The message text
        msg_type: One of 'info', 'success', 'warning', 'danger', 'event'
    
    Returns:
        Formatted message string
    """
    prefixes = {
        "info": ("ℹ", "CYAN"),
        "success": ("✓", "GREEN"),
        "warning": ("⚠", "YELLOW"),
        "danger": ("✗", "RED"),
        "event": ("★", "MAGENTA"),
    }
    
    symbol, color = prefixes.get(msg_type, ("•", "WHITE"))
    
    if Colors.ENABLED:
        return colorize(f" {symbol} {text}", color)
    else:
        return f" [{msg_type.upper()}] {text}"


def narrative(text: str, width: int = DIVIDER_WIDTH) -> str:
    """
    Format narrative/story text with proper wrapping.
    
    Wraps text to specified width and adds subtle formatting.
    """
    import textwrap
    
    wrapped = textwrap.fill(text, width=width - 4)
    lines = wrapped.split("\n")
    
    result = [""]
    for line in lines:
        result.append(f"  {line}")
    result.append("")
    
    return "\n".join(result)


def event_display(title: str, description: str, 
                  options: List[str] = None) -> str:
    """
    Display a game event with title, description, and options.
    
    Args:
        title: Event title
        description: Event description/narrative
        options: Optional list of choices
    
    Returns:
        Formatted event display string
    """
    lines = [
        "",
        divider("═"),
        colorize(f"  ★ {title}", "MAGENTA") if Colors.ENABLED else f"  [EVENT] {title}",
        divider("─"),
        narrative(description),
    ]
    
    if options:
        lines.append("")
        for i, option in enumerate(options, 1):
            lines.append(f"  {i}) {option}")
        lines.append("")
    
    lines.append(divider("═"))
    
    return "\n".join(lines)


# =============================================================================
# Party Display
# =============================================================================

def party_member_display(name: str, role: str, health: int, 
                         morale: int, conditions: List[str] = None) -> str:
    """
    Display a single party member's status.
    
    Args:
        name: Member name
        role: Member role/class
        health: Health value (0-100)
        morale: Morale value (0-100)
        conditions: List of current conditions/ailments
    
    Returns:
        Formatted party member display
    """
    lines = [
        f"  {name} ({role})",
        f"    Health: {health_bar(health, 100, 15)} {health_indicator(health)}",
        f"    Morale: {health_bar(morale, 100, 15)} {morale_indicator(morale)}",
    ]
    
    if conditions:
        cond_text = ", ".join(conditions)
        lines.append(f"    Status: {colorize(cond_text, 'RED')}")
    
    return "\n".join(lines)


def party_summary(members: List[Dict]) -> str:
    """
    Display a summary of the entire party.
    
    Args:
        members: List of dicts with keys: name, role, health, morale, conditions
    
    Returns:
        Formatted party summary
    """
    lines = [
        header("PARTY STATUS"),
        ""
    ]
    
    for member in members:
        lines.append(party_member_display(
            member.get("name", "Unknown"),
            member.get("role", "Traveler"),
            member.get("health", 100),
            member.get("morale", 100),
            member.get("conditions", [])
        ))
        lines.append("")
    
    lines.append(divider())
    
    return "\n".join(lines)


# =============================================================================
# Utility Functions
# =============================================================================

def pause(prompt: str = "Press Enter to continue..."):
    """Pause and wait for user to press Enter."""
    input(prompt)


def type_text(text: str, delay: float = 0.03):
    """
    Print text with a typewriter effect.
    
    Args:
        text: Text to display
        delay: Delay between characters in seconds
    """
    import time
    
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()  # Newline at end


def slow_print(text: str, delay: float = 0.5):
    """
    Print text line by line with delays.
    
    Args:
        text: Text to display (can contain newlines)
        delay: Delay between lines in seconds
    """
    import time
    
    for line in text.split("\n"):
        print(line)
        time.sleep(delay)


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demonstrate UI components."""
    clear_screen()
    
    # Title
    print(title_screen("THE GREAT DIVIDE TRAIL", "A Survival Journey - 1840"))
    pause()
    
    # Status display
    clear_screen()
    print(status_display(
        location="Upper Platte Basin",
        weather="Snowstorm",
        date="March 15, 1840",
        resources={"Food": "120 lbs", "Ammo": 38, "Morale": "Low"},
        party_status="4 members, 1 injured"
    ))
    
    # Menu
    options = ["Continue traveling", "Rest", "Hunt", "Check supplies", "Check party"]
    choice = get_menu_choice(options)
    print(f"\nYou selected: {options[choice]}")
    pause()
    
    # Event
    clear_screen()
    print(event_display(
        "Blizzard Approaching",
        "Dark clouds gather on the horizon. The temperature is dropping rapidly, "
        "and the wind is picking up. Your scout estimates you have about an hour "
        "before the storm hits. The nearest shelter is a small cave system about "
        "two miles to the east.",
        ["Push through the storm", "Seek shelter in the caves", "Set up camp here"]
    ))
    pause()
    
    # Party display
    clear_screen()
    members = [
        {"name": "John Walker", "role": "Trail Leader", "health": 85, "morale": 70, "conditions": []},
        {"name": "Mary Walker", "role": "Medic", "health": 100, "morale": 65, "conditions": []},
        {"name": "Thomas Grey", "role": "Hunter", "health": 45, "morale": 40, "conditions": ["Injured", "Exhausted"]},
        {"name": "Sarah Grey", "role": "Scout", "health": 90, "morale": 55, "conditions": []},
    ]
    print(party_summary(members))
    pause()
    
    # Messages
    clear_screen()
    print(header("MESSAGE TYPES"))
    print()
    print(message("You have arrived at Fort Laramie.", "info"))
    print(message("Successfully hunted 50 lbs of meat!", "success"))
    print(message("Food supplies are running low.", "warning"))
    print(message("Thomas Grey has fallen ill with dysentery.", "danger"))
    print(message("A stranger approaches your camp...", "event"))
    print()
    
    print("\nUI Demo complete!")


if __name__ == "__main__":
    demo()