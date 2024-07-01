# 음식점들 DB에 저장
# 경기도 음식 API 사용


#### 고칠점
# 1. API 가리기
# 2. 김밥, 중국식 데이터 뤵ㄱ들링?


import requests
from pymongo import MongoClient
import xml.etree.ElementTree as ET

# DB 연결
client = MongoClient('localhost', 27017)
db = client.bobMate
collection = db['restaurants']  # Ensure you have a collection named 'restaurants'

# Clear the collection before inserting new data
collection.delete_many({})

# API fetch
def fetch_data_from_api(api_url):
    response = requests.get(api_url)
    print(response)
    if response.status_code == 200:
        # Parse the XML response
        root = ET.fromstring(response.content)
        return root
    else:
        response.raise_for_status()

def parse_and_store_data(root):
    # Loop through the elements in the XML tree and store them in MongoDB
    for child in root.findall('.//row'):
        data = {}
        for elem in child:
            data[elem.tag] = elem.text
        print(data)
        collection.insert_one(data)

url_delicious = 'https://openapi.gg.go.kr/PlaceThatDoATasteyFoodSt?KEY=1771308795ca471db230aba989f8fc30&pIndex=1&pSize=500&SIGUN_CD=41110'
#url_dosirak = 'https://openapi.gg.go.kr/Genrestrtlunch?KEY=1771308795ca471db230aba989f8fc30&pIndex=1&pSize=500&SIGUN_CD=41110'
url_moving = 'https://openapi.gg.go.kr/Genrestrtmovmntcook?KEY=1771308795ca471db230aba989f8fc30&pIndex=1&pSize=500&SIGUN_CD=41110'
url_mobeom = 'https://openapi.gg.go.kr/ParagonRestaurant?KEY=1771308795ca471db230aba989f8fc30&pIndex=1&pSize=500&SIGUN_CD=41110'
#url_china = 'https://openapi.gg.go.kr/Genrestrtchifood?KEY=1771308795ca471db230aba989f8fc30SIGUN_CD=41110'
url_tang = 'https://openapi.gg.go.kr/Genrestrtsoup?KEY=1771308795ca471db230aba989f8fc30&pIndex=1&pSize=500&SIGUN_CD=41110'
url_fast = 'https://openapi.gg.go.kr/Genrestrtfastfood?KEY=1771308795ca471db230aba989f8fc30&pIndex=1&pSize=500&SIGUN_CD=41110'
url_japanese = 'https://openapi.gg.go.kr/Genrestrtjpnfood?KEY=1771308795ca471db230aba989f8fc30&pIndex=1&pSize=500&SIGUN_CD=41110'

restaurant_list = [ url_moving, url_mobeom, url_tang, url_fast, url_japanese] # 도시락(김밥)이랑 중국집 뺌

for url in restaurant_list:
    root = fetch_data_from_api(url)
    if root:
        parse_and_store_data(root)

print("Data stored successfully.")


