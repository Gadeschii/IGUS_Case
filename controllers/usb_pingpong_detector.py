import cv2
import supervision as sv
from ultralytics import YOLO

# Load YOLO model (pretrained on COCO)
model = YOLO("yolov8n.pt")  # Asegúrate de tener yolov8n.pt descargado

def usb_detect_pingpong(camera_index=1, debug=False) -> bool:
    """
    Detect a ping pong ball using a USB camera.

    Parameters
    ----------
    camera_index : int
        Index of the USB camera (usually 0 or 1)
    debug : bool
        If True, shows the image with bounding boxes

    Returns
    -------
    bool
        True if ping pong ball is detected, False otherwise
    """
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        raise RuntimeError("❌ Cannot open USB camera.")

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError("❌ Failed to capture image from USB camera.")

    # Run detection
    results = model(frame)[0]
    detections = sv.Detections.from_yolov8(results)

    labels = results.names
    for cls_id in detections.class_id:
        if labels[cls_id] == "sports ball":
            if debug:
                print("✅ USB camera detected ping pong ball.")
            return True

    if debug:
        print("⚠️ No ping pong ball detected in USB camera.")
    return False
