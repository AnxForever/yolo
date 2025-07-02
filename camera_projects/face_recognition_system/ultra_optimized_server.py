import os
import cv2
import time
import threading
import queue
from datetime import datetime
from flask import Flask, render_template, Response, jsonify, request, make_response
from flask_cors import CORS

from advanced_face_recognition import AdvancedFaceRecognitionSystem

app = Flask(__name__)
CORS(app)

class UltraOptimizedSystem:
    def __init__(self):
        print("⚡ 超级优化系统初始化...")
        self.face_system = AdvancedFaceRecognitionSystem()
        
        # 摄像头设置
        self.cap = None
        self.is_running = False
        self.camera_index = 0 # 跟踪当前摄像头索引
        
        # 双缓冲机制
        self.display_frame = None
        self.processing_frame = None
        self.frame_lock = threading.RLock()
        
        # 识别结果
        self.latest_results = {
            'face_count': 0,
            'face_names': [],
            'face_emotions': [],
            'face_locations': []
        }
        
        # 性能优化设置
        self.process_every_n_frames = 15  # 每15帧处理一次（大幅提升流畅度）
        self.frame_count = 0
        self.last_process_time = 0
        self.min_process_interval = 0.5  # 最小处理间隔0.5秒
        
        # 情绪检测开关
        self.emotion_detection_enabled = False  # 默认关闭以获得最佳性能
        self.emotion_detection_frequency = 30   # 情绪检测频率（每N帧检测一次）
        self.last_known_emotions = []  # 储存最近一次成功的情绪分析结果
        
        # 自动抓拍
        self.auto_capture_targets = set()
        self.capture_cooldown = {}
        self.capture_interval = 5
        self.capture_history = []
        
        # 目录
        self.auto_capture_dir = os.path.join(self.face_system.script_dir, "auto_captures")
        os.makedirs(self.auto_capture_dir, exist_ok=True)
        
        # FPS统计
        self.fps = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        
        # 处理线程
        self.processing_thread = None
        self.process_queue = queue.Queue(maxsize=2)
        
        print("✅ 超级优化系统就绪")
    
    def start_camera(self, camera_index=0):
        """启动高性能摄像头"""
        try:
            if self.is_running:
                return True
            
            print(f"📹 尝试启动摄像头 #{camera_index}...")
            
            # 尝试不同的后端
            for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
                self.cap = cv2.VideoCapture(camera_index, backend)
                if self.cap and self.cap.isOpened():
                    break
                if self.cap:
                    self.cap.release()
            
            if not self.cap or not self.cap.isOpened():
                print(f"❌ 摄像头 #{camera_index} 启动失败")
                return False
            
            self.camera_index = camera_index # 更新当前摄像头索引
            
            # 高性能摄像头配置
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)   # 更高分辨率
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)        # 最小缓冲
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M','J','P','G'))  # MJPEG编码
            
            # 获取实际设置
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            print(f"✅ 摄像头配置: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            self.is_running = True
            
            # 启动异步处理线程
            self.processing_thread = threading.Thread(target=self._async_processing_loop, daemon=True)
            self.processing_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ 摄像头启动失败: {e}")
            return False
    
    def stop_camera(self):
        """停止摄像头"""
        self.is_running = False
        
        if self.processing_thread:
            # self.processing_thread.join(timeout=1.0)
            pass # Let it terminate on its own
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        print("🛑 摄像头已停止")
    
    def switch_camera(self):
        """切换到下一个可用的摄像头"""
        print("🔄 正在切换摄像头...")
        self.stop_camera()
        time.sleep(0.5) # 给点时间释放资源
        
        # 尝试启动下一个摄像头，如果失败再试下一个，最多试4个
        for i in range(1, 5):
            next_index = (self.camera_index + i) % 5 
            if self.start_camera(next_index):
                print(f"✅ 成功切换到摄像头 #{self.camera_index}")
                return True
        
        print("❌ 未找到其他可用摄像头，将尝试重启默认摄像头")
        self.start_camera(0) # 如果都失败，回到默认
        return False
    
    def _async_processing_loop(self):
        """异步处理循环 - 独立线程"""
        while self.is_running:
            try:
                # 从队列获取帧进行处理
                frame_data = self.process_queue.get(timeout=1.0)
                if frame_data is None:
                    continue
                
                frame, frame_id = frame_data # 拆包，获取帧和它自己的ID
                current_time = time.time()
                
                # 时间间隔控制
                if current_time - self.last_process_time < self.min_process_interval:
                    continue
                
                # 进行人脸检测和识别，传入正确的帧ID
                results = self._process_frame_heavy(frame, frame_id)
                
                # 更新结果
                with self.frame_lock:
                    self.latest_results = results
                    self.last_process_time = current_time
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ 异步处理错误: {e}")
                time.sleep(0.1)
    
    def _process_frame_heavy(self, frame, frame_id):
        """重度处理 - 在异步线程中执行"""
        try:
            # 人脸检测
            face_locations = self.face_system.detect_faces_yolo(frame)
            face_names = []
            face_emotions = []
            
            if face_locations:
                # 转换颜色空间
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 人脸识别
                face_names = self.face_system.recognize_faces(rgb_frame, face_locations)
                
                # 如果检测到的人脸数量与记忆中的数量不符，则清空记忆，防止数据错乱
                if len(face_locations) != len(self.last_known_emotions):
                    self.last_known_emotions = []

                # 智能情绪分析：使用传入的frame_id进行判断
                if self.emotion_detection_enabled and frame_id % self.emotion_detection_frequency == 0 and face_locations:
                    try:
                        # 分析并更新"记忆芯片"
                        analyzed_emotions = self.face_system._analyze_emotions(frame, face_locations)
                        self.last_known_emotions = analyzed_emotions
                        print(f"😊 情绪记忆已更新: {self.last_known_emotions}")
                    except Exception as e:
                        print(f"⚠️ 情绪检测失败，清空记忆: {e}")
                        self.last_known_emotions = [] # 分析失败时也清空

                # 最终结果：始终使用"记忆芯片"里的数据
                face_emotions = self.last_known_emotions
            
            # 检查自动抓拍
            if face_names:
                self._check_auto_capture(frame, face_names, face_emotions)
            
            return {
                'face_count': len(face_locations),
                'face_names': face_names,
                'face_emotions': face_emotions,
                'face_locations': face_locations
            }
            
        except Exception as e:
            print(f"❌ 重度处理错误: {e}")
            return {
                'face_count': 0,
                'face_names': [],
                'face_emotions': [],
                'face_locations': []
            }
    
    def generate_frames(self):
        """超高性能视频流生成"""
        if not self.start_camera():
            return
        
        print("🎬 启动超高性能视频流...")
        
        while self.is_running and self.cap:
            try:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    print("⚠️ 读取帧失败")
                    time.sleep(0.01)
                    continue
                
                # 更新显示帧
                with self.frame_lock:
                    self.display_frame = frame.copy()
                
                self.frame_count += 1
                
                # 智能处理调度
                current_time = time.time()
                should_process = (
                    self.frame_count % self.process_every_n_frames == 0 and
                    current_time - self.last_process_time >= self.min_process_interval
                )
                
                if should_process:
                    # 异步提交处理任务
                    try:
                        frame_copy = frame.copy()
                        self.process_queue.put_nowait((frame_copy, self.frame_count))
                    except queue.Full:
                        pass  # 队列满时丢弃，保持流畅度
                
                # 绘制结果到显示帧
                display_frame = self._draw_lightweight_results(frame)
                
                # 高质量编码
                encode_params = [
                    cv2.IMWRITE_JPEG_QUALITY, 90,  # 提高质量
                    cv2.IMWRITE_JPEG_OPTIMIZE, 1,  # 优化编码
                ]
                
                ret, buffer = cv2.imencode('.jpg', display_frame, encode_params)
                
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                # 简单的帧率控制
                time.sleep(0.001)  # 微小延迟，避免CPU占用过高
                
            except Exception as e:
                print(f"❌ 视频流错误: {e}")
                time.sleep(0.05)
        
        print("🏁 视频流已停止")
    
    def _draw_lightweight_results(self, frame):
        """轻量级结果绘制"""
        with self.frame_lock:
            results = self.latest_results.copy()
        
        face_locations = results.get('face_locations', [])
        face_names = results.get('face_names', [])
        face_emotions = results.get('face_emotions', [])
        
        # 绘制人脸框和标签
        for i, (top, right, bottom, left) in enumerate(face_locations):
            name = face_names[i] if i < len(face_names) else "Unknown"
            emotion = face_emotions[i] if i < len(face_emotions) else ""
            
            # 设置颜色
            if name != "未知":
                color = (0, 255, 0)
                if name in self.auto_capture_targets:
                    color = (255, 165, 0)  # 橙色 - 自动抓拍目标
            else:
                color = (0, 0, 255)
            
            # 绘制人脸框 - 加粗
            cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
            
            # 准备文本
            display_text = name
            if emotion:
                display_text = f"{name} ({emotion})"
            if name in self.auto_capture_targets:
                display_text += " [AUTO]"
            
            # 计算文本大小
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            thickness = 2
            (text_width, text_height), _ = cv2.getTextSize(display_text, font, font_scale, thickness)
            
            # 绘制文本背景
            cv2.rectangle(frame, (left, bottom - text_height - 10), 
                         (left + text_width + 10, bottom), color, cv2.FILLED)
            
            # 绘制文本
            cv2.putText(frame, display_text, (left + 5, bottom - 5), 
                       font, font_scale, (255, 255, 255), thickness)
        
        return frame
    
    def _check_auto_capture(self, frame, face_names, face_emotions):
        """自动抓拍检查"""
        if not self.auto_capture_targets:
            return
        
        current_time = time.time()
        
        for i, name in enumerate(face_names):
            if name in self.auto_capture_targets:
                last_capture = self.capture_cooldown.get(name, 0)
                if current_time - last_capture >= self.capture_interval:
                    emotion = face_emotions[i] if i < len(face_emotions) else ""
                    self._capture_person(frame, name, emotion)
                    self.capture_cooldown[name] = current_time
    
    def _capture_person(self, frame, person_name, emotion):
        """自动抓拍"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ultra_capture_{person_name}_{emotion}_{timestamp}.jpg"
            filepath = os.path.join(self.auto_capture_dir, filename)
            
            # 高质量保存
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
            
            print(f"📸 超级抓拍: {person_name} ({emotion})")
            
        except Exception as e:
            print(f"❌ 抓拍失败: {e}")

# 全局系统实例
system = UltraOptimizedSystem()

# Flask路由
@app.route('/')
def index():
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/video_feed')
def video_feed():
    print("🎥 请求超级视频流...")
    return Response(system.generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/start_recognition', methods=['POST'])
def start_recognition():
    if system.start_camera(system.camera_index):
        return jsonify({'status': 'success', 'message': '超级识别已启动'})
    return jsonify({'status': 'error', 'message': '启动失败'})

@app.route('/api/stop_recognition', methods=['POST'])
def stop_recognition():
    system.stop_camera()
    return jsonify({'status': 'success', 'message': '识别已停止'})

@app.route('/api/switch_camera', methods=['POST'])
def switch_camera():
    """切换摄像头"""
    if system.switch_camera():
        return jsonify({'status': 'success', 'message': f'已成功切换到摄像头 {system.camera_index}'})
    return jsonify({'status': 'error', 'message': '切换摄像头失败'})

@app.route('/api/recognition_status')
def recognition_status():
    return jsonify({
        'is_running': system.is_running,
        'results': system.latest_results,
        'auto_capture_targets': list(system.auto_capture_targets),
        'fps': system.fps,
        'emotion_detection_enabled': system.emotion_detection_enabled,
        'emotion_detection_frequency': system.emotion_detection_frequency
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
    data = request.get_json(silent=True) or {}
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
    
    data = request.get_json(silent=True) or {}
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
    if system.display_frame is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ultra_manual_{timestamp}.jpg"
        filepath = os.path.join(system.auto_capture_dir, filename)
        
        cv2.imwrite(filepath, system.display_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return jsonify({'status': 'success', 'message': f'超级抓拍: {filename}'})
    
    return jsonify({'status': 'error', 'message': '无法获取画面'})

# 情绪分析控制端点
@app.route('/api/toggle_emotion', methods=['POST'])
def toggle_emotion():
    """切换情绪分析开关"""
    try:
        data = request.get_json(silent=True) or {}
        action = data.get('action', 'toggle')
        
        if action == 'toggle':
            system.emotion_detection_enabled = not system.emotion_detection_enabled
        elif action == 'enable':
            system.emotion_detection_enabled = True
        elif action == 'disable':
            system.emotion_detection_enabled = False
        else:
            return jsonify({'status': 'error', 'message': '无效的操作'})
        
        status_text = "已启用" if system.emotion_detection_enabled else "已禁用"
        performance_note = "" if system.emotion_detection_enabled else " (性能模式)"
        
        return jsonify({
            'status': 'success', 
            'message': f'情绪检测{status_text}{performance_note}',
            'emotion_detection_enabled': system.emotion_detection_enabled
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'设置失败: {str(e)}'})

@app.route('/api/emotion_settings', methods=['GET', 'POST'])
def emotion_settings():
    """情绪检测设置"""
    if request.method == 'GET':
        return jsonify({
            'emotion_detection_enabled': system.emotion_detection_enabled,
            'emotion_detection_frequency': system.emotion_detection_frequency,
            'performance_impact': '高' if system.emotion_detection_frequency < 20 else '中' if system.emotion_detection_frequency < 40 else '低'
        })
    
    try:
        data = request.get_json(silent=True) or {}
        
        if 'frequency' in data:
            frequency = int(data['frequency'])
            if 10 <= frequency <= 60:
                system.emotion_detection_frequency = frequency
                impact = '高' if frequency < 20 else '中' if frequency < 40 else '低'
                return jsonify({
                    'status': 'success', 
                    'message': f'检测频率已设置为每{frequency}帧 (性能影响: {impact})',
                    'emotion_detection_frequency': system.emotion_detection_frequency
                })
            else:
                return jsonify({'status': 'error', 'message': '频率必须在10-60之间'})
        
        return jsonify({'status': 'error', 'message': '缺少有效参数'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'设置失败: {str(e)}'})

if __name__ == '__main__':
    print("🚀 启动超级优化版服务器...")
    print("⚡ 专注于流畅度和画质")
    print("📱 访问: http://localhost:5000")
    print("="*50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n正在停止...")
        system.stop_camera()
        print("👋 已停止") 