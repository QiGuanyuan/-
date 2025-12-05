import socketio
import time

sio = socketio.Client()

@sio.event
def connect():
    print("✅ 连接服务器成功")
    # 发送踢人请求
    sio.emit('kick_user', {'nickname': 'test_user_8fmrgs'})
    print(f"🔨 发送踢人请求: test_user_8fmrgs")
    time.sleep(1)
    sio.disconnect()

@sio.event
def disconnect():
    print("❌ 连接断开")

try:
    sio.connect('http://localhost:5000')
    sio.wait()
except Exception as e:
    print(f"连接失败: {e}")
