# config.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import openmeteo_requests
import requests_cache
from retry_requests import retry
from amadeus import Client as AmadeusClient  # ✅ Correct


# Load environment variables from .env file
load_dotenv()

# --- Environment Variables ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
AMADEUS_API_KEY = os.environ.get("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.environ.get("AMADEUS_API_SECRET")

# --- API Client Initialization ---

# Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Geopy for OpenStreetMap Geocoding
geolocator = Nominatim(user_agent="ai-travel-planner")
geocode_ratelimited = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# Amadeus for Flights
amadeus = AmadeusClient(
    client_id=AMADEUS_API_KEY,
    client_secret=AMADEUS_API_SECRET
) if AMADEUS_API_KEY and AMADEUS_API_SECRET else None

# OpenMeteo for Weather
# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)