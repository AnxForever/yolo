# --- Stage 1: The "Heavy-Lifting" Builder ---
# 我们先使用一个包含完整Python和编译工具的"重型工厂"镜像
# 它提供了所有编译 dlib 所需的工具 (like cmake, gcc)
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 更新操作系统包管理器，并安装编译 dlib 所需的核心依赖
# build-essential 提供了 C++ 编译器等工具
# cmake 是编译 dlib 的必要工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# 复制"零件清单"到工厂里
COPY requirements.txt .

# 在这个重型工厂里，安装所有Python零件。
# 这一步会进行最耗费内存的编译工作，但这是在构建阶段，不受Render免费套餐内存限制
RUN pip install --no-cache-dir -r requirements.txt


# --- Stage 2: The "Lightweight" Runner ---
# 现在，我们换用一个超轻量级的"运输卡车"镜像，只保留最核心的运行环境
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 从第一阶段的"重型工厂"中，只把安装好的Python零件（库文件）复制过来
# 这样，我们的最终集装箱就会非常小，启动飞快
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# 把我们自己的应用程序代码（服务器、人脸识别逻辑等）复制进来
COPY . .

# 暴露端口，告诉外界我们的程序将在5000端口提供服务
EXPOSE 5000

# 设置环境变量，确保Python输出是无缓冲的，方便在Render看日志
ENV PYTHONUNBUFFERED=1

# 集装箱的最终启动命令：使用Gunicorn专业服务器来运行我们的app
# 这个和我们之前在 render.yaml 里写的启动命令是一样的
CMD ["gunicorn", "--timeout", "60", "--workers", "1", "--threads", "4", "--worker-class", "gevent", "ultra_optimized_server:app", "--bind", "0.0.0.0:5000"] 