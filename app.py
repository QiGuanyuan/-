from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os
import sqlite3
import time
import requests
import re
from openai import OpenAI
from weather.weather_service import get_weather
import threading

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# 新闻API配置
NEWS_API_URL = 'https://api.qqsuu.cn/api/dm-it'
NEWS_API_KEY = '11b43765ab3125e3e070462a1c46532c'  # API密钥

# 实现get_news函数
def get_news(keyword=None):
    """获取新闻数据"""
    try:
        print(f"📰 开始获取新闻，关键词: {keyword}")
        params = {
            'num': 10,  # 请求10条新闻，然后过滤最多返回5条
            'key': NEWS_API_KEY
        }
        
        if keyword:
            params['word'] = keyword
        
        print(f"📤 发送新闻API请求: {NEWS_API_URL}, 参数: {params}")
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        response.raise_for_status()  # 检查HTTP错误
        
        data = response.json()
        print(f"📥 新闻API响应: {data}")
        
        # 构建标准化的新闻数据结构
        news_list = []
        
        # 检查响应格式 - 适应实际的API响应结构
        if data.get('code') == 200:
            # 获取新闻数据
            news_data = None
            
            # 分析响应结构
            print(f"响应结构分析:")
            print(f"- code: {data.get('code')}")
            print(f"- 包含data字段: {'data' in data}")
            
            if 'data' in data:
                main_data = data['data']
                print(f"- data类型: {type(main_data)}")
                
                if isinstance(main_data, dict):
                    # 检查data.data.list结构
                    if 'data' in main_data and isinstance(main_data['data'], dict):
                        if 'list' in main_data['data']:
                            news_data = main_data['data']['list']
                            print(f"- 发现data.data.list结构，包含{len(news_data)}条新闻")
                        elif 'newslist' in main_data['data']:
                            news_data = main_data['data']['newslist']
                            print(f"- 发现data.data.newslist结构，包含{len(news_data)}条新闻")
                    # 检查data.list结构
                    elif 'list' in main_data:
                        news_data = main_data['list']
                        print(f"- 发现data.list结构，包含{len(news_data)}条新闻")
                    # 检查data.newslist结构
                    elif 'newslist' in main_data:
                        news_data = main_data['newslist']
                        print(f"- 发现data.newslist结构，包含{len(news_data)}条新闻")
                    else:
                        print(f"- data字典中不包含list或newslist字段，键列表: {list(main_data.keys())}")
                
                elif isinstance(main_data, list):
                    news_data = main_data
                    print(f"- data直接是列表，包含{len(news_data)}条新闻")
            else:
                print(f"- 不包含data字段，检查result字段")
                # 检查原始result.list结构
                if 'result' in data and isinstance(data['result'], dict):
                    if 'list' in data['result']:
                        news_data = data['result']['list']
                        print(f"- 发现result.list结构，包含{len(news_data)}条新闻")
                    elif 'newslist' in data['result']:
                        news_data = data['result']['newslist']
                        print(f"- 发现result.newslist结构，包含{len(news_data)}条新闻")
                # 检查result直接是列表的结构
                elif 'result' in data and isinstance(data['result'], list):
                    news_data = data['result']
                    print(f"- result直接是列表，包含{len(news_data)}条新闻")
            
            if news_data:
                # 最多返回5条新闻
                for item in news_data[:5]:
                    news_item = {
                        'title': item.get('title', '无标题'),
                        'description': item.get('description', ''),
                        'url': item.get('url', ''),
                        'image': item.get('picUrl', ''),
                        'source': item.get('source', '未知来源'),
                        'time': item.get('ctime', '')
                    }
                    news_list.append(news_item)
            
        print(f"✅ 新闻获取完成，共 {len(news_list)} 条")
        return {
            'type': 'list',
            'data': news_list
        }
        
    except requests.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
    except Exception as e:
        print(f"❌ 新闻获取失败: {e}")
    
    # 返回空列表表示获取失败
    return {
        'type': 'list',
        'data': []
    }

