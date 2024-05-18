import requests
import http.client
import urllib.parse
import json
from fastapi import HTTPException
import math

# ======================================= Function API request stop places ======================================= # 
# get stop places within a certain distance of the given coordinates
def get_stop_places(lat, lon, distance=500):
    params = {
        'where': f"within_distance(geopos_haltestelle, geom'Point({lat} {lon})',{distance}m)",
        'limit': 5
    }

    params_str = urllib.parse.urlencode(params)

    conn = http.client.HTTPSConnection('data.sbb.ch', 443)
    conn.request('GET', '/api/explore/v2.1/catalog/datasets/haltestelle-haltekante/records?' + params_str)

    response = conn.getresponse()

    if response.status == 200:
        stop_places = json.loads(response.read())
        valid_stop_places = [stop_place for stop_place in stop_places['results'] if stop_place['meansoftransport'] is not None]

        if not valid_stop_places:
            raise Exception(f"No valid stop places found within {distance} m of coordinates {lat}, {lon}")
        
        return valid_stop_places
    else:
        print(f'Error: Failed to retrieve stop places for coordinates {lat}, {lon}')
        return None

# ======================================= Function Journey Maps API request routing ============================== #
# get the route between a coordinate and a stop place
session = requests.Session()

def get_route_jm(lat, lon, stop_place, type):
    params = {
        'client': 'webshop',
        'clientVersion': 'latest',
        'lang': 'de',
        'accessible': 'true',
        'api_key': '59b20b25750f56bf888ef149873f24da'
    }

    # set parameters based on whether the coordinate is the starting point or the destination
    if type == 'start':
        params['fromLatLng'] = f'{lat},{lon}'
        params['toStationID'] = stop_place
    elif type == 'dest':
        params['fromStationID'] = stop_place
        params['toLatLng'] = f'{lat},{lon}'
    else:
        print(f"Error: Invalid type {type}. Expected 'start' or 'dest'")
        return None

    url = 'https://journey-maps.api.sbb.ch/v1/transfer'
    response = session.get(url, params=params)

    print("Final request URL: ", response.url)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    route = response.json()
    coords = route['features'][0]['geometry']['coordinates']
    if not isinstance(coords[0], list):
        message = f"No route found between coordinates {lat}, {lon} and stop place {stop_place}."
        raise HTTPException(status_code=400, detail=str(message))
    return route

# ======================================= Function API request height profile ==================================== #
def get_height_profile(index, route, distance):
    geom = {
        'type': 'LineString',
        'coordinates': route,
    }

    # Convert the geom dictionary to a JSON string
    geom_json = json.dumps(geom)

    # define the number of points to be returned by the API
    if distance > 10:
        nb_points = int(distance/5)
    else:
        nb_points = int(distance)

    # Include the JSON string in the URL
    #data = {'geom': geom_json, 'sr': 2056, 'nb_points': nb_points}
    data = {'geom': geom_json, 'sr': 2056}
    response = requests.post('https://api3.geo.admin.ch/rest/services/profile.json', data=data)

    if response.status_code == 200:
        profile = response.json()
        # with open(f'data/route_{index}_profile.geojson', 'w') as f:
        #     json.dump(profile, f)
        return profile
    else:
        print(f'Error: Failed to retrieve height profile for route {index}')
        print(f'URL: {response.url}')
        print(f'Response status code: {response.status_code}')
        print(f'Response text: {response.text}')
        return None
    
# ======================================= Function calculate height meters ======================================= #
def calculate_slope(point1, point2):
    # Höhendifferenz zwischen den beiden Punkten
    delta_height = point2['alts']['COMB'] - point1['alts']['COMB']

    # Horizontale Distanz zwischen den beiden Punkten
    delta_distance = point2['dist'] - point1['dist']

    # Berechnung des Höhenwinkels in Grad
    slope = math.degrees(math.atan(delta_height / delta_distance))

    return slope

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
        # print(len(heights))

        # Calculate the differences between consecutive points
        for i in range(1, len(heights)):
            diff = heights[i] - heights[i-1]
            if diff > 0:
                upwards += diff
            elif diff < 0:
                downwards += abs(diff)

        height_meters.append((index, (round(upwards, 1), round(downwards, 1))))

    return height_meters

# ======================================= Function calculate weight ============================================== #
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