import os
from datetime import datetime
import cv2
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator

def detect_pingpong_presence(rtsp_url: str, show_debug: bool = False) -> bool:
    """
    Detects the presence of a ping pong ball using YOLO from an RTSP stream.

    Parameters
    ----------
    rtsp_url : str
        RTSP stream URL of the camera.

    show_debug : bool
        If True, displays and saves the analyzed frames.

    Returns
    -------
    bool
        True if a ping pong ball is detected.

    Raises
    ------
    RuntimeError
        If the stream fails or the ball is not detected.
    """
    model = YOLO("yolov8n.pt")
    save_dir = r"C:\Users\javie\Desktop\IgusRobotsCase\IgusRobotControllerCase\IGUS_Case\photos"
    os.makedirs(save_dir, exist_ok=True)

    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        raise RuntimeError("❌ Failed to open RTSP stream.")

    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError("❌ Could not read frame from camera.")

    # Get center square region
    h, w, _ = frame.shape
    square_size = 800
    cx, cy = w // 2, h // 2
    x1 = max(cx - square_size // 2, 0)
    y1 = max(cy - square_size // 2, 0)
    x2 = min(cx + square_size // 2, w)
    y2 = min(cy + square_size // 2, h)
    center_crop = frame[y1:y2, x1:x2]

    # Save the cropped region
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    crop_path = os.path.join(save_dir, f"pingpong_crop_{timestamp}.jpg")
    cv2.imwrite(crop_path, center_crop)

    # Run YOLO detection ONLY on cropped image
    results = model.predict(source=center_crop, conf=0.5)
    detections = results[0].boxes

    if not detections or len(detections.cls) == 0:
        raise RuntimeError("❌ No objects detected in cropped image.")

    # Debug visualization with bounding boxes
    if show_debug:
        annotator = Annotator(center_crop.copy())
        for box, cls_id in zip(detections.xyxy, detections.cls):
            annotator.box_label(box, label=f"cls {int(cls_id)}")
        cv2.imshow("Detection Overlay", annotator.result())
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # Check if any detected object is a sports ball (class 37)
    for cls in detections.cls:
        if int(cls) == 37:
            print(f"📦 Detected classes: {[int(cls) for cls in detections.cls]}")
            print(f"🟫 Bounding boxes: {detections.xyxy}")
            return True

    raise RuntimeError("❌ No ping pong ball detected.")
