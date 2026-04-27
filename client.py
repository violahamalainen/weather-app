# ============================================================
# the client is a terminal application that interacts
# with the user and talks to the gateway service
# ============================================================

import requests

# base url for the gateway service (entry point)
GATEWAY_URL = "http://localhost:8000"


# function asking for city, sending request to gateway
# and printing the results
def get_weather():
    city = input("\nEnter city: ").strip().lower()

    try:
        # sending GET request to gateway which will handle
        # the cache and weather service logics
        res = requests.get(f"{GATEWAY_URL}/weather?city={city}")

        # converting to json format
        data = res.json()
    except:
        # handling errors if gateway not running or unreachable
        print("Error: gateway not reachable\n")
        return

    print()


    # if the response has error -> dislpay it
    if "error" in data:
        print("Error:", data["error"])
        print()
        return

    # print where the data came (live / cache / stale-cache)
    print(f"Weather ({data['source']})")

    # if the data came from cache -> show how old it is
    if data["source"] == "cache":
        print(f"(cached {data['age']}s ago)")

    # extract nested weather data
    weather = data["data"]
    w = weather["weather"]


    # display the clean weather information
    print(f"City: {weather['city'].title()}")
    print(f"Temperature: {w['temperature']} {w['temperature_unit']}")
    print(f"Wind: {w['wind_speed']} {w['wind_speed_unit']} "f"(direction: {w['wind_direction']}{w['wind_direction_unit']})")
    print(f"Humidity: {w['humidity']} {w['humidity_unit']}")
    print(f"Precipitation: {w['precipitation']} {w['precipitation_unit']}")
    print(f"UV Index: {w['uv_index']}")
    print()



# function for showing the stats
# requests them from the gateway which requests them from the cache
def get_stats():
    try:
        # send request to gateway stats endpoint
        res = requests.get(f"{GATEWAY_URL}/stats")

        # convert response to json format
        data = res.json()

        # display the clean stats information
        print("\nSystem stats:")
        print(f"Cached cities: {data['cities_cached']}")
        print(f"Hits: {data['hits']}")
        print(f"Misses: {data['misses']}")
        print(f"Stores: {data['stores']}")
        print()

    except:
        # handling errors if stats can't be fetched
        print("Error: could not fetch stats\n")



# main function to handle UI and running the loop
def main():
    
    #infinite loop to keep program running
    while True:
        print("Weather App")
        print("-----------")
        print("1) Get weather")
        print("2) Show stats")
        print("0) Exit")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            get_weather()
        elif choice == "2":
            get_stats()
        elif choice == "0":
            print("Exiting...\n")
            break
        else:
            print("Invalid input\n")


# entry point of the program
if __name__ == "__main__":
    main()
