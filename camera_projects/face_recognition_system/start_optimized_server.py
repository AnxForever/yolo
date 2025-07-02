#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化版Web人脸识别系统启动脚本
"""

import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from optimized_web_server import app, web_system

if __name__ == '__main__':
    print("🚀 正在启动优化版智能人脸识别系统...")
    print("🔧 专业级性能优化已启用")
    print("📱 请在浏览器中访问: http://localhost:5000")
    print("⏹️  按 Ctrl+C 停止服务器")
    print("="*60)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n正在优雅关闭系统...")
        web_system.stop_recognition()
        print("👋 系统已安全停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1) 