from functions import get_stop_places, get_route_jm, get_height_profile, calculate_height_meters, weight_routes
from pyproj import Transformer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

# define lists for the coordinates of the routes
coords_routes_start = []
coords_routes_dest = []

# define transformer to convert coordinates from WGS84 to LV95
transformer = Transformer.from_crs('epsg:4326', 'epsg:2056')

# define lists for the coordinates of the routes in LV95
routes_start_lv95 = []
routes_dest_lv95 = []

# define lists for the height profiles of the routes
routes_start_heights = []
routes_dest_heights = []

@app.post("/route_journeymaps/")
async def create_route(coordinates: Coordinates):
    # get stop places within a certain distance of the given coordinates
    stop_places_start = get_stop_places(coordinates.lat1, coordinates.lon1)
    stop_places_dest = get_stop_places(coordinates.lat2, coordinates.lon2)

    # get the didok-numbers of the stop places
    didok_number_start = [entry['number'] for entry in stop_places_start]
    didok_number_dest = [entry['number'] for entry in stop_places_dest]

    # get the routes between the coordinates and the stop places
    routes_start = [get_route_jm(coordinates.lat1, coordinates.lon1, entry, 'start') for entry in didok_number_start]
    routes_dest = [get_route_jm(coordinates.lat2, coordinates.lon2, entry, 'dest') for entry in didok_number_dest]

    # get the coordinates of the routes
    for index, feature in enumerate(routes_start):
        route = feature['features'][0]['geometry']['coordinates']
        coords_routes_start.append((index, route))

    for index, feature in enumerate(routes_dest):
        route = feature['features'][0]['geometry']['coordinates']
        coords_routes_dest.append((index, route))
    print(coords_routes_start)
    print(coords_routes_dest)
    # convert the coordinates of the routes to LV95
    for index, route in coords_routes_start:
        route_lv95 = [(transformer.transform(latitude, longitude)) for longitude, latitude in route]
        routes_start_lv95.append((index, route_lv95))

    for index, route in coords_routes_dest:
        route_lv95 = [(transformer.transform(latitude, longitude)) for longitude, latitude in route]
        routes_dest_lv95.append((index, route_lv95))

    # get the height profiles of the routes
    for index, route in routes_start_lv95:
        profile = get_height_profile(index, route)
        routes_start_heights.append((index, profile))
        
    for index, route in routes_dest_lv95:
        profile = get_height_profile(index, route)
        routes_dest_heights.append((index, profile))

    # Calculate the heightmeters of the routes
    start_height_meters = calculate_height_meters(routes_start_heights)
    dest_height_meters = calculate_height_meters(routes_dest_heights)
    
    # Weight the start and destination routes
    start_route_weights = weight_routes(start_height_meters)
    dest_route_weights = weight_routes(dest_height_meters)

    # Choose the route with the lowest weight (route coordinates in WGS84)
    route_start = routes_start[start_route_weights[0]]
    route_dest = routes_dest[dest_route_weights[0]]

    # Call the get_journey function with the provided time and the calculated numbers
    # journey = get_journey(number_start, number_dest, coordinates.time)

    return route_start, route_dest