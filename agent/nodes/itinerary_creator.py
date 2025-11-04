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

    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    Create a detailed {num_days}-day itinerary for {travel_type} travelers visiting: {", ".join(destination_names)}.
    Structure your response EXACTLY like this format:

    ### [Destination] Itinerary
    **Selected Destinations:** {", ".join(destination_names)}
    **Travel Style:** {travel_type} Travel

    [Brief overview paragraph about the trip]

    ---

    **Day 1: [Day Title]**
    - Morning: [Activity with details]
    - Afternoon: [Activity with details]
    - Evening: [Activity with details]

    **Day 2: [Day Title]**
    - Morning: [Activity with details]
    - Afternoon: [Activity with details]
    - Evening: [Activity with details]

    [Continue for all days...]

    ---

    **Key Recommendations:**
    - Best restaurant: [Name] ([Cuisine type])
    - Must-try activity: [Activity]
    - Hidden gem: [Tip]
    - Local insight: [Cultural note]

    **Travel Tips:**
    - [Transportation advice]
    - [Packing suggestion]
    - [Budget tip]
    """

    try:
        response = model.generate_content(prompt)
        full_itinerary = response.text
        
        # Split the response into days
        day_sections = []
        current_day = []
        
        for line in full_itinerary.split('\n'):
            if line.startswith('**Day ') and current_day:
                day_sections.append('\n'.join(current_day))
                current_day = [line]
            else:
                current_day.append(line)
        
        if current_day:
            day_sections.append('\n'.join(current_day))
        
        # Assign each day section to the itinerary
        itinerary = []
        current_date = start_date
        
        for i, day_content in enumerate(day_sections[:num_days]):
            itinerary.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "activities": day_content.strip()
            })
            current_date += timedelta(days=1)
        
        # Add the recommendations section to the last day
        if len(itinerary) > 0:
            recommendations_section = "\n".join(
                line for line in full_itinerary.split('\n') 
                if line.startswith('**Key Recommendations:') or 
                   line.startswith('**Travel Tips:') or
                   line.startswith('-')
            )
            itinerary[-1]["activities"] += "\n\n" + recommendations_section
        
        state.itinerary = itinerary
        
    except Exception as e:
        # Fallback simple itinerary
        state.itinerary = [{
            "date": (start_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "activities": f"Day {i+1}: Explore {destination_names[0]}"
        } for i in range(num_days)]
    
    return state
