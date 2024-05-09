import pandas as pd
from functions import get_stop_places, get_height_profile, calculate_height_meters, weight_routes
from pyproj import Transformer
import json
import datetime
import requests
import xml.etree.ElementTree as ET
import folium

data = pd.read_csv('data/Start_Ziel.csv')

# starting coordinates
lat1 = data['X'][0]
lon1 = data['Y'][0]

# destination coordinates
lat2 = data['X'][1]
lon2 = data['Y'][1]

# get stop places within a certain distance of the given coordinates
stop_places_start = get_stop_places(lat1, lon1)
stop_places_dest = get_stop_places(lat2, lon2)

# get the didok-numbers of the stop places
didok_number_start = [(entry['number'], entry['designationofficial']) for entry in stop_places_start]
didok_number_dest = [(entry['number'], entry['designationofficial']) for entry in stop_places_dest]
print(didok_number_dest)

################################## OJP request ##################################
# define lists for the coordinates of the routes
coords_routes_start = []
coords_routes_dest = []

url = "https://api.opentransportdata.swiss/ojp2020"

headers = {
    "Content-Type": "application/xml",
    "Authorization": "Bearer eyJvcmciOiI2NDA2NTFhNTIyZmEwNTAwMDEyOWJiZTEiLCJpZCI6Ijc4MDlhMzhlOWUyMzQzODM4YmJjNWIwNjQxN2Y0NTk3IiwiaCI6Im11cm11cjEyOCJ9"
}

for start in didok_number_start:
    body = f"""
    <siri:OJP xmlns="http://www.vdv.de/ojp" xmlns:siri="http://www.siri.org.uk/siri" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xsi:schemaLocation="http://www.vdv.de/ojp" version="1.0">
        <siri:OJPRequest>
            <siri:ServiceRequest>
                <siri:RequestTimestamp>2024-05-04T17:35:43.773Z</siri:RequestTimestamp>
                <siri:RequestorRef>Routing_test</siri:RequestorRef>
                <OJPTripRequest>
                    <siri:RequestTimestamp>2024-05-04T17:35:43.773Z</siri:RequestTimestamp>
                    <Origin>
                        <PlaceRef>
                            <StopPlaceRef>{start[0]}</StopPlaceRef>
                            <LocationName>
                                <Text>{start[0]}</Text>
                            </LocationName>
                        </PlaceRef>
                        <DepArrTime>2024-05-04T15:56:37.323Z</DepArrTime>
                        <IndividualTransportOptions>
                            <Mode>walk</Mode>
                            <MaxDuration>PT3000M</MaxDuration>
                        </IndividualTransportOptions>
                    </Origin>
                    <Destination>
                        <PlaceRef>
                            <GeoPosition>
                                <siri:Longitude>{lat1}</siri:Longitude>
                                <siri:Latitude>{lon1}</siri:Latitude>
                            </GeoPosition>
                            <LocationName>
                                <Text>{lat1}, {lon1}</Text>
                            </LocationName>
                        </PlaceRef>
                    </Destination>
                    <Params>
                        <NumberOfResultsAfter>5</NumberOfResultsAfter>
                        <NumberOfResultsBefore>0</NumberOfResultsBefore>
                        <IncludeTrackSections>true</IncludeTrackSections>
                        <IncludeLegProjection>true</IncludeLegProjection>
                        <IncludeTurnDescription>true</IncludeTurnDescription>
                        <IncludeIntermediateStops>false</IncludeIntermediateStops>
                        <ItModesToCover>walk</ItModesToCover>
                    </Params>
                </OJPTripRequest>
            </siri:ServiceRequest>
        </siri:OJPRequest>
    </siri:OJP>
    """

    response = requests.post(url, headers=headers, data=body)

    print("Status code:", response.status_code)

    # write response to xml
    with open('output.xml', 'w') as f:
        f.write(response.text)

    # generate json with coordinates
    root = ET.fromstring(response.text)
    for link_projection in root.iter('{http://www.vdv.de/ojp}LinkProjection'):
        for position in link_projection.iter('{http://www.vdv.de/ojp}Position'):
            longitude = position.find('{http://www.siri.org.uk/siri}Longitude').text
            latitude = position.find('{http://www.siri.org.uk/siri}Latitude').text
            coords_routes_start.append([float(latitude), float(longitude)])
    print(coords_routes_start)
    print("-------------------")

