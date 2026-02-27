# 🚗 Realtime Vehicle Detection & License Plate OCR

A real-time computer vision system that detects and tracks vehicles, reads license plates via OCR, and logs directional traffic data (IN/OUT) to a SQLite database — all using YOLOv11 and EasyOCR.

---

## 📸 Features

- **Vehicle Detection & Tracking** — Detects cars, trucks, buses, motorcycles, and more using YOLOv11
- **License Plate Detection** — Custom-trained YOLO model (`best.pt`) locates plates within each vehicle crop
- **OCR on License Plates** — EasyOCR extracts plate text in English (with Nepali/Devanagari support available)
- **Directional Counting (IN/OUT)** — Virtual trip lines track vehicles crossing in each direction
- **SQLite Logging** — Every crossing event is logged with track ID, vehicle type, direction, plate text, and timestamp
- **CSV Export** — On exit, the full vehicle log is exported to `vehicle_log.csv`

---

## 🧰 Tech Stack

| Tool | Purpose |
|---|---|
| [Ultralytics YOLOv11](https://github.com/ultralytics/ultralytics) | Vehicle & license plate detection |
| [EasyOCR](https://github.com/JaidedAI/EasyOCR) | License plate text recognition |
| [OpenCV](https://opencv.org/) | Video I/O and frame rendering |
| [SQLite3](https://docs.python.org/3/library/sqlite3.html) | Local event logging |
| [Pandas](https://pandas.pydata.org/) | CSV export of vehicle log |

---

## 📁 Project Structure

```
├── main.py               # Main detection + tracking + OCR script
├── yolo11l.pt            # YOLOv11 large model for vehicle detection
├── requirements.txt      # Required libraries
├── best.pt               # Custom-trained YOLO model for license plates
├── test_video.mp4        # Input video file
├── vehicle_log.db        # SQLite database (auto-created on run)
└── vehicle_log.csv       # Exported log (generated on exit)
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/puriiiii/realtime-vehicle-person-detection-ocr.git
cd realtime-vehicle-person-detection-ocr
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
or 
pip install ultralytics easyocr opencv-python pandas
```

> **Note:** EasyOCR will download language model weights on first run. GPU is recommended for real-time performance.

### 3. Add your model weights and video

- Place `yolo11l.pt` (YOLOv11 large) in the project root — download from [Ultralytics](https://github.com/ultralytics/ultralytics)
- Place your custom license plate model as `best.pt` in the project root
- Place your input video as `test_video.mp4` in the project root

### 4. Run

```bash
python main.py
```

Press **`q`** to quit. The vehicle log will be automatically exported to `vehicle_log.csv` on exit.

---

## 🗄️ Database Schema

Events are stored in `vehicle_log.db` under the `vehicle_log` table:

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Auto-incremented primary key |
| `track_id` | INTEGER | Unique ID assigned to each tracked vehicle |
| `vehicle_type` | TEXT | Detected class (e.g. `car`, `truck`, `bus`) |
| `direction` | TEXT | `IN` or `OUT` |
| `number_plate` | TEXT | OCR-extracted plate text |
| `timestamp` | TEXT | Event time (`YYYY-MM-DD HH:MM:SS`) |

---

## ⚙️ Configuration

You can adjust the following variables in `main.py` to suit your camera setup:

```python

rtsp_url = "rtsp://<username>:<password>@<ip_address>:<port>/<stream_path>"  #RTSP of your local cctv camepra 
y_coordinate = 500   # Y-position of the virtual trip line

# IN line region (left side of frame)
cv2.line(frame, (100, y_coordinate), (550, y_coordinate), ...)

# OUT line region (right side of frame)
cv2.line(frame, (700, y_coordinate), (1050, y_coordinate), ...)
```

Modify the `x` ranges in the IN/OUT detection conditionals to match your video resolution and lane positions.

---

## 🌐 OCR Language Support

EasyOCR is initialized for English by default. To add Nepali (Devanagari) or other languages, update this line in `main.py`:

```python
reader = easyocr.Reader(['en', 'ne'])  # 'ne' for Nepali
```

Other supported South Asian scripts include Hindi (`hi`) and Newari.

---

## 📋 Output Example

```csv
id,track_id,vehicle_type,direction,number_plate,timestamp
1,4,car,IN,BA 1 KA 2345,2024-11-01 10:23:11
2,7,truck,OUT,BA 2 JA 9900,2024-11-01 10:23:18
```


https://github.com/user-attachments/assets/ce535cb5-f73e-4b00-a2cd-c05fda4381b2


---

## 📄 License

This project is open source. Feel free to use, modify, and distribute it.
