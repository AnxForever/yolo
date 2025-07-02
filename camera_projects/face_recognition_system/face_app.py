"""
Ultralytics YOLOv8 实时摄像头人脸检测脚本
帅哥专属版本 - 启动你的AI人脸识别之眼！
"""
import cv2
import os
from datetime import datetime
from ultralytics import YOLO
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
from tkinter import filedialog  # 修正导入方式
import time

class FaceApp(tk.Tk):
    """
    一个专业的多模式人脸检测与计数应用类。
    它能够智能识别输入源是实时摄像头、单个图片还是图片文件夹，
    并自动切换到对应的处理模式。
    """

    def __init__(self):
        """
        初始化FaceApp应用。
        """
        super().__init__()  # 先调用父类的构造函数
        
        self.title("AI人脸检测应用 | 专属模型版")
        
        # --- 让脚本变得"智能"，自动计算模型文件的绝对路径 ---
        # 1. 获取当前脚本文件所在的目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. 定义模型的相对路径 (相对于脚本的位置)
        relative_model_path = 'D:/YOLO/ultralytics/runs/detect/wider_full_training_20250630_234750/weights/best.pt'
        
        # 3. 将脚本目录和相对路径拼接成一个永远正确的绝对路径
        self.model_path = os.path.join(script_dir, relative_model_path)
        
        print(f"正在加载你的专属模型 '{self.model_path}'...")
        
        # 新增：实时检测状态
        self.is_realtime_running = False
        
        try:
            # 1. 基本配置
            self.window_name = "AI Face App - Professional Edition"
            self.snapshots_dir = "snapshots"
            self.results_dir = "results"  # 用于批量处理的输出目录

            # 2. 加载模型
            self.model = YOLO(self.model_path)
            print("✅ 模型加载成功。")

            # 3. 初始化摄像头对象
            self.cap = None
            
            # 4. 创建UI界面
            self._create_widgets()
            
            # 新增：优雅地关闭应用
            self.protocol("WM_DELETE_WINDOW", self._on_closing)

        except Exception as e:
            print(f"❌ 错误: 无法加载模型。{e}")

    def _create_output_dirs(self):
        """私有方法：检查并创建所有需要的输出文件夹。"""
        if not os.path.exists(self.snapshots_dir):
            os.makedirs(self.snapshots_dir)
            print(f"✅ 快照文件夹 '{self.snapshots_dir}' 已创建。")
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            print(f"✅ 批量结果文件夹 '{self.results_dir}' 已创建。")

    def _save_snapshot(self, frame, base_name="snapshot"):
        """私有方法：将当前画面保存为一张带有时间戳或自定义名字的图片。"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_{timestamp}.jpg"
        filepath = os.path.join(self.snapshots_dir, filename)
        cv2.imwrite(filepath, frame)
        print(f"📸 快照已保存至: {filepath}")
        return filepath

    def _process_frame(self, frame):
        """私有方法：处理单帧画面，返回带有人脸框和计数的画面。"""
        results = self.model(frame)
        annotated_frame = results[0].plot()
        face_count = len(results[0].boxes)
        text = f"Face Count: {face_count}"
        cv2.putText(annotated_frame, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        return annotated_frame

    def _cleanup(self):
        """私有方法：释放所有资源。"""
        print("🛑 正在释放资源...")
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("✅ 清理完成。")

    def _run_live_mode(self, source_index):
        """私有方法：运行实时摄像头检测模式。"""
        print(f"🚀 进入实时直播模式 (摄像头索引: {source_index})...")
        print("🔴 在弹出的窗口中按 'q' 键退出。")
        print("📸 在弹出的窗口中按 's' 键保存快照。")
        
        self.cap = cv2.VideoCapture(source_index)
        if not self.cap.isOpened():
            print(f"❌ 错误：无法打开索引为 {source_index} 的摄像头。")
            return

        while self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                break
            
            processed_frame = self._process_frame(frame)
            cv2.imshow(self.window_name, processed_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                self._save_snapshot(processed_frame)
        
        self._cleanup()

    def _run_image_mode(self, source_path):
        """私有方法：运行单张图片检测模式。"""
        print(f"🖼️ 进入图片分析模式 (文件: {source_path})...")
        frame = cv2.imread(source_path)
        if frame is None:
            print(f"❌ 错误: 无法读取图片 '{source_path}'。")
            return
        
        processed_frame = self._process_frame(frame)
        
        # 从原始文件名生成一个基础名字用于保存快照
        base_name = os.path.splitext(os.path.basename(source_path))[0]
        saved_path = self._save_snapshot(processed_frame, base_name=f"{base_name}_result")
        
        print(f"✅ 分析完成，结果已保存至 {saved_path}。")
        print("ℹ️ 按任意键关闭图片窗口。")
        
        cv2.imshow(self.window_name, processed_frame)
        cv2.waitKey(0)
        self._cleanup()

    def _run_batch_mode(self, source_path):
        """私有方法：运行文件夹批量处理模式。"""
        print(f"🗂️ 进入批量处理模式 (文件夹: {source_path})...")
        
        # 获取所有支持的图片文件
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        files = [f for f in os.listdir(source_path) if os.path.splitext(f)[1].lower() in image_extensions]
        
        if not files:
            print(f"⚠️ 在文件夹 '{source_path}' 中未找到任何支持的图片文件。")
            return
            
        total = len(files)
        print(f"找到 {total} 张图片，开始处理...")

        for i, filename in enumerate(files):
            filepath = os.path.join(source_path, filename)
            frame = cv2.imread(filepath)
            
            if frame is None:
                print(f"  -> [{i+1}/{total}] ⚠️ 跳过，无法读取: {filename}")
                continue

            print(f"  -> [{i+1}/{total}] 正在处理: {filename}")
            processed_frame = self._process_frame(frame)
            
            output_path = os.path.join(self.results_dir, filename)
            cv2.imwrite(output_path, processed_frame)
            
        print(f"\n✅ 批量处理完成！所有结果已保存至 '{self.results_dir}' 文件夹。")

    def run(self, source):
        """
        公共方法：作为智能调度中心，根据输入源启动不同模式。
        """
        self._create_output_dirs() # 确保所有输出文件夹都存在

        if isinstance(source, int):
            self._run_live_mode(source)
        elif os.path.isfile(source):
            self._run_image_mode(source)
        elif os.path.isdir(source):
            self._run_batch_mode(source)
        else:
            print(f"❌ 错误: 无效的输入源 '{source}'。请输入摄像头索引(如0), 图片文件路径, 或文件夹路径。")

    def _create_widgets(self):
        """创建应用程序的UI组件。"""
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(padx=10, pady=10)

        # --- File Processing Section ---
        file_frame = ttk.LabelFrame(self.main_frame, text="文件处理 (图片/视频)", padding=(10, 5))
        file_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.browse_button = ttk.Button(file_frame, text="选择文件", command=self._browse_file)
        self.browse_button.pack(side="left", padx=5)

        self.file_path_label = ttk.Label(file_frame, text="尚未选择文件", width=50)
        self.file_path_label.pack(side="left", padx=5, fill="x", expand=True)
        
        # --- Action Buttons Section ---
        action_frame = ttk.Frame(self.main_frame)
        action_frame.grid(row=1, column=0, columnspan=2, pady=5)

        self.process_button = ttk.Button(action_frame, text="处理选中文件", command=self._process_file)
        self.process_button.pack(side="left", padx=5)
        
        # --- Real-time Detection Section ---
        realtime_frame = ttk.LabelFrame(self.main_frame, text="摄像头实时检测", padding=(10, 5))
        realtime_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.realtime_button = ttk.Button(realtime_frame, text="启动实时摄像头检测", command=self._toggle_realtime_detection)
        self.realtime_button.pack(side="left", padx=5)

        self.status_label = ttk.Label(realtime_frame, text="状态: 已停止", font=("Helvetica", 10))
        self.status_label.pack(side="left", padx=5)
        
        # --- Snapshot Button ---
        self.snapshot_button = ttk.Button(action_frame, text="截取当前画面", command=self._take_snapshot, state="disabled")
        self.snapshot_button.pack(side="left", padx=5)

    def _browse_file(self):
        """处理文件选择事件。"""
        file_path = filedialog.askopenfilename(title="选择文件", filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff"), ("Video Files", "*.mp4;*.avi;*.mov"), ("All Files", "*.*")])
        if file_path:
            self.file_path_label.config(text=file_path)

    def _process_file(self):
        """处理文件处理事件。"""
        file_path = self.file_path_label.cget("text")
        if not file_path or file_path == "尚未选择文件":
            messagebox.showwarning("操作无效", "请先选择一个文件。")
            return
            
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            self._process_image(file_path)
        elif file_path.lower().endswith(('.mp4', '.avi', '.mov')):
            self._process_video(file_path)
        else:
            messagebox.showerror("文件类型错误", "不支持的文件类型。请选择图片或视频文件。")

    def _process_image(self, file_path):
        """处理单张图片文件。"""
        self.status_label.config(text=f"状态: 正在处理图片...", foreground="blue")
        self.update_idletasks()
        try:
            results = self.model(file_path, verbose=False)
            annotated_image = results[0].plot()

            self.status_label.config(text=f"状态: 处理完成", foreground="green")
            self._show_result_image(annotated_image, title=f"检测结果: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("处理错误", f"处理图片时发生错误: {e}")
            self.status_label.config(text=f"状态: 图片处理失败", foreground="red")
            
    def _process_video(self, file_path):
        """处理单个视频文件。"""
        self.status_label.config(text=f"状态: 正在处理视频...", foreground="blue")
        self.update_idletasks()
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            messagebox.showerror("视频错误", "无法打开视频文件。")
            self.status_label.config(text=f"状态: 视频处理失败", foreground="red")
            return

        while True:
            success, frame = cap.read()
            if not success:
                break

            results = self.model(frame, stream=True, verbose=False)
            for r in results:
                annotated_frame = r.plot()
                cv2.imshow("视频处理中 (按 'q' 退出)", annotated_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        self.status_label.config(text=f"状态: 视频处理完成", foreground="green")

    # --- 新增：实时检测核心方法 ---

    def _toggle_realtime_detection(self):
        """切换实时检测的启动/停止状态。"""
        if self.is_realtime_running:
            self._stop_realtime_detection()
        else:
            self._start_realtime_detection()

    def _start_realtime_detection(self):
        """启动摄像头进行实时检测。"""
        # 禁用文件处理功能，避免冲突
        self.browse_button.config(state="disabled")
        self.process_button.config(state="disabled")
        self.snapshot_button.config(state="normal") # 启用快照

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # 使用 CAP_DSHOW 提高Windows兼容性
        if not self.cap.isOpened():
            messagebox.showerror("摄像头错误", "无法打开摄像头。请检查摄像头是否连接或被其他应用占用。")
            self._stop_realtime_detection()  # 重置状态
            return

        self.is_realtime_running = True
        self.realtime_button.config(text="停止检测")
        self.status_label.config(text="状态: 摄像头运行中...", foreground="green")

        self._realtime_loop()

    def _stop_realtime_detection(self):
        """停止实时检测并释放资源。"""
        self.is_realtime_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()

        # 恢复UI组件状态
        self.realtime_button.config(text="启动实时摄像头检测")
        self.status_label.config(text="状态: 已停止", foreground="black")
        self.browse_button.config(state="normal")
        self.process_button.config(state="normal")
        self.snapshot_button.config(state="disabled")

    def _realtime_loop(self):
        """实时检测的核心循环。"""
        if not self.is_realtime_running:
            return

        if self.cap is None:
            self._stop_realtime_detection()
            return
            
        success, self.current_frame = self.cap.read()
        if success:
            start_time = time.time()

            # 模型推理
            results = self.model(self.current_frame, stream=True, verbose=False)

            annotated_frame = self.current_frame.copy() # 先复制原始帧
            for r in results:
                annotated_frame = r.plot()  # plot会返回绘制好的帧

            # 计算并显示FPS
            fps = 1 / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
            cv2.putText(annotated_frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(annotated_frame, "Press 'q' in this window to stop", (10, annotated_frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

            cv2.imshow("实时人脸检测 (专属模型)", annotated_frame)

            # 通过OpenCV窗口按q键也可以停止
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self._stop_realtime_detection()
                return

            # 使用 after 方法实现非阻塞循环
            self.after(10, self._realtime_loop)
        else:
            self._stop_realtime_detection()
            messagebox.showinfo("信息", "视频流结束或摄像头断开连接。")

    def _on_closing(self):
        """处理窗口关闭事件，确保资源被释放。"""
        if self.is_realtime_running:
            self._stop_realtime_detection()
        self.destroy()

    def _show_result_image(self, image, title="Detection Result"):
        """在一个新的OpenCV窗口中显示结果图片。"""
        try:
            cv2.imshow(title, image)
            cv2.waitKey(0)
        except Exception as e:
            messagebox.showerror("显示错误", f"显示结果图像时发生错误: {e}")

    def _take_snapshot(self):
        """截取当前摄像头画面并进行分析。"""
        if self.is_realtime_running and hasattr(self, 'current_frame'):
            self.status_label.config(text=f"状态: 正在分析快照...", foreground="blue")
            self.update_idletasks()
            
            snapshot = self.current_frame.copy()
            results = self.model(snapshot, verbose=False)
            annotated_image = results[0].plot()

            # 保存快照
            self._create_output_dirs()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snapshot_{timestamp}.jpg"
            save_path = os.path.join(self.snapshots_dir, filename)
            cv2.imwrite(save_path, annotated_image)
            
            self.status_label.config(text=f"状态: 快照已保存", foreground="green")
            self._show_result_image(annotated_image, title=f"快照结果: {filename}")
        else:
            messagebox.showwarning("快照错误", "请先启动实时摄像头检测。")

if __name__ == "__main__":
    """
    主程序入口:
    创建并运行FaceApp图形界面应用。
    """
    app = FaceApp()
    app.mainloop() 