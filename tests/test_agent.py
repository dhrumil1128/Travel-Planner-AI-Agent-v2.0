from agent.state import AgentState
from agent.graph import build_graph

# Create the graph
travel_agent = build_graph()

# Simulated user message
user_input = "I want a beach trip in Europe on a low budget for 7 days in summer"

# Create initial state with the message
initial_state = AgentState(
    chat_history=[{"user": user_input}]
)

# Run the graph with the state
final_state = travel_agent.invoke(initial_state)

# Print the final response from the agent
print("----- Final Agent Response -----")
print(final_state.final_response)
