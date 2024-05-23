import pandas as pd
from functions import get_stop_places, get_height_profile, calculate_height_meters, weight_routes
from pyproj import Transformer
import json
import datetime
import requests
import xml.etree.ElementTree as ET
import folium
import time
import statistics
import math

data = pd.read_csv('data/Start_Ziel.csv')

# starting coordinates
lon1 = data['X'][0]
lat1 = data['Y'][0]

# destination coordinates
lon2 = data['X'][1]
lat2 = data['Y'][1]

# # get stop places within a certain distance of the given coordinates
# stop_places_start = get_stop_places(lat1, lon1)
# stop_places_dest = get_stop_places(lat2, lon2)

# # get the didok-numbers of the stop places
# didok_number_start = [(entry['number'], entry['designationofficial']) for entry in stop_places_start]
# didok_number_dest = [(entry['number'], entry['designationofficial']) for entry in stop_places_dest]
# print(didok_number_start)

################################## OJP request ##################################
# define lists for the coordinates of the routes
coords_routes_start = []
coords_routes_dest = []

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
                            <ojp:Text>Kasparstrasse</ojp:Text>
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
                            <obj:Text>Dornhaldestrasse</obj:Text>
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
start = time.time()
response = requests.post(url, headers=headers, data=body)
end = time.time()
print(f"Time request: {time.time() - start} seconds")
print("Status code:", response.status_code)

# write response to xml
with open('output.xml', 'w') as f:
    f.write(response.text)

root = ET.fromstring(response.text)
result_leg_ids = {}
for trip_result in root.iter('{http://www.vdv.de/ojp}TripResult'):
    result_id = trip_result.find('{http://www.vdv.de/ojp}ResultId').text
    leg_ids = {}
    for trip_leg in trip_result.iter('{http://www.vdv.de/ojp}TripLeg'):
        leg_id = trip_leg.find('{http://www.vdv.de/ojp}LegId').text
        coordinates = []
        if trip_leg.find('{http://www.vdv.de/ojp}ContinuousLeg') is not None:
            leg_type = 'ContinuousLeg'
            for link_projection in trip_leg.iter('{http://www.vdv.de/ojp}LinkProjection'):
                for position in link_projection.iter('{http://www.vdv.de/ojp}Position'):
                    longitude = float(position.find('{http://www.siri.org.uk/siri}Longitude').text)
                    latitude = float(position.find('{http://www.siri.org.uk/siri}Latitude').text)
                    coordinates.append([latitude, longitude])
        elif trip_leg.find('{http://www.vdv.de/ojp}TransferLeg') is not None:
            leg_type = 'TransferLeg'
            for link_projection in trip_leg.iter('{http://www.vdv.de/ojp}LinkProjection'):
                for position in link_projection.iter('{http://www.vdv.de/ojp}Position'):
                    longitude = float(position.find('{http://www.siri.org.uk/siri}Longitude').text)
                    latitude = float(position.find('{http://www.siri.org.uk/siri}Latitude').text)
                    coordinates.append([latitude, longitude])
        elif trip_leg.find('{http://www.vdv.de/ojp}TimedLeg') is not None:
            leg_type = 'TimedLeg'
        leg_ids[leg_id] = {'type': leg_type, 'coordinates': coordinates}
    result_leg_ids[result_id] = leg_ids
    #result_leg_ids.append((trip_result, leg_id))

#print(result_leg_ids)


# define transformer to convert coordinates from WGS84 to LV95
transformer = Transformer.from_crs('epsg:4326', 'epsg:2056')

def transform_coordinates_to_lv95(result_leg_ids_wgs84):

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

result_leg_ids_lv95 = transform_coordinates_to_lv95(result_leg_ids)
#print(result_leg_ids_lv95)

routes_start_heights = []

profiles = {}

for result_id, legs in result_leg_ids_lv95.items():
    for leg_id, leg_info in legs.items():
        route = leg_info['coordinates']
        # Ignore the entry if coordinates are empty or route has only two points
        if len(route) > 2:
            profile = get_height_profile(result_id, leg_id, route)
            # Add the profile to the dictionary
            if result_id not in profiles:
                profiles[result_id] = {}
            profiles[result_id][leg_id] = profile

#print(profiles)

average_distances = {}
standard_deviations = {}

for result_id, legs in profiles.items():
    for leg_id, leg_infos in legs.items():
        differences = []
        for i in range(1, len(leg_infos)):
            dist_difference = abs(leg_infos[i]['dist'] - leg_infos[i-1]['dist'])
            differences.append(dist_difference)
        average_distance = sum(differences) / len(differences) if differences else 0
        standard_deviation = statistics.stdev(differences) if len(differences) > 1 else 0
        if result_id not in average_distances:
            average_distances[result_id] = {}
            standard_deviations[result_id] = {}
        average_distances[result_id][leg_id] = average_distance
        standard_deviations[result_id][leg_id] = standard_deviation

