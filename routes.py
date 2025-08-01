# routes.py
from flask import request, jsonify, Blueprint
from config import supabase
from services import (
    generate_itinerary_with_coords,
    get_flight_options,
    simulate_train_options
)

# Create a Blueprint for API routes
api = Blueprint('api', __name__, url_prefix='/api/v1')

def get_user_from_token(request):
    """Helper function to get user from JWT token in request header."""
    token = request.headers.get('Authorization')
    if not token or len(token.split(" ")) < 2:
        return None, {"msg": "Missing or invalid Authorization header"}
    token = token.split(" ")[1]
    try:
        user = supabase.auth.get_user(token)
        return user, None
    except Exception as e:
        return None, {"msg": f"Invalid token: {e}"}

# --- Authentication Routes ---
@api.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    try:
        # Step 1: Let Supabase Auth handle the user creation securely.
        # This creates the user in auth.users
        auth_response = supabase.auth.sign_up({
            "email": data['email'],
            "password": data['password']
        })

        # Step 2: Create a corresponding public profile in public.profiles.
        # This is CRUCIAL for the foreign key constraint on the trips table.
        if auth_response.user:
            profile_data = {
                'id': auth_response.user.id,
                'email': auth_response.user.email,
                'name': data.get('name', data['email'].split('@')[0]), # Use provided name, or part of email as default
                'preferences': data.get('preferences', {})
            }
            # Insert the profile data. This will link the user to the 'profiles' table.
            supabase.table('profiles').insert(profile_data).execute()
            
        return jsonify({"msg": "User created successfully. Please check your email to confirm if email verification is enabled."}), 201
    except Exception as e:
        return jsonify({"msg": f"Registration failed: {e}"}), 500

@api.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    try:
        user_response = supabase.auth.sign_in_with_password({
            "email": data['email'],
            "password": data['password']
        })
        # If login is successful, user_response.session will contain the JWT
        if user_response and user_response.session:
            return jsonify({
                "msg": "Logged in successfully",
                "access_token": user_response.session.access_token,
                "user": user_response.user.dict()
            })
        else:
            return jsonify({"msg": "Login failed: Invalid credentials or user not found"}), 401
    except Exception as e:
        return jsonify({"msg": f"Login failed: {e}"}), 401

@api.route('/auth/logout', methods=['POST'])
def logout():
    try:
        supabase.auth.sign_out()
        return jsonify({"msg": "Logged out successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Logout failed: {e}"}), 500

# --- Trip Management Routes ---
@api.route('/trips', methods=['POST'])
def create_trip():
    user, error = get_user_from_token(request)
    if error: return jsonify(error), 401
    data = request.get_json()

    # Define required fields. 'name' is now mandatory per new schema.
    # 'budget' and 'interests' can be optional from frontend
    required_fields = ['destination', 'start_date', 'end_date', 'current_location']
    if not all(k in data for k in required_fields):
        return jsonify({"msg": f"Missing required fields. Required: {required_fields}"}), 400

    try:
        # Generate itinerary using external service
        plan = generate_itinerary_with_coords(
            data['destination'],
            data['start_date'],
            data['end_date'],
            data.get('budget'), # budget is optional
            data.get('interests', []), # interests is optional, default to empty list (correct for TEXT[] in DB)
            data['current_location']
        )
        
        # Determine the trip name. Use provided name, or fall back to destination.
        # Ensure a name is always present because the database requires it (NOT NULL).
        trip_name = data.get('name', data['destination']) 
        if not trip_name: # Fallback if destination is also empty (shouldn't happen if required)
            trip_name = "Untitled Trip"

        trip_data = {
            'user_id': user.user.id,
            'name': trip_name,
            'destination': data['destination'],
            'start_date': data['start_date'],
            'end_date': data['end_date'],
            'budget': data.get('budget'),
            'interests': data.get('interests', []), # This is a Python list, which supabase-py maps to TEXT[]
            'itinerary': plan['itinerary']
        }
        
        print(f"Attempting to insert trip with user_id: {user.user.id} and name: '{trip_name}'")
        
        response = supabase.table('trips').insert(trip_data).execute()
        
        return jsonify({
            "msg": "Trip created successfully", 
            "trip_id": response.data[0]['id'],
            "plan": plan
        }), 201
    except Exception as e:
        # It's good practice to log the full exception for debugging in production
        print(f"Error creating trip: {e}")
        return jsonify({"msg": f"Failed to create trip: {str(e)}"}), 500

