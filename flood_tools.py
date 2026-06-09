import requests
import pandas as pd
import json
import streamlit as st

# Global variable to hold the uploaded dataframe (bypasses Streamlit session state)
_INFRA_DF = None

def set_infrastructure_data(df):
    """Called from app.py after a successful upload to store the dataframe globally."""
    global _INFRA_DF
    _INFRA_DF = df

def get_infrastructure_data():
    """Return the current infrastructure dataframe, or None."""
    global _INFRA_DF
    return _INFRA_DF

def get_live_weather(city: str) -> str:
    """
    Fetches real-time 48-hour rainfall forecast using the free Open-Meteo API.
    """
    locations = {
        "Marikina": {"lat": 14.6507, "lon": 121.1029},
        "Pasig":   {"lat": 14.5764, "lon": 121.0851},
        "Cainta":  {"lat": 14.5794, "lon": 121.1165}
    }
    
    if city not in locations:
        return f"Error: Weather coordinates for {city} not found. Try Marikina, Pasig, or Cainta."
        
    coords = locations[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&hourly=precipitation&timezone=Asia/Manila"
    
    try:
        response = requests.get(url)
        data = response.json()
        rain_data = data['hourly']['precipitation'][:48]
        total_rain = sum(rain_data)
        return f"Real-time Weather Alert: The 48-hour forecasted rainfall for {city} is {total_rain:.2f} mm."
    except Exception:
        return f"API Error. Reverting to historical baseline. Expected rain for {city} is approximately 60 mm."

def get_infrastructure_status(city: str) -> str:
    """
    Retrieves the municipal flood control infrastructure assets,
    pumping stations, and conditions for a specific city.
    """
    global _INFRA_DF
    df = _INFRA_DF
    if df is None:
        return f"Error: No municipal dataset is currently loaded for {city}. Please upload a CSV file."

    city_data = df[df['City'].str.lower() == city.lower()]
    if city_data.empty:
        return f"Warning: No infrastructure assets found for '{city}' in the current database."

    report = f"Infrastructure Report for {city.upper()}:\n"
    for _, row in city_data.iterrows():
        report += f"- {row['Infrastructure_Asset']}: Status is '{row['Current_Status']}', Capacity: {row['Design_Capacity_mm']}mm, Maintenance Deficit: {row['Maintenance_Deficit_Pct']}%\n"
    return report

def get_safety_protocols() -> str:
    """
    Retrieves the official municipal flood response and evacuation protocols 
    for high, critical, and normal risk scenarios.
    """
    import os
    try:
        file_path = "flood_protocols.txt"
        if not os.path.exists(file_path):
            file_path = "data/flood_protocols.txt"
            
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except Exception:
        return "Fallback Protocol Error: Advise community to follow standard local LGU disaster broadcast mandates."

# --- QUICK LOCAL TEST ---
if __name__ == "__main__":
    print("Testing Weather API...")
    print(get_live_weather("Marikina"))
    
    print("\nTesting CSV Reader...")
    print(get_infrastructure_status("Marikina"))