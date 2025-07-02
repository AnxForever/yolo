#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端API测试脚本
用于验证FastAPI服务器是否正常工作
"""

import requests
import json
import time
import sys
import os

# API基础URL
BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查接口"""
    print("🏥 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            data = response.json()
            print(f"   版本: {data.get('version')}")
            print(f"   状态: {data.get('status')}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_models():
    """测试模型列表接口"""
    print("\n🤖 测试模型列表...")
    try:
        response = requests.get(f"{BASE_URL}/api/models")
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"✅ 找到 {len(models)} 个模型:")
            for model in models:
                status = "已加载" if model.get('loaded') else "未加载"
                print(f"   - {model['name']} ({model['size']}) - {status}")
            return True
        else:
            print(f"❌ 获取模型列表失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_system_status():
    """测试系统状态接口"""
    print("\n📊 测试系统状态...")
    try:
        response = requests.get(f"{BASE_URL}/api/system/status")
        if response.status_code == 200:
            data = response.json()
            print("✅ 系统状态正常:")
            print(f"   CPU使用率: {data.get('cpu', {}).get('usage_percent', 0)}%")
            print(f"   内存使用: {data.get('memory', {}).get('usage_percent', 0)}%")
            print(f"   活跃模型: {data.get('active_models', 0)}")
            print(f"   运行时间: {data.get('uptime', 0)} 秒")
            return True
        else:
            print(f"❌ 获取系统状态失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_image_detection():
    """测试图像检测接口"""
    print("\n🖼️ 测试图像检测...")
    
    # 查找测试图片
    test_images = ["../bus.jpg", "../detection_result.jpg"]
    test_image = None
    
    for img_path in test_images:
        if os.path.exists(img_path):
            test_image = img_path
            break
    
    if not test_image:
        print("⚠️ 没有找到测试图片，跳过检测测试")
        print("   可用的测试图片: bus.jpg, detection_result.jpg")
        return False
    
    print(f"📷 使用测试图片: {test_image}")
    
    try:
        with open(test_image, 'rb') as f:
            files = {'image': f}
            data = {
                'model': 'yolo11n',
                'confidence': 0.5,
                'nms': 0.4
            }
            
            print("🔄 正在发送检测请求...")
            response = requests.post(
                f"{BASE_URL}/api/detect/image",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 图像检测成功:")
                
                metrics = result.get('results', {}).get('metrics', {})
                detections = result.get('results', {}).get('detections', [])
                
                print(f"   推理时间: {metrics.get('inference_time', 0)}ms")
                print(f"   FPS: {metrics.get('fps', 0)}")
                print(f"   检测数量: {len(detections)}")
                print(f"   任务ID: {result.get('task_id', 'N/A')}")
                
                if detections:
                    print("   检测结果:")
                    for i, det in enumerate(detections[:3]):  # 只显示前3个
                        print(f"     {i+1}. {det['label']} (置信度: {det['confidence']:.3f})")
                
                return True
            else:
                print(f"❌ 检测失败: {response.status_code}")
                try:
                    error = response.json()
                    print(f"   错误信息: {error.get('detail', 'Unknown error')}")
                except:
                    print(f"   响应内容: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 检测请求失败: {e}")
        return False

def test_config():
    """测试配置接口"""
    print("\n⚙️ 测试配置接口...")
    try:
        response = requests.get(f"{BASE_URL}/api/config/detection")
        if response.status_code == 200:
            config = response.json()
            print("✅ 配置获取成功:")
            print(f"   置信度范围: {config.get('confidence_range')}")
            print(f"   支持格式: {config.get('supported_formats')}")
            print(f"   最大文件大小: {config.get('max_file_size', 0) / (1024*1024):.1f}MB")
            return True
        else:
            print(f"❌ 配置获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 YOLO Performance Hub - API测试")
    print("=" * 50)
    
    tests = [
        ("健康检查", test_health),
        ("模型列表", test_models),
        ("系统状态", test_system_status),
        ("检测配置", test_config),
        ("图像检测", test_image_detection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except KeyboardInterrupt:
            print("\n⏹️ 测试被用户中断")
            break
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n📋 测试结果汇总:")
    print("-" * 30)
    
    passed = 0
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:12} | {status}")
        if success:
            passed += 1
    
    print("-" * 30)
    print(f"通过率: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
    
    if passed == len(results):
        print("\n🎉 所有测试通过! 后端API工作正常")
    else:
        print(f"\n⚠️ {len(results) - passed} 个测试失败，请检查服务器状态")
    
    return passed == len(results)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server-check":
        # 仅检查服务器是否启动
        if test_health():
            print("✅ 服务器运行正常")
            sys.exit(0)
        else:
            print("❌ 服务器未响应")
            sys.exit(1)
    else:
        # 运行完整测试
        success = main()
        sys.exit(0 if success else 1) 