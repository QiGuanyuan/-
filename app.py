#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能瞭望数据分析处理系统 - 主应用
"""

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from utils.baidu_spider import BaiduSpider
import pdfkit
import datetime
import logging

# 确保日志目录存在
os.makedirs('logs', exist_ok=True)

# 配置日志
print('开始配置日志...')
# 确保logs目录存在
if not os.path.exists('logs'):
    print('创建logs目录')
    os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    filename='logs/app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# 添加控制台日志
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
print('日志配置完成')

# 创建Flask应用
app = Flask(__name__)
app.secret_key = os.urandom(24)  # 用于会话加密

# 数据库配置
DB_PATH = 'data.db'

# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建数据仓库表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_warehouse (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT,
            url TEXT NOT NULL,
            content TEXT,
            keywords TEXT NOT NULL,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建管理员用户（如果不存在）
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', 'admin888'))
    
    conn.commit()
    conn.close()

# 数据库连接装饰器
def with_db_connection(func):
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        result = func(cursor, *args, **kwargs)
        conn.commit()
        conn.close()
        return result
    return wrapper

# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

# 登出功能
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 导入functools模块
import functools

# 检查登录状态的装饰器
def login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

# 首页/后台主页
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    print(f'请求方法: {request.method}')
    if request.method == 'POST':
        print('处理POST请求')
        try:
            keywords = request.form['keywords']
            pages = request.form.get('pages', 1, type=int)
            print(f'获取到关键词: {keywords}, 页数: {pages}')
            
            try:
                print(f'开始搜索关键词: {keywords}, 页数: {pages}')
                
                # 使用百度爬虫获取数据
                spider = None
                try:
                    print('创建BaiduSpider实例...')
                    spider = BaiduSpider()
                    print('创建BaiduSpider实例成功')
                    
                    print(f'开始爬取关键词: {keywords}')
                    results = spider.search(keywords, pages=pages)
                    print(f'爬取完成，获取到 {len(results)} 条结果')
                    
                    # 保存搜索结果到会话中
                    print(f'保存搜索结果到会话，共 {len(results)} 条')
                    session['search_results'] = results
                    session['current_keywords'] = keywords
                    print('搜索结果保存到会话成功')
                    
                finally:
                    if spider:
                        print('关闭BaiduSpider实例...')
                        spider.close()
                        print('BaiduSpider实例已关闭')
                
                print('渲染模板...')
                return render_template('index.html', results=results, keywords=keywords)
            except Exception as e:
                import traceback
                print(f'爬虫搜索失败: {str(e)}')
                print(f'错误堆栈: {traceback.format_exc()}')
                error_message = f'获取数据失败: {str(e)}'
                flash(error_message, 'error')
                logging.error(f'爬虫搜索失败: {str(e)}')
                logging.error(f'错误堆栈: {traceback.format_exc()}')
        except Exception as e:
            import traceback
            print(f'请求处理失败: {str(e)}')
            print(f'错误堆栈: {traceback.format_exc()}')
            flash(f'请求处理失败: {str(e)}', 'error')
    
    # 从会话中获取搜索结果
    results = session.get('search_results', [])
    keywords = session.get('current_keywords', '')
    print(f'处理GET请求，返回 {len(results)} 条结果')
    
    return render_template('index.html', results=results, keywords=keywords)

# 批量保存数据到数据库
@app.route('/save_data', methods=['POST'], endpoint='save_data')
@login_required
def save_data():
    selected_ids = request.form.getlist('selected_items')
    search_results = session.get('search_results', [])
    keywords = session.get('current_keywords', '')
    
    if not selected_ids:
        flash('请选择要保存的数据', 'error')
        return redirect(url_for('index'))
    
    try:
        # 将字符串ID转换为整数
        selected_indices = [int(id) for id in selected_ids]
        
        # 保存选中的数据到数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        saved_count = 0
        for idx in selected_indices:
            if idx < len(search_results):
                result = search_results[idx]
                cursor.execute('''
                    INSERT INTO data_warehouse (title, source, url, content, keywords)
                    VALUES (?, ?, ?, ?, ?)
                ''', (result['title'], result['source'], result['url'], result['content'], keywords))
                saved_count += 1
        
        conn.commit()
        conn.close()
        
        flash(f'成功保存 {saved_count} 条数据到数据仓库', 'success')
    except Exception as e:
        flash(f'保存数据失败: {str(e)}', 'error')
        logging.error(f'保存数据到仓库失败: {str(e)}')
    
    return redirect(url_for('index'))

# 数据仓库页面
@app.route('/data_warehouse', methods=['GET'], endpoint='data_warehouse')
@login_required
def data_warehouse():
    keywords = request.args.get('keywords', '')
    date = request.args.get('date', '')
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = 'SELECT * FROM data_warehouse WHERE 1=1'
    params = []
    
    if keywords:
        query += ' AND keywords LIKE ?'
        params.append(f'%{keywords}%')
    
    if date:
        query += ' AND DATE(crawled_at) = ?'
        params.append(date)
    
    query += ' ORDER BY crawled_at DESC'
    
    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()
    
    return render_template('data_warehouse.html', data=data, keywords=keywords, date=date)

# 生成PDF报告
@app.route('/generate_pdf', methods=['POST'], endpoint='generate_pdf')
@login_required
def generate_pdf():
    selected_ids = request.form.getlist('selected_data')
    
    if not selected_ids:
        flash('请选择要生成报告的数据', 'error')
        return redirect(url_for('data_warehouse'))
    
    try:
        selected_ids = [int(id) for id in selected_ids]
        
        # 从数据库获取选中的数据
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        placeholders = ','.join(['?'] * len(selected_ids))
        cursor.execute(f'SELECT * FROM data_warehouse WHERE id IN ({placeholders})', selected_ids)
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            flash('没有找到选中的数据', 'error')
            return redirect(url_for('data_warehouse'))
        
        # 生成HTML内容
        html_content = render_template('pdf_template.html', data=data)
        
        # 生成PDF文件名
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f'report_{timestamp}.pdf'
        pdf_path = os.path.join('static', 'reports', pdf_filename)
        
        # 确保reports目录存在
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        
        # 生成PDF
        pdfkit.from_string(html_content, pdf_path)
        
        flash('PDF报告生成成功', 'success')
        return redirect(url_for('data_warehouse', pdf=pdf_filename))
    except Exception as e:
        flash(f'生成PDF失败: {str(e)}', 'error')
        logging.error(f'生成PDF报告失败: {str(e)}')
        return redirect(url_for('data_warehouse'))

# 初始化应用
if __name__ == '__main__':
    print("正在初始化应用...")
    logging.info("应用启动开始")
    try:
        init_db()
        logging.info("数据库初始化完成")
        print("正在启动Flask服务器...")
        logging.info("Flask服务器启动中")
        app.run(debug=True, host='127.0.0.1', port=5000)
    except Exception as e:
        print(f"应用启动失败: {str(e)}")
        logging.error(f"应用启动失败: {str(e)}", exc_info=True)
