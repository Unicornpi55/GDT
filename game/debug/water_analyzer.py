#!/usr/bin/env python3
"""
Water Consumption Analyzer - The Great Divide Trail

Helps diagnose water management issues and shows consumption rates.
"""

def analyze_water_consumption():
    """Analyze water consumption for different scenarios."""
    print("=" * 60)
    print("WATER CONSUMPTION ANALYZER")
    print("=" * 60)
    print()
    
    # Base consumption: 1 gallon per person per day
    base_per_person = 1.0
    
    # Party size
    party_size = 4
    
    # Rationing levels
    rationing = {
        "filling": 1.5,
        "normal": 1.0,
        "meager": 0.5,
        "starving": 0.25,
    }
    
    # Terrain multipliers (from resources.py)
    terrain_mults = {
        "desert": 2.0,
        "plains": 1.0,
        "mountains": 1.0,
        "forest": 0.8,
        "tundra": 0.5,
        "river": 0.5,
    }
    
    # Default water capacity
    water_capacity = 100  # gallons
    
    print(f"Party Size: {party_size} people")
    print(f"Water Capacity: {water_capacity} gallons")
    print(f"Base Consumption: {base_per_person} gallon per person per day")
    print()
    
    print("DAILY CONSUMPTION BY TERRAIN & RATIONS:")
    print("-" * 60)
    print(f"{'Terrain':<15} {'Normal':<10} {'Filling':<10} {'Meager':<10} {'Days':<10}")
    print("-" * 60)
    
    for terrain, terrain_mult in terrain_mults.items():
        normal_daily = base_per_person * party_size * rationing["normal"] * terrain_mult
        filling_daily = base_per_person * party_size * rationing["filling"] * terrain_mult
        meager_daily = base_per_person * party_size * rationing["meager"] * terrain_mult
        
        days_normal = water_capacity / normal_daily if normal_daily > 0 else 999
        
        print(f"{terrain.title():<15} {normal_daily:<10.1f} {filling_daily:<10.1f} {meager_daily:<10.1f} {days_normal:<10.1f}")
    
    print()
    print("KEY INSIGHTS:")
    print("-" * 60)
    
    # Desert scenario (worst case)
    desert_days = water_capacity / (base_per_person * party_size * 2.0)
    print(f"❌ DESERT (Normal rations): {desert_days:.1f} days of water")
    print(f"   → You need water refills every ~{int(desert_days)} days in desert!")
    
    # Forest scenario (best case)
    forest_days = water_capacity / (base_per_person * party_size * 0.8)
    print(f"✓  FOREST (Normal rations): {forest_days:.1f} days of water")
    
    # Normal terrain
    normal_days = water_capacity / (base_per_person * party_size * 1.0)
    print(f"✓  PLAINS (Normal rations): {normal_days:.1f} days of water")
    
    print()
    print("RECOMMENDATIONS:")
    print("-" * 60)
    print("1. Always refill at water locations (look for 💧 indicator)")
    print("2. In desert: Refill every chance you get!")
    print("3. Use 'Meager' rations in desert to extend water (12.5 days)")
    print("4. Plan route to pass water locations every 15-20 days")
    print("5. Check locations.json for water_available: true")
    print()
    
    # Distance between water sources
    print("DISTANCE BETWEEN KEY WATER SOURCES:")
    print("-" * 60)
    water_locations = [
        ("Start (Santa Fe)", 0),
        ("San Luis Valley", 150),
        ("Steamboat Springs", 480),
        ("Three Forks", 1120),
        ("Flathead Lake", 1420),
        ("Peace River", 1900),
    ]
    
    for i in range(len(water_locations) - 1):
        current = water_locations[i]
        next_loc = water_locations[i + 1]
        distance = next_loc[1] - current[1]
        days_at_15_miles = distance / 15
        
        print(f"{current[0]} → {next_loc[0]}")
        print(f"  Distance: {distance} miles (~{days_at_15_miles:.1f} days at 15 miles/day)")
        
        # Check if water will last
        if days_at_15_miles > normal_days:
            print(f"  ⚠️  WARNING: Longer than {normal_days:.1f} days of water!")
        else:
            print(f"  ✓  Should have enough water")
    
    print()


def check_water_balance():
    """Check if water consumption is balanced."""
    print()
    print("=" * 60)
    print("WATER BALANCE CHECK")
    print("=" * 60)
    print()
    
    # Simulate a journey
    party_size = 4
    water = 100  # Start with full water
    days = 0
    
    print("Simulating 30-day journey (Plains, Normal rations)...")
    print()
    
    daily_consumption = 1.0 * party_size * 1.0 * 1.0  # base * party * ration * terrain
    
    for day in range(1, 31):
        water -= daily_consumption
        days = day
        
        if water <= 0:
            print(f"❌ RAN OUT OF WATER on Day {day}!")
            print(f"   Last water amount: {water + daily_consumption:.1f} gallons")
            print(f"   Daily consumption: {daily_consumption:.1f} gallons")
            break
        
        if day % 10 == 0:
            print(f"Day {day}: {water:.1f} gallons remaining")
    
    else:
        print(f"✓  After 30 days: {water:.1f} gallons remaining")
    
    print()
    print(f"Conclusion: Water lasts {days} days without refills")
    print(f"Expected: {100 / daily_consumption:.1f} days")
    print()
    
    if 100 / daily_consumption >= 25:
        print("✓  BALANCE: Water consumption is reasonable")
    else:
        print("⚠️  BALANCE: Water consumption may be too high")


def main():
    """Main entry point."""
    analyze_water_consumption()
    check_water_balance()
    
    print()
    print("=" * 60)
    print("TIP: If you're running out of water:")
    print("  1. Look for '💧 Water source available here' message")
    print("  2. Select 'Refill water' from the menu")
    print("  3. Plan your route around water locations")
    print("  4. Use Meager rations in desert terrain")
    print("=" * 60)


if __name__ == "__main__":
    main()