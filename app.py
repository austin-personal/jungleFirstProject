from bson import ObjectId
from pymongo import MongoClient
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.bobMate
res_collection = db['posts']
user_collection = db['users']

# 홈페이지 - 리스트
@app.route('/')
def home():
    return render_template('index.html')
