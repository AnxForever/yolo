import os
import cv2
import time
import threading
import queue
import logging
from datetime import datetime
from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS

from advanced_face_recognition import AdvancedFaceRecognitionSystem

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class SimpleOptimizedSystem:
    def __init__(self):
        print("🚀 初始化系统...")
        self.face_system = AdvancedFaceRecognitionSystem()
        
        # 摄像头相关
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # 识别结果
        self.latest_results = {
            'face_count': 0,
            'face_names': [],
            'face_emotions': [],
            'face_locations': []
        }
        
        # 自动抓拍
        self.auto_capture_targets = set()
        self.capture_cooldown = {}
        self.capture_interval = 5
        self.capture_history = []
        
        # 创建目录
        self.auto_capture_dir = os.path.join(self.face_system.script_dir, "auto_captures")
        os.makedirs(self.auto_capture_dir, exist_ok=True)
        
        # 性能统计
        self.fps = 0
        self.last_fps_time = time.time()
        self.frame_count = 0
        
        print("✅ 系统初始化完成")
    
    def start_camera(self):
        """启动摄像头"""
        try:
            if self.is_running:
                return True
                
            print("📹 正在启动摄像头...")
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            
            if not self.cap or not self.cap.isOpened():
                print("❌ 摄像头启动失败")
                return False
            
            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            self.is_running = True
            print("✅ 摄像头启动成功")
            return True
            
        except Exception as e:
            print(f"❌ 摄像头启动异常: {e}")
            return False
    
    def stop_camera(self):
        """停止摄像头"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        print("🛑 摄像头已停止")
    
    def generate_frames(self):
        """生成视频流"""
        if not self.start_camera():
            return
            
        print("🎬 开始生成视频流...")
        
        while self.is_running and self.cap:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    print("⚠️ 无法读取摄像头画面")
                    time.sleep(0.1)
                    continue
                
                # 更新当前帧
                with self.frame_lock:
                    self.current_frame = frame.copy()
                
                # 进行人脸检测和识别
                processed_frame = self.process_frame(frame)
                
                # 计算FPS
                self.update_fps()
                
                # 在画面上绘制FPS
                cv2.putText(processed_frame, f"FPS: {self.fps:.1f}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # 编码为JPEG
                ret, buffer = cv2.imencode('.jpg', processed_frame, 
                                         [cv2.IMWRITE_JPEG_QUALITY, 85])
                
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
            except Exception as e:
                print(f"❌ 视频流生成错误: {e}")
                time.sleep(0.1)
        
        print("🏁 视频流已停止")
    
    def process_frame(self, frame):
        """处理帧 - 简化版本"""
        try:
            # 每5帧处理一次，提高性能
            if self.frame_count % 5 != 0:
                self.frame_count += 1
                return frame
            
            # 人脸检测
            face_locations = self.face_system.detect_faces_yolo(frame)
            face_names = []
            face_emotions = []
            
            if face_locations:
                # 转换颜色空间
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 人脸识别
                face_names = self.face_system.recognize_faces(rgb_frame, face_locations)
                
                # 简化情绪分析 - 可选择性禁用
                try:
                    face_emotions = self.face_system._analyze_emotions(frame, face_locations)
                except:
                    face_emotions = [""] * len(face_locations)
            
            # 更新结果
            self.latest_results = {
                'face_count': len(face_locations),
                'face_names': face_names,
                'face_emotions': face_emotions,
                'face_locations': face_locations
            }
            
            # 检查自动抓拍
            self.check_auto_capture(frame, face_names, face_emotions)
            
            # 绘制结果
            frame = self.draw_results(frame, face_locations, face_names, face_emotions)
            
            self.frame_count += 1
            return frame
            
        except Exception as e:
            print(f"❌ 帧处理错误: {e}")
            return frame
    
    def draw_results(self, frame, face_locations, face_names, face_emotions):
        """绘制识别结果"""
        for i, (top, right, bottom, left) in enumerate(face_locations):
            # 获取信息
            name = face_names[i] if i < len(face_names) else "Unknown"
            emotion = face_emotions[i] if i < len(face_emotions) else ""
            
            # 设置颜色
            color = (0, 255, 0) if name != "未知" else (0, 0, 255)
            if name in self.auto_capture_targets:
                color = (255, 165, 0)  # 橙色表示自动抓拍目标
            
            # 绘制人脸框
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # 准备文本
            display_text = name
            if emotion:
                display_text = f"{name} ({emotion})"
            if name in self.auto_capture_targets:
                display_text += " [AUTO]"
            
            # 绘制标签
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, display_text, (left + 6, bottom - 6), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def check_auto_capture(self, frame, face_names, face_emotions):
        """检查自动抓拍"""
        if not self.auto_capture_targets:
            return
        
        current_time = time.time()
        
        for i, name in enumerate(face_names):
            if name in self.auto_capture_targets:
                last_capture = self.capture_cooldown.get(name, 0)
                if current_time - last_capture >= self.capture_interval:
                    self.capture_person(frame, name, face_emotions[i] if i < len(face_emotions) else "")
                    self.capture_cooldown[name] = current_time
    
    def capture_person(self, frame, person_name, emotion):
        """自动抓拍"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"auto_capture_{person_name}_{emotion}_{timestamp}.jpg"
            filepath = os.path.join(self.auto_capture_dir, filename)
            
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            record = {
                'person_name': person_name,
                'emotion': emotion,
                'timestamp': datetime.now().isoformat(),
                'filename': filename
            }
            
            self.capture_history.append(record)
            if len(self.capture_history) > 100:
                self.capture_history = self.capture_history[-100:]
            
            print(f"📸 自动抓拍: {person_name} ({emotion})")
            
        except Exception as e:
            print(f"❌ 自动抓拍失败: {e}")
    
    def update_fps(self):
        """更新FPS"""
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time

