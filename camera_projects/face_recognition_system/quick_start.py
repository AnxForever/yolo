#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速启动脚本 - 解决加载慢的问题
"""

import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from simple_optimized_server import app, system

if __name__ == '__main__':
    print("⚡ 快速启动模式")
    print("🔧 已优化初始化速度")
    print("📱 浏览器访问: http://localhost:5000")
    print("🎬 页面打开后会自动启动视频流")
    print("="*50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n正在停止...")
        system.stop_camera()
        print("👋 已停止")
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1) 