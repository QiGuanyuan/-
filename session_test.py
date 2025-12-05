import requests
import json

# 创建session对象
session = requests.Session()

# 测试服务器是否响应
print('测试服务器响应...')
try:
    response = session.get('http://localhost:5000/')
    print(f'GET请求状态码: {response.status_code}')
    print(f'GET请求内容: {response.text[:500]}...')
    print(f'当前cookie: {session.cookies}')
except Exception as e:
    print(f'GET请求失败: {str(e)}')
    import traceback
    traceback.print_exc()

# 测试登录
print('\n测试登录...')
try:
    login_data = {'username': 'admin', 'password': 'admin888'}
    response = session.post('http://localhost:5000/login', data=login_data, allow_redirects=True)
    print(f'登录请求状态码: {response.status_code}')
    print(f'登录请求历史: {[resp.status_code for resp in response.history]}')
    print(f'登录请求最终URL: {response.url}')
    print(f'登录后cookie: {session.cookies}')
    print(f'登录请求内容: {response.text[:500]}...')
    
    # 测试搜索
    print('\n测试搜索...')
    search_data = {'keywords': '人工智能', 'pages': 1}
    response = session.post('http://localhost:5000/', data=search_data)
    print(f'搜索请求状态码: {response.status_code}')
    print(f'搜索请求内容: {response.text[:1000]}...')
    
    # 检查是否有错误信息
    if '获取数据失败' in response.text:
        print('\n搜索失败，页面中包含错误信息')
    
    if response.status_code == 500:
        print('\n搜索请求返回500错误，请查看服务器日志获取详细信息')
    
except Exception as e:
    print(f'测试失败: {str(e)}')
    import traceback
    traceback.print_exc()