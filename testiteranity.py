'''#import Libraries.
import streamlit as st
import requests
import datetime
import re
import google.generativeai as genai   # For Geminai API key . 

#  API Keys .
GEMINI_API_KEY = "AIzaSyBoQsCnxICf0keun64246GM0p2dwIR-X3I"
UNSPLASH_ACCESS_KEY = "7_EKtKVpcR4ObamVZ2rlihklzXBPHBPjqNbPQl06qMI"
RAPIDAPI_KEY = "56531449a5msha6825acbcb0c4d7p183678jsn99ace807947d"

#  Gemini Setup - For  Chatbot intigration .
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.0-flash")

#  Streamlit Config 
st.set_page_config(page_title="AI Travel Agent", layout="wide")

#  Styling (CSS)
st.markdown("""
<style>
    section[data-testid="stSidebar"] {
        background-color: #0f0f0f !important;
        color: #0f0f0f !important;
        border: none;
        padding: 1rem;
    }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] label {
        color: white !important;
    }
    .destination-card {
        border-radius: 12px;
        padding: 1rem;
        background-color: #1e1e1e;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    }
    .destination-card:hover {
        background-color: #333333;
        transform: translateY(-5px);
    }
    .map-button {
        background-color: #111111;
        color: #ffffff;
        padding: 8px 18px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        transition: all 0.3s ease;
        display: inline-block;
        box-shadow: 0px 4px 12px rgba(0, 82, 204, 0.5);
    }
    .map-button:hover {
        background-color: #00bfff;
        box-shadow: 0 0 12px 2px rgba(0, 191, 255, 0.7);
        color: white;
    }
    img {
        height: 200px;
        object-fit: cover;
        border-radius: 10px;
    }
    .center-message {
        text-align: center;
        font-size: 18px;
        padding: 50px 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper Classes .
class AgentState:
    def __init__(self, preferences=None):
        self.preferences = preferences or {}
        self.suggested_destinations = []

def find_destinations(state: AgentState) -> AgentState:
    query = state.preferences.get("preferred_city", "")
    if not query:
        state.suggested_destinations = []
        return state

    url = "https://travel-advisor.p.rapidapi.com/locations/search"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "travel-advisor.p.rapidapi.com"
    }
    params = {
        "query": query,
        "limit": "15",
        "currency": "USD",
        "lang": "en_US"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        results = response.json().get("data", [])
        suggestions = []

        for place in results:
            result = place.get("result_object")
            if not result:
                continue
            name = result.get("name")
            location = result.get("location_string", "")
            lat = result.get("latitude")
            lon = result.get("longitude")
            if name and lat and lon and query.lower() in location.lower():
                suggestions.append({
                    "name": name,
                    "region": location,
                    "latitude": lat,
                    "longitude": lon
                })

        state.suggested_destinations = suggestions
        return state
    except Exception as e:
        print("API error:", e)
        state.suggested_destinations = []
        return state

def get_image_url(destination_name):
    url = f"https://api.unsplash.com/photos/random?query={destination_name}&client_id={UNSPLASH_ACCESS_KEY}&orientation=landscape"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["urls"]["regular"]
    return None

#  Tabs
tab1, tab2 = st.tabs(["🧳 AI Travel Chat", "🧭 Destination Finder"])

#  Tab 1:  Chat  Agent 
#  Our AI AGent Feature .
with tab1:
    st.title("🧳 AI Travel Chat Assistant")
    st.markdown("Ask about travel plans, tips, places, or anything travel related!")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for chat in st.session_state.chat_history:
        st.markdown(f"**You:** {chat['question']}")
        st.markdown(f"**AI:** {chat['answer']}")

    user_input = st.text_input("Your travel question", placeholder="e.g. Suggest a 5-day Paris itinerary")
    if st.button("Ask Agent "):
        if user_input.strip():
            with st.spinner("Thinking..."):
                try:
                    response = model.generate_content(user_input)
                    answer = response.text
                    st.session_state.chat_history.append({"question": user_input, "answer": answer})
                    st.success("Here is  suggestion:")
                    st.markdown(answer)
                except Exception as e:
                    st.error(f"Gemini Error: {e}")
        else:
            st.warning("Please enter a question first!")

#  Tab 2: Destination Finder 
#  Our Second Feature .
with tab2:
    st.markdown("""
        <h1 style='text-align: center; color: white;'>🧭 Travel Planner</h1>
        <h4 style='text-align: center; color: #cccccc;'>Discover destinations based on your vibe</h4>
    """, unsafe_allow_html=True)

    st.sidebar.header("🧭 Travel Preferences")

    city = st.sidebar.text_input("🌇 Preferred City", placeholder="e.g. Rome")
    start_date = st.sidebar.date_input("📅 Start Date", datetime.date.today())
    end_date = st.sidebar.date_input("📅 End Date", datetime.date.today() + datetime.timedelta(days=3))

    interest = st.sidebar.selectbox("🌍 Travel Style", ["", "Beaches", "Mountains", "City Tours", "Nature Escapes", "Historical Places"])
    budget = st.sidebar.selectbox("💰 Budget", ["", "Budget", "Moderate", "Luxury"])
    travel_type = st.sidebar.selectbox("🧳 Travel Type", ["", "Solo", "Couple", "Family", "Friends"])
    show_result = st.sidebar.button("🔍 Find Destinations")

    if show_result:
        if not all([city, interest, budget, travel_type]):
            st.warning("⚠️ Please fill out all preferences.")
        else:
            state = AgentState(preferences={"preferred_city": city})
            updated_state = find_destinations(state)

            st.markdown("### 📍 Suggested Destinations")
            if not updated_state.suggested_destinations:
                st.warning("No suggestions found.")
            else:
                cols = st.columns(4)
                for i, dest in enumerate(updated_state.suggested_destinations):
                    with cols[i % 4]:
                        st.markdown('<div class="destination-card">', unsafe_allow_html=True)
                        st.subheader(dest["name"])
                        img_url = get_image_url(dest["name"])
                        if img_url:
                            st.image(img_url, use_container_width=True)
                        st.markdown(f"**Region:** {dest['region']}")
                        map_link = f"https://www.google.com/maps/search/?api=1&query={dest['region'].replace(' ', '+')}"
                        st.markdown(f'<a href="{map_link}" target="_blank" class="map-button">📍 View on Map</a>', unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

            
    else:
        st.markdown("<div class='center-message'>🕵️‍♂️ Fill out your preferences in the sidebar and hit <b>'Find Destinations'</b></div>", unsafe_allow_html=True)

#  Footer Section.
st.markdown("---")
st.markdown("<center>🧳Traval Agent Power By Dhrumil Pawar</center>", unsafe_allow_html=True)'''
