from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_socketio import SocketIO, send
import json, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'zalo-secret-key'
socketio = SocketIO(app)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

USERS_FILE = 'users.json'
CHAT_LOG = []
message_history = []

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

@app.route('/')
def home():
    if 'username' in session:
        return redirect('/chat')
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return 'Tài khoản đã tồn tại!'
        users[username] = password
        save_users(users)
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']
        if users.get(username) == password:
            session['username'] = username
            return redirect('/chat')
        return 'Sai thông tin đăng nhập!'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect('/login')
    return render_template('index.html', username=session['username'])

# Gửi tin nhắn
@socketio.on('message')
def handle_msg(msg):
    CHAT_LOG.append(msg)
    send(msg, broadcast=True)

# API: Gửi tin nhắn trước đó
@app.route('/messages')
def get_messages():
    return jsonify(CHAT_LOG)
    
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    # Gửi toàn bộ lịch sử khi user mới kết nối
    for msg in message_history:
        send(msg)

@socketio.on('message')
def handle_message(msg):
    message_history.append(msg)
    send(msg, broadcast=True)


@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No filename'}), 400
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return jsonify({'url': f'/static/uploads/{filename}'})

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    socketio.run(app, host='0.0.0.0', port=12345)

