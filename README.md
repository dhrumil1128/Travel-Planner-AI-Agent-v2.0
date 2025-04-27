# Travel-Planner-AI-Agent-v2.0

Travel-Planner-AI-Agent-v2.0 is a personalized travel recommendation web application built with Streamlit and optionally extensible. Users input their travel preferences, such as destination, travel style, budget, type of travel, and duration, to generate custom destination suggestions, with itinerary creation, a visa checker function , a trip cost estimator, and also with the display of the live money exchange rate with flight deals. The app leverages the AI Agent to intelligently refine recommendations and handle follow-up queries. It also includes Unsplash API integration for destination images and Google Maps for location insights. With the addition of real-time travel data from the Travel Advisor API, users can access suggestions for hotels, restaurants, and attractions. The app features a responsive UI, custom CSS styling, and animations. It can be deployed on Streamlit Cloud for easy access.

---

## Features

- City-based travel preference selection
- Start and end date input for travel duration
- Multiple travel styles (Beaches, Mountains, Nature, City Tours, etc.)
- Travel types including Solo, Couple, Family, and Friends
- Budget-friendly options including Budget, Moderate, Luxury, and Premium
- AI Agent handles user input and intelligently provides personalized responses and destination suggestions.
- Random destination image from Unsplash API
- Region-specific Google Maps location integration
- Responsive UI with custom CSS styling and animations
- Integrated with Travel Advisor API via RapidAPI
- Real-Time Weather Forecasts — Get updated weather for destinations
- Language & Currency Assistant — Learn local phrases + currency rates
- Visa Checker — Check visa requirements between countries
- Trip Cost Estimator — Estimate total trip budget (Budget / Mid-range / Luxury)
- Fully deployable on Streamlit Cloud

---

## Project Structure

```
travel-planner-ai/
│
├── agent/
│   ├── __init__.py
│   ├── graph.py
│   ├── state.py
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── destination_finder.py
│   │   ├── followup_handler.py
│   │   ├── itinerary_creator.py
│   │   ├── preference_extractor.py
│   │   └── response_generator.py
│   └── tools/
│       ├── __init__.py
│       ├── graph.py
│       ├── state.py
│       └── destination_db.py
│
├── data/
│   └── destinations.json
│
├── Frontend/
│   └── app.py
│
├── tests/
│   └── test_agent.py
│
├── main.py
├── README.md
└── requirements.txt
```

---

## Technologies Used

| Layer       | Technology         |
|-------------|--------------------|
| Frontend    | Streamlit          |
| Backend     | FastAPI (optional) |
| Image API   | Unsplash API       |
| Travel Data | Travel Advisor API (via RapidAPI) |
| Map Service | Google Maps URL API |
| Chatbot API | Gemin AI  API |
| FLight Deals | amadeus API |
| Live Wheather infromation|  Open Whather  API |
| Live currency Conversion Rate | Exchengerate API |
| For Travel Style | Opentripmap API |

---

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/travel-planner-ai.git
cd travel-planner-ai
```

2. **Create a virtual environment (optional but recommended):**
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the app:**
```bash
streamlit run Frontend/app.py
```

---

## Deployment

### Deploy on Streamlit Cloud

1. Push the repository to your GitHub account.
2. Visit [https://streamlit.io/cloud](https://streamlit.io/cloud)
3. Sign in with GitHub and link your repository.
4. Select the repository and deploy.
5. Your app will be live with a public URL.

---

## Example Requirements.txt

```txt
streamlit
requests
fastapi
uvicorn
```

---

## Optional Streamlit Configuration (`.streamlit/config.toml`)

```toml
[theme]
base="dark"
primaryColor="#0052cc"
backgroundColor="#0f0f0f"
secondaryBackgroundColor="#1e1e1e"
textColor="#ffffff"
```

---

## Screenshots
## 1. Destination Finder 
![image](https://github.com/user-attachments/assets/6fc246eb-5b1d-4846-8a5c-9643cd87e3ad)
## 2. AI Travel Chat
![image](https://github.com/user-attachments/assets/0a242d74-4143-45f3-987d-f381d86e5304)
## 3. Flight Deal's 
![image](https://github.com/user-attachments/assets/102940ca-a841-41a5-8c12-0760595c5beb)
## 4. Langugae & Currency
![image](https://github.com/user-attachments/assets/9918e847-53da-4f31-9982-03214bf81bb0)
## 5. Trip Cost Estimater
![image](https://github.com/user-attachments/assets/75361030-0f96-4772-b09b-86e2a894360d)
## 6. Visa Checker
![image](https://github.com/user-attachments/assets/8cec248d-8670-4ec1-86c2-a94cc0769dde)







---

## License

This project is licensed under the MIT License. You are free to use, modify, and distribute this software with attribution.

---

## Acknowledgements

- [Unsplash API](https://unsplash.com/developers) for images
- [Streamlit](https://streamlit.io) for UI framework
- [FastAPI](https://fastapi.tiangolo.com) for backend API capabilities
- [Travel Advisor API](https://rapidapi.com/apidojo/api/travel-advisor) for travel data
- [Google Maps](https://developers.google.com/maps/documentation/urls/get-started) for location queries

---

## Author

**Dhrumil Pawar**  
[LinkedIn](https://www.linkedin.com/in/dhrumil-pawar/) 



