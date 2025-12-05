#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度爬虫模块
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import logging
import urllib.parse

# 配置日志
logging.basicConfig(
    filename='logs/spider.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BaiduSpider:
    """百度搜索爬虫类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'cache-control': 'max-age=0',
            'connection': 'keep-alive',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
            'upgrade-insecure-requests': '1'
        }
        self.initialized = False
    
    def _initialize(self):
        """初始化会话，访问百度首页获取必要的Cookie"""
        if not self.initialized:
            try:
                response = self.session.get('https://www.baidu.com', headers=self.headers, timeout=10)
                if response.status_code == 200:
                    self.initialized = True
                    logging.info('百度爬虫会话初始化成功')
                else:
                    logging.warning(f'百度爬虫会话初始化失败，状态码: {response.status_code}')
            except Exception as e:
                logging.error(f'百度爬虫会话初始化错误: {str(e)}')
                raise
    
    def search(self, keywords, pages=1):
        """
        执行百度搜索
        
        参数:
            keywords: 搜索关键词
            pages: 爬取的页数
            
        返回:
            list: 搜索结果列表，每个元素是包含title, url, source, content的字典
        """
        if not keywords:
            raise ValueError('搜索关键词不能为空')
        
        if pages < 1:
            pages = 1
        
        self._initialize()
        
        # 编码关键词
        encoded_keywords = urllib.parse.quote(keywords)
        
        results = []
        unique_urls = set()  # 用于去重
        
        try:
            for page in range(pages):
                # 计算百度搜索的pn参数
                pn = page * 10
                url = f'https://www.baidu.com/s?wd={encoded_keywords}&pn={pn}'
                
                # 添加随机延迟，避免被反爬
                if page > 0:
                    delay = random.uniform(1, 3)
                    time.sleep(delay)
                
                logging.info(f'正在爬取百度搜索第 {page+1} 页: {url}')
                
                # 发送请求
                response = self.session.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()  # 检查请求是否成功
                
                # 解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找搜索结果
                result_containers = soup.find_all(['div', 'div'], class_=['result', 'result-op', 'result-tts', 'result-game-item'])
                
                if not result_containers:
                    logging.warning(f'第 {page+1} 页未找到搜索结果')
                    continue
                
                page_results = 0
                for idx, container in enumerate(result_containers):
                    try:
                        # 提取标题
                        title_element = container.find(['h3', 'div'], class_=['t', 'result-title', 'result-op-title', 'tts-title'])
                        if not title_element:
                            continue
                        
                        title = title_element.get_text(strip=True)
                        
                        # 提取URL
                        url_element = title_element.find(['a'], href=True)
                        if not url_element:
                            continue
                        
                        url = url_element['href']
                        
                        # 去重检查
                        if url in unique_urls:
                            continue
                        unique_urls.add(url)
                        
                        # 提取来源
                        source = '未知'
                        source_element = container.find(['span', 'div'], class_=['c-showurl', 'c-showurl c-color-gray', 'result-op-source', 'tts-source'])
                        if source_element:
                            source = source_element.get_text(strip=True)
                        
                        # 提取内容摘要
                        content = ''
                        content_elements = container.find_all(['div', 'div', 'p'], class_=['c-abstract', 'content', 'op_exactqa_s_answer', 'c-span-last', 'result-game-desc', 'tts-content'])
                        
                        for content_elem in content_elements:
                            content_text = content_elem.get_text(strip=True)
                            if content_text:
                                content += content_text + ' '  # 合并所有可能的摘要内容
                        
                        content = content.strip()
                        
                        # 添加结果
                        results.append({
                            'title': title,
                            'url': url,
                            'source': source,
                            'content': content
                        })
                        
                        page_results += 1
                        
                    except Exception as e:
                        logging.error(f'解析第 {page+1} 页第 {idx+1} 条结果时出错: {str(e)}')
                        continue
                
                logging.info(f'第 {page+1} 页爬取完成，获取 {page_results} 条有效结果')
                
                # 如果当前页结果少于10条，可能没有更多页了
                if page_results < 10 and page < pages - 1:
                    logging.info(f'检测到第 {page+1} 页结果不足10条，停止后续爬取')
                    break
        
        except requests.exceptions.RequestException as e:
            logging.error(f'百度搜索请求错误: {str(e)}')
            raise
        except Exception as e:
            logging.error(f'百度搜索爬取错误: {str(e)}')
            raise
        
        logging.info(f'百度搜索完成，共获取 {len(results)} 条有效结果')
        return results

    def close(self):
        """关闭会话"""
        self.session.close()
        logging.info('百度爬虫会话已关闭')

if __name__ == '__main__':
    # 测试代码
    try:
        spider = BaiduSpider()
        results = spider.search('人工智能', pages=2)
        print(f'共获取 {len(results)} 条结果')
        for i, result in enumerate(results[:5]):  # 打印前5条
            print(f'\n结果 {i+1}:')
            print(f'标题: {result["title"]}')
            print(f'来源: {result["source"]}')
            print(f'URL: {result["url"]}')
            print(f'内容: {result["content"]}')
        spider.close()
    except Exception as e:
        print(f'测试失败: {str(e)}')
