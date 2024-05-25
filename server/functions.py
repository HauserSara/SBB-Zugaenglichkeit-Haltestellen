import requests
import http.client
import urllib.parse
import json
from fastapi import HTTPException
import math
import xml.etree.ElementTree as ET

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

    #print("Final request URL: ", response.url)

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

# ======================================= Function OJP request routing =========================================== #
def get_routes_ojp(lon1, lat1, lon2, lat2):
    url = "https://api.opentransportdata.swiss/ojp2020"

    headers = {
        "Content-Type": "application/xml",
        "Authorization": "Bearer eyJvcmciOiI2NDA2NTFhNTIyZmEwNTAwMDEyOWJiZTEiLCJpZCI6Ijc4MDlhMzhlOWUyMzQzODM4YmJjNWIwNjQxN2Y0NTk3IiwiaCI6Im11cm11cjEyOCJ9"
    }

    body = f"""
    <?xml version="1.0" encoding="utf-8"?>
    <OJP xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://www.siri.org.uk/siri" version="1.0" xmlns:ojp="http://www.vdv.de/ojp" xsi:schemaLocation="http://www.siri.org.uk/siri ../ojp-xsd-v1.0/OJP.xsd">
        <OJPRequest>
            <ServiceRequest>
                <RequestTimestamp>2024-05-20T12:00:10.154Z</RequestTimestamp>
                <RequestorRef>API-Explorer</RequestorRef>
                <ojp:OJPTripRequest>
                    <RequestTimestamp>2024-05-20T12:00:10.154Z</RequestTimestamp>
                    <ojp:Origin>
                        <ojp:PlaceRef>
                            <ojp:GeoPosition>
                                <Longitude>{lon1}</Longitude>
                                <Latitude>{lat1}</Latitude>
                            </ojp:GeoPosition>
                            <ojp:LocationName>
                                <ojp:Text>{lon1}, {lat1}</ojp:Text>
                            </ojp:LocationName>
                        </ojp:PlaceRef>
                        <ojp:DepArrTime>2024-05-20T11:57:19</ojp:DepArrTime>
                        <ojp:IndividualTransportOptions>
                            <ojp:Mode>walk</ojp:Mode>
                            <ojp:MaxDistance>1000</ojp:MaxDistance>
                        </ojp:IndividualTransportOptions>
                    </ojp:Origin>
                    <ojp:Destination>
                        <ojp:PlaceRef>
                            <ojp:GeoPosition>
                                <Longitude>{lon2}</Longitude>
                                <Latitude>{lat2}</Latitude>
                            </ojp:GeoPosition>
                            <ojp:LocationName>
                                <obj:Text>{lon2}, {lat2}</obj:Text>
                            </ojp:LocationName>
                        </ojp:PlaceRef>
                        <ojp:IndividualTransportOptions>
                            <ojp:Mode>walk</ojp:Mode>
                            <ojp:MaxDistance>1000</ojp:MaxDistance>
                        </ojp:IndividualTransportOptions>
                    </ojp:Destination>
                    <ojp:Params>
                        <ojp:IncludeTrackSections>true</ojp:IncludeTrackSections>
                        <ojp:IncludeLegProjection>true</ojp:IncludeLegProjection>
                        <ojp:IncludeTurnDescription>true</ojp:IncludeTurnDescription>
                        <ojp:IncludeIntermediateStops>false</ojp:IncludeIntermediateStops>
                    </ojp:Params>
                </ojp:OJPTripRequest>
            </ServiceRequest>
        </OJPRequest>
    </OJP>
    """

    response = requests.post(url, headers=headers, data=body)

    # ADD ERROR HANDLING
    # ...

    print("Status code:", response.status_code)

    # write response to xml
    with open('output.xml', 'w') as f:
        f.write(response.text)
    # Parse the response text as XML
    root = ET.fromstring(response.text)

    return root

# ======================================= Handle Trip Leg for accessing coordinates (OJP) ========================= #
def handle_leg(trip_leg, leg_type):
    coordinates = []
    for link_projection in trip_leg.iter('{http://www.vdv.de/ojp}LinkProjection'):
        for position in link_projection.iter('{http://www.vdv.de/ojp}Position'):
            longitude = float(position.find('{http://www.siri.org.uk/siri}Longitude').text)
            latitude = float(position.find('{http://www.siri.org.uk/siri}Latitude').text)
            coordinates.append([latitude, longitude])
    return {'type': leg_type, 'coordinates': coordinates}

# ======================================= Function OJP convert coordinates (WGS84 to LV95) ======================= #
def transform_coordinates(result_leg_ids_wgs84, transformer):

    result_leg_ids_lv95 = {}
    for result_id, legs in result_leg_ids_wgs84.items():
        leg_ids_lv95 = {}
        for leg_id, leg_info in legs.items():
            coordinates_lv95 = []
            for latitude, longitude in leg_info['coordinates']:
                # Transform the coordinates to LV95
                lv95_Y, lv95_X = transformer.transform(latitude, longitude)
                coordinates_lv95.append([round(lv95_Y, 1), round(lv95_X, 1)])
            leg_ids_lv95[leg_id] = {'type': leg_info['type'], 'coordinates': coordinates_lv95}
        result_leg_ids_lv95[result_id] = leg_ids_lv95

    return result_leg_ids_lv95

