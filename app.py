from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from pymongo import MongoClient
from bson import ObjectId
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'


# MongoDB 연결 설정
client = MongoClient('localhost', 27017)
db = client['bobMate']
posts_collection = db['posts']
users_collection = db['users']

# 홈페이지 - 리스트
@app.route('/')
def home():
    posts = posts_collection.find()
    return render_template('index.html', posts=posts)

# 회원가입
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        existing_user = users_collection.find_one({'email': email})
        print(email, username)
        if existing_user:
            return render_template('register.html', message='Email already exists, please choose another one')

        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        user_data = {
            'email': email,
            'username': username,
            'password': hashed_password,
            'attending_events': []  # 예시로 사용자가 참석하는 이벤트 목록을 저장할 수 있습니다
        }

        users_collection.insert_one(user_data)

        session['email'] = email  # 회원가입 후 자동으로 로그인 처리
        return redirect(url_for('home'))

    return render_template('register.html')

# 로그인
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        user = users_collection.find_one({'email': email})

        if user and bcrypt.checkpw(password, user['password']):
            session['email'] = email
            return redirect(url_for('home'))
        else:
            return render_template('login.html', message='Invalid email or password')

    return render_template('login.html')

# 로그아웃
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home')) 
    # 리다이렉트를 로그인 페이지로?????? 해야하지 않나????

# 포스팅 작성
@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        email = session.get('email')

        if email:
            user = users_collection.find_one({'email': email})
            author = user['username']
            post_id = posts_collection.insert_one({'title': title, 'content': content, 'author': author}).inserted_id
            return redirect(url_for('post_detail', post_id=post_id))
        else:
            return redirect(url_for('login'))

    return render_template('post.html')


# 포스팅 업데이트
@app.route('/post/<post_id>/update', methods=['GET', 'POST'])
def update_post(post_id):
    post = posts_collection.find_one({'_id': ObjectId(post_id)})
    if not post:
        return 'Post not found', 404

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        posts_collection.update_one({'_id': ObjectId(post_id)}, {'$set': {'title': title, 'content': content}})
        return redirect(url_for('post_detail', post_id=post_id))

    return render_template('update_post.html', post=post)

# 포스팅 삭제
@app.route('/post/<post_id>/delete', methods=['POST'])
def delete_post(post_id):
    posts_collection.delete_one({'_id': ObjectId(post_id)})
    return redirect(url_for('home'))

# 포스팅 상세 페이지
@app.route('/post/<post_id>')
def post_detail(post_id):
    post = posts_collection.find_one({'_id': ObjectId(post_id)})
    if not post:
        return 'Post not found', 404

    return render_template('post_detail.html', post=post)

# 사용자 참석 여부 업데이트
@app.route('/post/<post_id>/attend', methods=['POST'])
def update_attendance(post_id):
    email = session.get('email')
    if not email:
        return redirect(url_for('login'))

    user = users_collection.find_one({'email': email})
    if not user:
        return 'User not found', 404

    post = posts_collection.find_one({'_id': ObjectId(post_id)})
    if not post:
        return 'Post not found', 404

    attending = request.form.get('attending') == 'true'  # 예시로 checkbox 등에서 받아온 값을 처리

    if attending:
        # 예시로 users_collection에 사용자의 참석 여부를 업데이트하는 로직 추가
        users_collection.update_one({'_id': user['_id']}, {'$addToSet': {'attending_events': post_id}})
    else:
        users_collection.update_one({'_id': user['_id']}, {'$pull': {'attending_events': post_id}})

    return redirect(url_for('post_detail', post_id=post_id))

if __name__ == '__main__':
    app.run('0.0.0.0', port=5002, debug=True)
