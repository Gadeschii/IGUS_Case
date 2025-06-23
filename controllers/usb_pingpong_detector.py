import cv2
import os
from datetime import datetime
import numpy as np
from ultralytics import YOLO

# Load YOLO model
model = YOLO("yolov8n.pt")  # Asegúrate de tenerlo descargado

def usb_detect_pingpong_color(camera_index=1, debug=True) -> str | None:
    """
    Detects a ping pong ball using a USB camera and determines its color.

    Returns "white" or "black" based on brightness, or None if not detected.
    """
    save_dir = os.path.join(os.getcwd(), "photosUsb")
    os.makedirs(save_dir, exist_ok=True)

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError("❌ Cannot open USB camera.")

    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError("❌ Failed to capture image from USB camera.")

    # Save full frame
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_frame_path = os.path.join(save_dir, f"usb_full_frame_{timestamp}.jpg")
    cv2.imwrite(full_frame_path, frame)

    # Run YOLO detection
    results = model.predict(frame, conf=0.3)[0]

    if results.boxes is None or results.boxes.cls is None:
        if debug:
            print("⚠️ No detections.")
        return None

    for box, cls_id in zip(results.boxes.xyxy, results.boxes.cls):
        cls_id = int(cls_id.item())
        if model.names[cls_id] == "sports ball":
            x1, y1, x2, y2 = map(int, box)
            ball_crop = frame[y1:y2, x1:x2]

            # Save cropped ball
            ball_crop_path = os.path.join(save_dir, f"usb_ball_crop_{timestamp}.jpg")
            cv2.imwrite(ball_crop_path, ball_crop)

            # Determine brightness
            hsv = cv2.cvtColor(ball_crop, cv2.COLOR_BGR2HSV)
            brightness = hsv[:, :, 2].mean()
            color = "white" if brightness > 100 else "black"

            if debug:
                print(f"✅ Ping pong ball detected. Brightness: {brightness:.1f}")
                print(f"🎨 Detected color: {color}")
                cv2.imshow("Ping Pong Ball (USB)", ball_crop)
                cv2.waitKey(1000)
                cv2.destroyAllWindows()

            return color

    if debug:
        print("⚠️ No sports ball detected in USB image.")
    return None
