#This file defines the Agent's State — essentially its memory.
#The Agent keeps track of everything during the travel planning process here.

# import the library
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class AgentState:
    # 1. User preferences like destination type, region, budget, etc.
    preferences: Dict[str, Any] = field(default_factory=dict)

    # 2. List of matching destinations returned from API
    suggested_destinations: List[Dict[str, Any]] = field(default_factory=list)

    # 3. Planned itinerary (e.g., 3-day plan)
    itinerary: List[Dict[str, Any]] = field(default_factory=list)

    # 4. Conversation history (can be useful for follow-ups or personalization)
    chat_history: List[Dict[str, str]] = field(default_factory=list)

    # 5. Flag to indicate if the user asked for changes / follow-up
    is_followup: bool = False

    # 6. Final message shown to the user
    final_response: Optional[str] = None
