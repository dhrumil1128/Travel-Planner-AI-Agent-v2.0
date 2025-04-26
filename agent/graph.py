# This File defines the flow of our travel planning AI agent.
# Importing state management, agent state, and all functional nodes used to build the travel planning conversational flow.

from langgraph.graph import StateGraph, END
from agent.state import AgentState  # Fixed: Relative import for sibling file
from .nodes.preference_extractor import extract_preferences  # Fixed: Relative import
from .nodes.destination_finder import filter_destinations  # Fixed: Relative import
from .nodes.itinerary_creator import create_itinerary  # Fixed: Relative import
from .nodes.followup_handler import check_followup  # Fixed: Relative import
from .nodes.response_generator import generate_response  # Fixed: Relative import


def build_graph():
    graph = StateGraph(AgentState)

    # Add each node representing a stage of the travel planning pipeline
    graph.add_node("extract_preferences", extract_preferences)  # Reads what the user wants (node-1)
    graph.add_node("find_destinations", filter_destinations)  # Suggests matching places (node-2)
    graph.add_node("check_followup", check_followup)  # Checks if user asked for changes (node-3) 
    graph.add_node("create_itinerary", create_itinerary)  # Plans a 3-day trip (node-4) 
    graph.add_node("generate_response", generate_response)  # Builds a response message (node-5)

    # Set where the graph starts
    graph.set_entry_point("extract_preferences")

    # Define the path through each node
    graph.add_edge("extract_preferences", "find_destinations")
    graph.add_edge("find_destinations", "check_followup")
    graph.add_edge("check_followup", "create_itinerary")
    graph.add_edge("create_itinerary", "generate_response")
    graph.add_edge("generate_response", END)
    
    return graph.compile()  # Compiles and returns the executable graph