import os
import threading
from datetime import datetime
import cv2
import numpy as np
import time
from ultralytics import *

model = YOLO("C:/Users/javie/Desktop/IgusRobotsCase/IgusRobotControllerCase/IGUS_Case/train14/weights/best.pt")

# def detect_ball_and_color(rtsp_url: str, expected_colors=("white", "blue", "orange"), debug=False) -> tuple[bool, str | None]:
#     """
#     Detecta si hay una pelota y determina su color usando YOLO, con depuración visual y validación.
    
#     Returns:
#         (bool, color) → Ej: (True, "white") o (False, None)
#     """
#     cap = cv2.VideoCapture(rtsp_url)
#     ret, frame = cap.read()
#     cap.release()

#     if not ret:
#         print("❌ No se pudo capturar la imagen de la cámara.")
#         return False, None

#     # 🖼️ Guarda imagen para debugging visual (desactivar si no se necesita)
#     if debug:
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         cv2.imwrite("debug_latest.jpg", frame)
#         cv2.imshow("🖼️ Vista de cámara", frame)
#         cv2.waitKey(0)

#     # 🔍 Ejecuta la detección
#     results = model(frame, conf=0.5)[0]
#     detected_color = None
    
#     for box in results.boxes:
#         class_id = int(box.cls[0])
#         class_name = model.names[class_id]

#         if class_name == "PingPongWhite" and "white" in expected_colors:
#             detected_color = "white"
#             return True, detected_color
#         elif class_name == "PingPongBlue" and "blue" in expected_colors:
#             detected_color = "blue"
#             return True, detected_color
#         elif class_name == "PingPongOrange" and "orange" in expected_colors:
#             detected_color = "orange"
#             return True, detected_color

#     return False, None









class VisionManager:
    def __init__(self, rtsp_sources: dict[str, str], poll_interval=1.0):
        """
        rtsp_sources: Dict like {"scara": "rtsp://url1", "rebel": "rtsp://url2"}
        poll_interval: seconds between YOLO inferences
        """
        self.rtsp_sources = rtsp_sources
        self.poll_interval = poll_interval
        self.detections = {name: (False, None, 0.0) for name in rtsp_sources}
        self._threads = []
        self._lock = threading.Lock()

        for name, url in rtsp_sources.items():
            t = threading.Thread(target=self._update_loop, args=(name, url), daemon=True)
            t.start()
            self._threads.append(t)

    def _update_loop(self, name: str, rtsp_url: str):
        while True:
            try:
                cap = cv2.VideoCapture(rtsp_url)
                ret, frame = cap.read()
                cap.release()

                if not ret:
                    self._set_detection(name, (False, None))
                    time.sleep(self.poll_interval)
                    continue

                results = model(frame, conf=0.5)[0]
                found = False
                color = None

                for box in results.boxes:
                    class_id = int(box.cls[0].item())
                    label = model.names[class_id].lower()
                    if label.startswith("pingpong"):
                        found = True
                        if "white" in label:
                            color = "white"
                        elif "blue" in label:
                            color = "blue"
                        elif "orange" in label:
                            color = "orange"
                        else:
                            color = "unknown"
                        break

                self._set_detection(name, (found, color))
            except Exception as e:
                print(f"[{name.upper()} CAMERA ERROR] {e}")
                self._set_detection(name, (False, None))

            time.sleep(self.poll_interval)

    def _set_detection(self, name: str, detection: tuple[bool, str | None]):
        with self._lock:
            self.detections[name] = (*detection, time.time())


    def get_detection(self, name: str) -> tuple[bool, str | None, float]:
        with self._lock:
            return self.detections.get(name, (False, None, 0.0))










# def detect_pingpong_presence(rtsp_url: str, show_debug: bool = False) -> str | None:
#     """
#     Detects a ping pong ball by finding circular shapes in the center of the frame
#     and classifies its color (white or black) based on brightness.

#     Returns:
#         "white" / "black" if a circular ball is detected, or None otherwise.
#     """
#     save_dir = r"C:\Users\javie\Desktop\IgusRobotsCase\IgusRobotControllerCase\IGUS_Case\photos"
#     os.makedirs(save_dir, exist_ok=True)

#     cap = cv2.VideoCapture(rtsp_url)
#     if not cap.isOpened():
#         raise RuntimeError("❌ Failed to open RTSP stream.")

#     ret, frame = cap.read()
#     cap.release()
#     if not ret:
#         raise RuntimeError("❌ Could not read frame from camera.")

#     # Crop center region
#     h, w, _ = frame.shape
#     square_size = 800
#     cx, cy = w // 2, h // 2
#     x1 = max(cx - square_size // 2, 0)
#     y1 = max(cy - square_size // 2, 0)
#     x2 = min(cx + square_size // 2, w)
#     y2 = min(cy + square_size // 2, h)
#     center_crop = frame[y1:y2, x1:x2]

