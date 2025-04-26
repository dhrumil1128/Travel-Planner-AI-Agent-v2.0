from agent.state import AgentState
from datetime import timedelta
import google.generativeai as genai

def create_itinerary(state: AgentState) -> AgentState:
    if not state.suggested_destinations or not state.preferences.get("start_date"):
        return state

    start_date = state.preferences["start_date"]
    end_date = state.preferences["end_date"]
    num_days = (end_date - start_date).days + 1
    destination_names = [d["name"] for d in state.suggested_destinations]
    travel_type = state.preferences.get("travel_type", "general")

    model = genai.GenerativeModel("models/gemini-1.5-flash")
    
    prompt = f"""
    Create a detailed {num_days}-day itinerary for {travel_type} travelers visiting: {", ".join(destination_names)}.
    Structure your response EXACTLY like this template:

    ### 🏖️ Beach Vacation Itinerary
    **Selected Destinations:** Miami Beach, Key West
    **Travel Style:** Relaxed Family Trip

    **Day 1: Arrival & Exploration**
    - Morning: Check-in at beachfront resort
    - Afternoon: Lunch at [Local Restaurant], then beach relaxation
    - Evening: Sunset cruise

    **Day 2: Adventure Day**
    - Morning: Snorkeling trip
    - Afternoon: Beachside BBQ
    - Evening: Boardwalk entertainment

    **Key Recommendations:**
    - Best family restaurant: [Name]
    - Must-try activity: [Activity]
    - Insider tip: [Tip]

    ---
    Now create one for {destination_names} with:
    1. Daily structured plans (Morning/Afternoon/Evening)
    2. Categorized recommendations
    3. Local tips
    4. Markdown formatting
    """

    try:
        response = model.generate_content(prompt)
        itinerary = [{
            "date": (start_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "activities": response.text
        } for i in range(num_days)]
        
        state.itinerary = itinerary
    except Exception as e:
        # Fallback simple itinerary
        state.itinerary = [{
            "date": (start_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "activities": f"Day {i+1}: Explore {destination_names[0]}"
        } for i in range(num_days)]
    
    return state