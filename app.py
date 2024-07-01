from bson import ObjectId
from pymongo import MongoClient

from flask import Flask, render_template, jsonify, request
from flask.json.provider import JSONProvider

import json
import sys

from datetime import datetime

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.bobMate
res_collection = db['restaurants']
user_collection = db['users']


#홈페이지 - 리스트
@app.route('/')
def home():
    return render_template('index.html')



@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    restaurants = list(res_collection.find({}, {'_id': 1, 'BIZPLC_NM': 1, 'REFINE_ROADNM_ADDR': 1}))
    return jsonify(restaurants)
    a = jsonify(restaurants)
    print(a)



if __name__ == '__main__':
    app.run('0.0.0.0', port=5002, debug=True)