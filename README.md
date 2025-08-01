# AI Travel Planner

This is the backend for a comprehensive, AI-powered travel planning application. It's designed to generate personalized, intelligent, and practical travel itineraries based on user preferences. The system integrates multiple real-time data sources to provide a seamless and efficient trip-planning experience.

## ✨ Core Features

* **Intelligent Itinerary Generation:** Leverages the Google Gemini API to create detailed, day-by-day travel plans.

* **User Personalization:** Takes into account user's current location, destination, travel dates, budget, and interests.

* **Weather-Aware Planning:** Fetches real-time weather forecasts and instructs the AI to suggest appropriate indoor/outdoor activities.

* **Smart Transport Logistics:**

  * Integrates with the Amadeus API for real-time flight data.

  * Analyzes travel costs against the user's budget to recommend the most suitable mode of transport (flight or train).

  * Estimates the round-trip travel cost.

* **Rich Itinerary Details:** The AI enriches the plan with:

  * Local cuisine recommendations for each activity.

  * Information on special events or festivals.

  * A detailed, activity-by-activity budget breakdown.

* **Interactive Mapping:** Automatically geocodes every suggested location using OpenStreetMap for easy visualization on a map.

* **Secure User Management:** Uses Supabase for robust and secure user registration and authentication.

* **Full API Documentation:** Comes with a built-in Swagger UI for easy, browser-based testing of all features.

## 🛠️ Tech Stack

| Component | Technology / Service | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python (Flask) | Building the core REST API |
| **Database & Auth** | Supabase | User management & PostgreSQL data persistence |
| **AI Model** | Google Gemini | Itinerary generation & intelligent suggestions |
| **Geocoding** | OpenStreetMap (via GeoPy) | Converting place names to map coordinates |
| **Weather API** | Open-Meteo | Fetching real-time weather forecasts |
| **Flight Data API** | Amadeus | Real-time flight searches and pricing |
| **API Documentation** | Swagger UI | Interactive API testing and documentation |

## 🚀 Getting Started

Follow these instructions to get the project running on your local machine.

### 1. Prerequisites

* Python 3.9+

* A free [Supabase](https://supabase.com/) account.

* A [Google AI Studio](https://aistudio.google.com/) account for a Gemini API key.

* A free [Amadeus for Developers](https://developers.amadeus.com/) account for flight data.

### 2. Setup

**a. Clone the Repository**
```bash
git clone <your-repository-url>
cd <your-repository-folder>
```

**b. Create the `.env` File**
Create a file named `.env` in the root of the project. This file will store your secret keys and is ignored by Git.

```
# Supabase Credentials
SUPABASE_URL="YOUR_SUPABASE_URL"
SUPABASE_KEY="YOUR_SUPABASE_ANON_PUBLIC_KEY"

# Gemini API Key
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

# Amadeus API Keys
AMADEUS_API_KEY="YOUR_AMADEUS_API_KEY"
AMADEUS_API_SECRET="YOUR_AMADEUS_API_SECRET"
```

**c. Install Dependencies**
It is highly recommended to use a virtual environment.

```bash
# Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install all required packages from requirements.txt
pip install -r requirements.txt
```

*(You will need to create a `requirements.txt` file by running `pip freeze > requirements.txt`)*

**d. Set Up the Database**
1. Go to the **SQL Editor** in your Supabase project.
2. Run the SQL script provided in `database_setup.sql` to create and configure the `profiles` and `trips` tables.

### 3. Running the Application

With the setup complete, start the Flask server from your terminal:
```bash
python app.py
```
The server will start and be available at `http://127.0.0.1:5000`.

## ⚙️ How to Use

The application can be accessed in two ways:

1. **Web Interface:**
   * Navigate to **`http://127.0.0.1:5000/`** in your web browser.
   * This will load the full frontend, allowing you to register, log in, and generate travel plans through a user-friendly interface.

2. **API Documentation (Swagger UI):**
   * Navigate to **`http://127.0.0.1:5000/api/docs`** in your web browser.
   * This provides an interactive interface to test each API endpoint directly.
