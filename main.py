# Fast API File : 
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware     #allowing frontend apps from other origins to communicate with this API
from agent.state import AgentState
from agent.graph import build_graph

app = FastAPI()

# Allow frontend access (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to "http://localhost:8501" if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/recommend")
async def recommend(request: Request):
    data = await request.json()
    trip_type = data.get("trip_type")
    region = data.get("region")
    budget = data.get("budget")

    user_input = f"I want a {trip_type} trip in {region} with a {budget} budget."

    # Setup agent state
    state = AgentState(chat_history=[{"user": user_input}])
    graph = build_graph()
    result = graph.invoke(state)

    final_response = result.get("final_response", "⚠️ Sorry, I couldn’t find anything.")

    return {"result": final_response}
