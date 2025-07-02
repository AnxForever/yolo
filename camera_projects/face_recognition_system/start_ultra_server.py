#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 超级优化人脸识别服务器启动器
专注于流畅度和画质优化
"""

import sys
import os
import subprocess
import time

def main():
    print("🚀 超级优化人脸识别服务器")
    print("⚡ 流畅度优先 + 高画质")
    print("="*50)
    
    # 确保在正确目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 检查必要文件
    required_files = [
        'ultra_optimized_server.py',
        'advanced_face_recognition.py',
        'templates/index.html'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ 缺少必要文件:")
        for file in missing_files:
            print(f"   - {file}")
        return
    
    print("✅ 所有文件检查完成")
    
    # 启动信息
    print("\n📊 性能优化特性:")
    print("   🎯 每15帧处理一次 (3倍性能提升)")
    print("   🎥 720p高清分辨率")
    print("   🚀 异步处理架构")
    print("   💨 智能缓冲管理")
    print("   ⚡ 临时禁用情绪分析 (可选开启)")
    print("   📈 实时FPS监控")
    
    print("\n🌐 访问地址:")
    print("   📱 本地: http://localhost:5000")
    print("   🌍 局域网: http://[你的IP]:5000")
    
    print("\n🎮 控制说明:")
    print("   - 自动开始识别")
    print("   - 支持自动抓拍")
    print("   - 实时性能监控")
    print("   - 响应式界面")
    
    print("\n" + "="*50)
    input("📍 按回车键启动服务器...")
    
    try:
        # 启动服务器
        print("\n🚀 正在启动超级优化服务器...")
        subprocess.run([sys.executable, 'ultra_optimized_server.py'], check=True)
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户停止服务器")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 服务器启动失败: {e}")
    except Exception as e:
        print(f"\n💥 未知错误: {e}")
    
    print("\n👋 服务器已停止")

if __name__ == '__main__':
    main() 