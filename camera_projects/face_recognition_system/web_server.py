import os
import cv2
import json
import time
import base64
from datetime import datetime
from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
from threading import Thread, Event
import queue
import logging

from advanced_face_recognition import AdvancedFaceRecognitionSystem

app = Flask(__name__)
CORS(app)

# 配置日志
logging.basicConfig(level=logging.INFO)

class WebFaceRecognitionSystem:
    def __init__(self):
        self.face_system = AdvancedFaceRecognitionSystem()
        self.is_running = False
        self.current_frame = None
        self.recognition_results = []
        self.frame_queue = queue.Queue(maxsize=2)
        self.auto_capture_targets = set()  # 需要自动抓拍的人员名单
        self.capture_cooldown = {}  # 抓拍冷却时间（避免连续抓拍同一人）
        self.capture_interval = 5  # 对同一人的抓拍间隔（秒）
        self.capture_history = []  # 抓拍历史记录
        
        # 创建抓拍保存目录
        self.auto_capture_dir = os.path.join(self.face_system.script_dir, "auto_captures")
        os.makedirs(self.auto_capture_dir, exist_ok=True)
        
    def generate_frames(self):
        """生成视频流帧"""
        cap = cv2.VideoCapture(self.face_system.current_camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return
            
        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                break
                
            # 进行人脸检测和识别
            results = self.process_frame(frame)
            
            # 检查是否需要自动抓拍
            self.check_auto_capture(frame, results)
            
            # 在帧上绘制识别结果
            frame = self.draw_results_on_frame(frame, results)
            
            # 编码为JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        cap.release()
        
    def process_frame(self, frame):
        """处理单帧，返回识别结果"""
        face_locations = self.face_system.detect_faces_yolo(frame)
        face_names = []
        face_emotions = []
        
        if face_locations:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_names = self.face_system.recognize_faces(rgb_frame, face_locations)
            face_emotions = self.face_system._analyze_emotions(frame, face_locations)
        
        results = {
            'face_locations': face_locations,
            'face_names': face_names,
            'face_emotions': face_emotions,
            'face_count': len(face_locations),
            'timestamp': datetime.now().isoformat()
        }
        
        self.recognition_results = results
        return results
    
    def check_auto_capture(self, frame, results):
        """检查是否需要自动抓拍"""
        if not self.auto_capture_targets:
            return
            
        current_time = time.time()
        
        for i, name in enumerate(results['face_names']):
            if name in self.auto_capture_targets:
                # 检查冷却时间
                last_capture_time = self.capture_cooldown.get(name, 0)
                if current_time - last_capture_time >= self.capture_interval:
                    self.capture_person(frame, results, i, name)
                    self.capture_cooldown[name] = current_time
    
    def capture_person(self, frame, results, person_index, person_name):
        """自动抓拍指定人员"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            emotion = results['face_emotions'][person_index] if person_index < len(results['face_emotions']) else "unknown"
            
            filename = f"auto_capture_{person_name}_{emotion}_{timestamp}.jpg"
            filepath = os.path.join(self.auto_capture_dir, filename)
            
            cv2.imwrite(filepath, frame)
            
            # 记录抓拍历史
            capture_record = {
                'person_name': person_name,
                'emotion': emotion,
                'timestamp': datetime.now().isoformat(),
                'filename': filename,
                'filepath': filepath
            }
            self.capture_history.append(capture_record)
            
            # 保持历史记录在合理范围内
            if len(self.capture_history) > 100:
                self.capture_history = self.capture_history[-100:]
                
            app.logger.info(f"自动抓拍: {person_name} ({emotion}) -> {filename}")
            
        except Exception as e:
            app.logger.error(f"自动抓拍失败: {e}")
    
    def draw_results_on_frame(self, frame, results):
        """在帧上绘制识别结果"""
        face_locations = results['face_locations']
        face_names = results['face_names']
        face_emotions = results['face_emotions']
        
        for i, (top, right, bottom, left) in enumerate(face_locations):
            # 获取人名和情绪
            name = face_names[i] if i < len(face_names) else "Unknown"
            emotion = face_emotions[i] if i < len(face_emotions) else ""
            
            # 绘制人脸框
            color = (0, 255, 0) if name != "未知" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # 准备显示文本
            display_text = name
            if emotion:
                display_text = f"{name} ({emotion})"
                
            # 如果是自动抓拍目标，添加特殊标记
            if name in self.auto_capture_targets:
                display_text += " [AUTO]"
                
            # 绘制标签背景
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            
            # 绘制文本
            cv2.putText(frame, display_text, (left + 6, bottom - 6), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        return frame

# 创建全局Web系统实例
web_system = WebFaceRecognitionSystem()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """视频流端点"""
    return Response(web_system.generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/start_recognition', methods=['POST'])
def start_recognition():
    """启动人脸识别"""
    if not web_system.is_running:
        web_system.is_running = True
        return jsonify({'status': 'success', 'message': '人脸识别已启动'})
    return jsonify({'status': 'error', 'message': '人脸识别已在运行'})

@app.route('/api/stop_recognition', methods=['POST'])
def stop_recognition():
    """停止人脸识别"""
    web_system.is_running = False
    return jsonify({'status': 'success', 'message': '人脸识别已停止'})

@app.route('/api/recognition_status')
def recognition_status():
    """获取识别状态"""
    return jsonify({
        'is_running': web_system.is_running,
        'results': web_system.recognition_results,
        'auto_capture_targets': list(web_system.auto_capture_targets)
    })

@app.route('/api/database_info')
def database_info():
    """获取数据库信息"""
    known_names = list(set(web_system.face_system.known_face_names))
    return jsonify({
        'known_people': known_names,
        'total_people': len(known_names),
        'total_features': len(web_system.face_system.known_face_encodings)
    })

@app.route('/api/update_database', methods=['POST'])
def update_database():
    """更新人脸数据库"""
    data = request.get_json()
    augment = data.get('augment', False)
    
    try:
        web_system.face_system.rescan_and_encode_database(augment=augment)
        web_system.face_system.load_face_database()
        return jsonify({'status': 'success', 'message': '数据库更新成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'数据库更新失败: {str(e)}'})

@app.route('/api/auto_capture_targets', methods=['GET', 'POST'])
def auto_capture_targets():
    """管理自动抓拍目标"""
    if request.method == 'GET':
        return jsonify({'targets': list(web_system.auto_capture_targets)})
    
    elif request.method == 'POST':
        data = request.get_json()
        action = data.get('action')
        person_name = data.get('person_name')
        
        if action == 'add' and person_name:
            web_system.auto_capture_targets.add(person_name)
            return jsonify({'status': 'success', 'message': f'已添加 {person_name} 到自动抓拍列表'})
        
        elif action == 'remove' and person_name:
            web_system.auto_capture_targets.discard(person_name)
            return jsonify({'status': 'success', 'message': f'已从自动抓拍列表移除 {person_name}'})
        
        elif action == 'clear':
            web_system.auto_capture_targets.clear()
            return jsonify({'status': 'success', 'message': '已清空自动抓拍列表'})
        
        return jsonify({'status': 'error', 'message': '无效的操作'})

@app.route('/api/capture_history')
def capture_history():
    """获取抓拍历史"""
    return jsonify({
        'history': web_system.capture_history[-50:],  # 返回最近50条记录
        'total_captures': len(web_system.capture_history)
    })

@app.route('/api/manual_capture', methods=['POST'])
def manual_capture():
    """手动抓拍"""
    if web_system.current_frame is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"manual_capture_{timestamp}.jpg"
        filepath = os.path.join(web_system.auto_capture_dir, filename)
        
        cv2.imwrite(filepath, web_system.current_frame)
        return jsonify({'status': 'success', 'message': f'手动抓拍成功: {filename}'})
    
    return jsonify({'status': 'error', 'message': '无法获取当前画面'})

@app.route('/api/switch_camera', methods=['POST'])
def switch_camera():
    """切换摄像头"""
    try:
        web_system.face_system._switch_camera()
        return jsonify({'status': 'success', 'message': f'已切换到摄像头 {web_system.face_system.current_camera_index}'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'切换摄像头失败: {str(e)}'})

if __name__ == '__main__':
    print("🌐 正在启动Web人脸识别系统...")
    print("📱 请在浏览器中访问: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True) 