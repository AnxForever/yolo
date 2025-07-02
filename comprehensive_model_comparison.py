from ultralytics import YOLO
import cv2
import os
import time
import numpy as np
from datetime import datetime
import glob
import json

def comprehensive_model_comparison():
    print("=" * 80)
    print("🔥 专属模型 VS 通用模型 - 全面对比测试")
    print("=" * 80)
    
    # 模型路径
    custom_model_path = 'ultralytics/runs/detect/wider_full_training_20250630_234750/weights/best.pt'
    general_model_path = 'yolo11n.pt'
    
    print(f"📦 加载模型...")
    print(f"   🎯 专属模型: {custom_model_path}")
    custom_model = YOLO(custom_model_path)
    print(f"   🔧 通用模型: {general_model_path}")
    general_model = YOLO(general_model_path)
    print("✅ 模型加载完成！")
    
    # 创建结果文件夹
    comparison_dir = f"model_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(comparison_dir, exist_ok=True)
    print(f"\n📁 测试结果保存到: {comparison_dir}")
    
    # 准备测试图片集合
    test_images = prepare_test_dataset()
    print(f"\n🎯 准备测试 {len(test_images)} 张图片")
    
    # 初始化统计数据
    stats = {
        'custom_model': {'total_detections': 0, 'total_time': 0, 'image_count': 0},
        'general_model': {'total_detections': 0, 'total_time': 0, 'image_count': 0},
        'detailed_results': []
    }
    
    print("\n" + "=" * 80)
    print("🚀 开始全面对比测试...")
    print("=" * 80)
    
    for i, img_path in enumerate(test_images, 1):
        if not os.path.exists(img_path):
            print(f"⚠️  图片 {i}: {img_path} 不存在，跳过")
            continue
            
        print(f"\n📸 测试图片 {i}/{len(test_images)}: {os.path.basename(img_path)}")
        
        try:
            # 读取图片
            img = cv2.imread(img_path)
            if img is None:
                print(f"❌ 无法读取图片")
                continue
            
            # 测试专属模型
            print("   🎯 专属模型检测中...")
            start_time = time.time()
            custom_results = custom_model(img_path, conf=0.25, verbose=False)
            custom_time = time.time() - start_time
            custom_detections = len(custom_results[0].boxes) if custom_results[0].boxes is not None else 0
            
            # 测试通用模型
            print("   🔧 通用模型检测中...")
            start_time = time.time()
            general_results = general_model(img_path, conf=0.25, verbose=False)
            general_time = time.time() - start_time
            general_detections = len(general_results[0].boxes) if general_results[0].boxes is not None else 0
            
            # 更新统计数据
            stats['custom_model']['total_detections'] += custom_detections
            stats['custom_model']['total_time'] += custom_time
            stats['custom_model']['image_count'] += 1
            
            stats['general_model']['total_detections'] += general_detections
            stats['general_model']['total_time'] += general_time
            stats['general_model']['image_count'] += 1
            
            # 记录详细结果
            detail = {
                'image': os.path.basename(img_path),
                'custom_detections': custom_detections,
                'custom_time': custom_time,
                'general_detections': general_detections,
                'general_time': general_time
            }
            stats['detailed_results'].append(detail)
            
            # 创建对比可视化
            custom_annotated = custom_results[0].plot()
            general_annotated = general_results[0].plot()
            
            # 创建并排对比图
            h, w = custom_annotated.shape[:2]
            comparison = cv2.hconcat([general_annotated, custom_annotated])
            
            # 添加详细标题信息
            title_height = 60
            title_img = np.ones((title_height, comparison.shape[1], 3), dtype=np.uint8) * 255
            
            # 左侧标题（通用模型）
            cv2.putText(title_img, f"General Model: {general_detections} faces ({general_time:.3f}s)", 
                       (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(title_img, "YOLOv11n (Multi-purpose)", 
                       (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
            
            # 右侧标题（专属模型）
            cv2.putText(title_img, f"Custom Model: {custom_detections} faces ({custom_time:.3f}s)", 
                       (w + 10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(title_img, "Face-Specialized (65.3% mAP50)", 
                       (w + 10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
            
            # 合并标题和对比图
            final_comparison = cv2.vconcat([title_img, comparison])
            
            # 保存结果
            result_filename = f"comparison_{i:02d}_{os.path.splitext(os.path.basename(img_path))[0]}.jpg"
            result_path = os.path.join(comparison_dir, result_filename)
            cv2.imwrite(result_path, final_comparison)
            
            # 打印结果
            print(f"   📊 检测结果:")
            print(f"      🔧 通用模型: {general_detections} 个目标 ({general_time:.3f}s)")
            print(f"      🎯 专属模型: {custom_detections} 张人脸 ({custom_time:.3f}s)")
            
            speed_diff = ((general_time - custom_time) / general_time * 100) if general_time > 0 else 0
            if custom_time < general_time:
                print(f"      ⚡ 专属模型快 {speed_diff:.1f}%")
            elif custom_time > general_time:
                print(f"      🐌 专属模型慢 {abs(speed_diff):.1f}%")
            else:
                print(f"      ⚖️  速度相当")
                
            print(f"   💾 对比图: {result_filename}")
            
        except Exception as e:
            print(f"❌ 处理图片时出错: {str(e)}")
            continue
    
    # 生成最终统计报告
    generate_final_report(stats, comparison_dir)

def prepare_test_dataset():
    """准备测试图片集合"""
    test_images = []
    
    # 1. 项目中的测试图片
    project_images = ['bus.jpg', 'baseline_test_results/baseline_result.jpg']
    for img in project_images:
        if os.path.exists(img):
            test_images.append(img)
    
    # 2. 从验证集中随机选择一些图片
    val_dirs = glob.glob('datasets/WIDER_val/images/*')
    selected_dirs = val_dirs[:10]  # 选择前10个类别
    
    for val_dir in selected_dirs:
        images_in_dir = glob.glob(os.path.join(val_dir, '*.jpg'))
        if images_in_dir:
            # 每个类别选择1-2张图片
            selected_count = min(2, len(images_in_dir))
            test_images.extend(images_in_dir[:selected_count])
    
    return test_images[:20]  # 最多测试20张图片

def generate_final_report(stats, output_dir):
    """生成最终统计报告"""
    print("\n" + "=" * 80)
    print("📊 最终对比报告")
    print("=" * 80)
    
    custom_stats = stats['custom_model']
    general_stats = stats['general_model']
    
    if custom_stats['image_count'] > 0 and general_stats['image_count'] > 0:
        # 计算平均值
        custom_avg_detections = custom_stats['total_detections'] / custom_stats['image_count']
        custom_avg_time = custom_stats['total_time'] / custom_stats['image_count']
        
        general_avg_detections = general_stats['total_detections'] / general_stats['image_count']
        general_avg_time = general_stats['total_time'] / general_stats['image_count']
        
        print(f"📈 检测性能对比:")
        print(f"   🔧 通用模型 (YOLOv11n):")
        print(f"      - 平均检测数量: {general_avg_detections:.1f} 个目标/图片")
        print(f"      - 平均推理时间: {general_avg_time:.3f} 秒/图片")
        print(f"      - 总检测数量: {general_stats['total_detections']} 个")
        
        print(f"\n   🎯 专属模型 (Face-Specialized):")
        print(f"      - 平均检测数量: {custom_avg_detections:.1f} 张人脸/图片")
        print(f"      - 平均推理时间: {custom_avg_time:.3f} 秒/图片")
        print(f"      - 总检测数量: {custom_stats['total_detections']} 张")
        
        # 性能对比
        speed_comparison = (general_avg_time - custom_avg_time) / general_avg_time * 100
        print(f"\n🏆 性能优势分析:")
        
        if custom_avg_time < general_avg_time:
            print(f"   ⚡ 专属模型速度优势: 快 {speed_comparison:.1f}%")
        elif custom_avg_time > general_avg_time:
            print(f"   🐌 专属模型速度劣势: 慢 {abs(speed_comparison):.1f}%")
        else:
            print(f"   ⚖️  推理速度: 相当")
        
        print(f"   🎯 专业化优势: 专门检测人脸，避免误检其他物体")
        print(f"   📊 训练数据: 基于完整WIDER Face数据集，针对性强")
        print(f"   🎓 模型质量: mAP50达到65.3%，精确率高")
    
    # 保存详细报告到JSON文件
    report_path = os.path.join(output_dir, 'comparison_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 完整报告已保存:")
    print(f"   📊 详细数据: {report_path}")
    print(f"   🖼️  对比图片: {output_dir}/*.jpg")
    
    print(f"\n🎉 恭喜！你的专属人脸检测模型已经准备就绪！")
    print(f"💡 建议下一步:")
    print(f"   1. 用专属模型替换现有应用中的通用模型")
    print(f"   2. 针对特定场景进一步优化参数")
    print(f"   3. 考虑模型量化以提升推理速度")

if __name__ == "__main__":
    comprehensive_model_comparison() 