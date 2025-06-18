def detect_pingpong_color(rtsp_url: str, show_debug: bool = False) -> str:
    """
    Detects a ping pong ball using a YOLO model and determines its color (white or black)
    based on the brightness of the detected region.

    Parameters
    ----------
    rtsp_url : str
        RTSP stream URL of the camera.

    show_debug : bool
        If True, displays the analyzed frame for debugging.

    Returns
    -------
    str
        'white' if the ball is bright, 'black' otherwise.

    Raises
    ------
    RuntimeError
        If the camera stream fails or the ball is not detected.
    """
    from ultralytics import YOLO
    import cv2

    # Load the YOLOv8 model (ensure it's downloaded)
    model = YOLO("yolov8n.pt")

    # Open the RTSP stream
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        raise RuntimeError("❌ Failed to open RTSP stream.")

    # Capture a single frame
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError("❌ Could not read frame from camera.")

    # Run YOLO inference for class 37 (sports ball)
    results = model.predict(source=frame, conf=0.5)

    # Optionally show the frame for debugging
    if show_debug:
        cv2.imshow("Detected Frame", frame)
        cv2.waitKey(1000)  # Display the image for 1000ms
        cv2.destroyAllWindows()

    # If no detections, raise error
    if not results or not results[0].boxes or len(results[0].boxes.xyxy) == 0:
        raise RuntimeError("❌ No ping pong ball detected.")

    # Get the first detected bounding box
    box = results[0].boxes.xyxy[0].cpu().numpy().astype(int)
    x1, y1, x2, y2 = box
    ball_region = frame[y1:y2, x1:x2]

    # Convert the ball region to HSV to better analyze brightness
    hsv = cv2.cvtColor(ball_region, cv2.COLOR_BGR2HSV)
    brightness = hsv[:, :, 2].mean()

    return "white" if brightness > 100 else "black"
