# load and filter data from the JSON file :

# destination_db.py

import json
from typing import List, Dict
from agent.state import AgentState

def load_destinations() -> List[Dict]:
    """Loads all destination data from the JSON file"""
    with open("data/destinations.json", "r") as f:
        return json.load(f)

def filter_destinations(preferences: Dict) -> List[Dict]:
    """Filters destinations based on full user preferences"""
    all_destinations = load_destinations()
    filtered = []

    for dest in all_destinations:
        match = True

        # Region check
        if "preferred_city" in preferences:
            if preferences["preferred_city"].lower() not in dest.get("region", "").lower():
                match = False

        # Travel style (tags) check
        if "travel_style" in preferences:
            if preferences["travel_style"].lower() not in [tag.lower() for tag in dest.get("tags", [])]:
                match = False

        # Budget check
        if "budget" in preferences:
            if preferences["budget"].lower() != dest.get("budget", "").lower():
                match = False

        # Travel type check
        if "travel_type" in preferences:
            if preferences["travel_type"].lower() != dest.get("travel_type", "").lower():
                match = False

        if match:
            filtered.append(dest)

    return filtered
