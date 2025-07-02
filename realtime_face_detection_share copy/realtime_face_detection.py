import cv2
from ultralytics import YOLO
import os
import time
import numpy as np

class RealTimeFaceDetector:
    def __init__(self):
        # 模型路径优先级设置
        model_paths = [
            # 第一优先级：自定义训练的人脸检测模型
            r'D:\YOLO\ultralytics\runs\detect\wider_full_training_20250630_234750\weights\best.pt',
            # 第二优先级：当前目录下的自定义模型
            './models/best.pt',
            './best.pt',
            # 第三优先级：通用YOLO11模型（会自动下载）
            'yolo11n.pt'
        ]
        
        self.model_path = None
        self.model_type = "unknown"
        
        # 查找可用的模型
        for path in model_paths:
            if path == 'yolo11n.pt':
                # YOLO11通用模型，ultralytics会自动下载
                self.model_path = path
                self.model_type = "通用目标检测模型"
                print(f"🎯 Using general YOLO11 model: {path}")
                break
            elif os.path.exists(path):
                self.model_path = path
                if 'wider' in path or 'face' in path:
                    self.model_type = "专用人脸检测模型"
                else:
                    self.model_type = "自定义模型"
                print(f"🎯 Found custom model: {path}")
                break
        
        if not self.model_path:
            print("❌ Error: No suitable model found!")
            exit()
        
        # 加载YOLO模型
        print(f"🤖 Loading {self.model_type}...")
        try:
            self.model = YOLO(self.model_path)
            print("✅ Model loaded successfully.")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("🔄 Trying to download YOLO11n model...")
            self.model = YOLO('yolo11n.pt')
            self.model_type = "通用目标检测模型"
            print("✅ YOLO11n model loaded successfully.")
        
        # Initialize camera variables
        self.camera_index = 0
        self.cap = None
        self.available_cameras = []
        
        # Performance tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
        # Find available cameras
        self.find_available_cameras()
        
        # Initialize camera
        self.init_camera()
    
    def find_available_cameras(self):
        """检测可用的摄像头"""
        print("🔍 Searching for available cameras...")
        self.available_cameras = []
        
        # 检测最多10个摄像头
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    # 获取摄像头信息
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    
                    self.available_cameras.append({
                        'index': i,
                        'width': width,
                        'height': height,
                        'fps': fps
                    })
                    print(f"📷 Camera {i}: {width}x{height} @ {fps:.1f}FPS")
                cap.release()
        
        if not self.available_cameras:
            print("❌ No cameras found!")
            exit()
        
        print(f"✅ Found {len(self.available_cameras)} camera(s)")
    
    def init_camera(self):
        """初始化摄像头"""
        if self.cap is not None:
            self.cap.release()
        
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            print(f"❌ Error: Could not open camera {self.camera_index}")
            return False
        
        # 设置摄像头参数
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        print(f"✅ Camera {self.camera_index} opened successfully")
        return True
    
    def switch_camera(self):
        """切换摄像头"""
        if len(self.available_cameras) <= 1:
            print("⚠️ Only one camera available")
            return
        
        # 找到下一个可用摄像头
        current_idx = 0
        for i, cam in enumerate(self.available_cameras):
            if cam['index'] == self.camera_index:
                current_idx = i
                break
        
        next_idx = (current_idx + 1) % len(self.available_cameras)
        self.camera_index = self.available_cameras[next_idx]['index']
        
        print(f"🔄 Switching to camera {self.camera_index}")
        self.init_camera()
    
    def calculate_fps(self):
        """计算FPS"""
        self.fps_counter += 1
        
        if self.fps_counter >= 30:  # 每30帧计算一次FPS
            end_time = time.time()
            self.current_fps = self.fps_counter / (end_time - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = end_time
    
    def draw_info_panel(self, frame, face_count):
        """绘制信息面板"""
        height, width = frame.shape[:2]
        
        # 创建半透明背景
        overlay = frame.copy()
        info_height = 120
        cv2.rectangle(overlay, (0, 0), (width, info_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # 显示信息
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # 标题
        cv2.putText(frame, "Real-time Face Detection", (10, 25), 
                   font, 0.8, (0, 255, 255), 2)
        
        # 人脸数量 - 大号显示
        face_text = f"Faces Detected: {face_count}"
        cv2.putText(frame, face_text, (10, 55), 
                   font, 0.7, (0, 255, 0), 2)
        
        # FPS
        fps_text = f"FPS: {self.current_fps:.1f}"
        cv2.putText(frame, fps_text, (10, 80), 
                   font, 0.6, (255, 255, 255), 1)
        
        # 摄像头信息
        cam_text = f"Camera: {self.camera_index} ({len(self.available_cameras)} available)"
        cv2.putText(frame, cam_text, (10, 100), 
                   font, 0.6, (255, 255, 255), 1)
        
        # 模型信息
        model_text = f"Model: {self.model_type}"
        cv2.putText(frame, model_text, (10, 115), 
                   font, 0.5, (200, 200, 200), 1)
        
        # 在右侧显示控制提示
        controls = [
            "Controls:",
            "Q - Quit",
            "C - Switch Camera",
            "S - Screenshot"
        ]
        
        start_x = width - 200
        for i, control in enumerate(controls):
            y = 25 + i * 20
            color = (255, 255, 0) if i == 0 else (255, 255, 255)
            cv2.putText(frame, control, (start_x, y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return frame
    
    def save_screenshot(self, frame, face_count):
        """保存截图"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"face_detection_screenshot_{timestamp}_faces_{face_count}.jpg"
        cv2.imwrite(filename, frame)
        print(f"📸 Screenshot saved: {filename}")
    
    def run(self):
        """运行主程序"""
        print("\n🚀 Starting real-time face detection...")
        print("📋 Controls:")
        print("   Q - Quit")
        print("   C - Switch Camera") 
        print("   S - Take Screenshot")
        print("-" * 50)
        
        screenshot_count = 0
        
        while True:
            # 读取帧
            if self.cap is None or not self.cap.isOpened():
                print("❌ Error: Camera not available.")
                break
                
            ret, frame = self.cap.read()
            if not ret:
                print("❌ Error: Failed to capture frame.")
                break
            
            # 翻转图像（镜像效果）
            frame = cv2.flip(frame, 1)
            
            # 执行人脸检测
            results = self.model(frame, conf=0.25, verbose=False)
            
            # 获取检测结果
            detections = results[0].boxes
            face_count = len(detections) if detections is not None else 0
            
            # 绘制检测框
            annotated_frame = results[0].plot()
            
            # 翻转标注后的图像以匹配原始翻转
            annotated_frame = cv2.flip(annotated_frame, 1)
            
            # 绘制信息面板
            annotated_frame = self.draw_info_panel(annotated_frame, face_count)
            
            # 计算FPS
            self.calculate_fps()
            
            # 显示图像
            cv2.imshow('Real-time Face Detection (Custom Model)', annotated_frame)
            
            # 处理按键
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == ord('Q'):
                print("👋 Quitting...")
                break
            elif key == ord('c') or key == ord('C'):
                self.switch_camera()
            elif key == ord('s') or key == ord('S'):
                screenshot_count += 1
                self.save_screenshot(annotated_frame, face_count)
        
        # 清理资源
        self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
        print("🧹 Resources cleaned up. Goodbye!")

def main():
    """主函数"""
    try:
        detector = RealTimeFaceDetector()
        detector.run()
    except KeyboardInterrupt:
        print("\n⏹️ Program interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 