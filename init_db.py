import requests
from pymongo import MongoClient


# DB 연결
client = MongoClient('localhost', 27017)
db = client.bobMate


# API fetch
def fetch_data_from_api(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()  # Assuming the API returns JSON data
        print(response)
    else:
        response.raise_for_status()

url = 'https://openapi.gg.go.kr/ParagonRestaurant'
fetch_data_from_api(url)