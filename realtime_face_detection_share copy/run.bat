@echo off
chcp 65001 >nul
echo ================================
echo 🎯 启动实时人脸检测系统
echo 🎯 Starting Face Detection System
echo ================================
echo.

echo 📷 正在启动摄像头检测...
echo 💡 控制提示：
echo    Q - 退出程序
echo    C - 切换摄像头
echo    S - 保存截图
echo.

python realtime_face_detection.py

echo.
echo 程序已退出，按任意键关闭窗口...
pause >nul 