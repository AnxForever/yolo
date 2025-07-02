# 1. 基镜像：选择一个包含Python 3.10的轻量级镜像
FROM python:3.10-slim

# 2. 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. 设置工作目录
WORKDIR /app

# 4. 安装系统依赖 (用于OpenCV)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 5. 复制依赖管理文件
COPY requirements.txt .

# 6. 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 7. 复制项目代码
COPY . .

# 8. 暴露端口
EXPOSE 8000

# 9. 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 