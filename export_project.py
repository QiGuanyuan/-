#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目导出工具
用于将We唠嗑聊天室项目打包为zip文件
"""

import os
import zipfile
import datetime

def export_project():
    """
    导出项目文件到zip归档
    """
    # 项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 定义需要包含的文件和目录
    include_patterns = [
        'app.py',
        'config.json',
        'requirements.txt',
        'export_project.py',
        'static/',
        'templates/'
    ]
    
    # 使用桌面作为导出目录
    # 获取桌面路径
    if os.name == 'nt':  # Windows系统
        export_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
    else:  # Linux/Mac系统
        export_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
    
    # 生成zip文件名（包含时间戳）
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f'we_chat_room_{timestamp}.zip'
    zip_filepath = os.path.join(export_dir, zip_filename)
    
    try:
        # 创建zip文件
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 遍历需要包含的文件和目录
            for pattern in include_patterns:
                pattern_path = os.path.join(project_root, pattern)
                
                if os.path.isfile(pattern_path):
                    # 如果是文件，直接添加
                    zipf.write(pattern_path, os.path.relpath(pattern_path, project_root))
                    print(f'添加文件: {pattern}')
                elif os.path.isdir(pattern_path):
                    # 如果是目录，递归添加所有文件
                    for root, _, files in os.walk(pattern_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # 计算相对路径作为zip中的路径
                            zip_path = os.path.relpath(file_path, project_root)
                            zipf.write(file_path, zip_path)
                            print(f'添加文件: {zip_path}')
        
        print(f'\n项目导出成功!')
        print(f'导出文件: {zip_filepath}')
        print(f'导出大小: {os.path.getsize(zip_filepath) / 1024:.2f} KB')
        
        return zip_filepath
        
    except Exception as e:
        print(f'导出失败: {e}')
        return None

if __name__ == '__main__':
    print('=== We唠嗑聊天室 - 项目导出工具 ===')
    print('正在导出项目文件...')
    export_project()
    print('\n导出完成!')
