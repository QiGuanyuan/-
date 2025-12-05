import socketio
import time

# 创建 Socket.IO 客户端
sio = socketio.Client()

# 连接事件处理
@sio.event
def connect():
    print('✅ 连接服务器成功')
    
    # 发送踢人请求，踢掉多余的在线用户
    print('🔨 发送踢人请求...')
    sio.emit('kick_user', {'nickname': '211'})
    time.sleep(1)
    sio.emit('kick_user', {'nickname': 'test_user_b8ykt5'})
    
    # 断开连接
    print('🔌 断开连接')
    sio.disconnect()

# 错误事件处理
@sio.event
def error(data):
    print(f'❌ 发生错误: {data}')

# 连接到服务器
print('🔄 正在连接到服务器...')

try:
    sio.connect('http://127.0.0.1:5000')
    # 运行事件循环
    sio.wait()
except Exception as e:
    print(f'❌ 连接失败: {e}')