#     # Convert to grayscale and blur to improve circle detection
#     gray = cv2.cvtColor(center_crop, cv2.COLOR_BGR2GRAY)
#     gray_blurred = cv2.medianBlur(gray, 5)

#     # Detect circles
#     circles = cv2.HoughCircles(
#         gray_blurred,
#         cv2.HOUGH_GRADIENT,
#         dp=1.2,
#         minDist=50,
#         param1=100,
#         param2=30,
#         minRadius=10,
#         maxRadius=60
#     )

#     if circles is not None:
#         circles = np.uint16(np.around(circles))
#         for i, circle in enumerate(circles[0, :]):
#             x, y, r = circle
#             x1_crop = max(x - r, 0)
#             y1_crop = max(y - r, 0)
#             x2_crop = min(x + r, center_crop.shape[1])
#             y2_crop = min(y + r, center_crop.shape[0])
#             ball_crop = center_crop[y1_crop:y2_crop, x1_crop:x2_crop]

#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             ball_path = os.path.join(save_dir, f"circle_ball_crop_{timestamp}.jpg")
#             cv2.imwrite(ball_path, ball_crop)

#             # Analyze brightness
#             hsv = cv2.cvtColor(ball_crop, cv2.COLOR_BGR2HSV)
#             brightness = hsv[:, :, 2].mean()
#             color = "white" if brightness > 100 else "black"

#             print(f"✅ Circle detected. Brightness: {brightness:.1f}, Color: {color}")

#             if show_debug:
#                 annotated = center_crop.copy()
#                 cv2.circle(annotated, (x, y), r, (0, 255, 0), 2)
#                 cv2.imshow("Detected Circle", annotated)
#                 cv2.waitKey(1000)
#                 cv2.destroyAllWindows()

#             return color

#     print("⚠️ No circular ball detected.")
#     return None


# def detect_pingpong_presence_color_white(rtsp_url: str, show_debug: bool = False) -> str | None:
#     # model = YOLO("C:/Users/javie/Desktop/IgusRobotsCase/IgusRobotControllerCase/IGUS_Case/train14/weights/best.pt")

#     # Connect to camera
#     cap = cv2.VideoCapture(rtsp_url)
#     ret, frame = cap.read()
#     if not ret:
#         print("Cannot connect to camera")
#         return False
    
#     h, w = frame.shape[:2]
    
#     #Zone detection definition
#     roi_x, roi_y = int(w*0.575), int(h*0.375)
#     roi_w, roi_h = int(w*0.125), int(h*0.275)
#     zone_x1, zone_y1 = roi_x, roi_y
#     zone_x2, zone_y2 = roi_x+roi_w, roi_y+roi_h
    
#     results = model(frame, conf=0.5)[0]
#     whiteBallDetected = False
    
#     for box in results.boxes:
#         x1, y1, x2, y2 = map(int, box.xyxy[0])
#         cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

#         class_id = int(box.cls[0])
#         class_name = model.names[class_id]

#         # Check if PingPongWhite is on zone
#         if class_name == "PingPongWhite" and zone_x1 <= cx <= zone_x2 and zone_y1 <= cy <= zone_y2:
#             whiteBallDetected = True
#             cv2.putText(frame, f"{class_name} DETECTED", (x1, y1 - 10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)


#         # Draw bounding box
#         cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)
#         cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

#     # Draw Interest zone
#     cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (0, 255, 255), 2)

#     # Show state
#     estado = "Finded" if whiteBallDetected else "NO DETECTED"
#     cv2.putText(frame, f"PingPongWhite: {estado}", (10, 30),
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

#     # Show the frame
#     cv2.imshow("YOLOv8 - RTSP + Zona", frame)

#     cap.release()
#     cv2.destroyAllWindows()
#     return whiteBallDetected
    
# def detect_pingpong_presence_color_blue(rtsp_url: str, show_debug: bool = False) -> str | None:
#     # model = YOLO("C:/Users/javie/Desktop/IgusRobotsCase/IgusRobotControllerCase/IGUS_Case/train14/weights/best.pt")

#     # Connect to camera
#     cap = cv2.VideoCapture(rtsp_url)
#     ret, frame = cap.read()
#     if not ret:
#         print("Cannot connect to camera")
#         return False
    
#     h, w = frame.shape[:2]
    
#     #Zone detection definition
#     roi_x, roi_y = int(w*0.575), int(h*0.375)
#     roi_w, roi_h = int(w*0.125), int(h*0.275)
#     zone_x1, zone_y1 = roi_x, roi_y
#     zone_x2, zone_y2 = roi_x+roi_w, roi_y+roi_h
    
#     results = model(frame, conf=0.5)[0]
#     blueBallDetected = False
    
#     for box in results.boxes:
#         x1, y1, x2, y2 = map(int, box.xyxy[0])
#         cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

