# services.py
import json
import requests
from datetime import datetime
from config import geocode_ratelimited, openmeteo, amadeus, GEMINI_API_KEY

def get_weather_forecast(lat, lon, start_date, end_date):
    """Fetches weather forecast for the given location and duration."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min"],
        "timezone": "auto", "start_date": start_date, "end_date": end_date
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    daily = response.Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()
    daily_temp_max = daily.Variables(1).ValuesAsNumpy()
    daily_temp_min = daily.Variables(2).ValuesAsNumpy()
    time_points = range(daily.Time(), daily.TimeEnd(), daily.Interval())

    forecast = []
    for i, time in enumerate(time_points):
        forecast.append({
            "date": datetime.fromtimestamp(time).strftime("%Y-%m-%d"),
            "weather_code": int(daily_weather_code[i]),
            "temp_max": float(round(daily_temp_max[i], 1)),
            "temp_min": float(round(daily_temp_min[i], 1))
        })
    return forecast

def get_flight_options(origin_city, destination_city, travel_date):
    """Fetches real-time flight options from Amadeus."""
    if not amadeus:
        return {"error": "Amadeus API client not configured."}
    try:
        origin_airports = amadeus.reference_data.locations.get(keyword=origin_city, subType='CITY,AIRPORT').data
        if not origin_airports: return None
        origin_iata = origin_airports[0]['iataCode']

        dest_airports = amadeus.reference_data.locations.get(keyword=destination_city, subType='CITY,AIRPORT').data
        if not dest_airports: return None
        dest_iata = dest_airports[0]['iataCode']

        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin_iata,
            destinationLocationCode=dest_iata,
            departureDate=travel_date,
            adults=1,
            max=1 # We only need the cheapest option for comparison
        )
        return response.data
    except Exception as e:
        print(f"Amadeus Error: {e}")
        return None

def simulate_train_options(origin_city, destination_city, travel_date):
    """Generates simulated train options."""
    # In a real app, this would call a train API. Here we simulate.
    return [
        {"train_name": "Intercity Express", "price": {"amount": "1500", "currency": "INR"}},
        {"train_name": "Shatabdi Express", "price": {"amount": "2200", "currency": "INR"}}
    ]

def get_transport_recommendation(origin, destination, start_date, end_date, budget):
    """Analyzes transport options and recommends the best one based on budget."""
    recommendation = {
        "mode": "Not available",
        "estimated_cost_round_trip": None,
        "details": "Could not determine a suitable travel option."
    }

    # --- Flight Analysis ---
    onward_flights = get_flight_options(origin, destination, start_date)
    return_flights = get_flight_options(destination, origin, end_date)
    
    flight_cost = None
    if onward_flights and return_flights:
        onward_price = float(onward_flights[0]['price']['total'])
        return_price = float(return_flights[0]['price']['total'])
        flight_cost = onward_price + return_price

    # --- Train Analysis (Simulated) ---
    trains = simulate_train_options(origin, destination, start_date)
    train_cost = None
    if trains:
        # Assuming return cost is same as onward for simulation
        train_cost = float(trains[0]['price']['amount']) * 2

    # --- Decision Logic ---
    budget_max = float(budget.get('max', 0))
    
    if train_cost and flight_cost:
        if train_cost < (flight_cost * 0.7) and train_cost <= budget_max:
             recommendation['mode'] = "Train"
             recommendation['estimated_cost_round_trip'] = {"amount": train_cost, "currency": "INR"}
             recommendation['details'] = f"Recommended train: {trains[0]['train_name']}. Booking advised via local railway services."
             return recommendation

    if flight_cost and flight_cost <= budget_max:
        recommendation['mode'] = "Flight"
        recommendation['estimated_cost_round_trip'] = {"amount": flight_cost, "currency": onward_flights[0]['price']['currency']}
        recommendation['details'] = f"Cheapest flight option found with carrier {onward_flights[0]['itineraries'][0]['segments'][0]['carrierCode']}. Booking advised via airline or travel portal."
        return recommendation
        
    return recommendation


def generate_itinerary_with_coords(destination, start_date, end_date, budget, interests, current_location):
    """Generates a complete travel plan including transport recommendations."""
    main_location = geocode_ratelimited(destination)
    if not main_location:
        raise Exception(f"Could not find coordinates for destination: {destination}")

    weather_data = get_weather_forecast(main_location.latitude, main_location.longitude, start_date, end_date)
    transport_recommendation = get_transport_recommendation(current_location, destination, start_date, end_date, budget)

    weather_prompt_string = json.dumps(weather_data)
    transport_prompt_string = json.dumps(transport_recommendation)
    duration = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days + 1

    # START: Modified Prompt for point-based descriptions
    prompt = f"""
    Act as an expert travel agent. Create a detailed itinerary for a {duration}-day trip from {current_location} to {destination}, starting on {start_date}.
    The traveler's budget is between {budget.get('min')} and {budget.get('max')} {budget.get('currency')}. Their interests are {', '.join(interests)}.
    
    Based on analysis, here is the recommended mode of transport: {transport_prompt_string}.
    Please incorporate the travel from {current_location} to {destination} on the first day and the return journey on the last day into the itinerary.

    Here is the weather forecast: {weather_prompt_string}. Use this to suggest weather-appropriate activities.
    
    For each day, provide suggestions for 'morning', 'afternoon', and 'evening' in that specific order. For each suggestion, provide:
    1. A "name" of a real, geocodable point of interest.
    2. A "description" as a JSON list of short, descriptive strings (like bullet points).
    3. An "estimated_cost" object.
    4. A "local_cuisine_suggestion".
    5. A "special_event" (null if none).
    6. An "image_search_term", which is a simple, descriptive phrase for a stock photo (e.g., "Goa beach sunset", "historic church Goa").

    The sum of all 'estimated_cost' amounts must fall within the traveler's budget.
    Provide the output as a valid JSON array.
    """
    # END: Modified Prompt
    
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={GEMINI_API_KEY}', headers=headers, data=json.dumps(data))

    if response.status_code != 200:
        raise Exception(f"Failed to generate itinerary from Gemini. Status: {response.status_code}, Response: {response.text}")

    try:
        response_json = response.json()
        if 'candidates' not in response_json or not response_json['candidates']:
            raise ValueError("Gemini API response is missing 'candidates'.")
        
        response_text = response_json['candidates'][0]['content']['parts'][0]['text']
        
        json_start = response_text.find('```json')
        json_end = response_text.rfind('```')
        
        if json_start != -1 and json_end != -1 and json_start < json_end:
            cleaned_response = response_text[json_start + len('```json'):json_end].strip()
        else:
            cleaned_response = response_text.strip()
            print("Warning: JSON markdown fences not found, attempting to parse entire response text.")
            
        if not cleaned_response:
            raise ValueError("Gemini API returned an empty or unparseable text response.")
        
        itinerary = json.loads(cleaned_response)

    except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
        print(f"--- FAILED TO PARSE GEMINI RESPONSE ---\nError: {e}\nRaw Response: {response.text}\n------------------------------------")
        raise Exception("Could not parse the itinerary from the AI.")

    for i, day_plan in enumerate(itinerary):
        if i < len(weather_data): day_plan['weather'] = weather_data[i]
        for period in ['morning', 'afternoon', 'evening']:
            if period in day_plan and day_plan[period] and 'name' in day_plan[period]:
                location_name = day_plan[period]['name']
                try:
                    location = geocode_ratelimited(f"{location_name}, {destination}")
                    if location: day_plan[period]['location'] = {'name': location_name, 'lat': location.latitude, 'lng': location.longitude}
                    else: day_plan[period]['location'] = None
                except Exception as e:
                    print(f"Could not geocode {location_name}: {e}")
                    day_plan[period]['location'] = None
    
    return {"itinerary": itinerary, "transport_recommendation": transport_recommendation}
