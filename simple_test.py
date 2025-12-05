import requests
import json

# 测试服务器是否响应
print('测试服务器响应...')
try:
    response = requests.get('http://localhost:5000/')
    print(f'GET请求状态码: {response.status_code}')
    print(f'GET请求内容: {response.text[:500]}...')
except Exception as e:
    print(f'GET请求失败: {str(e)}')

# 测试登录
print('\n测试登录...')
try:
    login_data = {'username': 'admin', 'password': 'admin888'}
    # 允许重定向
    response = requests.post('http://localhost:5000/login', data=login_data, allow_redirects=True)
    print(f'登录请求状态码: {response.status_code}')
    print(f'登录请求历史: {[resp.status_code for resp in response.history]}')
    print(f'登录请求最终URL: {response.url}')
    
    # 获取会话cookie
    cookies = response.cookies
    print(f'获取到的cookies: {cookies}')
    
    # 测试搜索
    print('\n测试搜索...')
    search_data = {'keywords': '人工智能', 'pages': 1}
    response = requests.post('http://localhost:5000/', data=search_data, cookies=cookies)
    print(f'搜索请求状态码: {response.status_code}')
    print(f'搜索请求内容: {response.text[:1000]}...')
    
except Exception as e:
    print(f'测试失败: {str(e)}')
    import traceback
    traceback.print_exc()