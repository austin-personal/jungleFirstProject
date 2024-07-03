from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from pymongo import MongoClient
from bson import ObjectId
import bcrypt
from flask import flash
from datetime import datetime
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__)
app.secret_key = 'your_secret_key'


socketio = SocketIO(app, cors_allowed_origins="*")

# Current Time
def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# MongoDB 연결 설정
client = MongoClient('localhost', 27017)
db = client['bobMate']
posts_collection = db['posts']
users_collection = db['users']

# 홈페이지 - 리스트
@app.route('/')
def home():
    posts = posts_collection.find()
    return render_template('Home.html', posts=posts)

# 회원가입
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = ''
        if 'confirmEmail' in request.form:
            confirmEmail = request.form['confirmEmail']
            existing_user = users_collection.find_one({'email': confirmEmail})
            
            if existing_user:
                print(existing_user)
                return jsonify({'exists': True}), 200
            else:
                return jsonify({'exists': False}), 200
            
        else:
            email = request.form['email']
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
            return redirect(url_for('get_posts'))

    return render_template('register.html')

# 로그인
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        print(email, password)
        user = users_collection.find_one({'email': email})

        if user and bcrypt.checkpw(password, user['password']):
            session['email'] = email
            return redirect(url_for('get_posts'))
        else:
            flash('Invalid email or password')
            return render_template('login.html')

    return render_template('login.html')

# 로그아웃
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home')) 

# 포스트 디비에서 가져오기
@app.route('/posts', methods=['GET', 'POST'])
def get_posts():
    posts_data = []
    if request.method == 'POST':
        sort_food = request.form.get('sort_food')
        sort_bobmate = request.form.get('sort_bobmate')
        # 카테고리 딕셔너리
        food_category_map = {
            'chi': '중식',
            'jap': '일식',
            'kor': '한식',
            'ame': '양식',
            'all': '전체'
        }

        mate_category_map = {
            'del': '배달',
            'shop': '매장',
            'all': '전체'
        }
        # 기본값 설정
        food_category = food_category_map.get(sort_food, None)
        mate_category = mate_category_map.get(sort_bobmate, None)
        print(food_category, mate_category)
        
        # 전체 선택시 모든 포스트 디비 가져오기
        query = {}
        if sort_food != 'all':
            query['food_cat'] = sort_food
        if sort_bobmate != 'all':
            query['bobmate_cat'] = sort_bobmate
        print(query)
        
        # 조회 수행
        if food_category and mate_category:
            posts = posts_collection.find(query)
            print(posts)
            for post in posts:
                # 기간 만료시 포스트 데이터 로드 안함
                p_date = post['date']
                p_time = post['time']
                p_datetime_str = f"{p_date} {p_time}"
                p_datetime = datetime.strptime(p_datetime_str, "%Y-%m-%d %H:%M")
                print(p_datetime)
                if get_current_time() > p_datetime_str:
                    print("기간만료")
                    continue
                elif post['current_post_attendees_count'] == post['max_People']:
                    print("인원 충족")
                    continue
                else: 
                    posts_data.append({
                        'id': str(post['_id']),
                        'title': post['title'],
                        'content': post['content'],
                        'author_email': post['author_email'],
                        'bobmate_cat': post.get('bobmate_cat'),
                        'food_cat': translate_food_cat(post.get('food_cat')),
                        'date': post.get('date'),
                        'time': post.get('time'),
                        'open_chat': post.get('open_chat'),
                        'max_People': post.get('max_People'),
                        'current_post_attendees_count': len(post.get('attendees'))
                    })
                #참가자 다 찼을시 로드 안함
                
            print(posts_data)
    return render_template('posts.html', posts_data=posts_data)

# 포스팅 상세 페이지
@app.route('/post/<post_id>')
def post_detail(post_id):
    # Retrieve post data from MongoDB
    post = posts_collection.find_one({'_id': ObjectId(post_id)})
    post['food_cat'] = translate_food_cat(post.get('food_cat'))
    post['bobmate_cat'] = translate_bobmate_cat(post.get('bobmate_cat'))
    current_post_attendees_count = len(post.get('attendees', []))
    post['cur_attend_num'] = current_post_attendees_count

    user = users_collection.find_one({'email': post['author_email']})

    user['username']= user.get('username')

    # 작성자가 자신의 포스트 상세 페이지에 접근할때
    if session.get('email') == post['author_email']:
        return render_template('hostpage.html', post=post, user=user,is_author=True)
    if not post:
        return 'Post not found', 404
    
    # Pass post data to the template for rendering
    return render_template('post_detail.html', post=post, user=user)

# 포스팅 작성
@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        email = session.get('email')

        title = request.form['title']
        content = request.form['content']
        
        bobmate_cat = request.form.get('bobmate_cat')
        food_cat = request.form.get('food_cat')
        date = request.form.get('date')
        time = request.form.get('time')
        open_chat = request.form.get('open_chat')
        max_People = request.form.get('max_People')
        current_post_attendees_count = 0

        if email:
            user = users_collection.find_one({'email': email})
            author_email = user['email']
            post_id = posts_collection.insert_one({'title': title, 'content': content, 'author_email': author_email,'bobmate_cat':bobmate_cat,'food_cat':food_cat,'date':date,'time':time,'open_chat':open_chat, 'max_People':max_People, 'current_post_attendees_count':current_post_attendees_count, 'attendees':[]  }).inserted_id
            return redirect(url_for('post_detail', post_id=post_id))
        else:
            flash('로그인이 만료 되었습니다')
            return redirect(url_for('login'))

    return render_template('post.html')