#print(average_distances)

# # Print each average distance and standard deviation
# for result_id, legs in average_distances.items():
#     for leg_id, average_distance in legs.items():
#         #print(f"Average distance for result_id {result_id}, leg_id {leg_id}: {average_distance}")
#         #print(f"Standard deviation for result_id {result_id}, leg_id {leg_id}: {standard_deviations[result_id][leg_id]}")
#         print(f'durchschn. Distanz: {average_distance}')
#         print(f'Standardabweichung: {standard_deviations[result_id][leg_id]}')
#         print('-----------------------------------')

# Calculate slope between points
# slope_angles = {}

# for result_id, legs in profiles.items():
#     for leg_id, leg_infos in legs.items():
#         for i in range(1, len(leg_infos)):
#             height_difference = abs(leg_infos[i]['alts']['DTM25'] - leg_infos[i-1]['alts']['DTM25'])
#             dist_difference = abs(leg_infos[i]['dist'] - leg_infos[i-1]['dist'])
#             slope_angle = math.degrees(math.atan(height_difference / dist_difference)) if dist_difference != 0 else 0
#             if result_id not in slope_angles:
#                 slope_angles[result_id] = {}
#             if leg_id not in slope_angles[result_id]:
#                 slope_angles[result_id][leg_id] = []
#             slope_angles[result_id][leg_id].append({'dist': dist_difference, 'slope_angle': slope_angle})

# print(slope_angles)



slope_factors = {}

for result_id, legs in profiles.items():
    for leg_id, leg_infos in legs.items():
        for i in range(1, len(leg_infos)):
            height_difference = abs(leg_infos[i]['alts']['DTM25'] - leg_infos[i-1]['alts']['DTM25'])
            dist_difference = abs(leg_infos[i]['dist'] - leg_infos[i-1]['dist'])
            slope_angle = math.degrees(math.atan(height_difference / dist_difference)) if dist_difference != 0 else 0
            slope_factor = dist_difference * math.tan(math.radians(slope_angle))
            if slope_angle >= 0:
                slope_factor += dist_difference
            else:
                slope_factor -= dist_difference
            if result_id not in slope_factors:
                slope_factors[result_id] = {}
            if leg_id not in slope_factors[result_id]:
                slope_factors[result_id][leg_id] = []
            slope_factors[result_id][leg_id].append({'dist': dist_difference, 'slope_factor': slope_factor})

# Print each slope factor
# for result_id, legs in slope_factors.items():
#     for leg_id, leg_infos in legs.items():
#         for info in leg_infos:
#             print(f"Result_id {result_id}, leg_id {leg_id}, dist: {info['dist']}, slope factor: {info['slope_factor']}")

print(slope_factors)

for result_id in result_leg_ids.keys():
    print(result_id)
# Print each slope angle
# for result_id, legs in slope_angles.items():
#     for leg_id, leg_infos in legs.items():
#         for info in leg_infos:
#             print(f"Result_id {result_id}, leg_id {leg_id}, dist: {info['dist']}, slope angle: {info['slope_angle']}")
# # Write the profiles to a file
# with open('profiles.json', 'w') as f:
#     json.dump(profiles, f)

# # generate json with coordinates
# start = time.time()
# root = ET.fromstring(response.text)
# for link_projection in root.iter('{http://www.vdv.de/ojp}LinkProjection'):
#     for position in link_projection.iter('{http://www.vdv.de/ojp}Position'):
#         longitude = position.find('{http://www.siri.org.uk/siri}Longitude').text
#         latitude = position.find('{http://www.siri.org.uk/siri}Latitude').text
#         coords_routes_start.append([float(latitude), float(longitude)])
# end = time.time()
# print(coords_routes_start)
# print(f"Time parsing: {time.time() - start} seconds")
# print("-------------------")