#         class_id = int(box.cls[0])
#         class_name = model.names[class_id]

#         # Check if PingPongBlue is on zone
       

#         if class_name == "PingPongBlue" and zone_x1 <= cx <= zone_x2 and zone_y1 <= cy <= zone_y2:
#             blueBallDetected = True
#             cv2.putText(frame, f"{class_name} DETECTED", (x1, y1 - 10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

#         # Draw bounding box
#         cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)
#         cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

#     # Draw Interest zone
#     cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (0, 255, 255), 2)

#     # Show state
#     estado = "Finded" if blueBallDetected else "NO DETECTED"
#     cv2.putText(frame, f"PingPongBlue: {estado}", (10, 30),
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

#     # Show the frame
#     cv2.imshow("YOLOv8 - RTSP + Zona", frame)

#     cap.release()
#     cv2.destroyAllWindows()
#     return blueBallDetected
    
# def detect_pingpong_presence_color_white2(rtsp_url: str, show_debug: bool = False) -> str | None:
#     # model = YOLO("C:/Users/javie/Desktop/IgusRobotsCase/IgusRobotControllerCase/IGUS_Case/train14/weights/best.pt")

#     # Connect to camera
#     cap = cv2.VideoCapture(rtsp_url)
#     # cap = cv2.VideoCapture(1)
#     ret, frame = cap.read()
#     if not ret:
#         print("Cannot connect to camera")
#         return False
    
#     h, w = frame.shape[:2]
    
#     #Zone detection definition
#     roi_x, roi_y = int(w*0.575), int(h*0.375)
#     roi_w, roi_h = int(w*0.125), int(h*0.275)
#     zone_x1, zone_y1 = roi_x, roi_y
#     zone_x2, zone_y2 = roi_x+roi_w, roi_y+roi_h
    
#     results = model(frame, conf=0.5)[0]
#     whiteBallDetected = False
    
#     for box in results.boxes:
#         x1, y1, x2, y2 = map(int, box.xyxy[0])
#         cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

#         class_id = int(box.cls[0])
#         class_name = model.names[class_id]

#         # Check if PingPongWhite is on zone
#         if class_name == "PingPongWhite" and zone_x1 <= cx <= zone_x2 and zone_y1 <= cy <= zone_y2:
#             whiteBallDetected = True
#             cv2.putText(frame, f"{class_name} DETECTED", (x1, y1 - 10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)


#         # Draw bounding box
#         cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)
#         cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

#     # Draw Interest zone
#     cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (0, 255, 255), 2)

#     # Show state
#     estado = "Finded" if whiteBallDetected else "NO DETECTED"
#     cv2.putText(frame, f"PingPongWhite: {estado}", (10, 30),
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

#     # Show the frame
#     cv2.imshow("YOLOv8 - RTSP + Zona", frame)

#     cap.release()
#     cv2.destroyAllWindows()
#     return whiteBallDetected
    
# def detect_pingpong_presence_color_blue2(rtsp_url: str, show_debug: bool = False) -> str | None:
#     # model = YOLO("C:/Users/javie/Desktop/IgusRobotsCase/IgusRobotControllerCase/IGUS_Case/train14/weights/best.pt")

#     # Connect to camera
#     cap = cv2.VideoCapture(rtsp_url)
#     # cap = cv2.VideoCapture(1)
#     ret, frame = cap.read()
#     if not ret:
#         print("Cannot connect to camera")
#         return False
    
#     h, w = frame.shape[:2]
    
#     #Zone detection definition
#     roi_x, roi_y = int(w*0.575), int(h*0.375)
#     roi_w, roi_h = int(w*0.125), int(h*0.275)
#     zone_x1, zone_y1 = roi_x, roi_y
#     zone_x2, zone_y2 = roi_x+roi_w, roi_y+roi_h
    
#     results = model(frame, conf=0.5)[0]
#     blueBallDetected = False
    
#     for box in results.boxes:
#         x1, y1, x2, y2 = map(int, box.xyxy[0])
#         cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

#         class_id = int(box.cls[0])
#         class_name = model.names[class_id]

#         # Check if PingPongBlue is on zone
       

#         if class_name == "PingPongBlue" and zone_x1 <= cx <= zone_x2 and zone_y1 <= cy <= zone_y2:
#             blueBallDetected = True
#             cv2.putText(frame, f"{class_name} DETECTED", (x1, y1 - 10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

#         # Draw bounding box
#         cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)
#         cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

#     # Draw Interest zone
#     cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (0, 255, 255), 2)

#     # Show state
#     estado = "Finded" if blueBallDetected else "NO DETECTED"
#     cv2.putText(frame, f"PingPongBlue: {estado}", (10, 30),
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

#     # Show the frame
#     cv2.imshow("YOLOv8 - RTSP + Zona", frame)

#     cap.release()
#     cv2.destroyAllWindows()
#     return blueBallDetected

    

    




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
