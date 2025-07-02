from ultralytics import YOLO
import os

# Define the model path
# The user specified 'D:\YOLO\yolov11n-face.pt', which is 'yolov11n-face.pt' relative to the project root.
model_path = 'yolov11n-face.pt'
if not os.path.exists(model_path):
    print(f"Error: Model file not found at {model_path}")
    # Trying absolute path as a fallback
    model_path_abs = r'D:\YOLO\yolov11n-face.pt'
    if not os.path.exists(model_path_abs):
        print(f"Error: Model file not found at {model_path_abs} either.")
        exit()
    model_path = model_path_abs


# Load the YOLO model
print(f"Loading model from {model_path}...")
model = YOLO(model_path)
print("Model loaded successfully.")

# Define the image path
image_path = 'datasets/WIDER_train/images/0--Parade/0_Parade_Parade_0_771.jpg'
if not os.path.exists(image_path):
    print(f"Error: Image file not found at {image_path}")
    exit()

# Perform inference
print(f"Performing inference on {image_path}...")
results = model(image_path)
print("Inference complete.")

# The results object is a list of Results objects
# For a single image, it will be a list with one element
result = results[0]

# Save the image with bounding boxes
output_path = 'parade_crowd_result.jpg'
result.save(filename=output_path)

print(f"Result saved to {output_path}")

# To display the image (optional, works in local environment with GUI)
# try:
#     import cv2
#     import numpy as np
#     annotated_frame = results[0].plot()
#     cv2.imshow("YOLOv11 Face Detection", annotated_frame)
#     print("Press any key to close the image window.")
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
# except ImportError:
#     print("OpenCV not installed, cannot display the image. Please check the saved file.")
# except Exception as e:
#     print(f"Could not display image due to an error: {e}") 