import os
import cv2
import json
import time
import base64
import threading
import queue
import logging
from datetime import datetime
from collections import deque
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import psutil
import numpy as np

from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS

from advanced_face_recognition import AdvancedFaceRecognitionSystem

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    fps: float = 0.0
    processing_time: float = 0.0
    queue_size: int = 0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    total_frames: int = 0
    dropped_frames: int = 0
    recognition_accuracy: float = 0.0
    last_update: float = 0.0

@dataclass
class VideoFrame:
    """视频帧数据类"""
    frame: np.ndarray
    timestamp: float
    frame_id: int
    metadata: Dict[str, Any] = None

class OptimizedCameraManager:
    """优化的摄像头管理器"""
    
    def __init__(self, camera_index: int = 0, target_fps: int = 30):
        self.camera_index = camera_index
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.capture_thread: Optional[threading.Thread] = None
        
        # 帧队列 - 使用有限队列避免内存膨胀
        self.frame_queue = queue.Queue(maxsize=5)
        self.latest_frame: Optional[VideoFrame] = None
        
        # 性能监控
        self.metrics = PerformanceMetrics()
        self.fps_counter = deque(maxlen=30)  # 最近30帧用于计算FPS
        self.frame_counter = 0
        
        # 线程锁
        self.lock = threading.RLock()
        
    def start(self) -> bool:
        """启动摄像头"""
        try:
            if self.is_running:
                logger.warning("摄像头已在运行")
                return True
                
            # 初始化摄像头
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                logger.error(f"无法打开摄像头 {self.camera_index}")
                return False
            
            # 设置摄像头参数
            self._configure_camera()
            
            # 启动捕获线程
            self.is_running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            logger.info(f"摄像头 {self.camera_index} 启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动摄像头失败: {e}")
            return False
    
    def stop(self):
        """停止摄像头"""
        try:
            self.is_running = False
            
            if self.capture_thread:
                self.capture_thread.join(timeout=2.0)
                
            if self.cap:
                self.cap.release()
                self.cap = None
                
            # 清空队列
            while not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    break
                    
            logger.info("摄像头已停止")
            
        except Exception as e:
            logger.error(f"停止摄像头时出错: {e}")
    
    def _configure_camera(self):
        """配置摄像头参数"""
        if not self.cap:
            return
            
        # 设置分辨率 - 根据性能自适应
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # 设置FPS
        self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        
        # 设置缓冲区大小 - 减少延迟
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # 获取实际设置的参数
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        logger.info(f"摄像头配置: {actual_width}x{actual_height} @ {actual_fps}fps")
    
    def _capture_loop(self):
        """摄像头捕获循环"""
        last_capture_time = 0
        
        while self.is_running and self.cap:
            try:
                current_time = time.time()
                
                # 帧率控制
                if current_time - last_capture_time < self.frame_interval:
                    time.sleep(0.001)  # 短暂休眠
                    continue
                
                # 捕获帧
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    logger.warning("无法从摄像头读取帧")
                    self._handle_capture_error()
                    continue
                
                # 创建视频帧对象
                video_frame = VideoFrame(
                    frame=frame.copy(),
                    timestamp=current_time,
                    frame_id=self.frame_counter,
                    metadata={'capture_time': current_time}
                )
                
                # 更新最新帧
                with self.lock:
                    self.latest_frame = video_frame
                    self.frame_counter += 1
                
                # 尝试将帧放入队列
                try:
                    self.frame_queue.put_nowait(video_frame)
                except queue.Full:
                    # 队列满时丢弃最旧的帧
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(video_frame)
                        self.metrics.dropped_frames += 1
                    except queue.Empty:
                        pass
                
                # 更新性能指标
                self._update_performance_metrics(current_time)
                last_capture_time = current_time
                
            except Exception as e:
                logger.error(f"捕获循环错误: {e}")
                time.sleep(0.1)
    
    def _handle_capture_error(self):
        """处理捕获错误 - 尝试重新连接"""
        logger.warning("检测到捕获错误，尝试重新连接摄像头...")
        
        if self.cap:
            self.cap.release()
            
        time.sleep(1.0)  # 等待一秒后重试
        
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if self.cap and self.cap.isOpened():
            self._configure_camera()
            logger.info("摄像头重新连接成功")
        else:
            logger.error("摄像头重新连接失败")
    
    def _update_performance_metrics(self, current_time: float):
        """更新性能指标"""
        self.fps_counter.append(current_time)
        
        # 计算FPS
        if len(self.fps_counter) > 1:
            time_span = self.fps_counter[-1] - self.fps_counter[0]
            if time_span > 0:
                self.metrics.fps = (len(self.fps_counter) - 1) / time_span
        
        # 更新其他指标
        self.metrics.queue_size = self.frame_queue.qsize()
        self.metrics.total_frames = self.frame_counter
        self.metrics.last_update = current_time
        
        # 每秒更新一次系统资源指标
        if current_time - self.metrics.last_update > 1.0:
            try:
                process = psutil.Process()
                self.metrics.memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                self.metrics.cpu_usage = process.cpu_percent()
            except:
                pass
    
    def get_latest_frame(self) -> Optional[VideoFrame]:
        """获取最新帧"""
        with self.lock:
            return self.latest_frame
    
    def get_frame_for_processing(self) -> Optional[VideoFrame]:
        """获取用于处理的帧"""
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_metrics(self) -> PerformanceMetrics:
        """获取性能指标"""
        return self.metrics
    
    def switch_camera(self, new_index: int) -> bool:
        """切换摄像头"""
        try:
            was_running = self.is_running
            
            if was_running:
                self.stop()
                time.sleep(0.5)  # 等待完全停止
            
            self.camera_index = new_index
            
            if was_running:
                return self.start()
            
            return True
            
        except Exception as e:
            logger.error(f"切换摄像头失败: {e}")
            return False

