import os
from datetime import datetime
import cv2
import numpy as np

def detect_pingpong_presence(rtsp_url: str, show_debug: bool = False) -> str | None:
    """
    Detects a ping pong ball by finding circular shapes in the center of the frame
    and classifies its color (white or black) based on brightness.

    Returns:
        "white" / "black" if a circular ball is detected, or None otherwise.
    """
    save_dir = r"C:\Users\javie\Desktop\IgusRobotsCase\IgusRobotControllerCase\IGUS_Case\photos"
    os.makedirs(save_dir, exist_ok=True)

    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        raise RuntimeError("❌ Failed to open RTSP stream.")

    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError("❌ Could not read frame from camera.")

    # Crop center region
    h, w, _ = frame.shape
    square_size = 800
    cx, cy = w // 2, h // 2
    x1 = max(cx - square_size // 2, 0)
    y1 = max(cy - square_size // 2, 0)
    x2 = min(cx + square_size // 2, w)
    y2 = min(cy + square_size // 2, h)
    center_crop = frame[y1:y2, x1:x2]

    # Convert to grayscale and blur to improve circle detection
    gray = cv2.cvtColor(center_crop, cv2.COLOR_BGR2GRAY)
    gray_blurred = cv2.medianBlur(gray, 5)

    # Detect circles
    circles = cv2.HoughCircles(
        gray_blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=50,
        param1=100,
        param2=30,
        minRadius=10,
        maxRadius=60
    )

    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i, circle in enumerate(circles[0, :]):
            x, y, r = circle
            x1_crop = max(x - r, 0)
            y1_crop = max(y - r, 0)
            x2_crop = min(x + r, center_crop.shape[1])
            y2_crop = min(y + r, center_crop.shape[0])
            ball_crop = center_crop[y1_crop:y2_crop, x1_crop:x2_crop]

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ball_path = os.path.join(save_dir, f"circle_ball_crop_{timestamp}.jpg")
            cv2.imwrite(ball_path, ball_crop)

            # Analyze brightness
            hsv = cv2.cvtColor(ball_crop, cv2.COLOR_BGR2HSV)
            brightness = hsv[:, :, 2].mean()
            color = "white" if brightness > 100 else "black"

            print(f"✅ Circle detected. Brightness: {brightness:.1f}, Color: {color}")

            if show_debug:
                annotated = center_crop.copy()
                cv2.circle(annotated, (x, y), r, (0, 255, 0), 2)
                cv2.imshow("Detected Circle", annotated)
                cv2.waitKey(1000)
                cv2.destroyAllWindows()

            return color

    print("⚠️ No circular ball detected.")
    return None







# import os
# from datetime import datetime
# import cv2
# import numpy as np
# from ultralytics import YOLO

# def detect_pingpong_presence(rtsp_url: str, show_debug: bool = False) -> str | None:
#     """
#     Detects a ping pong ball (in a cropped region) using YOLO and classifies its color (white or black).

#     Returns:
#         "white" / "black" if detected, or None if no sports ball found.
#     """
#     save_dir = r"C:\Users\javie\Desktop\IgusRobotsCase\IgusRobotControllerCase\IGUS_Case\photos"
#     os.makedirs(save_dir, exist_ok=True)

#     model = YOLO("yolov8n.pt")

#     cap = cv2.VideoCapture(rtsp_url)
#     if not cap.isOpened():
#         raise RuntimeError("❌ Failed to open RTSP stream.")

#     ret, frame = cap.read()
#     cap.release()
#     if not ret:
#         raise RuntimeError("❌ Could not read frame from camera.")

#     # === Get center region to reduce detection area ===
#     h, w, _ = frame.shape
#     square_size = 550
#     cx, cy = w // 2, h // 2
#     x1 = max(cx - square_size // 2, 0)
#     y1 = max(cy - square_size // 2, 0)
#     x2 = min(cx + square_size // 2, w)
#     y2 = min(cy + square_size // 2, h)
#     center_crop = frame[y1:y2, x1:x2]

#     # Save cropped frame
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     crop_path = os.path.join(save_dir, f"pingpong_center_crop_{timestamp}.jpg")
#     cv2.imwrite(crop_path, center_crop)

#     # Run YOLO on the cropped region
#     results = model.predict(source=center_crop, conf=0.3)
#     detections = results[0].boxes

#     if not detections or len(detections.cls) == 0:
#         print("⚠️ No objects detected in center region.")
#         return None

#     for box, cls_id in zip(detections.xyxy, detections.cls):
#         if int(cls_id) == 37:  # sports ball
#             x1_box, y1_box, x2_box, y2_box = map(int, box.tolist())
#             ball_crop = center_crop[y1_box:y2_box, x1_box:x2_box]

#             # Save cropped ball
#             ball_crop_path = os.path.join(save_dir, f"pingpong_ball_crop_{timestamp}.jpg")
#             cv2.imwrite(ball_crop_path, ball_crop)

#             # Analyze brightness
#             hsv = cv2.cvtColor(ball_crop, cv2.COLOR_BGR2HSV)
#             brightness = hsv[:, :, 2].mean()
#             color = "white" if brightness > 100 else "black"

#             print(f"✅ Ping pong ball detected in center area. Brightness: {brightness:.1f}, Color: {color}")

#             if show_debug:
#                 annotated = center_crop.copy()
#                 cv2.rectangle(annotated, (x1_box, y1_box), (x2_box, y2_box), (0, 255, 0), 2)
#                 cv2.imshow("Ball Detection", annotated)
#                 cv2.waitKey(1000)
#                 cv2.destroyAllWindows()

#             return color

#     print("⚠️ No ping pong ball detected in center area.")
#     return None
