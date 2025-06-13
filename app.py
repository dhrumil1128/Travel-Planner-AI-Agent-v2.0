# ------------------ Import Libraries ------------------
import streamlit as st
import requests
import datetime
import google.generativeai as genai
from agent.nodes.itinerary_creator import create_itinerary
from amadeus import Client

# --------------Audio Library ----------------
from gtts import gTTS
from io import BytesIO
import base64

from dotenv import load_dotenv
import os
load_dotenv()

# ------------------ API Keys ------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
OPENTRIPMAP_API_KEY = os.getenv("OPENTRIPMAP_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
Money_Exchange_RATE_API_KEY = os.getenv("MONEY_EXCHANGE_RATE_API_KEY")



# ------------------ Gemini Setup ------------------
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")


# ------------------ TRIP COST ESTIMATOR (Enhanced Version) ------------------
def estimate_trip_cost(days, destinations, budget_level, travel_type, num_travelers=1, target_currency="USD"):
    """
    Enhanced trip cost estimator with multi-currency support and more accurate calculations
    Args:
        days: Duration of trip (int)
        destinations: List of destination names (list)
        budget_level: Budget tier - "budget", "mid-range", or "luxury" (str)
        travel_type: "solo", "couple", "family", or "friends" (str)
        num_travelers: Number of people traveling (int, default=1)
        target_currency: Currency code to return amount in (default="USD")
    Returns:
        Dictionary containing:
        - 'total_cost': Estimated amount in target currency (float)
        - 'base_cost_usd': Original amount in USD (float)
        - 'exchange_rate': Rate used for conversion (float)
        - 'currency_symbol': Symbol for target currency (str)
    """
    # ==================== 1. BASE COST CALCULATION (USD) ====================
    # Daily costs per person in USD (updated with more realistic 2024 prices)
    daily_costs = {
        "budget": {
            "solo": 60,      # Hostels, public transport, street food
            "couple": 100,   # Private budget rooms, local transport
            "family": 150,   # Family rooms, kid-friendly meals
            "friends": 90    # Shared accommodations
        },
        "mid-range": {
            "solo": 150,     # 3-star hotels, some taxis, restaurant meals
            "couple": 250,   # Nice hotels, dining out, some tours
            "family": 350,   # Family suites, activities for kids
            "friends": 200   # Shared nicer accommodations
        },
        "luxury": {
            "solo": 300,     # 4-5 star hotels, premium experiences
            "couple": 500,   # Luxury stays, fine dining, private tours
            "family": 750,   # High-end family resorts
            "friends": 400   # Luxury shared villas
        }
    }
    
    # Destination cost multipliers (updated with current data)
    destination_multipliers = {
        # North America
        "new york": 1.8, "los angeles": 1.6, "toronto": 1.4,
        # Europe
        "london": 1.7, "paris": 1.6, "rome": 1.4, "amsterdam": 1.5,
        # Asia
        "tokyo": 1.5, "singapore": 1.6, "dubai": 1.7, "bangkok": 1.0,
        # Oceania
        "sydney": 1.5, "auckland": 1.3,
        # Default
        "default": 1.0
    }
    
    # Calculate base cost in USD
    base_cost = daily_costs.get(budget_level.lower(), {}).get(travel_type.lower(), 100)
    
    # Apply destination multiplier (use highest if multiple destinations)
    multiplier = max(
        destination_multipliers.get(dest.lower(), destination_multipliers["default"])
        for dest in destinations
    )
    
    total_cost_usd = base_cost * days * multiplier * num_travelers
    total_cost_usd = round(total_cost_usd, 2)
    
    # ==================== 2. CURRENCY CONVERSION ====================
    # Currency data (symbols and sample rates - will be replaced by API)
    currency_data = {
        "USD": {"symbol": "$", "rate": 1.0},
        "INR": {"symbol": "₹", "rate": 83.5},
        "GBP": {"symbol": "£", "rate": 0.79},
        "EUR": {"symbol": "€", "rate": 0.93},
        "JPY": {"symbol": "¥", "rate": 151.0}
    }
    
    # Get current exchange rate (try API first, then fallback)
    exchange_rate = get_exchange_rate("USD", target_currency)
    
    # Calculate converted amount
    converted_amount = round(total_cost_usd * exchange_rate, 2)
    
    return {
        "total_cost": converted_amount,
        "base_cost_usd": total_cost_usd,
        "exchange_rate": exchange_rate,
        "currency_symbol": currency_data.get(target_currency, {}).get("symbol", "$"),
        "currency_code": target_currency
    }

# ------------------ EXCHANGE RATE HELPER ------------------
@st.cache_data(ttl=86400)  # Cache for 24 hours
def get_exchange_rate(base_currency, target_currency):
    """
    Gets current exchange rate from API with fallback to cached rates
    """
    if base_currency == target_currency:
        return 1.0
    
    try:
        # Try to get live rates (using your existing API key)
        url = f"https://v6.exchangerate-api.com/v6/f98260fb95e219fcdf1f6bea/latest/{base_currency}"
        res = requests.get(url, timeout=5).json()
        rate = res['conversion_rates'][target_currency]
        
        # Validate rate is reasonable
        if 0.0001 < rate < 10000:  # Sanity check range
            return rate
    except Exception:
        pass
    
    # Fallback rates (update these periodically)
    FALLBACK_RATES = {
        "USD_INR": 83.5,
        "USD_GBP": 0.79,
        "USD_EUR": 0.93,
        "USD_JPY": 151.0
    }
    
    return FALLBACK_RATES.get(f"{base_currency}_{target_currency}", 1.0)


# ------------------ NEW: Language/Currency Functions ------------------
# we use this LibreTranslate (Public Instance) There is no api key needed .
@st.cache_data(ttl=3600)
def translate_text(text, target_lang='en'):
    """
    Robust translation function with:
    - Input validation
    - Fallback dictionary
    - Error handling
    Args:
        text: English text to translate
        target_lang: 2-letter language code (default 'en')
    Returns:
        Translated text or original if translation fails
    """
    # If target language is English, return original text
    if target_lang == 'en':
        return text

    # Comprehensive phrase dictionary fallback
    PHRASE_DICTIONARY = {
        "Hello": {
            "fr": "Bonjour", "es": "Hola", "de": "Hallo", 
            "it": "Ciao", "hi": "नमस्ते", "ja": "こんにちは",
            "zh": "你好", "ru": "Привет", "ar": "مرحبا"
        },
        "Thank you": {
            "fr": "Merci", "es": "Gracias", "de": "Danke",
            "it": "Grazie", "hi": "धन्यवाद", "ja": "ありがとう",
            "zh": "谢谢", "ru": "Спасибо", "ar": "شكرا"
        },
        "Please": {
            "fr": "S'il vous plaît", "es": "Por favor", "de": "Bitte",
            "it": "Per favore", "hi": "कृपया", "ja": "お願いします",
            "zh": "请", "ru": "Пожалуйста", "ar": "من فضلك"
        },
        "Excuse me": {
            "fr": "Excusez-moi", "es": "Disculpe", "de": "Entschuldigung",
            "it": "Mi scusi", "hi": "माफ कीजिए", "ja": "すみません",
            "zh": "打扰一下", "ru": "Извините", "ar": "المعذرة"
        },
        "How much?": {
            "fr": "Combien?", "es": "¿Cuánto cuesta?", "de": "Wie viel?",
            "it": "Quanto costa?", "hi": "कितना?", "ja": "いくらですか？",
            "zh": "多少钱？", "ru": "Сколько стоит?", "ar": "كم الثمن؟"
        },
        "Where is the bathroom?": {
            "fr": "Où sont les toilettes?", "es": "¿Dónde está el baño?", 
            "de": "Wo ist die Toilette?", "it": "Dov'è il bagno?",
            "hi": "शौचालय कहाँ है?", "ja": "トイレはどこですか？",
            "zh": "洗手间在哪里？", "ru": "Где туалет?", "ar": "أين الحمام؟"
        },
        "Do you speak English?": {
            "fr": "Parlez-vous anglais?", "es": "¿Hablas inglés?", 
            "de": "Sprechen Sie Englisch?", "it": "Parli inglese?",
            "hi": "क्या आप अंग्रेजी बोलते हैं?", "ja": "英語を話しますか？",
            "zh": "你会说英语吗？", "ru": "Вы говорите по-английски?", "ar": "هل تتكلم الإنجليزية؟"
        },
        "Goodbye": {
            "fr": "Au revoir", "es": "Adiós", "de": "Auf Wiedersehen",
            "it": "Arrivederci", "hi": "अलविदा", "ja": "さようなら",
            "zh": "再见", "ru": "До свидания", "ar": "مع السلامة"
        }
    }

    # First try the phrase dictionary
    if text in PHRASE_DICTIONARY and target_lang in PHRASE_DICTIONARY[text]:
        return PHRASE_DICTIONARY[text][target_lang]

    # Then try the translation API
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {
            "q": text,
            "langpair": f"en|{target_lang}",
            "max_timeout": 15
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        translated = response.json().get("responseData", {}).get("translatedText")
        
        # Validate translation isn't an error message
        if translated and not translated.startswith("PLEASE SELECT"):
            return translated
        return text  # Return original if translation failed
    
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if all methods fail

# ---------------------- Visa Checker Functions -------------------------------
@st.cache_data(ttl=86400)
def get_visa_requirement(passport_code, destination_code):
    """
    Static visa data implementation with comprehensive country pairs
    """
    VISA_DATABASE = {
        # India passport requirements
        ("IN", "GB"): {
            "type": "error",
            "title": "✖ UK Visa Required for Indians",
            "content": """
            **Visa Type:** Standard Visitor Visa  
            **Processing Time:** 3-4 weeks  
            **Fee:** £115  
            **Documents Required:**  
            - Passport valid for 6 months  
            - Bank statements (3 months)  
            - Proof of accommodation  
            - Return flight ticket  
            
            [🔗 Apply on UK Government Website](https://www.gov.uk/standard-visitor/apply)
            """
        },
        ("IN", "US"): {
            "type": "error",
            "title": "✖ US Visa Required",
            "content": """
            **Visa Type:** B1/B2 Visitor Visa  
            **Processing Time:** 2-3 months (interview required)  
            **Fee:** $185  
            **Documents Required:**  
            - DS-160 form completed  
            - Recent photograph  
            - Proof of financial means  
            
            [🔗 Apply on US Travel Website](https://travel.state.gov/content/travel/en/us-visas/tourism-visit/visitor.html)
            """
        },
        ("IN", "FR"): {
            "type": "success",
            "title": "✅ Schengen Visa Required",
            "content": """
            **Visa Type:** Short-stay Schengen Visa  
            **Processing Time:** 15-30 days  
            **Fee:** €80  
            **Allowed Stay:** Up to 90 days in 180-day period
            
            [🔗 France Visa Info](https://france-visas.gouv.fr/)
            """
        },
        
        # US passport requirements
        ("US", "GB"): {
            "type": "success",
            "title": "✅ Visa Not Required",
            "content": """
            **Allowed Stay:** Up to 6 months  
            **Requirements:**  
            - Valid passport  
            - Proof of onward travel  
            - Sufficient funds for stay
            """
        },
        ("US", "IN"): {
            "type": "success",
            "title": "✅ eVisa Available",
            "content": """
            **Visa Type:** Electronic Tourist Visa  
            **Processing Time:** 3-5 business days  
            **Fee:** $25-$100 (depending on duration)  
            **Validity:** 30 days to 1 year  
            
            [🔗 Apply for India eVisa](https://indianvisaonline.gov.in/evisa/)
            """
        },
        
        # UK passport requirements
        ("GB", "US"): {
            "type": "success",
            "title": "✅ ESTA Required",
            "content": """
            **Authorization:** ESTA (Electronic System for Travel Authorization)  
            **Fee:** $21  
            **Validity:** 2 years  
            **Allowed Stay:** Up to 90 days  
            
            [🔗 Apply for ESTA](https://esta.cbp.dhs.gov/)
            """
        },
        ("GB", "IN"): {
            "type": "success",
            "title": "✅ eVisa Available",
            "content": """
            **Visa Type:** Electronic Tourist Visa  
            **Processing Time:** 3-5 business days  
            **Fee:** £25-£100  
            **Validity:** 30 days to 1 year  
            
            [🔗 Apply for India eVisa](https://indianvisaonline.gov.in/evisa/)
            """
        },
        
        # Add more country pairs as needed
        ("CA", "US"): {
            "type": "success",
            "title": "✅ Visa Not Required",
            "content": """
            **Allowed Stay:** Up to 6 months  
            **Requirements:**  
            - Valid passport  
            - Proof of onward travel
            """
        },
        ("AU", "GB"): {
            "type": "success",
            "title": "✅ Visa Not Required",
            "content": """
            **Allowed Stay:** Up to 6 months  
            **Requirements:**  
            - Valid passport  
            - Proof of sufficient funds
            """
        },
        ("JP", "US"): {
            "type": "success",
            "title": "✅ Visa Waiver Program",
            "content": """
            **Authorization:** ESTA required  
            **Fee:** $21  
            **Allowed Stay:** Up to 90 days  
            
            [🔗 Apply for ESTA](https://esta.cbp.dhs.gov/)
            """
        }
    }
    
    # Check static database first
    if (passport_code, destination_code) in VISA_DATABASE:
        return VISA_DATABASE[(passport_code, destination_code)]
    
    # Fallback to government links
    GOV_LINKS = {
        "GB": "https://www.gov.uk/check-uk-visa",
        "US": "https://travel.state.gov",
        "IN": "https://www.mea.gov.in",
        "CA": "https://www.canada.ca/en/immigration-refugees-citizenship.html",
        "AU": "https://immi.homeaffairs.gov.au",
        "JP": "https://www.mofa.go.jp"
    }
    
    return {
        "type": "warning",
        "title": "⚠️ Visa Info Not Available",
        "content": f"""
        Please check official government websites:
        - Destination Country: {GOV_LINKS.get(destination_code, 'https://www.iatatravelcentre.com')}
        - Your Country: {GOV_LINKS.get(passport_code, '')}
        """
    }

    
#----------------------- country region match function ------------------------------

def get_country_from_region(region_name):
    """
    Extracts country name from region string using city/country mapping
    Args:
        region_name (str): Input string containing location info (e.g. "Paris, France")
    Returns:
        str: Detected country name or None if not found
    """
    if not region_name:
        return None
        
    region_lower = region_name.lower()
    
    # --- City to Country Mapping ---
    city_mapping = {
        # Americas
        "new york": "United States",
        "los angeles": "United States",
        "toronto": "Canada",
        "vancouver": "Canada",
        "rio de janeiro": "Brazil",
        
        # Europe
        "london": "United Kingdom",
        "paris": "France",
        "berlin": "Germany",
        "rome": "Italy",
        "barcelona": "Spain",
        
        # Asia
        "tokyo": "Japan",
        "delhi": "India",
        "mumbai": "India",
        "beijing": "China",
        
        # Oceania
        "sydney": "Australia",
        "melbourne": "Australia"
    }
    
    # Check city matches first
    for city, country in city_mapping.items():
        if city in region_lower:
            return country
    
    # --- Country Name Detection ---
    country_keywords = {
        # North America
        "us": "United States",
        "usa": "United States",
        "united states": "United States",
        "canada": "Canada",
        
        # Europe
        "uk": "United Kingdom",
        "united kingdom": "United Kingdom",
        "france": "France",
        "germany": "Germany",
        "italy": "Italy",
        "spain": "Spain",
        
        # Asia
        "india": "India",
        "china": "China",
        "japan": "Japan",
        
        # Oceania
        "australia": "Australia"
    }
    
    # Check for country names
    for keyword, country in country_keywords.items():
        if keyword in region_lower:
            return country
            
    return None  # Explicit return if no matches found


# Country Code Mapping (ISO 3166-1 alpha-2)
COUNTRY_CODES = {
    # Americas
    "United States": "US",
    "Canada": "CA",
    "Brazil": "BR",
    
    # Europe
    "United Kingdom": "GB",
    "France": "FR",
    "Germany": "DE",
    "Italy": "IT",
    "Spain": "ES",
    
    # Asia
    "India": "IN",
    "China": "CN",
    "Japan": "JP",
    
    # Oceania
    "Australia": "AU",
    

}
#-------------------- Text to Speech Function ---------------------------------
def text_to_speech_base64(text, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang)
        buffer = BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)
        audio_base64 = base64.b64encode(buffer.read()).decode()
        audio_html = f'<audio controls src="data:audio/mp3;base64,{audio_base64}"></audio>'
        return audio_html
    except Exception as e:
        return f"🔇 Audio unavailable"
   
#--------------------------- get_exchange_rate() -----------------------------
# API key Url
@st.cache_data(ttl=86400)
def get_exchange_rate(base, target):
    try:
        url = f"https://v6.exchangerate-api.com/v6/f98260fb95e219fcdf1f6bea/latest/USD"
        res = requests.get(url).json()
        return round(res['conversion_rates'][target], 4)
    except Exception as e:
        print(f"Currency API Error: {e}")
        return None

#-------------------------------  The Country Detection -------------------------------
def get_country_info(region):
    
    region_lower = str(region).lower()  # Ensure string type
    
    if any(keyword in region_lower for keyword in ["london", "uk", "britain", "england"]):
        return {"currency": "GBP", "lang": "en"}
    elif any(keyword in region_lower for keyword in ["paris", "france"]):
        return {"currency": "EUR", "lang": "fr"}
    elif any(keyword in region_lower for keyword in ["delhi", "mumbai", "india"]):
        return {"currency": "INR", "lang": "hi"}
    elif any(keyword in region_lower for keyword in ["tokyo", "japan"]):
        return {"currency": "JPY", "lang": "ja"}
    else:
        return {"currency": "EUR", "lang": "en"}


# ------------------ Streamlit Config ------------------ 
st.set_page_config(page_title="AI Travel Agent", layout="wide")

# ------------------ YOUR EXISTING STYLING ------------------
st.markdown("""
<style>
    section[data-testid="stSidebar"] { background-color: #0f0f0f; color: #fff; }
    .destination-card { border-radius: 12px; padding: 1rem; background-color: #1e1e1e; 
                       box-shadow: 0 4px 10px rgba(0,0,0,0.4); margin-bottom: 1rem; }
    .destination-card:hover { background-color: #333; transform: translateY(-5px); }
    .map-button { background-color: #111; color: #fff; padding: 8px 18px; border-radius: 8px; 
                 text-decoration: none; font-weight: 600; display: inline-block; 
                 box-shadow: 0px 4px 12px rgba(0, 82, 204, 0.5); }
    .map-button:hover { background-color: #00bfff; box-shadow: 0 0 12px 2px rgba(0, 191, 255, 0.7); color: white; }
    img { height: 200px; object-fit: cover; border-radius: 10px; }
    .center-message { text-align: center; font-size: 18px; padding: 50px 0; }
    .itinerary-day { background-color: #1e1e1e; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; }
    .weather-badge { display: inline-block; padding: 4px 8px; border-radius: 12px;
                    background: linear-gradient(135deg, #6e8efb, #a777e3); color: white; font-size: 14px; margin: 4px 0; }
</style>
""", unsafe_allow_html=True)

# ------------------ Helper Classes ------------------
class AgentState:
    def __init__(self, preferences=None):
        self.preferences = preferences or {}
        self.suggested_destinations = []
        self.itinerary = []

def get_weather_emoji(condition_code):
    if 200 <= condition_code < 300: return "⛈️"
    elif 300 <= condition_code < 600: return "🌧️"
    elif 600 <= condition_code < 700: return "❄️"
    elif 700 <= condition_code < 800: return "🌫️"
    elif condition_code == 800: return "☀️"
    elif 801 <= condition_code < 900: return "⛅"
    else: return "🌎"

@st.cache_data(ttl=3600)
def get_destination_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        return {
            "temp": round(data['main']['temp']),
            "condition": data['weather'][0]['description'],
            "emoji": get_weather_emoji(data['weather'][0]['id']),
            "humidity": data['main']['humidity'],
            "wind": round(data['wind']['speed'] * 3.6)
        }
    except:
        return None

def format_popularity(rate):
    rate = str(rate)
    if rate == "1" or rate == "1h": return "⭐ Low (Less Crowded)"
    elif rate == "2" or rate == "2h": return "⭐⭐ Moderate (Known Spot)"
    elif rate == "3" or rate == "3h": return "⭐⭐⭐ High (Tourist Favorite)"
    else: return "❔ Not Rated"

def find_destinations(state: AgentState) -> AgentState:
    city = state.preferences.get("preferred_city", "")
    interest = state.preferences.get("interest", "").lower()
    popularity = state.preferences.get("popularity", "").lower()

    if not city:
        state.suggested_destinations = []
        return state

    geo_url = "https://opentripmap-places-v1.p.rapidapi.com/en/places/geoname"
    headers = {
        "X-RapidAPI-Key": OPENTRIPMAP_API_KEY,
        "X-RapidAPI-Host": "opentripmap-places-v1.p.rapidapi.com"
    }
    geo_params = {"name": city}

    try:
        geo_resp = requests.get(geo_url, headers=headers, params=geo_params)
        geo_data = geo_resp.json()

        if 'error' in geo_data:
            st.warning(f"API Error: {geo_data['error']}")
            return state

        lon = geo_data.get("lon")
        lat = geo_data.get("lat")
        if not lat or not lon:
            st.warning("Couldn't locate city.")
            return state
    except Exception as e:
        print("Geo Error:", e)
        return state

    places_url = "https://opentripmap-places-v1.p.rapidapi.com/en/places/radius"
    places_params = {
        "radius": "10000",
        "lon": lon,
        "lat": lat,
        "kinds": interest.replace(" ", "_"),
        "format": "json",
        "limit": "25"
    }

    try:
        places_resp = requests.get(places_url, headers=headers, params=places_params)
        results = places_resp.json()
        suggestions = []

        for item in results:
            if item.get("name"):
                rate = str(item.get("rate", ""))
                if popularity:
                    if popularity == "most popular" and rate not in ["3", "3h"]:
                        continue
                    elif popularity == "moderate" and rate not in ["2", "2h"]:
                        continue
                    elif popularity == "less crowded" and rate not in ["1", "1h"]:
                        continue

                suggestions.append({
                    "name": item.get("name"),
                    "region": city,
                    "latitude": item.get("point", {}).get("lat"),
                    "longitude": item.get("point", {}).get("lon"),
                    "xid": item.get("xid"),
                    "rate": rate
                })

        state.suggested_destinations = suggestions
        return state
    except Exception as e:
        print("Place fetch error:", e)
        return state

def get_image_url(destination_name):
    url = f"https://api.unsplash.com/photos/random?query={destination_name}&client_id={UNSPLASH_ACCESS_KEY}&orientation=landscape"
    res = requests.get(url)
    return res.json().get("urls", {}).get("regular") if res.status_code == 200 else None


    
# ------------------ Main App ------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧳 AI Travel Chat", "🧭 Destination Finder",  "📌 Trip Planning Essentials", "💰 Cost Estimator", "✈️ Flight & Deals"])


#---------------------------------- TAB 1 : AI Travel Chat -------------------------------------------
with tab1:
    # [YOUR EXISTING TAB1 CODE REMAINS UNCHANGED]
    st.title("🧳 AI Travel Chat Assistant")
    st.markdown("Ask about travel plans, tips, places, or anything travel related!")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for chat in st.session_state.chat_history:
        st.markdown(f"**You:** {chat['question']}")
        st.markdown(f"**AI:** {chat['answer']}")

    user_input = st.text_input("Your travel question", placeholder="e.g. Suggest a 5-day Paris itinerary")
    if st.button("Ask Agent"):
        if user_input.strip():
            with st.spinner("Thinking..."):
                try:
                    response = model.generate_content(user_input)
                    answer = response.text
                    st.session_state.chat_history.append({"question": user_input, "answer": answer})
                    st.success("Here is a suggestion:")
                    st.markdown(answer)
                except Exception as e:
                    st.error(f"Gemini Error: {e}")
        else:
            st.warning("Please enter a question first!")

    pass



# ------------------------------------------ TAB 2 : destination finder -----------------------------------
with tab2:
    st.markdown("<h1 style='text-align: center; color: white;'>🧭 Travel Planner</h1>", unsafe_allow_html=True)
    st.sidebar.header("🧭 Travel Preferences")

    # NEW: Add language/currency toggle
    show_culture = st.sidebar.checkbox("Show Language/Currency", True)
    base_currency = st.sidebar.selectbox("Your Currency", ["USD", "EUR", "GBP", "JPY", "INR"], index=0)
    st.session_state.base_currency = base_currency  # ✅ store it


    # [REST OF YOUR EXISTING SIDEBAR CODE REMAINS UNCHANGED...]
        # NEW: Weather toggle with help text
    show_weather = st.sidebar.checkbox(
        "Show Weather Info", 
        True,
        help="Display current weather conditions for each destination"
    )
    
    # User inputs
    city = st.sidebar.text_input("🌇 Preferred City", placeholder="e.g. London")
    start_date = st.sidebar.date_input("📅 Start Date", datetime.date.today())
    end_date = st.sidebar.date_input("📅 End Date", datetime.date.today() + datetime.timedelta(days=3))
    interest = st.sidebar.selectbox("🌍 Travel Style", ["", "Historical Places", "Beaches", "Mountains", "City Tours"])
    popularity = st.sidebar.selectbox("📊 Popularity", ["", "Most Popular", "Moderate", "Less Crowded"])
    travel_type = st.sidebar.selectbox("🧳 Travel Type", ["", "Solo", "Couple", "Family", "Friends"])
    
    if st.sidebar.button("🔍 Find Destinations"):
        if not all([city, interest, travel_type]):
            st.warning("⚠️ Please fill out all preferences.")
        else:
            state = AgentState(preferences={
                "preferred_city": city,
                "interest": interest,
                "popularity": popularity,
                "start_date": start_date,
                "end_date": end_date,
                "travel_type": travel_type,
                "base_currency": base_currency
            })
            updated_state = find_destinations(state)
            st.session_state.destinations = updated_state.suggested_destinations
            st.session_state.selected_places = [updated_state.suggested_destinations[0]["name"]] if updated_state.suggested_destinations else []
            st.rerun()

    if hasattr(st.session_state, 'destinations') and st.session_state.destinations:
        st.markdown("### 📍 Suggested Destinations")
        cols = st.columns(4)
        for i, dest in enumerate(st.session_state.destinations):
            with cols[i % 4]:
                st.markdown('<div class="destination-card">', unsafe_allow_html=True)
                st.subheader(dest["name"])
                img_url = get_image_url(dest["name"])
                if img_url:
                    st.image(img_url, use_container_width=True)

              
                if show_weather and "latitude" in dest:
                    weather = get_destination_weather(dest["latitude"], dest["longitude"])
                    if weather:
                        st.markdown(f"""
                        <div class="weather-badge">
                            {weather['emoji']} {weather['temp']}°C | {weather['condition'].title()}
                        </div>
                        <small>💧 {weather['humidity']}% | 🌬️ {weather['wind']} km/h</small>
                        """, unsafe_allow_html=True)

                else:
                        st.markdown("""
                        <div class="weather-badge weather-error">
                            ⚠️ Weather Unavailable
                        </div>
                        """, unsafe_allow_html=True)
                        print(f"Failed to get weather for {dest['name']}")

                if dest.get("xid"):
                    try:
                        xid_url = f"https://opentripmap-places-v1.p.rapidapi.com/en/places/xid/{dest['xid']}"
                        details_res = requests.get(xid_url, headers={
                            "X-RapidAPI-Key": OPENTRIPMAP_API_KEY,
                            "X-RapidAPI-Host": "opentripmap-places-v1.p.rapidapi.com"
                        })
                        info = details_res.json()
                        desc = info.get("wikipedia_extracts", {}).get("text", "No description available.")
                        st.markdown(f"**📝 Description:** {desc[:150]}...")
                        st.markdown(f"**⭐ Popularity:** {format_popularity(info.get('rate', ''))}")
                        st.markdown(f"**🏷️ Type:** {info.get('kinds', 'Unknown').split(',')[0].capitalize()}")
                    except:
                        st.markdown("ℹ️ No extra details available.")

                st.markdown(f"**Region:** {dest['region']}")
                map_link = f"https://www.google.com/maps/search/?api=1&query={dest['name'].replace(' ', '+')}"
                st.markdown(f'<a href="{map_link}" target="_blank" class="map-button">📍 View on Map</a>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        selected_places = st.multiselect(
            "🌟 Select places for your itinerary:",
            options=[d["name"] for d in st.session_state.destinations],
            default=st.session_state.selected_places
        )
        
        if st.button("✨ Generate Itinerary", type="primary"):
            with st.spinner("Creating your personalized itinerary..."):
                state = AgentState(preferences={
                    "preferred_city": city,
                    "start_date": start_date,
                    "end_date": end_date,
                    "travel_type": travel_type
                })
                state.suggested_destinations = [
                    d for d in st.session_state.destinations 
                    if d["name"] in selected_places
                ]
                updated_state = create_itinerary(state)
                st.session_state.itinerary_data = updated_state.itinerary
                st.session_state.itinerary_generated = True
                st.rerun()

    if st.session_state.get('itinerary_generated', False) and 'itinerary_data' in st.session_state:
        st.markdown("---")
        st.markdown("### 🗓️ Personalized Itinerary")
        for day in st.session_state.itinerary_data:
            with st.container():
                st.markdown(f"""
                <div class='itinerary-day'>
                    <h4>📅 {day['date']}</h4>
                    {day['activities'].replace('•', '✦')}
                </div>
                """, unsafe_allow_html=True)

    elif not hasattr(st.session_state, 'destinations'):
        st.markdown("<div class='center-message'>🕵️‍♂️ Fill out your preferences in the sidebar and hit <b>'Find Destinations'</b></div>", unsafe_allow_html=True)



#--------------------------------------------------Tab 3 : Trip Planning Essentials --------------------------------------------------
with tab3:
    st.header("📌 Trip Planning Essentials")
    
    # Check if destinations exist in session state
    if hasattr(st.session_state, 'destinations') and st.session_state.destinations:
        # Destination selection
        selected_dest = st.selectbox(
            "Select Destination", 
            options=[d["name"] for d in st.session_state.destinations],
            key="tab3_dest_select"
        )
        
        # Safely get destination object
        dest = next((d for d in st.session_state.destinations if d["name"] == selected_dest), None)
        
        if not dest:
            st.error("Selected destination not found")
            st.stop()
        
        country_info = get_country_info(dest.get("region", ""))

        # ---------------------- Language & Currency Section ----------------------
        st.subheader("💬 Language & Currency")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander("💬 Common Phrases with Audio", expanded=True):
                enable_audio = st.toggle("🔊 Enable Pronunciation Audio", value=True)
                
                phrases = [
                    "Hello", "Thank you", "Please", "Excuse me",
                    "How much?", "Where is the bathroom?", 
                    "Do you speak English?", "Goodbye"
                ]
                
                for phrase in phrases:
                    translated = translate_text(phrase, country_info['lang'])
                    st.markdown(f"**{phrase}:** {translated}")
                    
                    if enable_audio and 'text_to_speech_base64' in globals():
                        st.markdown(
                            text_to_speech_base64(translated, country_info['lang']), 
                            unsafe_allow_html=True
                        )
        
        with col2:
            st.markdown("**Currency Exchange**")
            base_currency = st.session_state.get("base_currency", "USD")
            
            if base_currency != country_info["currency"]:
                rate = get_exchange_rate(base_currency, country_info["currency"])
                if rate:
                    st.markdown(f"**1 {base_currency} = {rate:.2f} {country_info['currency']}**")
                    st.caption(f"Exchange rate updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
                else:
                    st.warning("Live currency conversion unavailable")
                    st.info(f"Using approximate rates for {country_info['currency']}")
            else:
                st.success(f"Same currency: {base_currency} (no conversion needed)")

        # ---------------------- Visa Checker Section ----------------------
        with st.container():
            st.subheader("🛂 Visa Checker")
            
            col1, col2 = st.columns(2)
            
            with col1:
                passport_country = st.selectbox(
                    "Your Passport Country",
                    options=list(COUNTRY_CODES.keys()),
                    index=list(COUNTRY_CODES.keys()).index("India"),
                    key="tab3_passport_country"
                )
            
            # Improved country detection
            raw_region = dest.get("region", "")
            detected_country = get_country_from_region(raw_region)
            
            with col2:
                if detected_country and detected_country in COUNTRY_CODES:
                    destination_country = st.selectbox(
                        "Destination Country",
                        options=[detected_country],
                        disabled=True,
                        key="tab3_detected_country"
                    )
                    st.success(f"✓ Auto-detected: {detected_country}")
                else:
                    destination_country = st.selectbox(
                        "Destination Country",
                        options=list(COUNTRY_CODES.keys()),
                        key="tab3_manual_country"
                    )
                    if raw_region:
                        st.warning(f"Couldn't auto-detect from: {raw_region}")
            
            # In your Streamlit UI code:
    if st.button("Check Visa Requirements", key="tab3_visa_check"):
        passport_code = COUNTRY_CODES[passport_country]
        destination_code = COUNTRY_CODES[destination_country]
        
        visa_result = get_visa_requirement(passport_code, destination_code)
        
        # Display results with proper formatting
        with st.expander(visa_result["title"], expanded=True):
            st.markdown(visa_result["content"])
            
            if visa_result["type"] == "error":
                st.error("Visa required - see details above")
            elif visa_result["type"] == "success":
                st.success("Visa not required or available online")
            else:
                st.warning("Check official sources")
        
        st.markdown("""
        **Always verify with official sources:**
        - [Timatic](https://www.iatatravelcentre.com)
        - [UK Visas](https://www.gov.uk/check-uk-visa) 
        - [US Visas](https://travel.state.gov)
        - [Indian MEA](https://www.mea.gov.in)
        """)
    else:
        st.markdown("""
        <div class='center-message'>
            🕵️‍♂️ Please select destinations in the 'Destination Finder' tab first
        </div>""", unsafe_allow_html=True)
        
        
        
        
# ----------------------------------------------------- TAB 4: COST ESTIMATOR -------------------------------------------------------------------------
with tab4:
    st.header("💰 Trip Cost Estimator")
    
    # Currency selection at the top (new addition)
    currency_col, _ = st.columns([1, 3])
    with currency_col:
        selected_currency = st.selectbox(
            "Display Currency",
            ["USD", "INR", "GBP", "EUR", "JPY"],
            index=0,
            key="tab4_currency_select"
        )
    
    # Check if destinations exist in session state
    if hasattr(st.session_state, 'destinations') and st.session_state.destinations:
        # Destination selection
        selected_dests = st.multiselect(
            "Select Destinations",
            options=[d["name"] for d in st.session_state.destinations],
            default=[st.session_state.destinations[0]["name"]],
            key="tab4_dest_select"
        )
        
        # Travel details
        col1, col2 = st.columns(2)
        with col1:
            travel_type = st.selectbox(
                "Travel Type",
                ["Solo", "Couple", "Family", "Friends"],
                index=0,
                key="tab4_travel_type"
            )
            
            num_travelers = st.number_input(
                "Number of Travelers",
                min_value=1,
                max_value=20,
                value=1,
                key="tab4_num_travelers"
            )
        
        with col2:
            budget_level = st.selectbox(
                "Budget Level",
                ["Budget", "Mid-range", "Luxury"],
                index=1,
                key="tab4_budget_level"
            )
            
            if hasattr(st.session_state, 'preferences'):
                days = (st.session_state.preferences["end_date"] - st.session_state.preferences["start_date"]).days
                st.info(f"Trip Duration: {days} days")
            else:
                days = st.number_input(
                    "Trip Duration (days)",
                    min_value=1,
                    max_value=365,
                    value=7,
                    key="tab4_trip_days"
                )
        
        # Calculate and display estimate
        if st.button("Calculate Estimated Cost", key="tab4_calculate"):
            if not selected_dests:
                st.warning("Please select at least one destination")
            else:
                # Get the full cost breakdown (using enhanced function)
                cost_data = estimate_trip_cost(
                    days=days,
                    destinations=selected_dests,
                    budget_level=budget_level.lower(),
                    travel_type=travel_type.lower(),
                    num_travelers=num_travelers,
                    target_currency=selected_currency
                )
                
                with st.expander("💰 Cost Breakdown", expanded=True):
                    # Main metric with selected currency
                    st.metric(
                        "Total Estimated Cost", 
                        f"{cost_data['currency_symbol']}{cost_data['total_cost']:,.2f} {cost_data['currency_code']}",
                        help=f"Converted from ${cost_data['base_cost_usd']:,.2f} USD (Rate: 1 USD = {cost_data['exchange_rate']:.2f} {cost_data['currency_code']})"
                    )
                    
                    # Detailed breakdown in selected currency
                    st.markdown("**Cost Components:**")
                    cols = st.columns(3)
                    
                    with cols[0]:
                        st.metric(
                            "Per Traveler", 
                            f"{cost_data['currency_symbol']}{(cost_data['total_cost']/num_travelers):,.2f}"
                        )
                    
                    with cols[1]:
                        st.metric(
                            "Per Day", 
                            f"{cost_data['currency_symbol']}{(cost_data['total_cost']/days):,.2f}"
                        )
                    
                    with cols[2]:
                        st.metric(
                            "Per Destination", 
                            f"{cost_data['currency_symbol']}{(cost_data['total_cost']/len(selected_dests)):,.2f}"
                        )
                    
                    # Conversion details
                    st.markdown("""
                    **Note:** This estimate includes:
                    - Accommodation
                    - Meals
                    - Local transportation
                    - Basic activities
                    """)
                    
                    if st.toggle("🧮 Show calculation example", key="currency_example_toggle"):
                        st.markdown(f"""
                        **Example:** If a hotel costs $100/night for 5 nights:  
                        - USD Total = $100 × 5 = **$500**  
                        - INR Total = $500 × 83.50 = **₹41,750**  
                        """)
                    
                    # Add visual comparison
                    st.progress(min(100, int(cost_data['total_cost']/1000)))  # Simple visual indicator
                    st.caption(f"Budget scale: {cost_data['currency_symbol']}1,000 increments")
                    
    else:
        st.markdown("""
        <div class='center-message'>
            🕵️‍♂️ Please select destinations in the 'Destination Finder' tab first
        </div>
        """, unsafe_allow_html=True)
        

# ==================== TAB 5: IMPROVED FLIGHT SEARCH ====================
import os 
from amadeus import Client
from dotenv import load_dotenv

load_dotenv()

amadeus = Client(
    client_id=os.getenv('KEsMGSME3EBpkAbFAWArzzUTrET15HYW'),
    client_secret=os.getenv('I31N9MjSvFqU925q')
)

# Airline data with properly sized logos (40x40)
AIRLINE_DATA = {
    "AI": {
        "name": "Air India", 
        "logo": "https://images.ixigo.com/img/common-resources/airline-new/AI.png",
        "logo_size": (40, 80),
        "short_name": "Air India"
    },
    "6E": {
        "name": "IndiGo", 
        "logo": "https://images.ixigo.com/img/common-resources/airline-new/6E.png",
        "logo_size": (40, 40),
        "short_name": "IndiGo"
    },
    "UK": {
        "name": "Vistara", 
        "logo": "https://logos-download.com/wp-content/uploads/2022/01/Vistara_Logo.png",
        "logo_size": (40, 40),
        "short_name": "Vistara"
    },
    "SG": {
        "name": "SpiceJet", 
        "logo": "https://images.ixigo.com/img/common-resources/airline-new/SG.png",
        "logo_size": (40, 80),
        "short_name": "SpiceJet"
    },
    "QR": {
        "name": "Qatar Airways", 
        "logo": "https://images.ixigo.com/img/common-resources/airline-new/QR.png",
        "logo_size": (40, 40),
        "short_name": "Qatar Airways"
    },
    "EK": {
        "name": "Emirates", 
        "logo": "https://images.ixigo.com/img/common-resources/airline-new/EK.png",
        "logo_size": (40, 40),
        "short_name": "Emirates"
    },
    "LH": {
        "name": "Lufthansa", 
        "logo": "https://images.ixigo.com/img/common-resources/airline-new/LH.png",
        "logo_size": (40, 40),
        "short_name": "Lufthansa"
    },
    "BA": {
        "name": "British Airways", 
        "logo": "https://images.ixigo.com/img/common-resources/airline-new/BA.png",
        "logo_size": (40, 40),
        "short_name": "British Airways"
    }
}

# Common airport codes reference
AIRPORT_CODES = {
    "DEL": "New Delhi (Indira Gandhi International)",
    "BOM": "Mumbai (Chhatrapati Shivaji Maharaj International)",
    "BLR": "Bangalore (Kempegowda International)",
    "HYD": "Hyderabad (Rajiv Gandhi International)",
    "MAA": "Chennai (Chennai International)",
    "CCU": "Kolkata (Netaji Subhas Chandra Bose International)",
    "GOI": "Goa (Dabolim International)",
    "PNQ": "Pune (Pune International)",
    "DXB": "Dubai (Dubai International)",
    "LHR": "London (Heathrow)",
    "JFK": "New York (John F. Kennedy International)",
    "SIN": "Singapore (Changi)",
    "BKK": "Bangkok (Suvarnabhumi)",
    "KUL": "Kuala Lumpur (International)",
    "HKG": "Hong Kong (International)"
}

def get_airline_info(airline_code):
    """Returns airline details with properly sized logo"""
    return AIRLINE_DATA.get(airline_code, {
        "name": airline_code,
        "logo": None,
        "logo_size": (40, 80),
        "short_name": airline_code
    })

def format_duration(duration_str):
    """Convert PT1H30M to 1h 30m format"""
    hours = duration_str.split('H')[0].replace('PT', '')
    minutes = duration_str.split('H')[1].replace('M', '') if 'H' in duration_str else '0'
    return f"{hours}h {minutes}m" if minutes != '0' else f"{hours}h"

def display_flight_card(flight):
    """Display flight card with white text and properly sized logos"""
    with st.container():
        # Extract flight data
        segments = flight['itineraries'][0]['segments']
        first_seg = segments[0]
        last_seg = segments[-1]
        airline_code = first_seg['carrierCode']
        airline_info = get_airline_info(airline_code)
        price = float(flight['price']['total'])
        duration = format_duration(flight['itineraries'][0]['duration'])
        stops = len(segments) - 1
        
        # Flight numbers (combining all segments)
        flight_numbers = ", ".join([f"{seg['carrierCode']}{seg['number']}" for seg in segments])
        
        # Build the flight card with dark theme
        st.markdown("""
        <style>
            .flight-card {
                background-color: #1e1e1e;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 16px;
                color: white;
            }
            .flight-logo {
                height: 40px;
                width: 80px;
                object-fit: contain;
            }
        </style>
        """, unsafe_allow_html=True)
        
        cols = st.columns([3, 2, 2, 2])
        
        # Column 1: Airline info and flight numbers
        with cols[0]:
            if airline_info['logo']:
                st.image(
                    airline_info['logo'],
                    width=airline_info['logo_size'][0],
                    use_container_width=False
                )
            st.markdown(f"""
            <div style="margin-top: 8px; font-size: 0.9rem; color: white;">
                <div>{airline_info['short_name']}</div>
                <div style="color: #aaa;">{flight_numbers}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Column 2: Departure and arrival times
        with cols[1]:
            st.markdown(f"""
            <div style="text-align: center; color: white;">
                <div style="font-size: 1.2rem; font-weight: bold;">{first_seg['departure']['at'][11:16]}</div>
                <div style="font-size: 0.9rem; color: #aaa;">{first_seg['departure']['iataCode']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="text-align: center; margin-top: 8px; color: white;">
                <div style="font-size: 0.9rem;">{duration}</div>
                <div style="font-size: 0.8rem; color: #ff5722;">
                    {'🔄 ' + str(stops) + ' stop' if stops else '✈️ Non-stop'}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="text-align: center; color: white;">
                <div style="font-size: 1.2rem; font-weight: bold;">{last_seg['arrival']['at'][11:16]}</div>
                <div style="font-size: 0.9rem; color: #aaa;">{last_seg['arrival']['iataCode']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Column 3: Layover info if applicable
        with cols[2]:
            if stops > 0:
                for i in range(1, len(segments)):
                    layover = (datetime.datetime.fromisoformat(segments[i]['departure']['at']) - 
                              datetime.datetime.fromisoformat(segments[i-1]['arrival']['at']))
                    layover_time = f"{layover.seconds//3600}h {(layover.seconds%3600)//60}m"
                    st.markdown(f"""
                    <div style="text-align: center; margin: 8px 0; padding: 8px; background: #333; border-radius: 4px; color: white;">
                        <div style="font-size: 0.8rem;">Layover at {segments[i]['departure']['iataCode']}</div>
                        <div style="font-size: 0.8rem; font-weight: bold;">{layover_time}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<div style='height: 60px;'></div>", unsafe_allow_html=True)  # Spacer
        
        # Column 4: Price
        with cols[3]:
            st.markdown(f"""
            <div style="text-align: right; color: white;">
                <div style="font-size: 1.5rem; font-weight: bold; color: #ff5722;">₹{price:,.0f}</div>
                <div style="font-size: 0.8rem; color: #aaa; margin-top: 20px;">
                    View Details >
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Flight details expander
        with st.expander("Flight Details >", expanded=False):
            st.markdown("### ✈️ Flight Segments")
            for seg in segments:
                st.markdown(f"""
                - **{seg['carrierCode']}{seg['number']}**: {seg['departure']['iataCode']} → {seg['arrival']['iataCode']}  
                  🕒 {seg['departure']['at'][11:16]} - {seg['arrival']['at'][11:16]}  
                  ⏱️ {format_duration(seg['duration'])} · {seg.get('aircraft', {}).get('code', 'Unknown aircraft')}
                """)
            
            st.markdown("### 💼 Baggage Information")
            baggage = flight.get('travelerPricings', [{}])[0].get('fareDetailsBySegment', [{}])[0].get('includedCheckedBags', {})
            st.markdown(f"🛄 Checked baggage: {baggage.get('quantity', '1')} × {baggage.get('weight', '15')}kg")
            st.markdown("💼 Cabin baggage: 1 × 7kg")

# Main flight search interface
with tab5:
    st.header("✈️ Flight Search", divider="blue")
    
    # Airport code reference expander
    # Update your CSS with this airport table styling
    st.markdown("""
    <style>
        .airport-table {
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
            font-size: 0.9em;
            font-family: sans-serif;
            min-width: 400px;
            box-shadow: 0 0 10px rgba(0, 191, 255, 0.2);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .airport-table thead tr {
            background-color: #1a5276;  /* Dark blue header */
            color: #ffffff;
            text-align: left;
            font-weight: bold;
        }
        
        .airport-table th,
        .airport-table td {
            padding: 12px 15px;
        }
        
        .airport-table tbody tr {
            border-bottom: 1px solid #2c3e50;
            background-color: #2c3e50;  /* Dark row background */
            color: #ecf0f1;  /* Light text */
        }
        
        .airport-table tbody tr:nth-of-type(even) {
            background-color: #34495e;  /* Slightly lighter dark for alternating */
        }
        
        .airport-table tbody tr:last-of-type {
            border-bottom: 2px solid #00bfff;  /* Blue accent */
        }
        
        .airport-table tbody tr:hover {
            background-color: #2980b9;  /* Blue hover */
            cursor: pointer;
        }
        
        .airport-code {
            font-weight: bold;
            color: #00bfff;  /* Bright blue for codes */
        }
        
        .airport-info-card {
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            color: white;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            border-left: 4px solid #00bfff;
        }
        
        .airport-info-card h4 {
            color: #00bfff;
            margin-top: 0;
        }
    </style>
    """, unsafe_allow_html=True)

    # Then use this updated table component
    with st.expander("🌍 Airport Codes Reference - Click to Expand", expanded=False):
        st.markdown("""
    <div class="airport-info-card">
        <h4>International Airport Codes</h4>
        <p style="font-size: 0.9em; color: #bdc3c7;">These are IATA airport codes used by airlines and travel agencies worldwide.</p>
    </div>
    
    <div style="max-height: 300px; overflow-y: auto;">
    <table class="airport-table">
        <thead>
            <tr>
                <th>Code</th>
                <th>Airport Name</th>
                <th>City/Country</th>
            </tr>
        </thead>
        <tbody>
            <tr><td class="airport-code">DEL</td><td>Indira Gandhi International</td><td>New Delhi, India</td></tr>
            <tr><td class="airport-code">BOM</td><td>Chhatrapati Shivaji Maharaj International</td><td>Mumbai, India</td></tr>
            <tr><td class="airport-code">BLR</td><td>Kempegowda International</td><td>Bangalore, India</td></tr>
            <tr><td class="airport-code">HYD</td><td>Rajiv Gandhi International</td><td>Hyderabad, India</td></tr>
            <tr><td class="airport-code">MAA</td><td>Chennai International</td><td>Chennai, India</td></tr>
            <tr><td class="airport-code">CCU</td><td>Netaji Subhas Chandra Bose International</td><td>Kolkata, India</td></tr>
            <tr><td class="airport-code">GOI</td><td>Dabolim International</td><td>Goa, India</td></tr>
            <tr><td class="airport-code">PNQ</td><td>Pune International</td><td>Pune, India</td></tr>
            <tr><td class="airport-code">DXB</td><td>Dubai International</td><td>Dubai, UAE</td></tr>
            <tr><td class="airport-code">AUH</td><td>Abu Dhabi International</td><td>Abu Dhabi, UAE</td></tr>
            <tr><td class="airport-code">LHR</td><td>Heathrow</td><td>London, UK</td></tr>
            <tr><td class="airport-code">LGW</td><td>Gatwick</td><td>London, UK</td></tr>
            <tr><td class="airport-code">JFK</td><td>John F. Kennedy International</td><td>New York, USA</td></tr>
            <tr><td class="airport-code">LAX</td><td>Los Angeles International</td><td>Los Angeles, USA</td></tr>
            <tr><td class="airport-code">ORD</td><td>O'Hare International</td><td>Chicago, USA</td></tr>
            <tr><td class="airport-code">SFO</td><td>San Francisco International</td><td>San Francisco, USA</td></tr>
            <tr><td class="airport-code">SIN</td><td>Changi</td><td>Singapore</td></tr>
            <tr><td class="airport-code">BKK</td><td>Suvarnabhumi</td><td>Bangkok, Thailand</td></tr>
            <tr><td class="airport-code">KUL</td><td>Kuala Lumpur International</td><td>Kuala Lumpur, Malaysia</td></tr>
            <tr><td class="airport-code">HKG</td><td>Hong Kong International</td><td>Hong Kong</td></tr>
            <tr><td class="airport-code">PEK</td><td>Beijing Capital International</td><td>Beijing, China</td></tr>
            <tr><td class="airport-code">PVG</td><td>Shanghai Pudong International</td><td>Shanghai, China</td></tr>
            <tr><td class="airport-code">CDG</td><td>Charles de Gaulle</td><td>Paris, France</td></tr>
            <tr><td class="airport-code">FRA</td><td>Frankfurt Airport</td><td>Frankfurt, Germany</td></tr>
            <tr><td class="airport-code">AMS</td><td>Schiphol</td><td>Amsterdam, Netherlands</td></tr>
            <tr><td class="airport-code">SYD</td><td>Kingsford Smith</td><td>Sydney, Australia</td></tr>
            <tr><td class="airport-code">MEL</td><td>Melbourne Airport</td><td>Melbourne, Australia</td></tr>
            <tr><td class="airport-code">YYZ</td><td>Pearson International</td><td>Toronto, Canada</td></tr>
            <tr><td class="airport-code">YVR</td><td>Vancouver International</td><td>Vancouver, Canada</td></tr>
            <tr><td class="airport-code">NRT</td><td>Narita International</td><td>Tokyo, Japan</td></tr>
            <tr><td class="airport-code">HND</td><td>Haneda Airport</td><td>Tokyo, Japan</td></tr>
            <tr><td class="airport-code">ICN</td><td>Incheon International</td><td>Seoul, South Korea</td></tr>
            <tr><td class="airport-code">DOH</td><td>Hamad International</td><td>Doha, Qatar</td></tr>
            <tr><td class="airport-code">IST</td><td>Istanbul Airport</td><td>Istanbul, Turkey</td></tr>
        </tbody>
    </table>
    </div>
    
    <div class="airport-info-card" style="margin-top: 15px;">
        <p style="font-size: 0.8em; color: #bdc3c7; margin-bottom: 0;">
            <span style="color: #00bfff;">💡 Pro Tip:</span> Use these 3-letter codes when searching for flights to ensure accurate results.
        </p>
    </div>
    """, unsafe_allow_html=True)
    # Search form
    with st.form("flight_search"):
        cols = st.columns([2, 2, 2, 1])
        with cols[0]:
            origin = st.text_input("From", "DEL", placeholder="City or airport (e.g. DEL)").upper()
        with cols[1]:
            destination = st.text_input("To", "BOM", placeholder="City or airport (e.g. BOM)").upper()
        with cols[2]:
            depart_date = st.date_input(
                "Departure",
                min_value=datetime.date.today(),
                value=datetime.date.today() + datetime.timedelta(days=7),
                format="DD/MM/YYYY"
            )
        with cols[3]:
            passengers = st.selectbox("Travellers", [1, 2, 3, 4, 5, 6])
        
        submitted = st.form_submit_button("Search Flights", type="primary")
    
    # Display results
    if submitted:
        try:
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=depart_date.strftime("%Y-%m-%d"),
                adults=passengers,
                currencyCode="INR"
            )
            
            if not response.data:
                st.info("No flights found. Try different dates or routes.")
                st.stop()
            
            flights = sorted(response.data, key=lambda x: float(x['price']['total']))
            
            st.success(f"✈️ Found {len(flights)} flights · {origin} → {destination}")
            
            for flight in flights:  # Show top 5 results
                display_flight_card(flight)
                
        except Exception as e:
            st.error(f"Error fetching flights: {str(e)}")
            
st.markdown("---")
st.markdown("<center>🧳 Travel Agent by Dhrumil Pawar</center>", unsafe_allow_html=True)
