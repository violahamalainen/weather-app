# ============================================================
# the gateway service acts as central entry point
# receiving requests from the client and coordinating them
# between the cache service and the weather service
# ============================================================

from fastapi import FastAPI
import requests


# app setup
app = FastAPI()


# base urls for the microservices
CACHE_URL = "http://localhost:5002/cache"
WEATHER_URL = "http://localhost:5001/weather"


# route 1: GET /weather
# the client calling to get weather data

@app.get("/weather")
def get_weather(city: str):

    # normalize city name (avoid duplicates)
    city = city.lower()

    # trying if the cache has the data
    try:
        cache_res = requests.get(f"{CACHE_URL}/{city}", timeout=2)

        # if cache returns 200 → we have fresh data
        if cache_res.status_code == 200:
            data = cache_res.json()

            return {
                "source": "cache",           # indicates data came from cache
                "age": data["age_seconds"],  # how old the cached data is
                "data": data["data"]         # actual weather data
            }

    except:
        # handling errors if cache service is down or unreachable
        print("Cache service not responding")


    # if data not in cache, trying the weather service
    try:
        weather_res = requests.get(f"{WEATHER_URL}/{city}", timeout=3)

        # if weather service returns error (e.g. city not found)
        if weather_res.status_code != 200:
            return weather_res.json()

        # extract fresh weather data
        weather_data = weather_res.json()

    except:
        # if weather service is down, try to return old cached data
        try:
            cache_res = requests.get(f"{CACHE_URL}/{city}", timeout=2)

            if cache_res.status_code == 200:
                data = cache_res.json()

                return {
                    "source": "stale-cache",   # "stale" indicates old cached data
                    "message": "weather service down, showing old data",
                    "data": data["data"]
                }

        except:
            pass

        # returning error message if both weather service and cache fail
        return {
            "error": "weather service unavailable and no cache data"
        }


    # storing the data to cache for improving performance
    # with following requests
    try:
        requests.post(f"{CACHE_URL}/{city}", json=weather_data, timeout=2)
    except:
        # cache failure should not break the system
        print("Failed to store in cache")

    # return fresh data to client
    return {
        "source": "live",
        "data": weather_data
    }



# route 2: GET /stats
# returns system statistics requested from cache service

@app.get("/stats")
def stats():
    try:
        # request stats from cache service
        res = requests.get("http://localhost:5002/cache/stats")

        # return stats directly to client
        return res.json()

    except:
        # failure handling if cache service is down
        return {"error": "cache service not reachable"}
    