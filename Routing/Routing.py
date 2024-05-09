from functions import get_stop_places, get_route_jm, get_height_profile, calculate_height_meters, weight_routes
from pyproj import Transformer
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

app = FastAPI()

origins = [
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Coordinates(BaseModel):
    lat1: float
    lon1: float
    lat2: float
    lon2: float
    time: str

# define transformer to convert coordinates from WGS84 to LV95
transformer = Transformer.from_crs('epsg:4326', 'epsg:2056')

@app.post("/route_journeymaps/")
async def create_route(coordinates: Coordinates):
    # nur für testzwecke
    print(coordinates)
    
    # get stop places within a certain distance of the given coordinates
    start_time = time.time()
    try:
        stop_places_start = get_stop_places(coordinates.lat1, coordinates.lon1)
        stop_places_dest = get_stop_places(coordinates.lat2, coordinates.lon2)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    print(f"Time taken for get_stop_places: {time.time() - start_time} seconds")

    # get the didok-numbers of the stop places
    start_time = time.time()
    didok_number_start = [entry['number'] for entry in stop_places_start]
    didok_number_dest = [entry['number'] for entry in stop_places_dest]
    print(f"Time taken for getting didok numbers: {time.time() - start_time} seconds")
    # TESTZWECKE
    # print("STOPPLACES")
    # print(len(didok_number_start))
    # print(didok_number_start)
    # print('----------------------------------------')
    # print(len(didok_number_dest))
    # print(didok_number_dest)
    # print("========================================")

    # get the routes between the coordinates and the stop places
    start_time = time.time()
    routes_start = [get_route_jm(coordinates.lat1, coordinates.lon1, entry, 'start') for entry in didok_number_start]
    routes_dest = [get_route_jm(coordinates.lat2, coordinates.lon2, entry, 'dest') for entry in didok_number_dest]
    print(f"Time taken for get_route: {time.time() - start_time} seconds")
    # TESTZWECKE
    # print("ROUTES")
    # print(len(routes_start))
    # print(routes_start)
    # print('----------------------------------------')
    # print(len(routes_dest))
    # print(routes_dest[0])
    # print("========================================")

    # define lists for the coordinates of the routes
    coords_routes_start = []
    coords_routes_dest = []

    # get the coordinates of the routes
    start_time = time.time()
    for index, feature in enumerate(routes_start):
        route = feature['features'][0]['geometry']['coordinates']
        #print(route)
        #print('----- TEST ------')
        coords_routes_start.append((index, route))
    # TESTZWECKE
    # print("COORDS")
    # print(len(coords_routes_start))
    # print(coords_routes_start)
    # print('----------------------------------------')

    for index, feature in enumerate(routes_dest):
        route = feature['features'][0]['geometry']['coordinates']
        coords_routes_dest.append((index, route))
    print(f"Time taken for getting coordinates: {time.time() - start_time} seconds")
    # TESTZWECKE
    # print(len(coords_routes_dest))
    # print(coords_routes_dest[0])
    # print("========================================")

    # define lists for the coordinates of the routes in LV95
    routes_start_lv95 = []
    routes_dest_lv95 = []

    # convert the coordinates of the routes to LV95
    start_time = time.time()
    for index, route in coords_routes_start:
        route_lv95 = [(transformer.transform(latitude, longitude)) for longitude, latitude in route]
        routes_start_lv95.append((index, route_lv95))

    for index, route in coords_routes_dest:
        route_lv95 = [(transformer.transform(latitude, longitude)) for longitude, latitude in route]
        routes_dest_lv95.append((index, route_lv95))
    print(f"Time taken for transforming coordinates: {time.time() - start_time} seconds")

    # define lists for the height profiles of the routes
    routes_start_heights = []
    routes_dest_heights = []
    # get the height profiles of the routes
    start_time = time.time()
    for index, route in routes_start_lv95:
        profile = get_height_profile(index, route)
        routes_start_heights.append((index, profile))
    # TESTZWECKE
    # print("PROFILES")
    # print(len(routes_start_heights))
    # for index, profile in routes_start_heights[:2]:
    #     print(index, profile[:2])
    # print('----------------------------------------')
        
    for index, route in routes_dest_lv95:
        profile = get_height_profile(index, route)
        routes_dest_heights.append((index, profile))
    print(f"Time taken for get_height_profile: {time.time() - start_time} seconds")
    # TESTZWECKE
    # print(len(routes_dest_heights))
    # for index, profile in routes_dest_heights[:2]:
    #     print(index, profile[:2])
    # print("========================================")

    # Calculate the heightmeters of the routes
    start_time = time.time()
    start_height_meters = calculate_height_meters(routes_start_heights)
    dest_height_meters = calculate_height_meters(routes_dest_heights)
    print(f"Time taken for calculate_height_meters: {time.time() - start_time} seconds")
    # TESTZWECKE
    # print("HEIGHTS")
    # print(start_height_meters)
    # print(dest_height_meters)
    # print("========================================")

    # Weight the start and destination routes
    start_time = time.time()
    start_route_weights = weight_routes(start_height_meters)
    dest_route_weights = weight_routes(dest_height_meters)
    print(f"Time taken for weight_routes: {time.time() - start_time} seconds")
    # TESTZWECKE
    # print("WEIGHTS")
    # print(start_route_weights)
    # print(dest_route_weights)
    # print("========================================")

    # Choose the route with the lowest weight (route coordinates in WGS84)
    start_time = time.time()
    route_start = routes_start[start_route_weights[0]]
    route_dest = routes_dest[dest_route_weights[0]]
    print(f"Time taken for choosing the route: {time.time() - start_time} seconds")

    # TESTZWECKE
    # print(route_start)
    # print(route_dest)

    # Call the get_journey function with the provided time and the calculated numbers
    # journey = get_journey(number_start, number_dest, coordinates.time)

    return route_start, route_dest