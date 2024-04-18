import pandas as pd
from functions import get_stop_places, get_route
from pyproj import Transformer
import json
import requests

data = pd.read_csv('Start_Ziel.csv')

# starting coordinates
X1 = data['X'][0]
Y1 = data['Y'][0]

# destination coordinates
X2 = data['X'][1]
Y2 = data['Y'][1]

# # get stop places within a certain distance of the given coordinates
# stop_places_start = get_stop_places(X1, Y1)
# with open('stop_places_start.json', 'w') as f:
#     json.dump(stop_places_start, f)
# stop_places_dest = get_stop_places(X2, Y2)
# with open('stop_places_dest.json', 'w') as f:
#     json.dump(stop_places_dest, f)

with open('stop_places_start.json', 'r') as f:
    stop_places_start = json.load(f)
with open('stop_places_dest.json', 'r') as f:
    stop_places_dest = json.load(f)

# get the didok-numbers of the stop places
didok_number_start = [entry['number'] for entry in stop_places_start['results']]
didok_number_dest = [entry['number'] for entry in stop_places_dest['results']]

# # get the routes between the coordinates and the stop places
# routes_start = [get_route(X1, Y1, entry, 'start') for entry in didok_number_start]
# with open('routes_start.json', 'w') as f:
#     json.dump(routes_start, f)
# routes_dest = [get_route(X2, Y2, entry, 'dest') for entry in didok_number_dest]
# with open('routes_dest.json', 'w') as f:
#     json.dump(routes_dest, f)

with open('routes_start.json', 'r') as f:
    routes_start = json.load(f)
with open('routes_dest.json', 'r') as f:  
    routes_dest = json.load(f)

# define lists for the coordinates of the routes
coords_routes_start = []
coords_routes_dest = []

# get the coordinates of the routes
for feature in routes_start:
    route = feature['features'][0]['geometry']['coordinates']
    coords_routes_start.append(route)

for feature in routes_dest:
    route = feature['features'][0]['geometry']['coordinates']
    coords_routes_dest.append(route)

# define transformer to convert coordinates from WGS84 to LV95
transformer = Transformer.from_crs('epsg:4326', 'epsg:2056')

# define lists for the coordinates of the routes in LV95
routes_start_lv95 = []
routes_dest_lv95 = []

# convert the coordinates of the routes to LV95
for route in coords_routes_start:
    route_lv95 = [(transformer.transform(latitude, longitude)) for longitude, latitude in route]
    routes_start_lv95.append(route_lv95)

for route in coords_routes_dest:
    route_lv95 = [(transformer.transform(latitude, longitude)) for longitude, latitude in route]
    routes_dest_lv95.append(route_lv95)

print(routes_dest_lv95)

######################## Function API request height profile ######################
def get_height_profile(route):
    geom = {
        "type": "LineString",
        "coordinates": route
    }

    # Convert the geom dictionary to a JSON string
    geom_json = json.dumps(geom)

    # Include the JSON string in the URL
    url = f"https://api3.geo.admin.ch/rest/services/profile.json?geom={geom_json}"
    response = requests.get(url)

    if response.status_code == 200:
        stop_places = response.json()
        return stop_places
    else:
        print(f"Error: Failed to retrieve data for route {route}")
        return None

profile = get_height_profile(routes_dest_lv95[0])
print(profile)