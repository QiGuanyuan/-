import socketio
import time

sio = socketio.Client()
online_users_list = []

@sio.event
def connect():
    print("✅ 连接服务器成功")
    # 先加入聊天室获取在线用户列表
    sio.emit('join', {'username': 'admin_checker', 'room': 'default'})
    time.sleep(1)
    
@sio.event
def welcome(data):
    print(f"📢 系统消息: {data['message']}")
    # 请求在线用户列表
    sio.emit('get_online_users')
    time.sleep(1)

@sio.event
def update_users(data):
    global online_users_list
    online_users_list = data['users']
    print(f"📋 当前在线用户: {online_users_list}")
    
    # 检查test_user_8fmrgs是否在线
    if 'test_user_8fmrgs' in online_users_list:
        print(f"⚠️  发现目标用户: test_user_8fmrgs")
        # 发送踢人请求
        sio.emit('kick_user', {'nickname': 'test_user_8fmrgs'})
        print(f"🔨 发送踢人请求: test_user_8fmrgs")
        time.sleep(2)
    else:
        print(f"✅ test_user_8fmrgs 不在在线用户列表中")
    
    # 离开聊天室并断开连接
    sio.disconnect()

@sio.event
def user_joined(data):
    print(f"👋 用户加入: {data['nickname']}")

@sio.event
def user_left(data):
    print(f"👋 用户离开: {data['nickname']}")

@sio.event
def disconnect():
    print("❌ 连接断开")

try:
    sio.connect('http://localhost:5000')
    sio.wait()
except Exception as e:
    print(f"连接失败: {e}")