# for start in didok_number_start:
#     body = f"""
#     <siri:OJP xmlns="http://www.vdv.de/ojp" xmlns:siri="http://www.siri.org.uk/siri" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xsi:schemaLocation="http://www.vdv.de/ojp" version="1.0">
#         <siri:OJPRequest>
#             <siri:ServiceRequest>
#                 <siri:RequestTimestamp>2024-05-04T17:35:43.773Z</siri:RequestTimestamp>
#                 <siri:RequestorRef>Routing_test</siri:RequestorRef>
#                 <OJPTripRequest>
#                     <siri:RequestTimestamp>2024-05-04T17:35:43.773Z</siri:RequestTimestamp>
#                     <Origin>
#                         <PlaceRef>
#                             <GeoPosition>
#                                 <siri:Longitude>{lat1}</siri:Longitude>
#                                 <siri:Latitude>{lon1}</siri:Latitude>
#                             </GeoPosition>
#                             <LocationName>
#                                 <Text>{lat1}, {lon1}</Text>
#                             </LocationName>
#                         </PlaceRef>
#                         <DepArrTime>2024-05-04T15:56:37.323Z</DepArrTime>
#                         <IndividualTransportOptions>
#                             <Mode>walk</Mode>
#                             <MaxDuration>PT3000M</MaxDuration>
#                         </IndividualTransportOptions>
#                     </Origin>
#                     <Destination>
#                         <PlaceRef>
#                             <GeoPosition>
#                                 <siri:Longitude>{lat2}</siri:Longitude>
#                                 <siri:Latitude>{lon2}</siri:Latitude>
#                             </GeoPosition>
#                             <LocationName>
#                                 <Text>{lat2}, {lon2}</Text>
#                             </LocationName>
#                         </PlaceRef>
#                     </Destination>
#                     <Params>
#                         <NumberOfResultsAfter>5</NumberOfResultsAfter>
#                         <NumberOfResultsBefore>0</NumberOfResultsBefore>
#                         <IncludeTrackSections>true</IncludeTrackSections>
#                         <IncludeLegProjection>true</IncludeLegProjection>
#                         <IncludeTurnDescription>true</IncludeTurnDescription>
#                         <IncludeIntermediateStops>false</IncludeIntermediateStops>
#                         <ItModesToCover>walk</ItModesToCover>
#                     </Params>
#                 </OJPTripRequest>
#             </siri:ServiceRequest>
#         </siri:OJPRequest>
#     </siri:OJP>
#     """
#     start = time.time()
#     response = requests.post(url, headers=headers, data=body)
#     end = time.time()
#     print(f"Time request: {time.time() - start} seconds")
#     print("Status code:", response.status_code)

#     # # write response to xml
#     # with open('output.xml', 'w') as f:
#     #     f.write(response.text)

#     # generate json with coordinates
#     start = time.time()
#     root = ET.fromstring(response.text)
#     for link_projection in root.iter('{http://www.vdv.de/ojp}LinkProjection'):
#         for position in link_projection.iter('{http://www.vdv.de/ojp}Position'):
#             longitude = position.find('{http://www.siri.org.uk/siri}Longitude').text
#             latitude = position.find('{http://www.siri.org.uk/siri}Latitude').text
#             coords_routes_start.append([float(latitude), float(longitude)])
#     end = time.time()
#     print(coords_routes_start)
#     print(f"Time parsing: {time.time() - start} seconds")
#     print("-------------------")

# # Write the data to a JSON file
# with open('coordinates.json', 'w') as file:
#     json.dump(data, file)

# coords_routes_start = []
# coords_routes_dest = []

# url = "https://api.opentransportdata.swiss/ojp2020"

# headers = {
#     "Content-Type": "application/xml",
#     "Authorization": "Bearer eyJvcmciOiI2NDA2NTFhNTIyZmEwNTAwMDEyOWJiZTEiLCJpZCI6Ijc4MDlhMzhlOWUyMzQzODM4YmJjNWIwNjQxN2Y0NTk3IiwiaCI6Im11cm11cjEyOCJ9"
# }

# ################################## Map ##################################
# Map of all entries
# Create a map centered at the first coordinate
# first_leg = next(iter(result_leg_ids.values()))
# first_coordinate = first_leg[next(iter(first_leg.keys()))]['coordinates'][0]
# m = folium.Map(location=[float(first_coordinate[0]), float(first_coordinate[1])], zoom_start=14)

# # Add each set of coordinates as a polyline on the map
# for result_id, legs in result_leg_ids.items():
#     for leg_id, leg_info in legs.items():
#         if leg_info['coordinates']:  # Check if coordinates is not empty
#             polyline = folium.PolyLine(leg_info['coordinates'], color="red", weight=2.5, opacity=1)
#             m.add_child(polyline)

# # Save the map to an HTML file
# m.save('map.html')

# Map of last entry
# # Create a map centered at the first coordinate
# first_leg = next(iter(result_leg_ids.values()))
# first_coordinate = first_leg[next(iter(first_leg.keys()))]['coordinates'][0]
# m = folium.Map(location=[float(first_coordinate[0]), float(first_coordinate[1])], zoom_start=14)

# # Get the last trip result
# last_result_id, last_result_legs = list(result_leg_ids.items())[-1]

# # Get the last leg of the last trip result
# last_leg_id, last_leg_info = list(last_result_legs.items())[-1]

# # Check if coordinates is not empty and create a polyline
# if last_leg_info['coordinates']:
#     polyline = folium.PolyLine(last_leg_info['coordinates'], color="red", weight=2.5, opacity=1)
#     m.add_child(polyline)

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