# ============================================================
# the weather service talks to the weather api on the internet
# the gateway calls this when the cache doesn't have fresh data
# ============================================================
 
from flask import Flask, jsonify
import requests
 

app = Flask(__name__) # app setup
 

# two separate apis:
#   1. geocoding api: converts a city name into latitude/longitude
#   2. forecast api: takes latitude/longitude and returns weather data

 
# geocoding api: we send a city name, it sends back coordinates
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
 
# forecast api: we send coordinates, it sends back weather data
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

 
def get_coordinates(city):
    params = {
        "name":  city,
        "count": 1 # only return the single best match
    }
 
    # make a get request to the geocoding api
    response = requests.get(GEOCODING_URL, params=params, timeout=10)
    result = response.json()
 
    # if the city name doesn't exist the "results" list will be empty or missing
    if not result.get("results"):
        # return None to signal to the caller that the city wasn't found
        return None
 
    # grab the first match from the results list
    location = result["results"][0]
 
    # return just the coordinates and country we need
    return {
        "latitude":  location["latitude"],
        "longitude": location["longitude"],
        "country":   location.get("country", "unknown") 
    }
 
 
def get_weather_data(latitude, longitude):
    params = {
        "latitude":  latitude,
        "longitude": longitude,
        "current":   ",".join([
            "temperature_2m",        # air temperature in celsius at 2 metres above ground
            "wind_speed_10m",        # wind speed in m/s at 10 metres above ground
            "wind_direction_10m",    # wind direction in degrees (0=north, 90=east etc.)
            "relative_humidity_2m",  # humidity percentage at 2 metres above ground
            "precipitation",         # rainfall/snowfall in mm for the current hour
            "uv_index"               # uv index (0=low risk, 11+=extreme)
        ]),
        "timezone": "auto"           # auto-detect the timezone from the coordinates
    }
 
    # make the request to the forecast api
    response = requests.get(FORECAST_URL, params=params, timeout=10)
    result = response.json()

    current = result["current"]
 
    # pull out each value and build a clean, readable dictionary to return
    units = result["current_units"]
 
    return {
        "temperature":     current["temperature_2m"],
        "temperature_unit": units["temperature_2m"],          # e.g. "°C"
        "wind_speed":      current["wind_speed_10m"],
        "wind_speed_unit": units["wind_speed_10m"],            # e.g. "m/s"
        "wind_direction":  current["wind_direction_10m"],
        "wind_direction_unit": units["wind_direction_10m"],    # e.g. "°"
        "humidity":        current["relative_humidity_2m"],
        "humidity_unit":   units["relative_humidity_2m"],      # e.g. "%"
        "precipitation":   current["precipitation"],
        "precipitation_unit": units["precipitation"],          # e.g. "mm"
        "uv_index":        current["uv_index"],
        "uv_index_unit":   units["uv_index"],                  # e.g. ""
        "time":            current["time"]                     # the timestamp of the reading
    }
 

# route 1: GET /weather/<city>
# the gateway calls this when the cache has no fresh data, we look up the city, fetch the weather, and return it

 
@app.route("/weather/<city>", methods=["GET"])
def get_weather(city):
    # convert the city name into coordinates
    coordinates = get_coordinates(city)
 
    # if coordinates came back as None, the city name wasn't recognised
    if coordinates is None:
        return jsonify({"error": f"city '{city}' not found"}), 404
 
    # use the coordinates to fetch the actual weather data
    # wrap this in a try/except to handle network errors
    try:
        weather = get_weather_data(coordinates["latitude"], coordinates["longitude"])
    except requests.exceptions.RequestException as e:
        # something went wrong with the network call (timeout, no internet etc.)
        # we return a 503 which means "service unavailable"
        return jsonify({"error": "weather api unreachable", "details": str(e)}), 503
 
    # combine location info and weather data into one response
    return jsonify({
        "city":    city.lower(),
        "country": coordinates["country"],
        "weather": weather,
        "source":  "live"   # tells the gateway this is fresh data, not from cache
    }), 200
 

# entry point
if __name__ == "__main__":
    print("starting weather service on port 5001...")
    app.run(host="0.0.0.0", port=5001, debug=True)