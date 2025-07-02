import cv2
import face_recognition
import os
import pickle
import numpy as np

def train_face_from_directory():
    """从face_database目录训练人脸识别"""
    
    # 设置路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    face_database_dir = os.path.join(script_dir, "face_database")
    encodings_file = os.path.join(face_database_dir, "face_encodings.pkl")
    
    print("="*60)
    print("🎯 人脸识别训练系统")
    print("="*60)
    print(f"📁 训练数据目录: {face_database_dir}")
    
    # 检查目录是否存在
    if not os.path.exists(face_database_dir):
        print(f"❌ 目录不存在: {face_database_dir}")
        return
    
    # 获取所有图像文件
    image_files = []
    supported_formats = ['.jpg', '.jpeg', '.png', '.bmp']
    
    for file in os.listdir(face_database_dir):
        if any(file.lower().endswith(fmt) for fmt in supported_formats):
            image_files.append(file)
    
    if not image_files:
        print("❌ 在目录中未找到图像文件")
        return
    
    print(f"📷 找到 {len(image_files)} 张图像:")
    for i, img in enumerate(image_files, 1):
        print(f"   {i}. {img}")
    
    # 获取用户姓名
    user_name = input("\n👤 请输入您的姓名 (用于识别标识): ").strip()
    if not user_name:
        user_name = "用户"
    
    print(f"\n🔍 开始训练人脸识别，标识为: {user_name}")
    print("-"*60)
    
    # 存储所有人脸编码
    all_encodings = []
    valid_images = []
    
    for i, image_file in enumerate(image_files, 1):
        image_path = os.path.join(face_database_dir, image_file)
        print(f"📸 处理第 {i}/{len(image_files)} 张图像: {image_file}")
        
        try:
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                print(f"   ❌ 无法读取图像文件")
                continue
            
            # 转换BGR到RGB (face_recognition使用RGB格式)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 检测人脸位置
            face_locations = face_recognition.face_locations(rgb_image)
            
            if len(face_locations) == 0:
                print(f"   ❌ 未检测到人脸")
                continue
            elif len(face_locations) > 1:
                print(f"   ⚠️  检测到 {len(face_locations)} 个人脸，使用最大的一个")
                # 选择最大的人脸
                areas = []
                for top, right, bottom, left in face_locations:
                    area = (bottom - top) * (right - left)
                    areas.append(area)
                max_area_index = np.argmax(areas)
                face_locations = [face_locations[max_area_index]]
            
            # 提取人脸特征
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            if len(face_encodings) > 0:
                encoding = face_encodings[0]
                all_encodings.append(encoding)
                valid_images.append(image_file)
                print(f"   ✅ 成功提取人脸特征")
                
                # 显示检测结果
                top, right, bottom, left = face_locations[0]
                cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(image, f"{user_name} - {i}", (left, top-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                
                # 显示图像2秒
                cv2.imshow(f'训练中: {image_file}', image)
                cv2.waitKey(2000)
                cv2.destroyAllWindows()
            else:
                print(f"   ❌ 无法提取人脸特征")
                
        except Exception as e:
            print(f"   ❌ 处理失败: {e}")
    
    print("-"*60)
    print(f"📊 训练结果统计:")
    print(f"   总图像数量: {len(image_files)}")
    print(f"   成功训练: {len(valid_images)}")
    print(f"   失败数量: {len(image_files) - len(valid_images)}")
    
    if len(all_encodings) == 0:
        print("\n❌ 没有成功提取任何人脸特征，训练失败！")
        return
    
    # 计算平均编码（可选，也可以保存所有编码）
    use_average = len(all_encodings) > 1
    if use_average:
        print(f"\n🧮 计算平均人脸特征...")
        average_encoding = np.mean(all_encodings, axis=0)
        final_encodings = [average_encoding]
        print("   ✅ 使用平均特征作为最终模型")
    else:
        final_encodings = all_encodings
        print("   ✅ 使用单一特征作为最终模型")
    
    # 保存人脸数据库
    try:
        # 检查是否已有数据库
        existing_encodings = []
        existing_names = []
        
        if os.path.exists(encodings_file):
            try:
                with open(encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    existing_encodings = data.get('encodings', [])
                    existing_names = data.get('names', [])
                print(f"📋 发现现有数据库，包含 {len(existing_names)} 个已注册人员")
            except:
                print("⚠️  现有数据库文件损坏，将创建新数据库")
        
        # 检查是否已存在同名用户
        if user_name in existing_names:
            choice = input(f"⚠️  用户 '{user_name}' 已存在，是否覆盖? (y/n): ").strip().lower()
            if choice == 'y' or choice == 'yes':
                # 移除旧数据
                user_indices = [i for i, name in enumerate(existing_names) if name == user_name]
                for index in reversed(user_indices):  # 从后向前删除
                    existing_encodings.pop(index)
                    existing_names.pop(index)
                print(f"🗑️  已移除旧的 '{user_name}' 数据")
            else:
                print("❌ 训练已取消")
                return
        
        # 添加新的编码
        for encoding in final_encodings:
            existing_encodings.append(encoding)
            existing_names.append(user_name)
        
        # 保存更新后的数据库
        data = {
            'encodings': existing_encodings,
            'names': existing_names
        }
        
        with open(encodings_file, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"\n✅ 人脸识别训练完成！")
        print(f"💾 数据已保存到: {encodings_file}")
        print(f"👥 数据库现在包含 {len(existing_names)} 个已注册人员")
        print(f"🎯 您的识别标识: {user_name}")
        
        # 显示最终统计
        from collections import Counter
        name_counts = Counter(existing_names)
        print(f"\n📈 数据库详情:")
        for name, count in name_counts.items():
            print(f"   {name}: {count} 个特征向量")
        
        print(f"\n🎉 现在可以使用实时人脸识别功能来识别您了！")
        
    except Exception as e:
        print(f"\n❌ 保存数据库失败: {e}")

if __name__ == "__main__":
    train_face_from_directory() 