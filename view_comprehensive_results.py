import cv2
import os
import glob
import json

def view_comprehensive_results():
    print("🎯 查看全面对比测试结果")
    print("=" * 60)
    
    # 查找最新的对比文件夹
    comparison_dirs = glob.glob("model_comparison_*")
    if not comparison_dirs:
        print("❌ 未找到对比测试结果文件夹")
        return
        
    latest_dir = max(comparison_dirs)
    print(f"📁 结果文件夹: {latest_dir}")
    
    # 读取详细报告
    report_path = os.path.join(latest_dir, 'comparison_report.json')
    if os.path.exists(report_path):
        with open(report_path, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        print_summary_report(stats)
    
    # 获取所有对比图片
    comparison_images = sorted(glob.glob(os.path.join(latest_dir, "comparison_*.jpg")))
    
    if not comparison_images:
        print("❌ 未找到对比图片")
        return
        
    print(f"\n🖼️  找到 {len(comparison_images)} 张对比图片")
    print("💡 操作说明:")
    print("   - 按 SPACE 或任意键: 下一张图片")
    print("   - 按 B: 上一张图片") 
    print("   - 按 ESC 或 Q: 退出查看")
    print("   - 按 S: 显示统计信息")
    
    current_index = 0
    
    while current_index < len(comparison_images):
        img_path = comparison_images[current_index]
        img_name = os.path.basename(img_path)
        
        print(f"\n🖼️  显示第 {current_index + 1}/{len(comparison_images)} 张: {img_name}")
        
        # 读取并显示图片
        img = cv2.imread(img_path)
        if img is None:
            print(f"❌ 无法读取图片: {img_path}")
            current_index += 1
            continue
            
        # 调整图片大小以适应屏幕
        height, width = img.shape[:2]
        max_width = 1600
        if width > max_width:
            scale = max_width / width
            new_width = max_width
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height))
            
        # 在图片上添加导航信息
        nav_text = f"Image {current_index + 1}/{len(comparison_images)} - SPACE:Next, B:Back, S:Stats, ESC:Quit"
        cv2.putText(img, nav_text, (10, img.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(img, nav_text, (10, img.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # 显示图片
        cv2.imshow('Comprehensive Model Comparison', img)
        
        # 等待按键
        key = cv2.waitKey(0) & 0xFF
        
        if key == 27 or key == ord('q') or key == ord('Q'):  # ESC或Q键
            print("👋 退出查看")
            break
        elif key == ord('b') or key == ord('B'):  # B键 - 上一张
            if current_index > 0:
                current_index -= 1
            else:
                print("已是第一张图片")
        elif key == ord('s') or key == ord('S'):  # S键 - 显示统计
            if os.path.exists(report_path):
                show_detailed_stats(stats, current_index)
            else:
                print("统计信息文件不存在")
        else:  # 其他键 - 下一张
            current_index += 1
            
    cv2.destroyAllWindows()
    print("\n✅ 查看完成！")
    print(f"📁 所有对比结果保存在: {latest_dir}")

def print_summary_report(stats):
    """打印汇总报告"""
    print("\n" + "=" * 60)
    print("📊 测试汇总报告")
    print("=" * 60)
    
    custom_stats = stats['custom_model']
    general_stats = stats['general_model']
    
    if custom_stats['image_count'] > 0:
        custom_avg_detections = custom_stats['total_detections'] / custom_stats['image_count']
        custom_avg_time = custom_stats['total_time'] / custom_stats['image_count']
        
        general_avg_detections = general_stats['total_detections'] / general_stats['image_count']
        general_avg_time = general_stats['total_time'] / general_stats['image_count']
        
        print(f"🔧 通用模型 (YOLOv11n):")
        print(f"   平均检测: {general_avg_detections:.1f} 个目标/图")
        print(f"   平均时间: {general_avg_time:.3f} 秒/图")
        print(f"   总计检测: {general_stats['total_detections']} 个目标")
        
        print(f"\n🎯 专属模型 (Face-Specialized):")
        print(f"   平均检测: {custom_avg_detections:.1f} 张人脸/图")
        print(f"   平均时间: {custom_avg_time:.3f} 秒/图")
        print(f"   总计检测: {custom_stats['total_detections']} 张人脸")
        
        speed_ratio = custom_avg_time / general_avg_time
        print(f"\n⚡ 速度对比: 专属模型是通用模型的 {speed_ratio:.1f} 倍时间")
        if speed_ratio > 2:
            print("   💡 建议: 可考虑模型量化来提升速度")
        
        accuracy_ratio = custom_avg_detections / general_avg_detections
        print(f"🎯 检测数量对比: 专属模型检测量是通用模型的 {accuracy_ratio:.2f} 倍")

def show_detailed_stats(stats, current_index):
    """显示当前图片的详细统计"""
    if current_index < len(stats['detailed_results']):
        detail = stats['detailed_results'][current_index]
        print(f"\n📊 当前图片详细统计 - {detail['image']}:")
        print(f"   🔧 通用模型: {detail['general_detections']} 个目标 ({detail['general_time']:.3f}s)")
        print(f"   🎯 专属模型: {detail['custom_detections']} 张人脸 ({detail['custom_time']:.3f}s)")
        
        if detail['general_time'] > 0:
            speed_diff = (detail['custom_time'] - detail['general_time']) / detail['general_time'] * 100
            if speed_diff > 0:
                print(f"   ⏱️  专属模型慢 {speed_diff:.1f}%")
            else:
                print(f"   ⚡ 专属模型快 {abs(speed_diff):.1f}%")

if __name__ == "__main__":
    view_comprehensive_results() 