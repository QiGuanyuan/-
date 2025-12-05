import requests
import json

# 直接向服务器请求在线用户列表
try:
    # 使用长轮询方式获取在线用户列表
    response = requests.post('http://localhost:5000/socket.io/?EIO=4&transport=polling', 
                            data='2["get_online_users"]',
                            headers={'Content-Type': 'text/plain'})
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    # 解析响应内容
    if response.text.startswith('0'):
        # 连接响应
        print("这是连接响应，需要先建立连接")
        
        # 建立连接
        session_response = requests.get('http://localhost:5000/socket.io/?EIO=4&transport=polling')
        session_data = session_response.text
        print(f"会话响应: {session_data}")
        
        # 提取sid
        if session_data.startswith('9'):
            import re
            sid_match = re.search(r'sid":"([^"]+)"', session_data)
            if sid_match:
                sid = sid_match.group(1)
                print(f"获取到sid: {sid}")
                
                # 发送连接确认
                connect_response = requests.post(f'http://localhost:5000/socket.io/?EIO=4&transport=polling&sid={sid}', 
                                              data='40',
                                              headers={'Content-Type': 'text/plain'})
                print(f"连接确认响应: {connect_response.text}")
                
                # 请求在线用户列表
                users_response = requests.post(f'http://localhost:5000/socket.io/?EIO=4&transport=polling&sid={sid}', 
                                             data='2["get_online_users"]',
                                             headers={'Content-Type': 'text/plain'})
                print(f"在线用户响应: {users_response.text}")
                
                # 解析在线用户列表
                if users_response.text.startswith('42'):
                    # 提取JSON数据
                    json_data = users_response.text[2:]
                    data = json.loads(json_data)
                    if len(data) >= 2 and data[0] == 'update_users':
                        users = data[1]['users']
                        print(f"\n👥 当前在线用户列表: {users}")
                        
                        if 'test_user_8fmrgs' in users:
                            print("\n⚠️  发现目标用户: test_user_8fmrgs 仍然在线")
                        else:
                            print("\n✅ 目标用户: test_user_8fmrgs 已不在线")
                            print("🎉 踢人功能成功！test_user_8fmrgs 已被踢出聊天室")
    
    print("\n测试完成")
    
except Exception as e:
    print(f"❌ 请求失败: {e}")