# 포스팅 수정 페이지로 이동
@app.route('/post/<post_id>/edit', methods=['GET'])
def edit_post(post_id):
    email = session.get('email')
    if not email:
        return redirect(url_for('login'))

    post = posts_collection.find_one({'_id': ObjectId(post_id), 'author_email': email})
    if not post:
        return render_template('error.html', message='Unauthorized access or post not found')

    post['food_cat'] = translate_food_cat(post.get('food_cat'))
    post['bobmate_cat'] = translate_bobmate_cat(post.get('bobmate_cat'))

    return render_template('update.html', post=post)

# 포스팅 업데이트
@app.route('/post/<post_id>/update', methods=['POST'])
def update_post(post_id):
    if request.method == 'POST':
        email = session.get('email')

        # Ensure user is logged in
        if not email:
            return redirect(url_for('login'))

        # Get the updated data from the form
        title = request.form['title']
        content = request.form['content']
        bobmate_cat = request.form.get('bobmate_cat')
        food_cat = request.form.get('food_cat')
        date = request.form.get('date')
        time = request.form.get('time')
        open_chat = request.form.get('open_chat')
        max_People = request.form.get('max_People')

        #기존 데이터에서 가져오는 정보
        pre_post = posts_collection.find_one({'_id': ObjectId(post_id)})
        author_email =  pre_post['author_email']
        
        current_post_attendees_count = pre_post['current_post_attendees_count']
        # Update the post in the database
        updated_post = {
            'title': title,
            'content': content,
            'author_email' : author_email,
            'bobmate_cat': bobmate_cat,
            'food_cat': food_cat,
            'date': date,
            'time': time,
            'open_chat': open_chat,
            'max_People':max_People,
            'current_post_attendees_count': current_post_attendees_count
        }

        # Perform the update operation
        result = posts_collection.update_one(
            {'_id': ObjectId(post_id), 'author_email': email},
            {'$set': updated_post}
        )

        if result.modified_count == 1:
            return redirect(url_for('post_detail', post_id=post_id))
        else:
            return render_template('error.html', message='Unauthorized access or post not found')

    return redirect(url_for('get_posts'))  # Redirect to home if not a POST request

# 포스팅 삭제
@app.route('/post/<post_id>/delete', methods=['POST'])
def delete_post(post_id):
    if request.method == 'POST':
        email = session.get('email')

        # Ensure user is logged in
        if not email:
            return redirect(url_for('login'))

        # Check if the user is the author of the post
        post = posts_collection.find_one({'_id': ObjectId(post_id)})
        if not post or post['author_email'] != email:
            return render_template('error.html', message='Unauthorized access or post not found')

        # Perform the delete operation
        result = posts_collection.delete_one({'_id': ObjectId(post_id)})

        if result.deleted_count == 1:
            return redirect(url_for('get_posts'))
        else:
            return render_template('error.html', message='Error deleting post')

    return redirect(url_for('get_posts'))  # Redirect to home if not a POST request

# 사용자 참석 여부 업데이트
@app.route('/post/<post_id>/attend', methods=['POST'])
def update_attendance(post_id):
    email = session.get('email')
    print(email, post_id)
    if not email:
        return redirect(url_for('login'))

    user = users_collection.find_one({'email': email})
    if not user:
        return 'User not found', 404

    post = posts_collection.find_one({'_id': ObjectId(post_id)})
    if not post:
        return 'Post not found', 404
    
    users_collection.update_one({'_id': user['_id']}, {'$addToSet': {'attending_events': post_id}})
    posts_collection.update_one({'_id': post['_id']}, {'$addToSet': {'attendees': user['email']}})
    test = posts_collection.find_one({'_id': ObjectId(post_id)})
    print('test')
    return redirect(url_for('post_detail', post_id=post_id, user=user))


### TEST chat room redirect
@app.route('/chat')
def chat():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    room = request.args.get('room')
    username = session['email']
    return render_template('chat.html', room=room, username=username)


# WebSocket Chat Functionality
@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send(username + ' has entered the room.', to=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', to=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    send(data['message'], to=room)

def translate_food_cat(food_cat):
    if food_cat == 'chi':
        return '중식'
    elif food_cat == 'jap':
        return '일식'
    elif food_cat == 'kor':
        return '한식'
    elif food_cat == 'ame':
        return '양식'
    elif food_cat == 'all':
        return '전체'

def translate_bobmate_cat(bobmate_cat):
    if bobmate_cat == 'del':
        return '배달'
    elif bobmate_cat == 'shop':
        return '매장'
    elif bobmate_cat == 'all':
        return '전체'

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5002, debug=True)