class OptimizedWebFaceRecognitionSystem:
    """优化的Web人脸识别系统"""
    
    def __init__(self):
        self.face_system = AdvancedFaceRecognitionSystem()
        self.camera_manager = OptimizedCameraManager()
        
        # 处理线程
        self.processing_thread: Optional[threading.Thread] = None
        self.is_processing = False
        
        # 结果缓存
        self.latest_results: Dict[str, Any] = {}
        self.results_lock = threading.RLock()
        
        # 自动抓拍功能
        self.auto_capture_targets = set()
        self.capture_cooldown = {}
        self.capture_interval = 5
        self.capture_history = []
        
        # 创建目录
        self.auto_capture_dir = os.path.join(self.face_system.script_dir, "auto_captures")
        os.makedirs(self.auto_capture_dir, exist_ok=True)
        
        # 性能统计
        self.processing_times = deque(maxlen=50)
        
    def start_recognition(self) -> bool:
        """启动识别系统"""
        try:
            # 启动摄像头
            if not self.camera_manager.start():
                return False
            
            # 启动处理线程
            self.is_processing = True
            self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self.processing_thread.start()
            
            logger.info("识别系统启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动识别系统失败: {e}")
            return False
    
    def stop_recognition(self):
        """停止识别系统"""
        try:
            self.is_processing = False
            
            if self.processing_thread:
                self.processing_thread.join(timeout=2.0)
            
            self.camera_manager.stop()
            
            logger.info("识别系统已停止")
            
        except Exception as e:
            logger.error(f"停止识别系统失败: {e}")
    
    def _processing_loop(self):
        """处理循环"""
        while self.is_processing:
            try:
                # 获取待处理的帧
                video_frame = self.camera_manager.get_frame_for_processing()
                if video_frame is None:
                    time.sleep(0.01)
                    continue
                
                start_time = time.time()
                
                # 进行人脸检测和识别
                results = self._process_frame(video_frame)
                
                # 检查自动抓拍
                if results['face_names']:
                    self._check_auto_capture(video_frame.frame, results)
                
                # 更新结果缓存
                with self.results_lock:
                    self.latest_results = results
                
                # 更新处理时间统计
                processing_time = time.time() - start_time
                self.processing_times.append(processing_time)
                
                # 更新摄像头性能指标
                metrics = self.camera_manager.get_metrics()
                metrics.processing_time = processing_time
                
            except Exception as e:
                logger.error(f"处理循环错误: {e}")
                time.sleep(0.1)
    
    def _process_frame(self, video_frame: VideoFrame) -> Dict[str, Any]:
        """处理单帧"""
        frame = video_frame.frame
        
        # 人脸检测
        face_locations = self.face_system.detect_faces_yolo(frame)
        face_names = []
        face_emotions = []
        
        if face_locations:
            # 转换色彩空间
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 人脸识别
            face_names = self.face_system.recognize_faces(rgb_frame, face_locations)
            
            # 情绪分析（可以选择性禁用以提高性能）
            try:
                face_emotions = self.face_system._analyze_emotions(frame, face_locations)
            except Exception as e:
                logger.warning(f"情绪分析失败: {e}")
                face_emotions = [""] * len(face_locations)
        
        return {
            'face_locations': face_locations,
            'face_names': face_names,
            'face_emotions': face_emotions,
            'face_count': len(face_locations),
            'timestamp': video_frame.timestamp,
            'frame_id': video_frame.frame_id
        }
    
    def _check_auto_capture(self, frame: np.ndarray, results: Dict[str, Any]):
        """检查自动抓拍"""
        if not self.auto_capture_targets:
            return
        
        current_time = time.time()
        
        for i, name in enumerate(results['face_names']):
            if name in self.auto_capture_targets:
                last_capture_time = self.capture_cooldown.get(name, 0)
                if current_time - last_capture_time >= self.capture_interval:
                    self._capture_person(frame, results, i, name)
                    self.capture_cooldown[name] = current_time
    
    def _capture_person(self, frame: np.ndarray, results: Dict[str, Any], person_index: int, person_name: str):
        """自动抓拍人员"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            emotion = results['face_emotions'][person_index] if person_index < len(results['face_emotions']) else "unknown"
            
            filename = f"auto_capture_{person_name}_{emotion}_{timestamp}.jpg"
            filepath = os.path.join(self.auto_capture_dir, filename)
            
            # 保存高质量图片
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            # 记录抓拍历史
            capture_record = {
                'person_name': person_name,
                'emotion': emotion,
                'timestamp': datetime.now().isoformat(),
                'filename': filename,
                'filepath': filepath
            }
            
            self.capture_history.append(capture_record)
            
            # 保持历史记录数量
            if len(self.capture_history) > 200:
                self.capture_history = self.capture_history[-200:]
            
            logger.info(f"自动抓拍: {person_name} ({emotion}) -> {filename}")
            
        except Exception as e:
            logger.error(f"自动抓拍失败: {e}")
    
    def generate_video_stream(self):
        """生成优化的视频流"""
        while True:
            try:
                # 获取最新帧
                video_frame = self.camera_manager.get_latest_frame()
                if video_frame is None:
                    time.sleep(0.033)  # ~30fps
                    continue
                
                frame = video_frame.frame.copy()
                
                # 获取最新识别结果
                with self.results_lock:
                    results = self.latest_results.copy()
                
                # 在帧上绘制结果
                if results:
                    frame = self._draw_results_on_frame(frame, results)
                
                # 绘制性能指标
                frame = self._draw_performance_overlay(frame)
                
                # 编码为JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                ret, buffer = cv2.imencode('.jpg', frame, encode_param)
                
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
            except Exception as e:
                logger.error(f"视频流生成错误: {e}")
                time.sleep(0.1)
    
    def _draw_results_on_frame(self, frame: np.ndarray, results: Dict[str, Any]) -> np.ndarray:
        """在帧上绘制识别结果"""
        face_locations = results.get('face_locations', [])
        face_names = results.get('face_names', [])
        face_emotions = results.get('face_emotions', [])
        
        for i, (top, right, bottom, left) in enumerate(face_locations):
            # 获取信息
            name = face_names[i] if i < len(face_names) else "Unknown"
            emotion = face_emotions[i] if i < len(face_emotions) else ""
            
            # 设置颜色
            if name != "未知":
                color = (0, 255, 0)  # 绿色 - 识别成功
                if name in self.auto_capture_targets:
                    color = (255, 165, 0)  # 橙色 - 自动抓拍目标
            else:
                color = (0, 0, 255)  # 红色 - 未知人员
            
            # 绘制人脸框
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # 准备显示文本
            display_text = name
            if emotion:
                display_text = f"{name} ({emotion})"
            if name in self.auto_capture_targets:
                display_text += " [AUTO]"
            
            # 绘制标签
            label_size = cv2.getTextSize(display_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame, (left, bottom - 35), (left + label_size[0] + 10, bottom), color, cv2.FILLED)
            cv2.putText(frame, display_text, (left + 5, bottom - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def _draw_performance_overlay(self, frame: np.ndarray) -> np.ndarray:
        """绘制性能叠加信息"""
        metrics = self.camera_manager.get_metrics()
        
        # 创建半透明背景
        overlay = frame.copy()
        h, w = frame.shape[:2]
        cv2.rectangle(overlay, (w - 200, 10), (w - 10, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # 绘制性能信息
        info_lines = [
            f"FPS: {metrics.fps:.1f}",
            f"Queue: {metrics.queue_size}",
            f"Frames: {metrics.total_frames}",
            f"Dropped: {metrics.dropped_frames}",
        ]
        
        for i, line in enumerate(info_lines):
            y_pos = 30 + i * 20
            cv2.putText(frame, line, (w - 190, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return frame
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        metrics = self.camera_manager.get_metrics()
        
        # 计算平均处理时间
        avg_processing_time = 0
        if self.processing_times:
            avg_processing_time = sum(self.processing_times) / len(self.processing_times)
        
        with self.results_lock:
            results = self.latest_results.copy()
        
        return {
            'is_running': self.is_processing,
            'camera_fps': metrics.fps,
            'processing_time_ms': avg_processing_time * 1000,
            'queue_size': metrics.queue_size,
            'memory_usage_mb': metrics.memory_usage,
            'cpu_usage_percent': metrics.cpu_usage,
            'total_frames': metrics.total_frames,
            'dropped_frames': metrics.dropped_frames,
            'results': results,
            'auto_capture_targets': list(self.auto_capture_targets)
        }

# 创建全局系统实例
web_system = OptimizedWebFaceRecognitionSystem()

# Flask 路由（保持原有API接口）
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(web_system.generate_video_stream(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/start_recognition', methods=['POST'])
def start_recognition():
    if web_system.start_recognition():
        return jsonify({'status': 'success', 'message': '人脸识别已启动'})
    return jsonify({'status': 'error', 'message': '启动失败'})

@app.route('/api/stop_recognition', methods=['POST'])
def stop_recognition():
    web_system.stop_recognition()
    return jsonify({'status': 'success', 'message': '人脸识别已停止'})

@app.route('/api/recognition_status')
def recognition_status():
    return jsonify(web_system.get_system_status())

@app.route('/api/database_info')
def database_info():
    known_names = list(set(web_system.face_system.known_face_names))
    return jsonify({
        'known_people': known_names,
        'total_people': len(known_names),
        'total_features': len(web_system.face_system.known_face_encodings)
    })

@app.route('/api/update_database', methods=['POST'])
def update_database():
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
    return jsonify({
        'history': web_system.capture_history[-50:],
        'total_captures': len(web_system.capture_history)
    })

@app.route('/api/manual_capture', methods=['POST'])
def manual_capture():
    video_frame = web_system.camera_manager.get_latest_frame()
    if video_frame:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"manual_capture_{timestamp}.jpg"
        filepath = os.path.join(web_system.auto_capture_dir, filename)
        
        cv2.imwrite(filepath, video_frame.frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return jsonify({'status': 'success', 'message': f'手动抓拍成功: {filename}'})
    
    return jsonify({'status': 'error', 'message': '无法获取当前画面'})

@app.route('/api/switch_camera', methods=['POST'])
def switch_camera():
    data = request.get_json()
    camera_index = data.get('camera_index', 0)
    
    if web_system.camera_manager.switch_camera(camera_index):
        return jsonify({'status': 'success', 'message': f'已切换到摄像头 {camera_index}'})
    return jsonify({'status': 'error', 'message': '切换摄像头失败'})

if __name__ == '__main__':
    print("🚀 正在启动优化版Web人脸识别系统...")
    print("📱 请在浏览器中访问: http://localhost:5000")
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n正在优雅关闭系统...")
        web_system.stop_recognition()
        print("👋 系统已安全停止") 