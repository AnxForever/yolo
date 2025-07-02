# 📷 摄像头项目集合

这里包含了三个不同的摄像头相关项目，每个都有不同的功能和用途。

## 🚀 项目概览

### 1. 实时人脸检测 (realtime_face_detection)
**功能**: 高性能实时人脸检测与计数
- ✨ **智能摄像头切换**: 自动检测并切换多个摄像头
- 👥 **实时人脸计数**: 精确显示检测到的人脸数量
- ⚡ **FPS监控**: 实时性能指标显示
- 📸 **智能截图**: 一键保存检测结果
- 🎯 **专属模型**: 使用WIDER Face训练的高精度人脸检测模型

**启动方式**:
```bash
cd realtime_face_detection
python realtime_face_detection.py
```

**控制按键**:
- `Q`: 退出程序
- `C`: 切换摄像头
- `S`: 保存截图

---

### 2. 人脸识别系统 (face_recognition_system)
**功能**: 完整的人脸识别训练和识别系统
- 🤖 **人脸训练**: 从个人照片训练人脸识别模型
- 🔍 **人脸识别**: 识别并标记已知人员
- 💾 **数据库管理**: 管理人脸特征数据库
- 🖥️ **图形界面**: 用户友好的GUI界面
- 📊 **多模式支持**: 支持实时摄像头、单张图片、批量处理

**主要文件**:
- `face_app.py` - 主应用程序(GUI界面)
- `train_my_face.py` - 人脸训练脚本
- `advanced_face_recognition.py` - 高级人脸识别功能
- `test_face_recognition.py` - 系统测试脚本
- `face_database/` - 人脸数据库目录

**启动方式**:
```bash
cd face_recognition_system
# 训练人脸
python train_my_face.py
# 启动主应用
python face_app.py
```

---

### 3. 摄像头测试工具 (camera_testing)
**功能**: 摄像头设备检测和测试工具
- 🔍 **设备检测**: 自动扫描所有可用摄像头
- 📊 **性能测试**: 显示摄像头分辨率、帧率等信息
- 🎬 **实时预览**: 测试摄像头画质和稳定性
- ⚙️ **设置调试**: 帮助调试摄像头问题

**启动方式**:
```bash
cd camera_testing
python camera_test.py
```

## 🛠️ 环境要求

```bash
# 安装依赖
pip install ultralytics opencv-python face-recognition numpy tkinter
```

## 📁 项目结构

```
camera_projects/
├── README.md                          # 本文件
├── realtime_face_detection/           # 实时人脸检测
│   └── realtime_face_detection.py
├── face_recognition_system/           # 人脸识别系统
│   ├── face_app.py
│   ├── train_my_face.py
│   ├── advanced_face_recognition.py
│   ├── test_face_recognition.py
│   └── face_database/                 # 人脸数据库
└── camera_testing/                    # 摄像头测试
    └── camera_test.py
```

## 🎯 使用建议

1. **新用户**: 先运行 `camera_testing/camera_test.py` 确保摄像头工作正常
2. **人脸识别**: 使用 `face_recognition_system` 建立个人人脸数据库
3. **实时检测**: 使用 `realtime_face_detection` 进行高性能人脸检测

## 📸 截图存储

所有截图文件已移动到根目录的 `screenshots/` 文件夹中，便于管理和查看。

---

*每个项目都有独立的功能，可以根据需求选择使用。建议从摄像头测试开始，确保硬件正常后再使用其他功能。* 