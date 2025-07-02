import os
import sys
import time

print(" YOLO模型性能测试")
print("=" * 40)

# 检查环境
print(f"Python版本: {sys.version_info.major}.{sys.version_info.minor}")
print(f"当前目录: {os.getcwd()}")

# 检查数据集
print("\n 数据集状态:")
val_path = 'datasets/micro_wider/images/val'
if os.path.exists(val_path):
    img_count = len([f for f in os.listdir(val_path) if f.endswith('.jpg')])
    print(f" micro_wider验证集: {img_count} 张图片")
else:
    print(" micro_wider验证集不存在")

# 检查模型
print("\n 可用模型:")
models = ['yolo11n.pt', 'yolov11n-face.pt', 'yolov8n.pt']
available = []
for model in models:
    if os.path.exists(model):
        size = os.path.getsize(model) / (1024*1024)
        print(f" {model} ({size:.1f}MB)")
        available.append(model)
    else:
        print(f" {model}")

# 测试ultralytics
print("\n ultralytics测试:")
try:
    sys.path.insert(0, './ultralytics')
    from ultralytics import YOLO
    print(" ultralytics导入成功")
    
    if available and os.path.exists('bus.jpg'):
        print(f"\n 性能测试 (使用bus.jpg):")
        print("-" * 30)
        
        for model_path in available[:3]:  # 测试前3个模型
            try:
                print(f"测试 {model_path}...")
                model = YOLO(model_path)
                
                start_time = time.time()
                results = model('bus.jpg', verbose=False)
                inference_time = time.time() - start_time
                
                detections = 0
                if results and len(results) > 0 and results[0].boxes is not None:
                    detections = len(results[0].boxes)
                
                fps = 1.0 / inference_time
                print(f"  时间: {inference_time:.3f}s | FPS: {fps:.1f} | 检测: {detections}")
                
            except Exception as e:
                print(f"   错误: {e}")
                
    else:
        print(" 缺少模型或测试图片")
        
except Exception as e:
    print(f" 导入错误: {e}")

print("\n 测试完成!")
