from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# 在线用户列表，格式：{session_id: {nickname, room}}
online_users = {}
# 已登录的昵称列表
nicknames = set()

# 加载配置文件
def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {"servers": [{"name": "本地服务器", "url": "http://127.0.0.1:5000"}]}

config = load_config()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    nickname = request.json.get('nickname')
    server_url = request.json.get('server_url')
    
    if not nickname:
        return jsonify({"status": "error", "message": "请输入昵称"})
    
    if nickname in nicknames:
        return jsonify({"status": "error", "message": "该昵称已被使用，请更换昵称"})
    
    return jsonify({"status": "success"})

@app.route('/chat')
def chat():
    nickname = request.args.get('nickname')
    if not nickname:
        return render_template('login.html')
    return render_template('chat.html', nickname=nickname)

@app.route('/config')
def get_config():
    return jsonify(config)

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@socketio.on('connect')
def handle_connect():
    print(f"新连接: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    if session_id in online_users:
        user_info = online_users[session_id]
        nickname = user_info['nickname']
        room = user_info['room']
        
        # 从在线用户列表和昵称集合中移除
        del online_users[session_id]
        nicknames.remove(nickname)
        
        # 广播用户离开消息
        emit('user_left', {"nickname": nickname}, room=room)
        # 更新在线用户列表
        emit('update_users', {"users": list(nicknames)}, room=room)
        
        print(f"用户离开: {nickname}")

@socketio.on('join')
def handle_join(data):
    session_id = request.sid
    nickname = data.get('nickname')
    room = data.get('room', 'default')
    
    if not nickname:
        return
    
    # 检查昵称是否已被使用
    if nickname in nicknames:
        emit('error', {"message": "该昵称已被使用，请更换昵称"})
        return
    
    # 加入房间
    join_room(room)
    
    # 存储用户信息
    online_users[session_id] = {"nickname": nickname, "room": room}
    nicknames.add(nickname)
    
    # 发送欢迎消息给新用户
    welcome_message = {"sender": "系统", "message": f"欢迎 {nickname} 加入聊天室！", "type": "system"}
    emit('welcome', welcome_message)
    
    # 广播用户加入消息给房间内其他用户
    emit('user_joined', {"nickname": nickname}, room=room, include_self=False)
    
    # 更新在线用户列表
    emit('update_users', {"users": list(nicknames)}, room=room)
    
    print(f"用户加入: {nickname}")

@socketio.on('send_message')
def handle_message(data):
    session_id = request.sid
    if session_id not in online_users:
        return
    
    user_info = online_users[session_id]
    sender = user_info['nickname']
    room = user_info['room']
    message = data.get('message', '')
    
    # 处理消息类型
    message_type = "text"
    # 检查是否是@指令
    if message.startswith('@'):
        parts = message.split(' ', 1)
        if len(parts) > 1:
            command = parts[0].lower()
            content = parts[1]
            
            if command == '@电影':
                message_type = "movie"
                message = content
            elif command == '@川小农':
                message_type = "ai"
                message = content
    
    # 发送消息给房间内所有用户
    emit('new_message', {
        "sender": sender,
        "message": message,
        "type": message_type,
        "timestamp": ""
    }, room=room)

@socketio.on('get_online_users')
def handle_get_users():
    session_id = request.sid
    if session_id in online_users:
        room = online_users[session_id]['room']
        emit('update_users', {"users": list(nicknames)})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)