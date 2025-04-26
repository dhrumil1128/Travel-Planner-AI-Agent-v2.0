# This node reads the user's message and pulls out travel preferences :
#Extracts user travel preferences from the latest and recent  message and updates the state.

from agent.state import AgentState
def extract_preferences(state: AgentState) -> AgentState:
    latest_message = state.chat_history[-1]["user"] if state.chat_history else ""
    preferences = {}

    # Very simple mock extraction using keyword checks
    if "beach" in latest_message.lower():
        preferences["interest"] = "beach"
    if "mountain" in latest_message.lower():
        preferences["interest"] = "mountain"
    if "europe" in latest_message.lower():
        preferences["region"] = "europe"
    if "low budget" in latest_message.lower():
        preferences["budget"] = "low"
    if "summer" in latest_message.lower():
        preferences["season"] = "summer"
    if "7 days" in latest_message.lower():
        preferences["duration"] = "7 days"

    # Update the state
    state.preferences.update(preferences)
    return state
