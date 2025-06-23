import cv2
import os
from datetime import datetime
import numpy as np
import supervision as sv
from ultralytics import YOLO

# Load YOLO model (pretrained on COCO)
model = YOLO("yolov8n.pt")  # Make sure it's downloaded

def usb_detect_pingpong_color(camera_index=1, debug=True) -> str | None:
    """
    Detects a ping pong ball using a USB camera and determines its color.

    Parameters
    ----------
    camera_index : int
        USB camera index (typically 0 or 1).
    debug : bool
        If True, shows and saves debug images.

    Returns
    -------
    str or None
        "white" or "black" based on brightness, or None if ball is not detected.
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
    results = model(frame)[0]
    detections = sv.Detections.from_yolov8(results)
    labels = results.names

    for i, cls_id in enumerate(detections.class_id):
        if labels[cls_id] == "sports ball":
            # Extract bounding box
            x1, y1, x2, y2 = detections.xyxy[i].astype(int)
            ball_crop = frame[y1:y2, x1:x2]

            # Save cropped ball
            ball_crop_path = os.path.join(save_dir, f"usb_ball_crop_{timestamp}.jpg")
            cv2.imwrite(ball_crop_path, ball_crop)

            # Calculate brightness
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
        print("⚠️ No ping pong ball detected in USB camera.")
    return None
