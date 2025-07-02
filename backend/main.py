#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO Model Performance Hub - Backend API
FastAPI后端服务，支持模型检测、实时WebSocket、性能监控
"""

import os
import sys
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

# FastAPI核心组件
from fastapi import FastAPI, File, UploadFile, Form, WebSocket, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocketDisconnect

# 数据模型
from pydantic import BaseModel, Field
import base64
import cv2
import numpy as np
from PIL import Image
import psutil

# 确保能导入ultralytics
sys.path.insert(0, '../ultralytics')
from ultralytics import YOLO

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="YOLO Model Performance Hub API",
    description="专业的YOLO模型性能对比与检测API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
loaded_models: Dict[str, YOLO] = {}  # 按需加载的模型缓存
active_sessions: Dict[str, Dict] = {}  # 活跃的WebSocket会话
performance_history: List[Dict] = []  # 性能历史数据
detection_results: Dict[str, Dict] = {}  # 检测结果缓存

# 创建必要的目录
os.makedirs("uploads", exist_ok=True)
os.makedirs("results", exist_ok=True)
os.makedirs("static", exist_ok=True)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 数据模型定义
class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    size: str
    type: str
    supported_classes: List[str]
    performance: Dict[str, Any]

class DetectionRequest(BaseModel):
    model: str
    confidence: float = Field(default=0.5, ge=0.1, le=1.0)
    nms: float = Field(default=0.4, ge=0.1, le=1.0)
    quality: Optional[float] = Field(default=1.0, ge=0.1, le=1.0)
    return_image: bool = True

class RealtimeStartRequest(BaseModel):
    model: str
    confidence: float = 0.5
    nms: float = 0.4
    detection_interval: int = 2000
    performance_mode: str = "balanced"

class RealtimeStopRequest(BaseModel):
    session_id: str

class DetectionBox(BaseModel):
    box: List[float]  # [x1, y1, x2, y2]
    label: str
    confidence: float
    class_id: int

class DetectionMetrics(BaseModel):
    inference_time: float
    fps: float
    detected_objects: int
    model_used: str
    image_size: List[int]

class DetectionResult(BaseModel):
    success: bool
    task_id: str
    results: Dict[str, Any]
    timestamp: str

# 可用模型配置
AVAILABLE_MODELS = {
    "yolo11n": {
        "id": "yolo11n",
        "name": "YOLO11n",
        "description": "通用快速模型，轻量级设计",
        "file_path": "../yolo11n.pt",
        "size": "6.2MB",
        "type": "object_detection",
        "supported_classes": ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck"],
        "performance": {"avg_inference_time": 15, "avg_fps": 65}
    },
    "face_model": {
        "id": "face_model", 
        "name": "自定义人脸模型",
        "description": "专为人脸检测优化的模型",
        "file_path": "../yolov11n-face.pt",
        "size": "5.2MB",
        "type": "face_detection",
        "supported_classes": ["person"],
        "performance": {"avg_inference_time": 20, "avg_fps": 50}
    },
    "yolov8n": {
        "id": "yolov8n",
        "name": "YOLOv8n", 
        "description": "YOLOv8 Nano版本，对比基准",
        "file_path": "../yolov8n.pt",
        "size": "6.2MB",
        "type": "object_detection",
        "supported_classes": ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck"],
        "performance": {"avg_inference_time": 18, "avg_fps": 55}
    }
}

def get_system_stats() -> Dict[str, Any]:
    """获取系统状态信息"""
    try:
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 内存信息
        memory = psutil.virtual_memory()
        
        # GPU信息 (尝试获取)
        gpu_info = {"usage_percent": 0, "memory_used": "0MB", "memory_total": "0MB", "temperature": 0}
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_info = {
                    "usage_percent": round(gpu.load * 100, 1),
                    "memory_used": f"{round(gpu.memoryUsed / 1024, 1)}GB",
                    "memory_total": f"{round(gpu.memoryTotal / 1024, 1)}GB", 
                    "temperature": gpu.temperature
                }
        except:
            pass
        
        return {
            "gpu": gpu_info,
            "cpu": {
                "usage_percent": round(cpu_percent, 1),
                "cores": cpu_count,
                "frequency": "3.2GHz"  # 简化处理
            },
            "memory": {
                "used": f"{round(memory.used / (1024**3), 1)}GB",
                "total": f"{round(memory.total / (1024**3), 1)}GB",
                "usage_percent": round(memory.percent, 2)
            },
            "active_models": len(loaded_models),
            "active_sessions": len(active_sessions),
            "uptime": int(time.time() - startup_time)
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return {"error": "Failed to get system stats"}

def load_model(model_id: str) -> YOLO:
    """按需加载模型"""
    if model_id in loaded_models:
        return loaded_models[model_id]
    
    if model_id not in AVAILABLE_MODELS:
        raise HTTPException(status_code=404, detail=f"模型 {model_id} 不存在")
    
    model_config = AVAILABLE_MODELS[model_id]
    model_path = model_config["file_path"]
    
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail=f"模型文件不存在: {model_path}")
    
    try:
        logger.info(f"正在加载模型: {model_id}")
        model = YOLO(model_path)
        loaded_models[model_id] = model
        logger.info(f"模型 {model_id} 加载成功")
        return model
    except Exception as e:
        logger.error(f"加载模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"模型加载失败: {str(e)}")

def process_detection(image: np.ndarray, model: YOLO, confidence: float, nms: float) -> tuple:
    """处理图像检测"""
    start_time = time.time()
    
    try:
        # YOLO推理
        results = model(image, conf=confidence, iou=nms, verbose=False)
        inference_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        detections = []
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                box = boxes.xyxy[i].cpu().numpy().tolist()
                conf = float(boxes.conf[i].cpu().numpy())
                cls_id = int(boxes.cls[i].cpu().numpy())
                
                # 获取类别名称
                class_names = model.names
                label = class_names.get(cls_id, f"class_{cls_id}")
                
                detections.append({
                    "box": box,
                    "label": label,
                    "confidence": round(conf, 3),
                    "class_id": cls_id
                })
        
        # 绘制检测结果
        result_image = image.copy()
        if len(results) > 0:
            result_image = results[0].plot()
        
        return detections, result_image, inference_time
        
    except Exception as e:
        logger.error(f"检测处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")

async def collect_performance_data():
    """后台任务：定期收集性能数据"""
    while True:
        try:
            stats = get_system_stats()
            stats["timestamp"] = int(time.time() * 1000)
            
            performance_history.append(stats)
            
            # 只保留最近24小时的数据 (24 * 60 * 6 = 8640个数据点，每10秒一个)
            if len(performance_history) > 8640:
                performance_history.pop(0)
                
        except Exception as e:
            logger.error(f"性能数据收集失败: {e}")
        
        await asyncio.sleep(10)  # 每10秒收集一次

# API路由定义

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global startup_time
    startup_time = time.time()
    logger.info("YOLO Performance Hub API 启动成功")
    
    # 启动性能监控任务
    asyncio.create_task(collect_performance_data())

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "detection_engine": "running",
            "model_loader": "running", 
            "file_storage": "running",
            "websocket": "running"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/models")
async def get_models():
    """获取可用模型列表"""
    models = []
    for model_id, config in AVAILABLE_MODELS.items():
        model_info = {
            "id": config["id"],
            "name": config["name"],
            "description": config["description"],
            "size": config["size"],
            "type": config["type"],
            "supported_classes": config["supported_classes"],
            "performance": config["performance"],
            "loaded": model_id in loaded_models
        }
        models.append(model_info)
    
    return {"models": models}

@app.get("/api/models/{model_id}/info")
async def get_model_info(model_id: str):
    """获取特定模型详细信息"""
    if model_id not in AVAILABLE_MODELS:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    config = AVAILABLE_MODELS[model_id]
    return {
        "id": config["id"],
        "name": config["name"],
        "version": "1.0.0",
        "architecture": "YOLO",
        "input_size": [640, 640],
        "classes": config["supported_classes"],
        "performance_benchmarks": {
            "cpu": {"inference_time": 25, "fps": 40},
            "gpu": {"inference_time": 15, "fps": 65}
        },
        "memory_requirements": "2GB",
        "created_at": "2024-01-01T00:00:00Z",
        "loaded": model_id in loaded_models
    }

@app.post("/api/detect/image")
async def detect_image(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    model: str = Form(...),
    confidence: float = Form(0.5),
    nms: float = Form(0.4),
    quality: float = Form(1.0),
    return_image: bool = Form(True)
):
    """单张图片检测"""
    
    # 生成任务ID
    task_id = f"detect_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    try:
        # 验证文件格式
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="文件必须是图片格式")
        
        # 读取图片
        image_data = await image.read()
        
        # 保存原始图片
        original_path = f"uploads/{task_id}_original.jpg"
        with open(original_path, "wb") as f:
            f.write(image_data)
        
        # 转换为OpenCV格式
        nparr = np.frombuffer(image_data, np.uint8)
        cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if cv_image is None:
            raise HTTPException(status_code=400, detail="图片格式不支持或已损坏")
        
        # 加载模型
        yolo_model = load_model(model)
        
        # 执行检测
        detections, result_image, inference_time = process_detection(
            cv_image, yolo_model, confidence, nms
        )
        
        # 保存结果图片
        result_path = f"results/{task_id}_result.jpg"
        cv2.imwrite(result_path, result_image)
        
        # 计算指标
        fps = 1000.0 / inference_time if inference_time > 0 else 0
        image_height, image_width = cv_image.shape[:2]
        
        # 构建响应
        result = {
            "success": True,
            "task_id": task_id,
            "results": {
                "detections": detections,
                "metrics": {
                    "inference_time": round(inference_time, 1),
                    "fps": round(fps, 1),
                    "detected_objects": len(detections),
                    "model_used": model,
                    "image_size": [image_width, image_height]
                },
                "result_image_url": f"/api/results/{task_id}/image" if return_image else None
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 缓存结果
        detection_results[task_id] = {
            "original_path": original_path,
            "result_path": result_path,
            "data": result,
            "created_at": datetime.now()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"图片检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")

@app.get("/api/results/{task_id}/image")
async def get_result_image(task_id: str):
    """获取检测结果图片"""
    if task_id not in detection_results:
        raise HTTPException(status_code=404, detail="结果不存在")
    
    result_path = detection_results[task_id]["result_path"]
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="结果图片不存在")
    
    return FileResponse(result_path, media_type="image/jpeg")

@app.get("/api/results/{task_id}/data")
async def get_result_data(task_id: str):
    """获取检测结果数据"""
    if task_id not in detection_results:
        raise HTTPException(status_code=404, detail="结果不存在")
    
    result_info = detection_results[task_id]
    return {
        "task_id": task_id,
        "original_image_url": f"/api/results/{task_id}/original",
        "result_image_url": f"/api/results/{task_id}/image",
        "detections": result_info["data"]["results"]["detections"],
        "metrics": result_info["data"]["results"]["metrics"],
        "created_at": result_info["created_at"].isoformat()
    }

@app.delete("/api/results/{task_id}")
async def delete_result(task_id: str):
    """删除检测结果"""
    if task_id not in detection_results:
        raise HTTPException(status_code=404, detail="结果不存在")
    
    try:
        result_info = detection_results[task_id]
        
        # 删除文件
        for path in [result_info["original_path"], result_info["result_path"]]:
            if os.path.exists(path):
                os.remove(path)
        
        # 删除缓存
        del detection_results[task_id]
        
        return {"success": True, "message": "结果删除成功"}
        
    except Exception as e:
        logger.error(f"删除结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@app.get("/api/system/status")
async def get_system_status():
    """获取系统状态"""
    return get_system_stats()

@app.get("/api/system/performance/history")
async def get_performance_history():
    """获取性能历史数据"""
    return {
        "metrics": performance_history[-1000:],  # 最近1000个数据点
        "interval": 10
    }

@app.get("/api/config/detection")
async def get_detection_config():
    """获取检测配置选项"""
    return {
        "confidence_range": [0.1, 1.0],
        "nms_range": [0.1, 1.0],
        "supported_formats": ["jpg", "jpeg", "png"],
        "max_file_size": 10485760,  # 10MB
        "detection_intervals": [500, 1000, 2000, 3000, 5000],
        "performance_modes": ["quality", "balanced", "performance"]
    }

# WebSocket实时检测 (基础版本，可以后续扩展)
@app.websocket("/ws/detect/{session_id}")
async def websocket_detect(websocket: WebSocket, session_id: str):
    """WebSocket实时检测"""
    await websocket.accept()
    logger.info(f"WebSocket连接建立: {session_id}")
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "frame":
                # 处理帧数据
                try:
                    # 解码base64图片
                    image_data = base64.b64decode(message["data"])
                    nparr = np.frombuffer(image_data, np.uint8)
                    cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if cv_image is not None:
                        # 使用默认模型检测
                        model = load_model("yolo11n")
                        detections, result_image, inference_time = process_detection(
                            cv_image, model, 0.5, 0.4
                        )
                        
                        # 编码结果图片
                        _, buffer = cv2.imencode('.jpg', result_image)
                        result_b64 = base64.b64encode(buffer).decode()
                        
                        # 发送结果
                        response = {
                            "type": "detection_result",
                            "data": {
                                "detections": detections,
                                "metrics": {
                                    "inference_time": round(inference_time, 1),
                                    "fps": round(1000.0 / inference_time, 1),
                                    "detected_objects": len(detections)
                                },
                                "result_image": result_b64
                            },
                            "timestamp": int(time.time() * 1000)
                        }
                        
                        await websocket.send_text(json.dumps(response))
                        
                except Exception as e:
                    logger.error(f"WebSocket处理失败: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 