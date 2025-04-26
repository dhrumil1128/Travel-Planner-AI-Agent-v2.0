# This node helps the agent understand whether the user is asking a follow-up question.

from agent.state import AgentState
def check_followup(state: AgentState) -> AgentState:                                    # Checks if the user's latest message is a follow-up and updates the state.
    latest_message = state.chat_history[-1]["user"] if state.chat_history else ""
    followup_keywords = ["change", "another", "cheaper", "instead", "more", "different", "else", "alternative"]

    is_followup = any(keyword in latest_message.lower() for keyword in followup_keywords)
    
    state.is_followup = is_followup
    return state
