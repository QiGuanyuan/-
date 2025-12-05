import socketio
import time
import json

sio = socketio.Client(logger=True, engineio_logger=True)
online_users = []
user_joined = False

@sio.event
def connect():
    print("\n✅ 连接服务器成功")
    print(f"连接ID: {sio.sid}")

@sio.event
def connect_error(data):
    print(f"\n❌ 连接失败: {data}")

@sio.event
def disconnect():
    print("\n❌ 连接断开")

@sio.event
def welcome(data):
    global user_joined
    user_joined = True
    print(f"\n📢 系统欢迎消息: {data['message']}")
    # 请求在线用户列表
    print("📋 请求在线用户列表...")
    sio.emit('get_online_users')

@sio.event
def update_users(data):
    global online_users
    online_users = data['users']
    print(f"\n👥 当前在线用户列表: {online_users}")
    
    # 检查目标用户是否在线
    if 'test_user_8fmrgs' in online_users:
        print("\n⚠️  发现目标用户: test_user_8fmrgs")
        print("🔨 准备发送踢人请求...")
        
        # 发送踢人请求
        try:
            sio.emit('kick_user', {'nickname': 'test_user_8fmrgs'})
            print("✅ 踢人请求发送成功")
            
            # 等待2秒后再次检查在线用户列表
            time.sleep(2)
            print("\n🔄 再次请求在线用户列表...")
            sio.emit('get_online_users')
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ 发送踢人请求失败: {e}")
    else:
        print("\n✅ 目标用户test_user_8fmrgs不在在线列表中")
    
    # 断开连接
    time.sleep(1)
    sio.disconnect()

@sio.event
def error(data):
    print(f"\n❌ 错误消息: {data['message']}")

# 处理所有其他事件
def handle_all_events(event, data):
    print(f"\n📡 收到事件: {event}")
    if data:
        print(f"📦 事件数据: {data}")

# 注册所有事件的处理函数
sio.on('*', handle_all_events)

# 连接到服务器
try:
    print("🔄 正在连接服务器...")
    sio.connect('http://localhost:5000', wait_timeout=10)
    
    # 加入聊天室
    print("\n👋 正在加入聊天室...")
    sio.emit('join', {'username': 'debug_admin', 'room': 'default'})
    
    # 等待连接建立和事件处理
    sio.wait()
    
except Exception as e:
    print(f"\n❌ 连接失败: {e}")
