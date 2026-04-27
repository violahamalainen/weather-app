# ============================================================
# the cache service stores weather data
# so that we don't have to call the real weather api every single time
# ============================================================

from flask import Flask, request, jsonify
import time


app = Flask(__name__) # app setup


# the cache itself:

cache = {}  # a plain python dictionary

CACHE_TTL = 600 # how many seconds until cached data is considered stale (10 minutes)


# stats counters
# every time something happens we add 1 to the right counter

stats = {
    "hits":   0,  # how many times we found fresh data in the cache
    "misses": 0,  # how many times the data wasn't there or was too old
    "stores": 0,  # how many times new data was saved into the cache
}


# freshness check function:
# it returns True if the data is fresh enough to use, False if it's too old

def is_fresh(entry):
    # we subtract when the data was stored to get the "age" in seconds
    age_in_seconds = time.time() - entry["stored_at"]

    # if the age is less than our TTL limit, the data is still good
    return age_in_seconds < CACHE_TTL


# route 1: GET /cache/<city>
# the gateway calls this to ask if there is fresh data for a city


@app.route("/cache/<city>", methods=["GET"])
def get_cache(city):
    city = city.lower()
    if city not in cache: # check if this city exists in our cache dictionary at all
        stats["misses"] += 1 # we didn't find anything, update the miss counter

        return jsonify({"error": "not in cache"}), 404  # return a 404 response so the gateway knows to go fetch fresh data

    # we found the city, now check if the data is still fresh
    entry = cache[city]

    if not is_fresh(entry):
        # the data exists but it's too old
        stats["misses"] += 1

        return jsonify({"error": "cache expired"}), 404

    # if we made it here: data exists and is fresh, this is a cache hit
    stats["hits"] += 1

    # calculate how old the data is in seconds so the client can see it
    age = int(time.time() - entry["stored_at"])

    # return the cached weather data along with a note saying it came from cache
    return jsonify({
        "source": "cache",        # tells the gateway/client this came from cache
        "age_seconds": age,       # how old the data is
        "data": entry["data"]     # the actual weather info dictionary
    }), 200                       # 200 means everything worked


# route 2: POST /cache/<city>
# the gateway calls this after fetching fresh data from the weather service, asking to store it


@app.route("/cache/<city>", methods=["POST"])
def store_cache(city):
    city = city.lower()

    weather_data = request.get_json()

    if not weather_data:     # if the body is empty or not valid json, we can't store anything
        return jsonify({"error": "no data provided"}), 400  # 400 = bad request

    # store the data in our cache dictionary
    cache[city] = {
        "data":      weather_data,   # the weather info to store
        "stored_at": time.time()     # the exact moment we stored it
    }

    # update the store counter
    stats["stores"] += 1

    # return a simple success message
    return jsonify({"message": "stored successfully"}), 200


# route 3: GET /cache/stale/<city>
# only used as a fallback when the weather service is down
# returns data even if it's expired, there is no freshness check

@app.route("/cache/stale/<city>", methods=["GET"])
def get_stale(city):
    city = city.lower()
    if city not in cache:
        return jsonify({"error": "not in cache"}), 404
    # return data even if expired — no freshness check
    entry = cache[city]
    return jsonify({"source": "stale-cache", "data": entry["data"]}), 200


# route 4: GET /cache/stats
# the gateway calls this when someone asks for system statistics, returns how many hits, misses and stores have happened

@app.route("/cache/stats", methods=["GET"])
def get_stats():
    return jsonify({
        "hits":          stats["hits"],
        "misses":        stats["misses"],
        "stores":        stats["stores"],
        "cities_cached": len(cache),
        "cities":        list(cache.keys())
    }), 200




# entry point:

# this block only runs when you start this file directly
# with: python cache.py
# it won't run if this file is imported by another file
if __name__ == "__main__":
    print("starting cache service on port 5002...")
    app.run(host="0.0.0.0", port=5002, debug=True)