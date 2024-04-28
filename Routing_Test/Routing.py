import pandas as pd
from functions import get_stop_places, get_route, get_height_profile
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

print(routes_start_heights[0][0])

######################## Function calculate height profile ########################
def calculate_height_meters(height_profiles):
    height_meters = []

    for profile in height_profiles:
        if profile is None:
            height_meters.append(None)
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

        height_meters.append((round(upwards, 1), round(downwards, 1)))

    return height_meters

start_height_meters = calculate_height_meters(routes_start_heights)
print(start_height_meters)

dest_height_meters = calculate_height_meters(routes_dest_heights)
print(dest_height_meters)