#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端服务启动脚本
检查环境依赖并启动FastAPI服务器
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def check_dependencies():
    """检查必要的依赖包"""
    required_packages = [
        'fastapi',
        'uvicorn', 
        'pydantic',
        'opencv-python',
        'psutil',
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'opencv-python':
                import cv2
            else:
                importlib.import_module(package)
            print(f"✅ {package} - 已安装")
        except ImportError:
            print(f"❌ {package} - 未安装")
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies():
    """安装缺失的依赖"""
    print("📦 开始安装依赖包...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def check_models():
    """检查模型文件是否存在"""
    model_files = [
        "../yolo11n.pt",
        "../yolov11n-face.pt", 
        "../yolov8n.pt"
    ]
    
    available_models = []
    for model_path in model_files:
        if os.path.exists(model_path):
            size = os.path.getsize(model_path) / (1024*1024)
            print(f"✅ {model_path} ({size:.1f}MB)")
            available_models.append(model_path)
        else:
            print(f"⚠️ {model_path} - 文件不存在")
    
    return available_models

def check_ultralytics():
    """检查ultralytics是否可用"""
    try:
        sys.path.insert(0, '../ultralytics')
        from ultralytics import YOLO
        print("✅ ultralytics - 可用")
        return True
    except ImportError as e:
        print(f"❌ ultralytics导入失败: {e}")
        return False

def start_server():
    """启动FastAPI服务器"""
    print("\n🚀 启动YOLO Performance Hub API服务器...")
    print("=" * 50)
    
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n⏹️ 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

def main():
    """主函数"""
    print("🔧 YOLO Performance Hub - 后端环境检查")
    print("=" * 50)
    
    # 检查当前目录
    print(f"📁 当前工作目录: {os.getcwd()}")
    
    # 检查依赖
    print("\n📦 检查Python依赖:")
    missing = check_dependencies()
    
    if missing:
        print(f"\n⚠️ 发现 {len(missing)} 个缺失的依赖包")
        install_choice = input("是否自动安装? (y/n): ").lower()
        if install_choice == 'y':
            if not install_dependencies():
                print("❌ 依赖安装失败，请手动安装后重试")
                return
        else:
            print("请手动安装缺失的依赖后重新运行")
            return
    
    # 检查ultralytics
    print("\n🤖 检查AI框架:")
    if not check_ultralytics():
        print("❌ ultralytics不可用，请检查../ultralytics目录")
        return
    
    # 检查模型文件
    print("\n🎯 检查模型文件:")
    models = check_models()
    if not models:
        print("⚠️ 没有找到任何模型文件，API仍可启动但无法进行检测")
    
    # 启动服务器
    print("\n✅ 环境检查完成")
    start_choice = input("是否启动服务器? (y/n): ").lower()
    if start_choice == 'y':
        start_server()
    else:
        print("💡 要启动服务器，请运行: python main.py")

if __name__ == "__main__":
    main() 