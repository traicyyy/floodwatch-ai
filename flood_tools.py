import requests
import pandas as pd
import json

def get_live_weather(city: str) -> str:
    """
    Fetches real-time 48-hour rainfall forecast using the free Open-Meteo API.
    """
    # Simple coordinate mapper for our target cities
    locations = {
        "Marikina": {"lat": 14.6507, "lon": 121.1029},
        "Pasig": {"lat": 14.5764, "lon": 121.0851},
        "Cainta": {"lat": 14.5794, "lon": 121.1165}
    }
    
    if city not in locations:
        return f"Error: Weather coordinates for {city} not found in database. Try Marikina, Pasig, or Cainta."
        
    coords = locations[city]
    
    # Open-Meteo URL for hourly precipitation
    url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&hourly=precipitation&timezone=Asia/Manila"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Aggregate the first 48 hours of expected rainfall
        rain_data = data['hourly']['precipitation'][:48]
        total_rain = sum(rain_data)
        
        return f"Real-time Weather Alert: The 48-hour forecasted rainfall for {city} is {total_rain:.2f} mm."
        
    except Exception as e:
        # Fallback Protocol if the API goes down
        return f"API Error. Reverting to historical baseline. Expected rain for {city} is approximately 60 mm."

def get_infrastructure_status(city: str) -> str:
    """
    Queries the local infrastructure CSV file to check for vulnerabilities.
    """
    try:
        # Read the local CSV file using Pandas
        df = pd.read_csv('data/infrastructure_dime.csv')
        
        # Filter the data for the requested city
        city_data = df[df['City'].str.contains(city, case=False, na=False)]
        
        if city_data.empty:
            return f"No infrastructure data found for {city}."
            
        # Convert the filtered rows into a readable JSON string for the LLM
        return city_data.to_json(orient="records")
        
    except FileNotFoundError:
        return "CRITICAL ERROR: 'data/infrastructure_dime.csv' file is missing."

# --- QUICK LOCAL TEST ---
if __name__ == "__main__":
    print("Testing Weather API...")
    print(get_live_weather("Marikina"))
    
    print("\nTesting CSV Reader...")
    print(get_infrastructure_status("Marikina"))