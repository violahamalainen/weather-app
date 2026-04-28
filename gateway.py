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
        # extract fresh weather data
        if weather_res.status_code == 200:
            weather_data = weather_res.json()
        
            # store to cache
            try:
                requests.post(f"{CACHE_URL}/{city}", json=weather_data, timeout=2)

            except:
                print("Cache store failed")

            return {
                "source": "live",
                "data": weather_data
            }
        
        elif weather_res.status_code != 503:
            # 404 = city not found → return
            return weather_res.json()
    
    except:
        pass


    # try cache again (stale data logic)
    try:
        cache_res = requests.get(f"{CACHE_URL}/stale/{city}", timeout=2)

        if cache_res.status_code == 200:
            data = cache_res.json()

            return {
                "source": "stale-cache",
                "message": "weather service unavailable, showing cached data",
                "data": data["data"]
            }

    except:
        pass


    # complete and handle failure
    return {
        "error": "weather service unavailable and no cache data"
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
    