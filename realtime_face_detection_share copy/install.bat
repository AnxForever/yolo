@echo off
chcp 65001 >nul
echo ================================
echo 🚀 实时人脸检测系统安装脚本
echo 🚀 Real-time Face Detection Setup
echo ================================
echo.

echo 📋 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python环境
    echo 请先安装Python 3.8+: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python环境检查完成

echo.
echo 📦 正在安装依赖包...
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ 依赖安装失败，尝试使用国内镜像源...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo.
echo 🎯 正在下载YOLO11模型...
python -c "from ultralytics import YOLO; model = YOLO('yolo11n.pt'); print('✅ 模型下载完成')"

echo.
echo ================================
echo ✅ 安装完成！
echo ================================
echo.
echo 🎮 使用方法：
echo    1. 双击 run.bat 启动程序
echo    或者运行: python realtime_face_detection.py
echo.
echo 📖 更多信息请查看 README.md
echo.
pause 