import cv2
import face_recognition
import numpy as np
import os
from ultralytics import YOLO
import json
import pickle
from datetime import datetime
import time
from scipy.ndimage import rotate
from PIL import Image, ImageDraw, ImageFont
from deepface import DeepFace

class AdvancedFaceRecognitionSystem:
    """高级人脸识别系统 - 整合YOLO检测和face-recognition识别"""
    
    def __init__(self):
        # 获取脚本所在目录的绝对路径
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # YOLO模型路径（保安 - 负责检测人脸位置）
        self.yolo_model_path = os.path.join(
            self.script_dir,
            "../../",  # 返回两级到YOLO根目录
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
        
        # 摄像头与界面状态
        self.available_cameras = []
        self.current_camera_index = -1
        self.cap = None
        
        # FPS 计算
        self.prev_frame_time = 0
        self.new_frame_time = 0
        
        # 界面显示设置
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.info_panel_height = 90
        self.show_info_panel = True
        
        # 截图保存目录
        self.screenshots_dir = os.path.join(self.script_dir, "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)

        # 加载中文字体
        self.font_path = os.path.join(self.script_dir, "fonts", "simhei.ttf")
        self.name_font = self._load_font(self.font_path, 30)

        # 聘请情绪识别专家 (使用DeepFace)
        print("🙂 正在聘请情绪识别专家 (DeepFace - 首次运行可能需要下载模型)...")
        # DeepFace 会在第一次使用时自动下载模型，这里不需要初始化
        print("✅ 情绪识别专家已准备就绪。")

        self._initialize_system()
        
    def _load_font(self, path, size):
        """安全地加载字体文件"""
        try:
            return ImageFont.truetype(path, size)
        except IOError:
            print(f"❌ 字体文件未找到: {path}")
            print("   请确保 'simhei.ttf' (或类似中文字体) 已放置在 'fonts' 文件夹中。")
            print("   程序将无法正确显示中文。")
            return None

    def _initialize_system(self):
        """初始化系统，加载模型并检测摄像头"""
        print("🚀 系统初始化开始...")
        
        # 1. 加载YOLO模型
        if not self.load_yolo_model():
            return False # 如果模型加载失败，则终止

        # 2. 加载人脸数据库
        self.load_face_database()
        
        # 3. 检测可用摄像头
        print("🔍 正在检测可用摄像头...")
        self.available_cameras = []
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    h, w, _ = frame.shape
                    self.available_cameras.append({'index': i, 'width': w, 'height': h})
                    print(f"  ✅ 发现摄像头 {i} (分辨率: {w}x{h})")
                cap.release()
        
        if not self.available_cameras:
            print("❌ 错误：未检测到任何可用的摄像头。")
            return False
        
        self.current_camera_index = self.available_cameras[0]['index']
        print(f"🎯 成功检测到 {len(self.available_cameras)} 个摄像头，默认使用索引 {self.current_camera_index}")
        print("🎉 系统初始化完成！")
        return True

    def load_yolo_model(self):
        """加载YOLO人脸检测模型（保安）"""
        try:
            if os.path.exists(self.yolo_model_path):
                self.yolo_model = YOLO(self.yolo_model_path)
                print("  ✅ YOLO人脸检测模型加载成功")
            else:
                print(f"  ❌ 错误: YOLO模型文件不存在于 '{self.yolo_model_path}'")
                print("  🤔 请确认路径是否正确，或模型文件是否存在。")
                return False
        except Exception as e:
            print(f"  ❌ 错误: YOLO模型加载失败: {e}")
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
                print(f"  ✅ 人脸数据库加载成功，共 {len(set(self.known_face_names))} 人，总计 {len(self.known_face_encodings)} 个面部特征样本")
            else:
                print("  📝 信息: 人脸数据库为空，请运行更新程序进行注册。")
        except Exception as e:
            print(f"  ❌ 错误: 人脸数据库加载失败: {e}")

    def save_face_database(self):
        """保存人脸识别数据库"""
        try:
            data = {
                'encodings': self.known_face_encodings,
                'names': self.known_face_names
            }
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(data, f)
            print("  ✅ 人脸数据库保存成功")
            return True
        except Exception as e:
            print(f"  ❌ 错误: 人脸数据库保存失败: {e}")
            return False

    def _get_rotated_images(self, image):
        """
        对输入的图像进行数据增强，生成旋转后的副本。
        """
        augmented_images = []
        # 原始图像必须保留
        augmented_images.append(image)
        
        # 定义旋转角度
        angles = [-15, 15, 90, -90, 180]
        
        for angle in angles:
            # 使用scipy进行图像旋转，reshape=False保持原尺寸
            rotated_image = rotate(image, angle, reshape=False)
            augmented_images.append(rotated_image)
            
        return augmented_images

    def rescan_and_encode_database(self, augment: bool = False):
        """
        全面扫描face_database文件夹，为每个子文件夹（代表一个人）中的所有照片创建编码。
        这将覆盖现有的数据库。
        :param augment: 是否启用数据增强（旋转图像）以提升角度识别能力。
        """
        if augment:
            print("\n--- ✨ 开始 [增强模式] 扫描并更新人脸数据库 (过程较慢) ---")
        else:
            print("\n--- 🔄 开始 [标准模式] 扫描并更新人脸数据库 ---")
            
        self.known_face_encodings.clear()
        self.known_face_names.clear()
        
        subfolders = [f.path for f in os.scandir(self.face_database_dir) if f.is_dir()]
        
        if not subfolders:
            print("⚠️ 警告：在 face_database 中未找到任何人员文件夹（子目录）。")

        total_features_count = 0
        for person_dir in subfolders:
            person_name = os.path.basename(person_dir)
            print(f"📁 正在处理人员: {person_name}")
            
            image_count = 0
            for image_name in os.listdir(person_dir):
                image_path = os.path.join(person_dir, image_name)
                
                if image_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    try:
                        original_image = face_recognition.load_image_file(image_path)
                        
                        images_to_process = []
                        if augment:
                            images_to_process = self._get_rotated_images(original_image)
                            print(f"  - 增强照片: {image_name} (生成 {len(images_to_process)} 个版本)")
                        else:
                            images_to_process = [original_image]

                        # 处理原始及所有增强后的图像
                        for i, image in enumerate(images_to_process):
                            # 步骤1: 强制使用YOLO来检测人脸位置
                            face_locations = self.detect_faces_yolo(image)

                            if face_locations:
                                # 步骤2: 如果YOLO找到了人脸，就让face_recognition在指定位置提取特征
                                encodings = face_recognition.face_encodings(image, known_face_locations=face_locations)
                                
                                if encodings:
                                    for encoding in encodings:
                                        self.known_face_encodings.append(encoding)
                                        self.known_face_names.append(person_name)
                                        total_features_count += 1
                                    if i == 0: # 只在处理原始图片时打印主学习信息
                                        print(f"    - ✅ [YOLO定位成功] 已学习: {image_name} (发现 {len(encodings)} 个面部特征)")
                            elif i == 0: # 如果原始图片YOLO都检测不到，就告警
                                print(f"    - ⚠️  [YOLO定位失败] 在原始照片 {image_name} 中未检测到人脸，已跳过。")
                        
                        image_count += 1
                            
                    except Exception as e:
                        print(f"  - ❌ 错误: 处理 {image_name} 时失败: {e}")
            
            if image_count == 0:
                 print(f"  - ⚠️ 警告: 文件夹 '{person_name}' 中没有任何可学习的照片。")
                        
        if self.known_face_encodings:
            self.save_face_database()
            print(f"\n--- ✅ 数据库更新完成！共 {len(set(self.known_face_names))} 人, {total_features_count} 个面部特征样本已保存。 ---")
        else:
            print("\n--- ⚠️ 数据库为空或未学到任何有效特征，未保存任何内容。 ---")

    def detect_faces_yolo(self, frame):
        """使用YOLO检测人脸位置（保安的工作）"""
        if self.yolo_model is None:
            return []
        
        try:
            results = self.yolo_model(frame, verbose=False)
            face_locations = []
            
            if results and results[0].boxes is not None:
                for box in results[0].boxes:
                    # 获取边界框坐标
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    # 转换为face_recognition库使用的格式 (top, right, bottom, left)
                    face_locations.append((y1, x2, y2, x1))
            
            return face_locations
        except Exception as e:
            print(f"❌ YOLO人脸检测时发生错误: {e}")
            return []

    def recognize_faces(self, frame_rgb, face_locations):
        """识别人脸身份（接待员的工作）"""
        # 如果数据库为空，直接返回"未知"
        if not self.known_face_encodings:
            return ["未知"] * len(face_locations)
        
        try:
            # 提取当前帧中所有人脸的特征
            current_face_encodings = face_recognition.face_encodings(frame_rgb, face_locations)
            
            face_names = []
            for face_encoding in current_face_encodings:
                # 将当前人脸与数据库中的所有人脸进行比较
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.5)
                name = "未知"
                
                # 计算与数据库中所有人脸的距离，找到最相似的一个
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    # 如果最相似的人脸确实匹配，并且距离足够近
                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]
                
                face_names.append(name)
            
            return face_names
        except Exception as e:
            print(f"❌ 人脸识别时发生错误: {e}")
            return ["错误"] * len(face_locations)

    def _draw_info_panel(self, frame, fps, face_count):
        """在画面上绘制信息面板"""
        if not self.show_info_panel:
            return frame

        h, w, _ = frame.shape
        # 创建一个半透明的黑色背景
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h - self.info_panel_height), (w, h), (0, 0, 0), -1)
        alpha = 0.6  # 透明度
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # 组织要显示的信息
        cam_info = self.available_cameras[self.current_camera_index]
        info_lines = [
            f"FPS: {fps:.1f}",
            f"Faces: {face_count}",
            f"Camera: {cam_info['index']} ({cam_info['width']}x{cam_info['height']})",
            "Controls: [C] Change Cam | [S] Screenshot | [H] Hide Panel | [Q] Quit"
        ]
        
        # 逐行绘制信息
        for i, line in enumerate(info_lines):
            y_pos = h - self.info_panel_height + 25 + (i * 20)
            cv2.putText(frame, line, (10, y_pos), self.font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            
        return frame

    def _save_snapshot(self, frame):
        """保存当前帧的快照"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshot_{timestamp}_faces_{len(self.detect_faces_yolo(frame))}.jpg"
        filepath = os.path.join(self.screenshots_dir, filename)
        cv2.imwrite(filepath, frame)
        print(f"📸 快照已保存: {filepath}")

    def _switch_camera(self):
        """切换到下一个可用的摄像头"""
        if len(self.available_cameras) <= 1:
            print("ℹ️ 只有一个可用摄像头，无法切换。")
            return
            
        # 计算下一个摄像头的索引
        current_cam_list_index = next((i for i, cam in enumerate(self.available_cameras) if cam['index'] == self.current_camera_index), None)
        
        if current_cam_list_index is None:
            # 如果当前摄像头索引不在可用列表中（异常情况），安全起见切换回第一个
            next_cam_list_index = 0
        else:
            # 正常循环切换
            next_cam_list_index = (current_cam_list_index + 1) % len(self.available_cameras)
            
        self.current_camera_index = self.available_cameras[next_cam_list_index]['index']
        
        # 释放旧的摄像头对象
        if self.cap:
            self.cap.release()
            
        # 创建新的摄像头对象
        self.cap = cv2.VideoCapture(self.current_camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            print(f"❌ 错误: 无法切换到摄像头 {self.current_camera_index}")
            self.cap = None
        else:
            print(f"🔄 已切换到摄像头 {self.current_camera_index}")

    def _analyze_emotions(self, frame, face_locations):
        """使用DeepFace库分析人脸情绪"""
        emotions_result = []
        for (top, right, bottom, left) in face_locations:
            # 精确裁剪出人脸区域
            # 注意：要确保坐标不超出图像边界
            top = max(0, top)
            left = max(0, left)
            bottom = min(frame.shape[0], bottom)
            right = min(frame.shape[1], right)
            
            cropped_face = frame[top:bottom, left:right]

            if cropped_face.size == 0:
                emotions_result.append("")
                continue

            # 使用DeepFace检测情绪
            try:
                # DeepFace.analyze 返回情绪分析结果
                result = DeepFace.analyze(cropped_face, actions=['emotion'], enforce_detection=False)
                if result and len(result) > 0:
                    # DeepFace返回的是一个列表，取第一个结果
                    emotion_data = result[0]['emotion']
                    # 找到得分最高的情绪
                    top_emotion = max(emotion_data, key=emotion_data.get)
                    emotions_result.append(top_emotion)
                else:
                    emotions_result.append("") # 未检测到情绪
            except Exception as e:
                # print(f"情绪分析时出错: {e}") # 调试时可打开
                emotions_result.append("") # 出错时也返回空
        
        return emotions_result

    def _draw_results_on_frame(self, frame, face_locations, face_names, face_emotions):
        """使用Pillow在画面上绘制结果，支持中文和情绪"""
        # 将OpenCV图像(BGR)转换为Pillow图像(RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        draw = ImageDraw.Draw(pil_image)

        for (top, right, bottom, left), name, emotion in zip(face_locations, face_names, face_emotions):
            # 绘制人脸框
            draw.rectangle(((left, top), (right, bottom)), outline=(0, 255, 0), width=2)
            
            # 组合最终显示的文本
            display_text = name
            if emotion:
                display_text = f"{name} ({emotion})"

            # 判断是否加载了字体
            if self.name_font:
                # 使用Pillow绘制带中文的标签
                text_size = draw.textbbox((0, 0), display_text, font=self.name_font)
                text_width = text_size[2] - text_size[0]
                text_height = text_size[3] - text_size[1]
                
                label_bottom = bottom
                label_top = label_bottom - text_height - 10
                label_right = left + text_width + 10
                
                draw.rectangle(((left, label_top), (label_right, label_bottom)), fill=(0, 255, 0))
                draw.text((left + 5, label_top + 5), display_text, font=self.name_font, fill=(0, 0, 0))
            else:
                # 字体加载失败时的后备方案
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, display_text, (left + 6, bottom - 6), self.font, 0.7, (0, 0, 0), 2)


        # 将Pillow图像转换回OpenCV图像(BGR)
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def run_realtime_recognition(self):
        """运行实时人脸检测与识别的主循环"""
        if self.current_camera_index == -1:
            print("❌ 无法启动：系统未成功初始化或未找到摄像头。")
            return
            
        self.cap = cv2.VideoCapture(self.current_camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            print(f"❌ 错误: 无法打开摄像头 {self.current_camera_index}")
            return
            
        print("\n--- 实时识别已启动 ---")
        print("在视频窗口按 'Q' 退出")

        while True:
            if self.cap is None:
                break
                
            ret, frame = self.cap.read()
            if not ret:
                print("⚠️ 无法从摄像头读取画面，可能已断开连接。")
                break
            
            # 1. 计算FPS
            self.new_frame_time = time.time()
            fps = 1 / (self.new_frame_time - self.prev_frame_time)
            self.prev_frame_time = self.new_frame_time
            
            # 2. YOLO人脸检测
            face_locations = self.detect_faces_yolo(frame)
            face_count = len(face_locations)
            
            face_names = []
            face_emotions = []
            if face_count > 0:
                # 转换颜色空间以供face_recognition使用
                rgb_small_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # 3. 识别人脸
                face_names = self.recognize_faces(rgb_small_frame, face_locations)

                # 4. 分析情绪
                face_emotions = self._analyze_emotions(frame, face_locations)

            # 5. 在画面上绘制结果
            frame = self._draw_results_on_frame(frame, face_locations, face_names, face_emotions)

            # 6. 绘制信息面板
            frame = self._draw_info_panel(frame, fps, face_count)

            # 7. 显示最终画面
            cv2.imshow("实时人脸识别系统", frame)

            # 8. 处理键盘输入
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("👋 正在关闭系统...")
                break
            elif key == ord('s'):
                self._save_snapshot(frame)
            elif key == ord('c'):
                self._switch_camera()
            elif key == ord('h'):
                self.show_info_panel = not self.show_info_panel
        
        # 清理资源
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("✅ 系统已成功关闭。")

    def process_single_image(self, image_path):
        """处理单张图像"""
        try:
            print(f"🖼️ 正在处理单张图片: {image_path}")
            frame = cv2.imread(image_path)
            if frame is None:
                print(f"❌ 错误: 无法读取图片 {image_path}")
                return

            # YOLO人脸检测
            face_locations = self.detect_faces_yolo(frame)
            print(f"  检测到 {len(face_locations)} 个人脸")

            face_names = []
            if face_locations:
                # 识别人脸
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_names = self.recognize_faces(rgb_frame, face_locations)

            # 绘制结果
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), self.font, 1.0, (0, 0, 0), 2)
            
            # 保存结果
            base, ext = os.path.splitext(os.path.basename(image_path))
            output_path = os.path.join(self.screenshots_dir, f"{base}_recognized{ext}")
            cv2.imwrite(output_path, frame)
            print(f"  ✅ 结果已保存到: {output_path}")

            # 显示结果
            cv2.imshow("图片识别结果", frame)
            print("  在图片窗口按任意键退出...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        except Exception as e:
            print(f"❌ 处理图片时发生错误: {e}")


def main():
    """主函数 - 启动应用"""
    face_system = AdvancedFaceRecognitionSystem()

    if face_system.yolo_model is None:
        print("\n❌ 系统核心组件加载失败，程序已退出。请检查错误信息。")
        return

    while True:
        print("\n" + "="*50)
        print("          高级人脸识别系统 - 主菜单")
        print("="*50)
        print("1. 🚀 启动实时人脸识别")
        print("2. 🔄 [标准] 更新人脸数据库 (快速)")
        print("3. ✨ [增强] 更新人脸数据库 (提升角度识别，较慢)")
        print("4. 👋 退出系统")
        print("-"*50)

        choice = input("请选择操作 (1-4): ").strip()

        if choice == '1':
            if not face_system.known_face_encodings:
                print("\n⚠️ 警告: 人脸数据库为空或未加载。")
                print("   请先将照片放入 'face_database' 下的个人文件夹中，然后运行更新数据库选项。")
                continue
            
            print("\n即将启动实时识别...")
            face_system.run_realtime_recognition()
            print("\n返回主菜单...")

        elif choice == '2':
            face_system.rescan_and_encode_database(augment=False)
            print("\n数据库已更新。正在自动重新加载数据...")
            face_system.load_face_database()

        elif choice == '3':
            face_system.rescan_and_encode_database(augment=True)
            print("\n数据库已通过增强模式更新。正在自动重新加载数据...")
            face_system.load_face_database()
            
        elif choice == '4':
            print("👋 感谢使用，再见！")
            break
        else:
            print("❌ 无效输入，请输入 1, 2, 3 或 4。")


if __name__ == "__main__":
    main() 