# 创建全局系统实例
system = SimpleOptimizedSystem()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """视频流端点"""
    print("🎥 请求视频流...")
    return Response(system.generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/start_recognition', methods=['POST'])
def start_recognition():
    if system.start_camera():
        return jsonify({'status': 'success', 'message': '识别已启动'})
    return jsonify({'status': 'error', 'message': '启动失败'})

@app.route('/api/stop_recognition', methods=['POST'])
def stop_recognition():
    system.stop_camera()
    return jsonify({'status': 'success', 'message': '识别已停止'})

@app.route('/api/recognition_status')
def recognition_status():
    return jsonify({
        'is_running': system.is_running,
        'results': system.latest_results,
        'auto_capture_targets': list(system.auto_capture_targets),
        'fps': system.fps
    })

@app.route('/api/database_info')
def database_info():
    known_names = list(set(system.face_system.known_face_names))
    return jsonify({
        'known_people': known_names,
        'total_people': len(known_names),
        'total_features': len(system.face_system.known_face_encodings)
    })

@app.route('/api/update_database', methods=['POST'])
def update_database():
    data = request.get_json()
    augment = data.get('augment', False)
    
    try:
        system.face_system.rescan_and_encode_database(augment=augment)
        system.face_system.load_face_database()
        return jsonify({'status': 'success', 'message': '数据库更新成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'更新失败: {str(e)}'})

@app.route('/api/auto_capture_targets', methods=['GET', 'POST'])
def auto_capture_targets():
    if request.method == 'GET':
        return jsonify({'targets': list(system.auto_capture_targets)})
    
    data = request.get_json()
    action = data.get('action')
    person_name = data.get('person_name')
    
    if action == 'add' and person_name:
        system.auto_capture_targets.add(person_name)
        return jsonify({'status': 'success', 'message': f'已添加 {person_name}'})
    elif action == 'remove' and person_name:
        system.auto_capture_targets.discard(person_name)
        return jsonify({'status': 'success', 'message': f'已移除 {person_name}'})
    elif action == 'clear':
        system.auto_capture_targets.clear()
        return jsonify({'status': 'success', 'message': '已清空列表'})
    
    return jsonify({'status': 'error', 'message': '无效操作'})

@app.route('/api/capture_history')
def capture_history():
    return jsonify({
        'history': system.capture_history[-50:],
        'total_captures': len(system.capture_history)
    })

@app.route('/api/manual_capture', methods=['POST'])
def manual_capture():
    if system.current_frame is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"manual_capture_{timestamp}.jpg"
        filepath = os.path.join(system.auto_capture_dir, filename)
        
        cv2.imwrite(filepath, system.current_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return jsonify({'status': 'success', 'message': f'抓拍成功: {filename}'})
    
    return jsonify({'status': 'error', 'message': '无法获取画面'})

if __name__ == '__main__':
    print("🚀 启动简化优化版Web服务器...")
    print("📱 访问地址: http://localhost:5000")
    print("⏹️  按 Ctrl+C 停止")
    print("="*50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n正在停止系统...")
        system.stop_camera()
        print("👋 系统已停止") 