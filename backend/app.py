#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
戏讯解析助手 - Flask后端服务
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from parser import WeChatArticleParser
import json
import os
from datetime import datetime

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# 全局解析器实例
parser = None

def get_parser():
    """获取解析器实例"""
    global parser
    if parser is None:
        parser = WeChatArticleParser(headless=True)
    return parser


@app.route('/')
def index():
    """首页"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/parse', methods=['POST'])
def parse_article():
    """
    解析微信公众号文章
    
    请求体:
    {
        "url": "https://mp.weixin.qq.com/s/..."
    }
    """
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({
                'success': False,
                'error': '请提供文章链接'
            }), 400
        
        if 'mp.weixin.qq.com' not in url:
            return jsonify({
                'success': False,
                'error': '请提供有效的微信公众号文章链接'
            }), 400
        
        print(f"\n收到解析请求: {url}")
        
        # 使用解析器解析文章
        parser_instance = get_parser()
        result = parser_instance.parse_article(url)
        
        # 保存解析结果
        if result['success']:
            # 确保data目录存在
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 保存完整JSON结果
            json_filepath = os.path.join(data_dir, f"result_{timestamp}.json")
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"JSON结果已保存: {json_filepath}")
            
            # 保存原始HTML内容供分析
            html_filepath = os.path.join(data_dir, f"content_{timestamp}.html")
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(result['data'].get('content_html', ''))
            print(f"HTML内容已保存: {html_filepath}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/export', methods=['POST'])
def export_data():
    """
    导出数据
    
    请求体:
    {
        "format": "excel|csv|json",
        "data": [...]
    }
    """
    try:
        data = request.get_json()
        export_format = data.get('format', 'json')
        export_data = data.get('data', [])
        
        # TODO: 实现导出功能
        
        return jsonify({
            'success': True,
            'message': f'导出{export_format}格式功能开发中'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': '戏讯解析助手',
        'version': '1.0.0'
    })


if __name__ == '__main__':
    print("=" * 60)
    print("戏讯解析助手后端服务")
    print("=" * 60)
    print("服务地址: http://localhost:5001")
    print("API文档:")
    print("  POST /api/parse   - 解析文章")
    print("  POST /api/export  - 导出数据")
    print("  GET  /api/health  - 健康检查")
    print("=" * 60)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5001)
