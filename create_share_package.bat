@echo off
chcp 65001 >nul
echo ================================
echo 📦 创建分享包脚本
echo 📦 Creating Share Package
echo ================================
echo.

set "package_name=realtime_face_detection_v1.0"
set "timestamp=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "timestamp=%timestamp: =0%"

echo 📁 正在打包分享文件...

if exist "%package_name%.zip" (
    echo 🗑️ 删除旧的压缩包...
    del "%package_name%.zip"
)

echo 📦 创建新的压缩包: %package_name%.zip
powershell Compress-Archive -Path "realtime_face_detection_share\*" -DestinationPath "%package_name%.zip" -Force

if exist "%package_name%.zip" (
    echo ✅ 分享包创建成功！
    echo 📁 文件名: %package_name%.zip
    echo 📏 文件大小:
    dir "%package_name%.zip" | findstr /R "[0-9].*\.zip"
    echo.
    echo 🎉 现在可以将这个zip文件发送给你的朋友了！
) else (
    echo ❌ 创建失败，请检查文件权限
)

echo.
echo 📋 分享包内容：
echo    - realtime_face_detection.py (主程序)
echo    - install.bat (一键安装脚本)
echo    - run.bat (一键运行脚本)
echo    - requirements.txt (依赖列表)
echo    - README.md (详细说明文档)
echo    - 安装说明.txt (简单安装指南)
echo.
pause 