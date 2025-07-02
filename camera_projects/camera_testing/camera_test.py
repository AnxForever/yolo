import cv2
import numpy as np

def test_camera_devices():
    """测试可用的摄像头设备"""
    print("🔍 正在检测可用的摄像头设备...")
    
    available_cameras = []
    
    # 测试前10个摄像头索引
    for index in range(10):
        cap = cv2.VideoCapture(index)
        
        if cap.isOpened():
            # 尝试读取一帧
            ret, frame = cap.read()
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(f"✅ 摄像头 {index}: 可用 - 分辨率 {width}x{height}")
                available_cameras.append({
                    'index': index,
                    'width': width,
                    'height': height
                })
                
                # 显示预览（按任意键继续）
                cv2.imshow(f'摄像头 {index} 预览', frame)
                print(f"   按任意键查看下一个摄像头...")
                cv2.waitKey(2000)  # 显示2秒
                cv2.destroyAllWindows()
            else:
                print(f"❌ 摄像头 {index}: 无法读取画面")
            cap.release()
        else:
            if index == 0:
                print(f"❌ 摄像头 {index}: 无法打开")
    
    return available_cameras

def test_specific_camera(camera_index):
    """测试指定摄像头的详细信息"""
    print(f"\n📹 测试摄像头 {camera_index} 的详细功能...")
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"❌ 无法打开摄像头 {camera_index}")
        return False
    
    # 获取摄像头属性
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"📊 摄像头属性:")
    print(f"   分辨率: {width}x{height}")
    print(f"   帧率: {fps:.2f} FPS")
    
    # 尝试设置更高的分辨率
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    new_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    new_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if new_width != width or new_height != height:
        print(f"✅ 已调整分辨率为: {new_width}x{new_height}")
    
    print(f"\n🎬 实时预览测试 (按 'q' 退出)")
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ 无法读取摄像头画面")
            break
        
        frame_count += 1
        
        # 添加信息文字
        cv2.putText(frame, f"Camera {camera_index} - Frame {frame_count}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Resolution: {frame.shape[1]}x{frame.shape[0]}", 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Press 'q' to quit", 
                   (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow(f'摄像头 {camera_index} 测试', frame)
        
        # 按键检测
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ 摄像头测试完成")
    return True

def main():
    print("="*50)
    print("📹 摄像头设备检测工具")
    print("="*50)
    
    # 检测所有可用摄像头
    cameras = test_camera_devices()
    
    if not cameras:
        print("\n❌ 未检测到可用的摄像头设备")
        print("请检查:")
        print("1. 摄像头是否正确连接")
        print("2. 摄像头驱动是否安装")
        print("3. 是否有其他应用正在使用摄像头")
        return
    
    print(f"\n✅ 检测到 {len(cameras)} 个可用摄像头:")
    for cam in cameras:
        print(f"   摄像头 {cam['index']}: {cam['width']}x{cam['height']}")
    
    # 询问用户要测试哪个摄像头
    while True:
        try:
            choice = input(f"\n请选择要详细测试的摄像头 (0-{len(cameras)-1}, 或 'q' 退出): ").strip()
            if choice.lower() == 'q':
                break
            
            camera_index = int(choice)
            if camera_index in [cam['index'] for cam in cameras]:
                test_specific_camera(camera_index)
            else:
                print("❌ 无效的摄像头索引")
        except ValueError:
            print("❌ 请输入有效的数字")
    
    print("\n👋 摄像头测试完成!")

if __name__ == "__main__":
    main() 