import pandas as pd
from functions import get_stop_places, get_route, get_height_profile, calculate_height_meters, weight_routes
from pyproj import Transformer
import json
import requests
import datetime
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Coordinates(BaseModel):
    X1: float
    Y1: float
    X2: float
    Y2: float
    time: str

@app.post("/route/")
async def create_route(coordinates: Coordinates):
    # Assuming routes_start, routes_dest, didok_number_start, didok_number_dest, coords_routes_start, coords_routes_dest are defined elsewhere
    # Choose the route with the lowest weight (route coordinates in WGS84)
    route_start = routes_start[coordinates.X1]
    route_dest = routes_dest[coordinates.Y1]

    # Choose starting coordinates, didok number and route coordinates
    coord_start = route_start['features'][1]['geometry']['coordinates']
    number_start = didok_number_start[coordinates.X1]
    coords_route_start = coords_routes_start[coordinates.X1]
    print(number_start)

    # Choose destination coordinates, didok number and route coordinates
    coord_dest = route_dest['features'][2]['geometry']['coordinates']
    number_dest = didok_number_dest[coordinates.Y1]
    coords_route_dest = coords_routes_dest[coordinates.Y1]
    print(coord_dest)

    # Call the get_journey function with the provided time and the calculated numbers
    journey = get_journey(number_start, number_dest, coordinates.time)

    return {"journey": journey}

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

# # get the height profiles of the routes
# routes_start_heights = []
# routes_dest_heights = []

# for route in routes_start_lv95:
#     profile = get_height_profile(route)
#     routes_start_heights.append(profile)
# with open('height_profiles_start.json', 'w') as f:
#     json.dump(routes_start_heights, f)
    
# for route in routes_dest_lv95:
#     profile = get_height_profile(route)
#     routes_dest_heights.append(profile)
# with open('height_profiles_dest.json', 'w') as f:
#     json.dump(routes_dest_heights, f)

with open('height_profiles_start.json', 'r') as f:
    routes_start_heights = json.load(f)
with open('height_profiles_dest.json', 'r') as f:
    routes_dest_heights = json.load(f)

start_height_meters = calculate_height_meters(routes_start_heights)
dest_height_meters = calculate_height_meters(routes_dest_heights)

# Weight the start and destination routes
start_route_weights = weight_routes(start_height_meters)
dest_route_weights = weight_routes(dest_height_meters)

print(start_route_weights)
print(dest_route_weights)

# Get the index of the route with the lowest weight
index_start = start_route_weights[0]
index_dest = dest_route_weights[0]

# Choose the route with the lowest weight (route coordinates in WGS84)
route_start = routes_start[index_start]
route_dest = routes_dest[index_dest]

# Choose starting coordinates, didok number and route coordinates
coord_start = route_start['features'][1]['geometry']['coordinates']
number_start = didok_number_start[index_start]
coords_route_start = coords_routes_start[index_start]
print(number_start)

# Choose destination coordinates, didok number and route coordinates
coord_dest = route_dest['features'][2]['geometry']['coordinates']
number_dest = didok_number_dest[index_dest]
coords_route_dest = coords_routes_dest[index_dest]
print(coord_dest)

######################## Function API request ÖV Journey ##########################
def get_journey(number_start, number_dest, time):
    params = {
        "from": number_start,
        "to": number_dest,
        "time": time
    }

    url = "http://transport.opendata.ch/v1/connections"
    response = requests.get(url, params=params)

    if response.status_code == 200:
        stop_places = response.json()
        return stop_places
    else:
        print(f"Error: Failed to retrieve data for numbers {number_start}, {number_dest}")
        return None
    
current_time = datetime.datetime.now().strftime("%H:%M")
journey = get_journey(number_start, number_dest, current_time)
with open('journey.json', 'w') as f:
    json.dump(journey, f)