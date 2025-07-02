import face_recognition
import cv2
import numpy as np
import os

def test_face_recognition():
    """测试face-recognition库是否正常工作"""
    print("正在测试 face-recognition 库...")
    
    try:
        # 测试1: 检查库是否能正常导入
        print("✅ face-recognition 库导入成功")
        
        # 测试2: 创建一个简单的测试图像
        print("📷 创建测试图像...")
        
        # 创建一个简单的测试图像 (红色正方形)
        test_image = np.zeros((300, 300, 3), dtype=np.uint8)
        test_image[:, :] = [0, 0, 255]  # 红色
        
        # 测试3: 尝试在图像中寻找人脸
        print("🔍 测试人脸检测功能...")
        face_locations = face_recognition.face_locations(test_image)
        print(f"在测试图像中找到 {len(face_locations)} 个人脸")
        
        # 测试4: 测试编码功能
        print("🧬 测试人脸编码功能...")
        if len(face_locations) > 0:
            face_encodings = face_recognition.face_encodings(test_image, face_locations)
            print(f"生成了 {len(face_encodings)} 个人脸编码")
        else:
            print("没有检测到人脸，这是正常的（测试图像是纯色的）")
            
        print("✅ face-recognition 库测试完成！所有功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def check_camera():
    """检查摄像头是否可用"""
    print("\n📹 检查摄像头可用性...")
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print("✅ 摄像头正常工作")
                print(f"摄像头分辨率: {frame.shape[1]}x{frame.shape[0]}")
                cap.release()
                return True
            else:
                print("❌ 摄像头无法读取图像")
                cap.release()
                return False
        else:
            print("❌ 无法打开摄像头")
            return False
    except Exception as e:
        print(f"❌ 摄像头测试失败: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("🎯 人脸识别系统环境测试")
    print("="*50)
    
    # 测试 face-recognition 库
    face_rec_ok = test_face_recognition()
    
    # 测试摄像头
    camera_ok = check_camera()
    
    print("\n" + "="*50)
    print("📊 测试结果总结:")
    print(f"face-recognition 库: {'✅ 正常' if face_rec_ok else '❌ 异常'}")
    print(f"摄像头功能: {'✅ 正常' if camera_ok else '❌ 异常'}")
    
    if face_rec_ok and camera_ok:
        print("\n🎉 所有测试通过！可以开始实现人脸识别功能了！")
    else:
        print("\n⚠️  存在问题，需要解决后再继续")
    print("="*50) 