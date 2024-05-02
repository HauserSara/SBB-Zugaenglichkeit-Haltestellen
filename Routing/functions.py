import requests
import http.client
import urllib.parse
import json

######################## Function API request stop places #########################
# get stop places within a certain distance of the given coordinates
def get_stop_places(X, Y, distance=500):
    params = {
        "where": f"within_distance(geopos_haltestelle, geom'Point({X} {Y})',{distance}m)",
        "limit": 20
    }

    params_str = urllib.parse.urlencode(params)

    conn = http.client.HTTPSConnection("data.sbb.ch", 443)
    conn.request("GET", "/api/explore/v2.1/catalog/datasets/haltestelle-haltekante/records?" + params_str)

    response = conn.getresponse()

    if response.status == 200:
        stop_places = json.loads(response.read())
        valid_stop_places = [stop_place for stop_place in stop_places['results'] if stop_place['meansoftransport'] is not None]
        return valid_stop_places
    else:
        print(f"Error: Failed to retrieve stop places for coordinates {X}, {Y}")
        return None
    
######################## Function API request routing #########################
# get the route between a coordinate and a stop place
def get_route(X, Y, stop_place, type):
    params = {
        "client": "webshop",
        "clientVersion": "latest",
        "lang": "de",
        "accessible": True,
        "api_key": "59b20b25750f56bf888ef149873f24da"
    }

    # set parameters based on whether the coordinate is the starting point or the destination
    if type == "start":
        params["fromLatLng"] = f"{Y},{X}"
        params["toStationID"] = stop_place
    elif type == "dest":
        params["fromStationID"] = stop_place
        params["toLatLng"] = f"{Y},{X}"
    else:
        print(f"Error: Invalid type {type}. Expected 'start' or 'dest'.")
        return None

    url = "https://journey-maps.api.sbb.ch/v1/transfer"
    response = requests.get(url, params=params)

    if response.status_code == 200:
        route = response.json()
        return route
    else:
        print(f"Error: Failed to retrieve route for stop place {stop_place} and coordinates {X}, {Y}")
        print(f"URL: {response.url}")
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")
        return None
    
######################## Function API request height profile ######################
def get_height_profile(index, route):
    geom = {
        "type": "LineString",
        "coordinates": route
    }

    # Convert the geom dictionary to a JSON string
    geom_json = json.dumps(geom)

    # Include the JSON string in the URL
    data = {"geom": geom_json, "sr": 2056}
    #url = f"https://api3.geo.admin.ch/rest/services/profile.json?geom={geom_json}&sr=2056"
    #response = requests.get(url)
    response = requests.post("https://api3.geo.admin.ch/rest/services/profile.json", data=data)

    if response.status_code == 200:
        profile = response.json()
        return profile
    else:
        print(f"Error: Failed to retrieve height profile for route {index}")
        print(f"URL: {response.url}")
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")
        return None
    
######################## Function calculate height meters #########################
def calculate_height_meters(height_profiles):
    height_meters = []

    for index, profile in height_profiles:
        if profile is None:
            height_meters.append((index, None))
            continue
        upwards = 0
        downwards = 0

        # Get the heights from the profile
        heights = [point['alts']['DTM25'] for point in profile]

        # Calculate the differences between consecutive points
        for i in range(1, len(heights)):
            diff = heights[i] - heights[i-1]
            if diff > 0:
                upwards += diff
            elif diff < 0:
                downwards += abs(diff)

        height_meters.append((index, (round(upwards, 1), round(downwards, 1))))

    return height_meters

######################## Function calculate weight ################################
def weight_routes(height_meters, upwards_weight=1, downwards_weight=0.2):
    weighted_routes = []

    for index, height_meter in height_meters:
        if height_meter is None:
            weight = None
        else:
            upwards, downwards = height_meter
            weight = upwards * upwards_weight + downwards * downwards_weight
        weighted_routes.append((index, weight))

    # return route with minimal weight, None values are ignored
    return min(weighted_routes, key=lambda x: x[1] if x[1] is not None else float('inf'))