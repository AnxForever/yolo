#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web人脸识别系统启动脚本
"""

import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from web_server import app

if __name__ == '__main__':
    print("🚀 正在启动智能人脸识别Web系统...")
    print("📱 请在浏览器中访问: http://localhost:5000")
    print("⏹️  按 Ctrl+C 停止服务器")
    print("="*50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1) 