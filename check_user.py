import socketio
import time

sio = socketio.Client()
user_found = False

@sio.event
def connect():
    print("✅ 连接服务器成功")
    # 请求在线用户列表
    sio.emit('get_online_users')

@sio.event
def connect_error(data):
    print(f"❌ 连接失败: {data}")

@sio.event
def disconnect():
    print("❌ 连接断开")

@sio.event
def update_users(data):
    global user_found
    users = data['users']
    print(f"\n👥 当前在线用户列表: {users}")
    
    if 'test_user_8fmrgs' in users:
        print("\n⚠️  发现目标用户: test_user_8fmrgs 仍然在线")
        user_found = True
    else:
        print("\n✅ 目标用户: test_user_8fmrgs 已不在线")
        user_found = False
    
    # 断开连接
    time.sleep(1)
    sio.disconnect()

# 连接到服务器
try:
    print("🔄 正在连接服务器...")
    sio.connect('http://localhost:5000', wait_timeout=10)
    sio.wait()
    
    if not user_found:
        print("\n🎉 踢人功能成功！test_user_8fmrgs 已被踢出聊天室")
    else:
        print("\n❌ 踢人功能失败！test_user_8fmrgs 仍然在线")
        
except Exception as e:
    print(f"\n❌ 连接失败: {e}")
