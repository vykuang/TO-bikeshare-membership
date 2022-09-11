# sample input
"""
trip_id,trip_start_time,trip_stop_time,trip_duration_seconds,from_station_id,from_station_name,to_station_id,to_station_name,user_type
712382,1/1/2017 0:00,1/1/2017 0:03,223,7051,Wellesley St E / Yonge St Green P,7089,Church St  / Wood St,Member

"""
import sys

import requests

# input = pd.read_csv('test-2017.csv')
# input_json = input.to_json()
# input = {
#     'trip_id': [712382, 712384],
#     'trip_start_time': ["1/1/2017 0:00", "1/1/2017 0:05",
#     'trip_stop_time': ["1/1/2017 0:03", "1/1/2017 0:29",
#     'trip_duration_seconds': [223, 1394],
#     'from_station_id': 7051,
#     "from_station_name": "Wellesley St E / Yonge St Green P",
#     'to_station_id': 7089,
#     "to_station_name": "Church St  / Wood St",
#     "user_type": "Member",
# }
input_dict = {
    "trip_id": 712382,
    "trip_start_time": "1/1/2017 0:00",
    "trip_stop_time": "1/1/2017 0:03",
    "trip_duration_seconds": 1130,
    "from_station_id": 7051,
    "from_station_name": "Wellesley St E / Yonge St Green P",
    "to_station_id": 7089,
    "to_station_name": "Church St  / Wood St",
    "user_type": "Member",
}

host_ip = str(sys.argv[1])
url = f"http://{host_ip}:9393/predict"
response = requests.put(url, json=input_dict, timeout=90)

print(response.json())
