
### Real-Time Vehicle & Pedestrian Directional Tracking System

LibertyTrack 🚗🚶

[![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)](https://www.python.org/)
[![YOLOv11](https://img.shields.io/badge/YOLO-11n%20%2F%2011l-darkgreen?logo=ultralytics)](https://docs.ultralytics.com/models/yolo11/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![arXiv](https://img.shields.io/badge/Paper-arXiv-red)](https://arxiv.org/)
[![Deployment](https://img.shields.io/badge/Deployed%20at-Liberty%20College%2C%20Nepal-orange)]()

> A fault-tolerant, real-time computer vision system that detects and tracks vehicles and pedestrians, reads license plates via OCR, classifies directional movement (IN/OUT), and logs all events — deployed at **Liberty College, and Global College, Kathmandu, Nepal**.


---


https://github.com/user-attachments/assets/424e83c7-0f66-4583-8f43-618ea3ced993


## 📄 Research Paper

This repository accompanies the academic paper:

> **LibertyTrack: A Real-Time Vehicle and Pedestrian Directional Tracking System for Resource-Constrained Environments**  
> Danish Puri — New York University, Tandon School of Engineering  
> *Prepared for IEEE-style submission*

The paper documents the full system design, methodology, and real-world evaluation results including:
- 20.8 FPS sustained throughput on Apple M2 (no CUDA required)
- 92–95% IN/OUT directional classification accuracy
- 18-hour uninterrupted runtime with zero data loss
- Failure case analysis: low-light, motion blur, motorcycle clustering

📥 **[Download the paper (PDF)](./final_publication_ready_paper.pdf)** · 📋 **[arXiv preprint](#)** *(link to be added upon upload)*

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Vehicle & Pedestrian Detection** | Detects cars, motorcycles, and people using YOLO11 |
| 🪪 **License Plate Detection** | Custom-trained YOLO model locates plates within each vehicle crop |
| 🔤 **OCR on License Plates** | EasyOCR extracts plate text with Nepali/Devanagari script support |
| ↕️ **Directional Counting (IN/OUT)** | Virtual trip lines classify each crossing as entering or exiting |
| 🗄️ **SQLite Logging** | Every event logged with track ID, class, direction, plate text, and timestamp |
| 📊 **CSV Export** | Full vehicle log exported to `vehicle_log.csv` on exit |
| ⚡ **Fault-Tolerant** | Crash-safe logging; RTSP reconnection with exponential back-off |
| 🍎 **Apple Silicon Support** | Runs on M1/M2 via PyTorch MPS backend — no CUDA required |

---

## 🧰 Tech Stack

| Tool | Purpose |
|---|---|
| [Ultralytics YOLO11](https://docs.ultralytics.com/models/yolo11/) | Vehicle, pedestrian & license plate detection + tracking |
| [EasyOCR](https://github.com/JaidedAI/EasyOCR) | License plate text recognition |
| [OpenCV](https://opencv.org/) | Video I/O, RTSP stream handling, frame rendering |
| [SQLite3](https://www.sqlite.org/) | Local event logging |
| [Pandas](https://pandas.pydata.org/) | CSV export of vehicle log |

---

## 📁 Project Structure

```
realtime-vehicle-person-detection-ocr/
├── main.py               # Main detection + tracking + OCR pipeline
├── yolo11l.pt            # YOLO11 large model for vehicle detection
├── best.pt               # Custom-trained YOLO model for license plates
├── requirements.txt      # Python dependencies
├── test_video.mp4        # Sample input video (not included in repo)
├── vehicle_log.db        # SQLite database (auto-created on first run)
└── vehicle_log.csv       # Exported crossing log (generated on exit)
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
# or manually:
pip install ultralytics easyocr opencv-python pandas
```

> **Note:** EasyOCR downloads language model weights on first run. GPU is recommended but not required — the system runs on Apple M2 via MPS.

### 3. Add model weights and video

- Place `yolo11l.pt` (YOLO11 large) in the project root — download from [Ultralytics](https://docs.ultralytics.com/models/yolo11/)
- Place your custom license plate model as `best.pt` in the project root
- Place your input video as `test_video.mp4`, **or** configure an RTSP stream (see [Configuration](#-configuration))

### 4. Run

```bash
python main.py
```

Press `q` to quit. The vehicle log will be automatically exported to `vehicle_log.csv` on exit.

---

## ⚙️ Configuration

Edit the following variables at the top of `main.py` to match your camera and environment:

```python
# RTSP stream from Hikvision or any IP camera (TCP mode recommended)
rtsp_url = "rtsp://<username>:<password>@<ip_address>:<port>/<stream_path>"

# Y-coordinate of the virtual crossing line (adjust to your frame resolution)
y_coordinate = 500

# IN region (left lane) — adjust X range to match your video
cv2.line(frame, (100, y_coordinate), (550, y_coordinate), ...)

# OUT region (right lane) — adjust X range to match your video
cv2.line(frame, (700, y_coordinate), (1050, y_coordinate), ...)
```

> **Tip:** Run with a static video first to find the right `y_coordinate` for your camera angle before switching to live RTSP.

---

## 🗄️ Database Schema

Events are logged to `vehicle_log.db` under the `vehicle_log` table:

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Auto-incremented primary key |
| `track_id` | INTEGER | Unique ID assigned to each tracked object |
| `vehicle_type` | TEXT | Detected class (`car`, `motorcycle`, `person`, etc.) |
| `direction` | TEXT | `IN` or `OUT` |
| `number_plate` | TEXT | OCR-extracted plate text (empty if not detected) |
| `timestamp` | TEXT | Event time (`YYYY-MM-DD HH:MM:SS`) |

---

## 🌐 OCR Language Support

EasyOCR is initialised for English by default. To add Nepali (Devanagari) support, update this line in `main.py`:

```python
reader = easyocr.Reader(['en', 'ne'])  # 'ne' = Nepali / Devanagari
```

Other supported South Asian scripts: Hindi (`hi`), Newari.

---

## 📋 Sample Output

```csv
id,track_id,vehicle_type,direction,number_plate,timestamp
1,4,car,IN,BA 1 KA 2345,2024-11-01 10:23:11
2,7,motorcycle,OUT,,2024-11-01 10:23:18
3,12,person,IN,,2024-11-01 10:24:05
```

---

## 📊 Evaluation Results

Results from the Liberty College and Global College deployment (approx. 14 hours, 3 scenarios):

| Metric | Result |
|---|---|
| Mean throughput | 20.8 FPS |
| Max uninterrupted runtime | 18 hours |
| Data loss events | 0 |
| IN/OUT directional accuracy | 92–95% |
| Hardware | Apple M2 (no CUDA) |

See the [research paper](#-research-paper) for the full methodology and analysis.

---

## 🗺️ Deployment Context

LibertyTrack was developed and evaluated as part of a research project at **Liberty College, and Global College Kathmandu, Nepal** — a real-world environment characterised by:

- Low-resolution Hikvision CCTV cameras over RTSP/TCP
- Congested campus Wi-Fi with intermittent dropouts
- Mixed traffic: pedestrians, cars, and dense motorcycle clusters
- No on-site GPU hardware

The system is specifically designed for institutions in **developing countries** that lack the infrastructure assumed by most published computer vision pipelines.

---

## 🔭 Roadmap

- [ ] Nepali licence plate fine-tuning dataset (public release)
- [ ] Multi-camera fusion support
- [ ] Real-time web dashboard (Flask/FastAPI)
- [ ] Model fine-tuning on Nepal-specific vehicle classes (e-rickshaws, tempos)
- [ ] Low-light enhancement pre-processing stage


---

## 📄 License

This project is open source under the [MIT License](LICENSE). Feel free to use, modify, and distribute it — attribution appreciated.

---

<p align="center">
  Built by <a href="https://github.com/puriiiii">Danish Puri</a> · NYU Tandon School of Engineering · Deployed in Kathmandu, Nepal
</p>ments/assets/ce535cb5-f73e-4b00-a2cd-c05fda4381b2


---