@api.route('/trips', methods=['GET'])
def get_trips():
    user, error = get_user_from_token(request)
    if error: return jsonify(error), 401
    
    try:
        # RLS will ensure only the user's own trips are returned
        response = supabase.table('trips').select('*').execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"msg": f"Failed to retrieve trips: {e}"}), 500

@api.route('/trips/<int:trip_id>', methods=['GET'])
def get_trip(trip_id):
    user, error = get_user_from_token(request)
    if error: return jsonify(error), 401
    
    try:
        # RLS will ensure only the user's own trip is returned
        response = supabase.table('trips').select('*').eq('id', trip_id).execute()
        if not response.data:
            return jsonify({"msg": "Trip not found or not authorized"}), 404
        return jsonify(response.data[0]), 200
    except Exception as e:
        return jsonify({"msg": f"Failed to retrieve trip: {e}"}), 500

@api.route('/trips/<int:trip_id>', methods=['PUT'])
def update_trip(trip_id):
    user, error = get_user_from_token(request)
    if error: return jsonify(error), 401
    data = request.get_json()
    
    try:
        # Ensure 'name' is handled for updates if it's sent
        if 'name' in data and not data['name']:
            data['name'] = "Untitled Trip" # Prevent setting name to empty string if it's NOT NULL

        # RLS will ensure only the user's own trip can be updated
        response = supabase.table('trips').update(data).eq('id', trip_id).eq('user_id', user.user.id).execute()
        if not response.data:
            return jsonify({"msg": "Trip not found or not authorized"}), 404
        return jsonify({"msg": "Trip updated successfully", "trip": response.data[0]}), 200
    except Exception as e:
        return jsonify({"msg": f"Failed to update trip: {e}"}), 500

@api.route('/trips/<int:trip_id>', methods=['DELETE'])
def delete_trip(trip_id):
    user, error = get_user_from_token(request)
    if error: return jsonify(error), 401
    
    try:
        # RLS will ensure only the user's own trip can be deleted
        response = supabase.table('trips').delete().eq('id', trip_id).eq('user_id', user.user.id).execute()
        if not response.data:
            return jsonify({"msg": "Trip not found or not authorized"}), 404
        return jsonify({"msg": "Trip deleted successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Failed to delete trip: {e}"}), 500

# --- Standalone Transport Routes (kept for direct queries) ---
# These routes were part of the initial setup; ensure they are still desired.
# They require authentication and query Amadeus/simulated data.

@api.route('/transport/flights', methods=['GET'])
def get_flights_standalone():
    user, error = get_user_from_token(request)
    if error: return jsonify(error), 401
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')
    if not all([origin, destination, date]):
        return jsonify({"msg": "Missing required query parameters: origin, destination, date"}), 400
    flight_options = get_flight_options(origin, destination, date)
    return jsonify(flight_options)

@api.route('/transport/trains', methods=['GET'])
def get_trains_standalone():
    user, error = get_user_from_token(request)
    if error: return jsonify(error), 401
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')
    if not all([origin, destination, date]):
        return jsonify({"msg": "Missing required query parameters: origin, destination, date"}), 400
    train_options = simulate_train_options(origin, destination, date)
    return jsonify(train_options)



    trip_data = {
            'user_id': user.user.id,
            'name': trip_name,
            'destination': data['destination'],
            'start_date': data['start_date'],
            'end_date': data['end_date'],
            'budget': data.get('budget'),
            'interests': data.get('interests', []),
            'itinerary': plan['itinerary'],
            # Add this line to save the transport recommendation
            'transport_recommendation': plan['transport_recommendation']
        }