# 初始化SQLite数据库
def init_db():
    """初始化数据库并添加管理员权限字段"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # 创建用户表，添加管理员权限字段
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        admin INTEGER DEFAULT 0
    )
    ''')
    
    # 检查是否需要添加管理员字段（如果表已存在）
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'admin' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN admin INTEGER DEFAULT 0")
    
    # 设置默认管理员账号：admin / admin
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    admin_user = cursor.fetchone()
    if not admin_user:
        cursor.execute("INSERT INTO users (username, password, admin) VALUES (?, ?, ?)", ('admin', 'admin', 1))
    
    conn.commit()
    conn.close()

# 调用数据库初始化函数
init_db()

# 配置OpenAI客户端
client = OpenAI(
    api_key="sk-qfrzyjqdudifwtzqqfrpilargwrglufqvzlxznpbnnoetckk",
    base_url="https://api.siliconflow.cn/v1/"  # 修正了URL中的ν为v
)
MODEL_NAME = "qwen/qwen2.5-7b-instruct"  # 更新为正确的模型名称格式

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


def build_weather_html(weather_data):
    """
    构建天气信息的HTML内容
    :param weather_data: 天气API返回的JSON数据
    :return: HTML字符串
    """
    try:
        data = weather_data.get('data', {})
        city = data.get('city', '未知城市')
        weather_list = data.get('data', [])
        
        # 构建HTML模板
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{city} 天气</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    background-color: #f0f2f5;
                    margin: 0;
                }
                .weather-card {
                    background-color: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    max-width: 360px;
                }
                h2 {
                    margin-top: 0;
                    color: #333;
                    text-align: center;
                }
                .weather-info {
                    margin-bottom: 20px;
                }
                .current-weather {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .temp {
                    font-size: 48px;
                    font-weight: bold;
                    color: #1890ff;
                    margin: 10px 0;
                }
                .weather-desc {
                    font-size: 20px;
                    color: #666;
                }
                .forecast {
                    border-top: 1px solid #eee;
                    padding-top: 20px;
                }
                .forecast-item {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 10px;
                    padding: 10px;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                }
                .forecast-time {
                    font-weight: bold;
                    color: #333;
                }
                .forecast-details {
                    text-align: right;
                }
                .forecast-temp {
                    font-size: 16px;
                    color: #1890ff;
                }
                .forecast-desc {
                    font-size: 14px;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="weather-card">
                <h2>{city} 天气</h2>
                
                {build_current_weather(weather_list[0]) if weather_list else ''}
                
                <div class="forecast">
                    <h3>未来天气预报</h3>
                    {build_forecast_html(weather_list)}
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    except Exception as e:
        print(f"构建天气HTML失败: {e}")
        return "<h3>天气信息加载失败</h3>"


def build_current_weather(current_data):
    """
    构建当前天气信息的HTML
    :param current_data: 当前天气数据
    :return: HTML字符串
    """
    if not current_data:
        return ""
    
    temp = current_data.get('temperature', '未知')
    weather = current_data.get('weather', '未知')
    humidity = current_data.get('humidity', '未知')
    wind_dir = current_data.get('wind_dir', '未知')
    wind_speed = current_data.get('wind_speed', '未知')
    
    return f"""
    <div class="current-weather">
        <div class="temp">{temp}°C</div>
        <div class="weather-desc">{weather}</div>
        <div class="weather-info">
            <p>湿度: {humidity}</p>
            <p>风向: {wind_dir}</p>
            <p>风速: {wind_speed}</p>
        </div>
    </div>
    """


def build_forecast_html(weather_list):
    """
    构建天气预报的HTML
    :param weather_list: 天气预报数据列表
    :return: HTML字符串
    """
    if not weather_list:
        return "<p>暂无预报数据</p>"
    
    html = ""
    for item in weather_list[:6]:  # 只显示未来6个时间点的预报
        time = item.get('time', '未知')
        temp = item.get('temperature', '未知')
        weather = item.get('weather', '未知')
        
        html += f"""
        <div class="forecast-item">
            <div class="forecast-time">{time}</div>
            <div class="forecast-details">
                <div class="forecast-temp">{temp}°C</div>
                <div class="forecast-desc">{weather}</div>
            </div>
        </div>
        """
    
    return html

config = load_config()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    
    if not username or not password:
        return jsonify({"status": "error", "message": "请输入用户名和密码"})
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # 检查用户名是否已存在
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        conn.close()
        return jsonify({"status": "error", "message": "该用户名已被注册，请更换用户名"})
    
    # 插入新用户，默认不是管理员
    cursor.execute("INSERT INTO users (username, password, admin) VALUES (?, ?, ?)", (username, password, 0))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": "注册成功"})

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    server_url = request.json.get('server_url')
    
    if not username or not password:
        return jsonify({"status": "error", "message": "请输入用户名和密码"})
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # 验证用户名和密码，并获取管理员权限
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    conn.close()
    
    if not user:
        return jsonify({"status": "error", "message": "用户名不存在"})
    
    if user[1] != password:
        return jsonify({"status": "error", "message": "密码错误"})
    
    if username in nicknames:
        return jsonify({"status": "error", "message": "该用户已登录，请更换用户名"})
    
    # 设置会话信息
    session['username'] = username
    session['admin'] = user[2] if len(user) > 2 else 0
    
    return jsonify({"status": "success", "username": username, "admin": session['admin']})

@app.route('/chat')
def chat():
    # 检查用户是否已登录
    if 'username' not in session:
        return redirect(url_for('index'))
    
    username = session['username']
    admin = session['admin']
    return render_template('chat.html', nickname=username, admin=admin)

@app.route('/config')
def get_config():
    return jsonify(config)

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/logout')
def logout():
    """退出登录，清除会话信息"""
    session.pop('username', None)
    session.pop('admin', None)
    return redirect(url_for('index'))

@socketio.on('connect')
def handle_connect():
    print(f"新连接: {request.sid}")
    # 检查用户是否已登录
    if 'username' not in session:
        print("未登录用户尝试连接，断开连接")
        socketio.disconnect(request.sid)
        return

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
    nickname = data.get('username')  # 使用nickname变量
    room = data.get('room', 'default')
    
    if not nickname:
        return
    
    # 检查用户名是否已被使用
    if nickname in nicknames:
        emit('error', {"message": "该用户已登录，请更换用户名"})
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
@socketio.on('message')  # 同时支持旧版'message'事件
def handle_message(data):
    session_id = request.sid
    if session_id not in online_users:
        return
    
    user_info = online_users[session_id]
    sender = user_info['nickname']
    room = user_info['room']
    original_message = data.get('message', '')
    message = original_message
    
    # 处理消息类型
    message_type = "text"
    ai_content = None  # 用于存储AI回复内容
    weather_city = None  # 用于存储天气查询的城市
    
    # 检查是否是@指令
    if message.startswith('@'):
        parts = message.split(' ', 1)
        if len(parts) > 1:
            command = parts[0].lower()
            content = parts[1]
            
            if command == '@电影':
                message_type = "movie"
                message = content
                movie_name = content.strip()
            elif command == '@川小农':
                message_type = "ai"
                message = content  # 保留原始问题以便显示在聊天记录中
                ai_content = content  # 存储AI需要处理的内容
            elif command == '@天气':
                message_type = "weather"
                message = content  # 保留城市名称
                weather_city = content.strip()
            elif command == '@新闻':
                message_type = "news"
                message = content  # 保留关键词
                # 使用正则表达式提取可选的关键词
                match = re.match(r'^@新闻\s*(.*)', content)
                news_keyword = match.group(1).strip() if match else ''
            elif command == '@音乐':
                message_type = "music"
                message = content  # 保留音乐名称
                music_name = content.strip()
    
    # 先发送用户的原始消息
    emit('new_message', {
        "sender": sender,
        "message": message,
        "type": message_type,
        "timestamp": ""
    }, room=room)
    
    # 如果是@天气指令，直接调用天气API获取回复
    if weather_city:
        try:
            print(f"🔄 开始获取天气: {weather_city}")
            weather_result = get_weather(weather_city)
            print(f"📦 天气数据获取成功: {weather_result}")
            if weather_result and weather_result.get('code') == 200:
                # 直接使用天气服务返回的HTML内容
                weather_html = weather_result['content']
                emit('new_message', {
                    "sender": "系统",
                    "message": weather_html,
                    "type": "weather_card",
                    "timestamp": ""
                }, room=room)
                print(f"✅ 天气卡片发送完成到房间: {room}")
            else:
                error_message = f"无法获取{weather_city}的天气信息，请检查城市名称是否正确"
                emit('new_message', {
                    "sender": "系统",
                    "message": error_message,
                    "type": "system",
                    "timestamp": ""
                }, room=room)
                print(f"❌ 天气数据获取失败: {weather_result}")
        except Exception as e:
            error_message = f"获取天气信息出错: {str(e)}"
            emit('new_message', {
                "sender": "系统",
                "message": error_message,
                "type": "system",
                "timestamp": ""
            }, room=room)
            print(f"❌ 天气查询执行错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 如果是@新闻指令，异步获取新闻
    if 'news_keyword' in locals():
        # 发送'news_fetching'事件通知前端
        emit('news_fetching', room=room)
        
        # 使用Flask-SocketIO提供的start_background_task函数处理异步任务
        # 这是处理Flask-SocketIO异步任务的正确方式
        def fetch_news_async(keyword, user_room):
            try:
                print(f"🔄 开始获取新闻: {keyword}")
                news_result = get_news(keyword)
                print(f"📦 新闻数据获取成功: {news_result}")
                
                # 发送'news_results'事件给前端
                socketio.emit('news_results', {
                    "news": news_result
                }, room=user_room)
                print(f"✅ 新闻列表发送完成到房间: {user_room}")
            except Exception as e:
                error_message = f"获取新闻出错: {str(e)}"
                socketio.emit('new_message', {
                    "sender": "系统",
                    "message": error_message,
                    "type": "system",
                    "timestamp": ""
                }, room=user_room)
                print(f"❌ 新闻查询执行错误: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 启动异步任务获取新闻
        socketio.start_background_task(fetch_news_async, news_keyword, room)

    # 如果是@音乐指令，异步获取音乐信息
    if 'music_name' in locals():
        # 使用Flask-SocketIO提供的start_background_task函数处理异步任务
        socketio.start_background_task(fetch_music_async, music_name, room)

# 音乐代理路由
@app.route('/proxy_music/<music_id>')
def proxy_music(music_id):
    """代理音乐文件的路由"""
    try:
        API_KEY = '892e90f7e474bebe0ae8d24750536cf7'
        url = f'https://api.oick.cn/api/wyy?id={music_id}&apikey={API_KEY}'
        
        # 发送请求获取音乐文件
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # 设置响应头
        headers = {
            'Content-Type': response.headers.get('Content-Type', 'audio/mpeg'),
            'Content-Length': response.headers.get('Content-Length'),
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'public, max-age=31536000'
        }
        
        # 流式返回音乐文件
        return app.response_class(
            response.iter_content(chunk_size=8192),
            status=response.status_code,
            headers=headers
        )
    except Exception as e:
        print(f"音乐代理失败: {str(e)}")
        return "音乐代理失败", 500


def fetch_music_async(music_name, user_room):
    try:
        print(f"🎵 开始获取音乐: {music_name}")
        API_KEY = '892e90f7e474bebe0ae8d24750536cf7'
        
        # 预设的音乐ID映射（根据API测试，此API只支持通过ID获取音乐）
        music_id_map = {
            '遗失的心跳': '1966155051'  # 仅保留测试成功的歌曲
        }
        
        # 获取对应的音乐ID
        music_id = music_id_map.get(music_name)
        if not music_id:
            print(f"❌ 未找到预设的音乐ID: {music_name}")
            socketio.emit('new_message', {
                "sender": "系统",
                "message": f'暂不支持该歌曲: {music_name}。目前支持: {list(music_id_map.keys())}',
                "type": "system",
                "timestamp": ""
            }, room=user_room)
            return
        
        # 构建API请求URL
        api_url = f'https://api.oick.cn/api/wyy?id={music_id}&apikey={API_KEY}'
        print(f"📤 发送音乐API请求: {api_url}")
        
        # 发送请求验证音乐文件
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()  # 检查HTTP错误
        
        # 验证是否是音乐文件（通过Content-Type判断）
        content_type = response.headers.get('Content-Type')
        if content_type and ('audio' in content_type or 'mpeg' in content_type):
            print(f"✅ 获取到音乐文件: {content_type}")
            
            # 使用我们自己的代理路由作为音乐URL
            proxy_url = f'/proxy_music/{music_id}'
            
            # 构建音乐信息
            music_data = {
                'song': music_name,
                'singer': '萧亚轩',  # 预设的歌手信息
                'url': proxy_url,  # 使用代理URL
                'pic': 'https://p2.music.126.net/0I39qE1F3y4Wv7xHqXZ-9g==/109951165361012948.jpg'  # 预设的图片URL
            }
            
            # 发送音乐信息到聊天室
            socketio.emit('new_message', {
                "sender": "系统",
                "type": "music_player",
                "message": music_data,
                "timestamp": ""
            }, room=user_room)
            print(f"✅ 音乐信息已发送到房间: {user_room}")
        else:
            print(f"❌ 获取的不是音乐文件，内容类型: {content_type}")
            socketio.emit('new_message', {
                "sender": "系统",
                "type": "system",
                "message": f'音乐获取失败: 未获取到有效的音乐文件',
                "timestamp": ""
            }, room=user_room)
    except Exception as e:
        print(f"❌ 音乐处理异常: {str(e)}")
        socketio.emit('new_message', {
            "sender": "系统",
            "type": "system",
            "message": f'音乐处理异常: {str(e)}',
            "timestamp": ""
        }, room=user_room)

    # 如果是@川小农指令，直接调用AI模型获取回复
    if ai_content:
        try:
            print(f"🔄 开始获取AI回复: {ai_content}")
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "你是川小农，一个智能聊天机器人，用中文回复用户的问题。"},
                    {"role": "user", "content": ai_content}
                ],
                timeout=10  # 设置10秒超时
            )
            ai_response = response.choices[0].message.content
            print(f"📦 AI回复获取成功: {ai_response}")
            # 发送AI回复消息
            emit('new_message', {
                "sender": "川小农",
                "message": ai_response,
                "type": "ai",
                "timestamp": ""
            }, room=room)
        except Exception as e:
            error_message = f"AI回复出错: {str(e)}"
            print(f"❌ AI回复出错: {str(e)}")
            emit('new_message', {
                "sender": "系统",
                "message": error_message,
                "type": "system",
                "timestamp": ""
            }, room=room)

@socketio.on('get_online_users')
def handle_get_users():
    session_id = request.sid
    if session_id in online_users:
        room = online_users[session_id]['room']
        emit('update_users', {"users": list(nicknames)})

@socketio.on('kick_user')
def handle_kick_user(data):
    """强制断开特定用户连接"""
    # 检查当前用户是否为管理员
    if 'username' not in session or session['admin'] != 1:
        print("❌ 非管理员用户尝试执行踢人操作")
        return
    
    admin_username = session['username']
    print(f"📥 管理员 {admin_username} 收到踢人请求: {data}")
    target_nickname = data.get('nickname')
    if not target_nickname:
        print("⚠️  踢人请求缺少目标昵称")
        return
    
    # 禁止管理员踢自己
    if target_nickname == admin_username:
        print("❌ 管理员不能踢自己")
        return
    
    print(f"🔍 查找用户: {target_nickname}")
    print(f"📋 当前在线用户列表: {online_users}")
    
    # 查找目标用户的session_id
    target_sid = None
    user_room = None
    for sid, user_info in online_users.items():
        print(f"🔄 检查用户: {sid} -> {user_info}")
        if user_info['nickname'] == target_nickname:
            target_sid = sid
            user_room = user_info['room']
            break
    
    if target_sid:
        print(f"✅ 找到目标用户 {target_nickname}，session_id: {target_sid}，房间: {user_room}")
        
        # 向被踢用户发送消息
        socketio.emit('error', {'message': '您已被管理员踢出聊天室'}, room=target_sid)
        
        # 向所有用户发送系统消息
        kick_message = f"管理员 {admin_username} 将用户 {target_nickname} 踢出了聊天室"
        socketio.emit('system_message', {'message': kick_message}, room=user_room)
        
        try:
            # 强制断开连接
            print(f"🔨 执行断开连接操作")
            socketio.disconnect(target_sid)
            print(f"✅ 强制断开用户连接成功: {target_nickname}")
            
            # 记录踢人日志
            print(f"📝 踢人日志: {kick_message}")
        except Exception as e:
            print(f"❌ 断开连接失败: {e}")
            # 尝试另一种方法 - 直接从在线用户列表中移除
            if target_sid in online_users:
                user_nickname = online_users[target_sid]['nickname']
                del online_users[target_sid]
                if user_nickname in nicknames:
                    nicknames.remove(user_nickname)
                print(f"🔄 直接从在线列表中移除用户: {user_nickname}")
                # 更新用户列表
                update_users_list(user_room)
                
                # 记录踢人日志
                print(f"📝 踢人日志: {kick_message}")
    else:
        print(f"❌ 未找到目标用户: {target_nickname}")

@app.route('/check_online_users')
def check_online_users():
    """检查在线用户列表的HTTP端点"""
    users = [user['nickname'] for user in online_users.values()]
    return jsonify({'users': users})

@app.route('/about')
def about():
    """程序介绍页面"""
    return render_template('about.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)