# ======================================= Function API request height profile Journey Maps ==================================== #
def get_height_profile_jm(index, route, distance):
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
    
# ======================================= Function API request height profile OJP ==================================== #
def get_height_profile_ojp(result_id, leg_id, route):
    geom = {
        'type': 'LineString',
        'coordinates': route,
    }

    # Convert the geom dictionary to a JSON string
    geom_json = json.dumps(geom)

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
        print(f'Error: Failed to retrieve height profile for route {result_id}, {leg_id}')
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
def weight_routes(profile):
    weighted_routes = []

    for index, profile, total_distance in profile:
        total_resistance = 0
        if profile is None:
            total_resistance = None
        else:
            for i in range(1, len(profile)):
                height_difference = profile[i]['alts']['DTM25'] - profile[i-1]['alts']['DTM25']
                dist_difference = profile[i]['dist'] - profile[i-1]['dist']
                # calculate the slope angle between two coordinates of a leg
                slope_angle = math.degrees(math.atan(height_difference / dist_difference)) if dist_difference != 0 else 0
                # calculate the slope factor between two coordinates of a leg
                slope_factor = dist_difference * math.tan(math.radians(slope_angle))
                # calculate the resistance between two coordinates of a leg
                resistance = dist_difference * slope_factor
                total_resistance += resistance
            total_resistance *= total_distance  # multiply the total resistance by the total distance
        weighted_routes.append((index, total_resistance))
        
        # return route with minimal weight, None values are ignored
        return min(weighted_routes, key=lambda x: abs(x[1]) if x[1] is not None else float('inf'))
    
# ======================================= Function OJP request öV-Journey ======================================== #
def get_pt_routes_ojp(didok_start, name_start, didok_dest, name_dest):
    url = "https://api.opentransportdata.swiss/ojp2020"

    headers = {
        "Content-Type": "application/xml",
        "Authorization": "Bearer eyJvcmciOiI2NDA2NTFhNTIyZmEwNTAwMDEyOWJiZTEiLCJpZCI6Ijc4MDlhMzhlOWUyMzQzODM4YmJjNWIwNjQxN2Y0NTk3IiwiaCI6Im11cm11cjEyOCJ9"
    }
    body = f"""
    <?xml version="1.0" encoding="utf-8"?>
    <OJP xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://www.siri.org.uk/siri" version="1.0" xmlns:ojp="http://www.vdv.de/ojp" xsi:schemaLocation="http://www.siri.org.uk/siri ../ojp-xsd-v1.0/OJP.xsd">
        <OJPRequest>
            <ServiceRequest>
                <RequestTimestamp>2024-05-25T13:00:05.035Z</RequestTimestamp>
                <RequestorRef>API-Explorer</RequestorRef>
                <ojp:OJPTripRequest>
                    <RequestTimestamp>2024-05-25T13:00:05.035Z</RequestTimestamp>
                    <ojp:Origin>
                        <ojp:PlaceRef>
                            <ojp:StopPlaceRef>{didok_start}</ojp:StopPlaceRef>
                            <ojp:LocationName>
                                <ojp:Text>{name_start}</ojp:Text>
                            </ojp:LocationName>
                        </ojp:PlaceRef>
                        <ojp:DepArrTime>2024-05-25T14:59:39</ojp:DepArrTime>
                    </ojp:Origin>
                    <ojp:Destination>
                        <ojp:PlaceRef>
                            <ojp:StopPlaceRef>{didok_dest}</ojp:StopPlaceRef>
                            <ojp:LocationName>
                                <ojp:Text>{name_dest}</ojp:Text>
                            </ojp:LocationName>
                        </ojp:PlaceRef>
                    </ojp:Destination>
                    <ojp:Params>
                        <ojp:IncludeTrackSections>true</ojp:IncludeTrackSections>
                        <ojp:IncludeLegProjection>true</ojp:IncludeLegProjection>
                        <ojp:IncludeTurnDescription>true</ojp:IncludeTurnDescription>
                        <ojp:IncludeIntermediateStops>false</ojp:IncludeIntermediateStops>
                    </ojp:Params>
                </ojp:OJPTripRequest>
            </ServiceRequest>
        </OJPRequest>
    </OJP>
    """

    response = requests.post(url, headers=headers, data=body)

    # ADD ERROR HANDLING
    # ...

    print("Status code:", response.status_code)

    # # write response to xml
    # with open('output.xml', 'w') as f:
    #     f.write(response.text)
    # Parse the response text as XML
    root = ET.fromstring(response.text)

    return response.text