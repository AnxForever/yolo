# YOLO Performance Hub - 后端API

## 🚀 快速开始

### 1. 环境要求
- Python 3.8+
- pip包管理器
- （可选）NVIDIA GPU + CUDA支持

### 2. 安装依赖

```bash
# 进入后端目录
cd backend

# 安装依赖包
pip install -r requirements.txt
```

### 3. 启动服务器

#### 方式一：自动检查启动（推荐）
```bash
python start_server.py
```

#### 方式二：直接启动
```bash
python main.py
```

### 4. 验证服务

服务启动后，访问以下URL验证：
- API文档: http://localhost:8000/api/docs
- 健康检查: http://localhost:8000/api/health
- 模型列表: http://localhost:8000/api/models

## 📋 API接口说明

### 核心接口

#### 模型管理
- `GET /api/models` - 获取可用模型列表
- `GET /api/models/{model_id}/info` - 获取特定模型信息

#### 图像检测
- `POST /api/detect/image` - 单张图片检测
- `GET /api/results/{task_id}/image` - 获取检测结果图片
- `GET /api/results/{task_id}/data` - 获取检测结果数据

#### 系统监控
- `GET /api/system/status` - 获取系统状态
- `GET /api/system/performance/history` - 获取性能历史

#### 实时检测
- `WebSocket /ws/detect/{session_id}` - 实时检测WebSocket

### 使用示例

#### 图片检测
```bash
curl -X POST "http://localhost:8000/api/detect/image" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test.jpg" \
  -F "model=yolo11n" \
  -F "confidence=0.5"
```

## 🛠️ 技术架构

### 核心组件
- **FastAPI**: 现代高性能Web框架
- **ultralytics**: YOLO模型推理引擎
- **OpenCV**: 图像处理库
- **psutil**: 系统监控
- **WebSocket**: 实时通信

### 特性
- ✅ 按需模型加载 (节省内存)
- ✅ 异步并发处理
- ✅ 自动CORS支持
- ✅ 完整的错误处理
- ✅ 性能监控
- ✅ 结果缓存管理
- ✅ WebSocket实时检测

## 📁 项目结构

```
backend/
├── main.py              # FastAPI主应用
├── start_server.py      # 启动脚本
├── requirements.txt     # 依赖管理
├── README.md           # 使用说明
├── uploads/            # 上传图片存储
├── results/            # 检测结果存储
└── static/             # 静态文件
```

## ⚙️ 配置说明

### 模型配置
在 `main.py` 中的 `AVAILABLE_MODELS` 字典中配置可用模型：

```python
AVAILABLE_MODELS = {
    "yolo11n": {
        "id": "yolo11n",
        "name": "YOLO11n",
        "file_path": "../yolo11n.pt",
        # ... 其他配置
    }
}
```

### 服务配置
- 默认端口: 8000
- 默认主机: 0.0.0.0 (所有网卡)
- 性能采样: 每10秒
- 数据保留: 24小时

## 🔧 故障排除

### 常见问题

1. **模型文件不存在**
   - 确保模型文件在正确路径
   - 检查文件权限

2. **依赖包安装失败**
   ```bash
   # 升级pip
   pip install --upgrade pip
   
   # 手动安装关键包
   pip install fastapi uvicorn opencv-python
   ```

3. **GPU不可用**
   - 检查CUDA安装
   - 安装GPU版本的PyTorch
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

4. **端口已被占用**
   - 修改 `main.py` 中的端口号
   - 或杀死占用端口的进程

### 日志查看
服务器运行时会输出详细日志，包括：
- 模型加载状态
- 请求处理时间
- 错误信息
- 性能指标

## 🚀 部署建议

### 开发环境
- 使用 `reload=True` 自动重载
- 详细日志输出
- CORS允许所有域名

### 生产环境
- 使用Gunicorn + Uvicorn
- 配置反向代理 (Nginx)
- 限制CORS域名
- 启用HTTPS
- 添加监控和日志收集

```bash
# 生产环境启动示例
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 📞 技术支持

如果遇到问题，请检查：
1. Python版本是否兼容
2. 依赖包是否正确安装
3. 模型文件是否存在
4. 网络端口是否可用

更多技术细节请参考API文档: http://localhost:8000/api/docs 