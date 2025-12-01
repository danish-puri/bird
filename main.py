import cv2
import pandas as pd
from ultralytics import YOLO
from collections import defaultdict
import sqlite3
from datetime import datetime
import easyocr

# Load the YOLO models 
vehicle_model = YOLO('yolo11l.pt')  # for detecting vehicles
#best.pt is the custom trained model for license plates
plate_model = YOLO('best.pt')      # for detecting license plates
reader = easyocr.Reader(['en'])  # English + Nepali (Devanagari). #Newari, Hindi also available but not used.

# OCR function for cropped plate images
def perform_ocr_on_image(img, coordinates):
    x, y, w, h = map(int, coordinates)
    cropped_img = img[y:h, x:w]
    gray_img = cv2.cvtColor(cropped_img, cv2.COLOR_RGB2GRAY)
    results = reader.readtext(gray_img)

    text = ""
    for res in results:
        if len(results) == 1 or (len(res[1]) > 1 and res[2] > 0.2):
            text = res[1]
    return str(text)
class_list = vehicle_model.names

# Connect to SQLite database
conn = sqlite3.connect('vehicle_log.db')
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehicle_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        track_id INTEGER,
        vehicle_type TEXT,
        direction TEXT,
        number_plate TEXT,
        timestamp TEXT
    )
''')
conn.commit()

# Function to log events
def log_event(track_id, vehicle_type, direction, number_plate):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO vehicle_log (track_id, vehicle_type, direction, number_plate, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (track_id, vehicle_type, direction, number_plate, timestamp))
    conn.commit()

# Open the video file
cap = cv2.VideoCapture('test_video.mp4')

y_coordinate = 500  # Vehicle OUT/IN line position

# Count tracking
in_count = defaultdict(int)
out_count = defaultdict(int)
in_ids = set()
out_ids = set()
previous_y = {}

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = vehicle_model.track(frame, persist=True, classes=[0,1,2,3,5,6,7])

    if results[0].boxes.data is not None:
        boxes = results[0].boxes.xyxy.cpu()
        track_ids = results[0].boxes.id.int().cpu().tolist()
        class_indices = results[0].boxes.cls.int().cpu().tolist()
        confidences = results[0].boxes.conf.cpu()

        cv2.line(frame, (100, y_coordinate), (550, y_coordinate), (0, 255, 0), 3)  # IN line
        cv2.line(frame, (700, y_coordinate), (1050, y_coordinate), (0, 0, 255), 3)  # OUT line

        for box, track_id, class_idx in zip(boxes, track_ids, class_indices):
            x1, y1, x2, y2 = map(int, box)
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            class_name = class_list[class_idx]

            vehicle_crop = frame[y1:y2, x1:x2]
            plate_text = ""

            # Detect license plate in the cropped vehicle image
            plate_results = plate_model(vehicle_crop)

            if plate_results and plate_results[0].boxes.data is not None:
                plate_boxes = plate_results[0].boxes.xyxy.cpu()
                for plate_box in plate_boxes:
                    px1, py1, px2, py2 = map(int, plate_box)
                    px1, py1, px2, py2 = max(0, px1), max(0, py1), min(vehicle_crop.shape[1], px2), min(vehicle_crop.shape[0], py2)
                    try:
                        plate_text = perform_ocr_on_image(vehicle_crop, (px1, py1, px2, py2))
                        if plate_text:
                            break  # Use first detected plate
                    except:
                        continue

            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.putText(frame, f"ID: {track_id} {class_name}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            prev_cy = previous_y.get(track_id, cy)
            previous_y[track_id] = cy

            # IN detection (downward movement)
            if prev_cy < y_coordinate <= cy and 100 < cx < 550 and track_id not in in_ids:
                in_ids.add(track_id)
                in_count[class_name] += 1
                log_event(track_id, class_name, 'IN', plate_text)

            # OUT detection (upward movement)
            if prev_cy > y_coordinate >= cy and 700 < cx < 1050 and track_id not in out_ids:
                out_ids.add(track_id)
                out_count[class_name] += 1
                log_event(track_id, class_name, 'OUT', plate_text)

        # Display counts
        y_offset = 30
        for class_name, count in in_count.items():
            cv2.putText(frame, f"Number of {class_name}'s in: {count}", (50, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            y_offset += 30

        for class_name, count in out_count.items():
            cv2.putText(frame, f"Number of {class_name}'s out: {count}", (800, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            y_offset += 30

    cv2.imshow("YOLO Object Tracking & Counting", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
conn.close()
# Export database to CSV
df = pd.read_sql_query("SELECT * FROM vehicle_log", sqlite3.connect('vehicle_log.db'))
df.to_csv("vehicle_log.csv", index=False)
print("Exported vehicle log to vehicle_log.csv")
cv2.destroyAllWindows()

