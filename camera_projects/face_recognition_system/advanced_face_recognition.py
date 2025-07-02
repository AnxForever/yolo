import cv2
import face_recognition
import numpy as np
import os
from ultralytics import YOLO
import json
import pickle
from datetime import datetime

class AdvancedFaceRecognitionSystem:
    """高级人脸识别系统 - 整合YOLO检测和face-recognition识别"""
    
    def __init__(self):
        # 获取脚本所在目录的绝对路径
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # YOLO模型路径（保安 - 负责检测人脸位置）
        self.yolo_model_path = os.path.join(
            self.script_dir, 
            "ultralytics", 
            "runs", 
            "detect", 
            "wider_full_training_20250630_234750", 
            "weights", 
            "best.pt"
        )
        
        # 人脸数据库路径
        self.face_database_dir = os.path.join(self.script_dir, "face_database")
        self.encodings_file = os.path.join(self.face_database_dir, "face_encodings.pkl")
        
        # 创建人脸数据库目录
        os.makedirs(self.face_database_dir, exist_ok=True)
        
        # 初始化模型
        self.yolo_model = None
        self.known_face_encodings = []
        self.known_face_names = []
        
        # 加载模型和数据库
        self.load_yolo_model()
        self.load_face_database()
        
        print("🎯 高级人脸识别系统初始化完成！")
        print(f"📍 YOLO模型: {self.yolo_model_path}")
        print(f"📁 人脸数据库: {self.face_database_dir}")
        print(f"👥 已注册人员: {len(self.known_face_names)} 人")

    def load_yolo_model(self):
        """加载YOLO人脸检测模型（保安）"""
        try:
            if os.path.exists(self.yolo_model_path):
                self.yolo_model = YOLO(self.yolo_model_path)
                print("✅ YOLO人脸检测模型加载成功")
            else:
                print(f"❌ YOLO模型文件不存在: {self.yolo_model_path}")
                return False
        except Exception as e:
            print(f"❌ YOLO模型加载失败: {e}")
            return False
        return True

    def load_face_database(self):
        """加载人脸识别数据库（接待员的名册）"""
        try:
            if os.path.exists(self.encodings_file):
                with open(self.encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data['encodings']
                    self.known_face_names = data['names']
                print(f"✅ 人脸数据库加载成功，包含 {len(self.known_face_names)} 个已注册人员")
            else:
                print("📝 人脸数据库为空，可以开始注册新人员")
        except Exception as e:
            print(f"❌ 人脸数据库加载失败: {e}")

    def save_face_database(self):
        """保存人脸识别数据库"""
        try:
            data = {
                'encodings': self.known_face_encodings,
                'names': self.known_face_names
            }
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(data, f)
            print("✅ 人脸数据库保存成功")
            return True
        except Exception as e:
            print(f"❌ 人脸数据库保存失败: {e}")
            return False

    def register_new_person(self, image_path, person_name):
        """注册新人员到人脸数据库"""
        try:
            # 加载图像
            image = cv2.imread(image_path)
            if image is None:
                print(f"❌ 无法读取图像文件: {image_path}")
                return False
            # 转换BGR到RGB (face_recognition使用RGB格式)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 检测人脸并提取特征
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                print(f"❌ 在图像 {image_path} 中未检测到人脸")
                return False
            elif len(face_encodings) > 1:
                print(f"⚠️  在图像 {image_path} 中检测到多个人脸，使用第一个")
            
            # 添加到数据库
            face_encoding = face_encodings[0]
            self.known_face_encodings.append(face_encoding)
            self.known_face_names.append(person_name)
            
            # 保存数据库
            if self.save_face_database():
                print(f"✅ 成功注册新人员: {person_name}")
                return True
            else:
                # 如果保存失败，回滚
                self.known_face_encodings.pop()
                self.known_face_names.pop()
                return False
                
        except Exception as e:
            print(f"❌ 注册人员失败: {e}")
            return False

    def detect_faces_yolo(self, frame):
        """使用YOLO检测人脸位置（保安的工作）"""
        if self.yolo_model is None:
            return []
        
        try:
            results = self.yolo_model(frame, verbose=False)
            face_locations = []
            
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        # 获取边界框坐标
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        # 转换为face_recognition库使用的格式 (top, right, bottom, left)
                        face_locations.append((int(y1), int(x2), int(y2), int(x1)))
            
            return face_locations
        except Exception as e:
            print(f"❌ YOLO人脸检测失败: {e}")
            return []

    def recognize_faces(self, frame, face_locations):
        """识别人脸身份（接待员的工作）"""
        if len(self.known_face_encodings) == 0:
            return ["未知"] * len(face_locations)
        
        try:
            # 提取人脸特征
            face_encodings = face_recognition.face_encodings(frame, face_locations)
            
            face_names = []
            for face_encoding in face_encodings:
                # 比较人脸特征
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                name = "未知"
                
                # 计算相似度
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index] and face_distances[best_match_index] < 0.5:
                        name = self.known_face_names[best_match_index]
                        confidence = (1 - face_distances[best_match_index]) * 100
                        name = f"{name} ({confidence:.1f}%)"
                
                face_names.append(name)
            
            return face_names
        except Exception as e:
            print(f"❌ 人脸识别失败: {e}")
            return ["错误"] * len(face_locations)

    def select_camera(self):
        """选择摄像头设备"""
        print("🔍 正在检测可用摄像头...")
        available_cameras = []
        
        # 检测前5个摄像头索引
        for index in range(5):
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    available_cameras.append({
                        'index': index,
                        'width': width,
                        'height': height
                    })
                    print(f"✅ 摄像头 {index}: 分辨率 {width}x{height}")
                cap.release()
        
        if not available_cameras:
            print("❌ 未检测到可用摄像头")
            return None
        
        if len(available_cameras) == 1:
            selected = available_cameras[0]['index']
            print(f"🎯 自动选择摄像头 {selected}")
            return selected
        
        # 让用户选择摄像头
        while True:
            try:
                choice = input(f"请选择摄像头 (0-{len(available_cameras)-1}): ").strip()
                camera_index = int(choice)
                if camera_index in [cam['index'] for cam in available_cameras]:
                    return camera_index
                else:
                    print("❌ 无效选择，请重新输入")
            except ValueError:
                print("❌ 请输入有效数字")

    def run_realtime_recognition(self):
        """运行实时人脸识别"""
        print("🎬 启动实时人脸识别...")
        
        # 选择摄像头
        camera_index = self.select_camera()
        if camera_index is None:
            return
        
        print("按 'q' 退出，按 's' 截图保存")
        
        cap = cv2.VideoCapture(camera_index)
        
        # 设置摄像头参数
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        frame_count = 0
        face_locations = []
        face_names = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ 无法读取摄像头画面")
                break
            
            # 为了提高性能，每3帧处理一次
            frame_count += 1
            if frame_count % 3 == 0:
                # 缩小图像以提高处理速度
                small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                
                # 步骤1: YOLO检测人脸位置（保安）
                face_locations = self.detect_faces_yolo(small_frame)
                
                # 将坐标放大回原始大小
                face_locations = [(top*2, right*2, bottom*2, left*2) for top, right, bottom, left in face_locations]
                
                # 步骤2: 识别人脸身份（接待员）
                face_names = self.recognize_faces(frame, face_locations)
            
            # 绘制结果
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # 绘制边界框
                color = (0, 255, 0) if "未知" not in name and "错误" not in name else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # 绘制标签背景
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                
                # 绘制姓名
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
            
            # 添加系统信息
            info_text = f"注册人员: {len(self.known_face_names)} | 检测到: {len(face_locations)} 个人脸"
            cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # 显示画面
            cv2.imshow('高级人脸识别系统 - YOLO + face-recognition', frame)
            
            # 按键处理
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # 保存截图
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"recognition_snapshot_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"📸 截图已保存: {filename}")
        
        cap.release()
        cv2.destroyAllWindows()
        print("🎯 人脸识别系统已退出")

    def process_single_image(self, image_path):
        """处理单张图像"""
        try:
            # 读取图像
            frame = cv2.imread(image_path)
            if frame is None:
                print(f"❌ 无法读取图像: {image_path}")
                return
            
            # 检测人脸
            face_locations = self.detect_faces_yolo(frame)
            
            # 识别人脸
            face_names = self.recognize_faces(frame, face_locations)
            
            # 绘制结果
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                color = (0, 255, 0) if "未知" not in name and "错误" not in name else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            
            # 保存结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_filename = f"recognition_result_{timestamp}.jpg"
            cv2.imwrite(result_filename, frame)
            print(f"✅ 识别结果已保存: {result_filename}")
            
            # 显示结果
            cv2.imshow('识别结果', frame)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
        except Exception as e:
            print(f"❌ 图像处理失败: {e}")

def main():
    print("="*60)
    print("🎯 高级人脸识别系统")
    print("🤖 技术架构: YOLO(保安) + face-recognition(接待员)")
    print("="*60)
    
    # 初始化系统
    system = AdvancedFaceRecognitionSystem()
    
    while True:
        print("\n📋 请选择功能:")
        print("1. 注册新人员")
        print("2. 实时人脸识别")
        print("3. 处理单张图像")
        print("4. 查看已注册人员")
        print("5. 退出")
        
        choice = input("请输入选择 (1-5): ").strip()
        
        if choice == '1':
            image_path = input("请输入人员照片路径: ").strip()
            person_name = input("请输入人员姓名: ").strip()
            system.register_new_person(image_path, person_name)
            
        elif choice == '2':
            system.run_realtime_recognition()
            
        elif choice == '3':
            image_path = input("请输入图像路径: ").strip()
            system.process_single_image(image_path)
            
        elif choice == '4':
            print(f"\n👥 已注册人员 ({len(system.known_face_names)} 人):")
            for i, name in enumerate(system.known_face_names, 1):
                print(f"  {i}. {name}")
            
        elif choice == '5':
            print("👋 再见！")
            break
            
        else:
            print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    main() 