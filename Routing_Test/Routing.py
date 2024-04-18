import pandas as pd
import requests

data = pd.read_csv('Start_Ziel.csv')

######################## Function API request stop places #########################
def get_stop_places(X, Y, distance=500):
    params = {
        "where": f"within_distance(geopos_haltestelle, geom'Point({X} {Y})',{distance}m)",
        "limit": 20
    }

    url = "https://data.sbb.ch/api/explore/v2.1/catalog/datasets/haltestelle-haltekante/records"
    response = requests.get(url, params=params)
    print(response.url)

    if response.status_code == 200:
        stop_places = response.json()
        return stop_places
    else:
        print(f"Error: Failed to retrieve data for coordinates {X}, {Y}")
        return None
    
######################## Function API request routing #########################
def get_route(X, Y, stop_place, type):
    params = {
        "client": "webshop",
        "clientVersion": "latest",
        "lang": "de",
        "accessible": True,
        "api_key": "59b20b25750f56bf888ef149873f24da"
    }

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
        print(f"Error: Failed to retrieve data for coordinates {X}, {Y}")
        return None

# starting coordinates
X1 = data['X'][0]
Y1 = data['Y'][0]

# destination coordinates
X2 = data['X'][1]
Y2 = data['Y'][1]

stop_places_start = get_stop_places(X1, Y1)
stop_places_dest = get_stop_places(X2, Y2)

print(stop_places_start)
print(stop_places_dest)

didok_number_start = [entry['number'] for entry in stop_places_start['results']]
didok_number_dest = [entry['number'] for entry in stop_places_dest['results']]

print(didok_number_start)
print(didok_number_dest)

route_start = [get_route(X1, Y1, entry, "start") for entry in didok_number_start]
route_dest = [get_route(X2, Y2, entry, "dest") for entry in didok_number_dest]

print(route_start)
print(route_dest)

for feature in route_start["FeatureCollection"]:
    routes = feature["features"]['geometry']['coordinates']
    print(routes)