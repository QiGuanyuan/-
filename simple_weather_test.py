import socketio
import time

# 创建socketio客户端
sio = socketio.Client()

# 记录是否收到天气卡片
received_weather_card = False

@sio.event
def connect():
    print("已连接到服务器")
    # 连接后立即加入房间
    sio.emit('join', {'username': 'test_user', 'room': 'default'})
    print("已发送join事件，加入默认房间")

@sio.event
def new_message(data):
    global received_weather_card
    print(f"收到消息: {data}")
    if data['type'] == 'weather_card':
        received_weather_card = True
        print("收到天气卡片！")
        # 收到天气卡片后断开连接
        sio.disconnect()

@sio.event
def disconnect():
    print("与服务器断开连接")

# 连接服务器
sio.connect('http://127.0.0.1:5000')

# 加入房间后，发送天气查询
time.sleep(1)  # 给服务器一些时间处理join事件
sio.emit('send_message', {'message': '@天气 北京'})
print("已发送天气查询")

# 等待事件，最多等待30秒
start_time = time.time()
timeout = 30
while not received_weather_card and time.time() - start_time < timeout:
    time.sleep(0.1)

if received_weather_card:
    print("测试成功: 收到了天气卡片！")
else:
    print("测试失败: 超时未收到天气卡片！")
    sio.disconnect()