# # Write the data to a JSON file
# with open('coordinates.json', 'w') as file:
#     json.dump(data, file)

# ################################## Map ##################################

# # Load the coordinates from the JSON file
# with open('coordinates.json', 'r') as file:
#     data = json.load(file)
# coordinates = data['coordinates']
# coordinates_line1 = coordinates[:-1]
# coordinates_line2 = coordinates[-2:]

# # Create a map centered at the first coordinate
# m = folium.Map(location=[float(coordinates[0][0]), float(coordinates[0][1])], zoom_start=14)

# # Add the first line (from the first to the second-to-last point)
# folium.PolyLine(coordinates_line1, color="red", weight=2.5, opacity=1).add_to(m)

# # Add the second line (from the second-to-last to the last point)
# folium.PolyLine(coordinates_line2, color="red", weight=2.5, opacity=1).add_to(m)

# # Save the map to an HTML file
# m.save('map.html')

#########################################################################

# # get the routes between the coordinates and the stop places
# routes_start = [get_route_ojp(lat1, lon1, entry, 'start') for entry in didok_number_start]
# routes_dest = [get_route_ojp(lat2, lon2, entry, 'dest') for entry in didok_number_dest]

# # get the coordinates of the routes
# for index, feature in enumerate(routes_start):
#     route = feature['features'][0]['geometry']['coordinates']
#     coords_routes_start.append((index, route))

# for index, feature in enumerate(routes_dest):
#     route = feature['features'][0]['geometry']['coordinates']
#     coords_routes_dest.append((index, route))

# # define transformer to convert coordinates from WGS84 to LV95
# transformer = Transformer.from_crs('epsg:4326', 'epsg:2056')

# # define lists for the coordinates of the routes in LV95
# routes_start_lv95 = []
# routes_dest_lv95 = []

# # convert the coordinates of the routes to LV95
# for index, route in coords_routes_start:
#     route_lv95 = [(transformer.transform(latitude, longitude)) for longitude, latitude in route]
#     routes_start_lv95.append((index, route_lv95))

# for index, route in coords_routes_dest:
#     route_lv95 = [(transformer.transform(latitude, longitude)) for longitude, latitude in route]
#     routes_dest_lv95.append((index, route_lv95))

# # get the height profiles of the routes
# routes_start_heights = []
# routes_dest_heights = []

# for index, route in routes_start_lv95:
#     profile = get_height_profile(index, route)
#     routes_start_heights.append((index, profile))
    
# for index, route in routes_dest_lv95:
#     profile = get_height_profile(index, route)
#     routes_dest_heights.append((index, profile))

# start_height_meters = calculate_height_meters(routes_start_heights)
# dest_height_meters = calculate_height_meters(routes_dest_heights)

# # Weight the start and destination routes
# start_route_weights = weight_routes(start_height_meters)
# dest_route_weights = weight_routes(dest_height_meters)

# # Choose the route with the lowest weight (route coordinates in WGS84)
# route_start = routes_start[start_route_weights[0]]
# route_dest = routes_dest[dest_route_weights[0]]

# # Choose starting coordinates, didok number and route coordinates
# coord_start = route_start['features'][1]['geometry']['coordinates']
# number_start = didok_number_start[start_route_weights[0]]
# coords_route_start = coords_routes_start[start_route_weights[0]]

# # Choose destination coordinates, didok number and route coordinates
# coord_dest = route_dest['features'][2]['geometry']['coordinates']
# number_dest = didok_number_dest[dest_route_weights[0]]
# coords_route_dest = coords_routes_dest[dest_route_weights[0]]

# ######################## Function API request ÖV Journey ##########################
# def get_journey(number_start, number_dest, time):
#     params = {
#         "from": number_start,
#         "to": number_dest,
#         "time": time
#     }

#     url = "http://transport.opendata.ch/v1/connections"
#     response = requests.get(url, params=params)

#     if response.status_code == 200:
#         stop_places = response.json()
#         return stop_places
#     else:
#         print(f"Error: Failed to retrieve data for numbers {number_start}, {number_dest}")
#         return None
    
# current_time = datetime.datetime.now().strftime("%H:%M")
# journey = get_journey(number_start, number_dest, current_time)
# with open('data/journey.json', 'w') as f:
#     json.dump(journey, f)