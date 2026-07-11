<h1 align="center">Bird</h1>

<p align="center">🚗🚶 An autonomous traffic management system built for Nepal</p>

<p align="center">
<a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10-blue?logo=python" alt="Python 3.10"></a>
<a href="https://docs.ultralytics.com/models/yolo11/"><img src="https://img.shields.io/badge/YOLO-11n%20%2F%2011l-darkgreen?logo=ultralytics" alt="YOLO11"></a>
<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
<a href="https://arxiv.org/"><img src="https://img.shields.io/badge/Paper-arXiv-red" alt="arXiv"></a>
<img src="https://img.shields.io/badge/Deployed%20at-Kathmandu%2C%20Nepal-orange" alt="Deployed in Kathmandu, Nepal">
</p>

> Bird is a computer vision traffic system I built for real Nepali roads, and it has already run in the field at two campuses in Kathmandu. This document explains where the project is headed, what works today, how to run it yourself, and what I learned by deploying it.

---

https://github.com/user-attachments/assets/424e83c7-0f66-4583-8f43-618ea3ced993

---

## 1. Vision

Most traffic software is built for roads that do not look like Nepal. It assumes clean lane markings, smooth pavement, stable power, fast networks, and GPU servers. Nepali roads have potholes, dense motorcycle swarms, mixed Latin and Devanagari license plates, e-rickshaws and tempos, dust, monsoon rain, and frequent power and network cuts.

Bird aims to become an autonomous traffic management system fine tuned for these exact conditions. The long term goals are

- Detect and track vehicles and pedestrians in dense, mixed Nepali traffic
- Read Nepali license plates in both Latin and Devanagari script
- Detect road hazards such as potholes and flag them for repair
- Manage traffic flow at gates and intersections without constant human supervision
- Run on cheap, low power hardware that a school or municipality can actually afford

The current release is the first step. It is a working vehicle and pedestrian tracking pipeline that I deployed and tested in the real world, in Kathmandu, on a regular laptop, with no GPU.

> **Naming note.** Bird was earlier called LibertyTrack. The accompanying paper uses the old name.

---

## 2. Case Study Paper

This repository comes with a deployment case study paper.

> **LibertyTrack: A Deployment Case Study for Real-Time Vehicle and Pedestrian Tracking in a Resource-Constrained Campus Environment**
> Danish Puri, New York University, Tandon School of Engineering
> Prepared for IEEE style submission

The paper covers the full deployment process, the design choices, real world observations, and lessons learned. Highlights include

- 20.8 FPS sustained throughput on Apple M2 with no CUDA
- Consistent directional flow behavior during live operation (a qualitative observation, not validated against annotated ground truth)
- 18 hours of uninterrupted runtime with zero data loss
- Documented failure modes such as low light conditions, motion blur, and motorcycle clustering

📥 **[Download the paper (PDF)](https://osf.io/6s7aw/files/9kch3)**

---

## 3. What Bird Does Today

Bird watches a camera feed, detects vehicles and pedestrians, tracks them across frames, reads license plates when it can, and logs every crossing event with a direction and a timestamp. It was built to survive the conditions it was deployed in. That means it reconnects when the network drops, it keeps logging when OCR fails, and it writes every event to disk immediately so a crash cannot erase the log.

I deployed the system at Liberty College and Global College in Kathmandu. Both sites had

- Consumer grade Hikvision CCTV cameras streamed over RTSP in TCP mode
- Congested campus Wi-Fi with frequent dropouts
- Mixed traffic with pedestrians, cars, and dense motorcycle clusters
- No GPU hardware. My Apple M2 laptop ran all inference

Every design decision below came from these constraints.

### 3.1 Design Choices

| Feature | Implementation | Why this choice |
|---|---|---|
| 🔍 **Object detection** | YOLO11 (n and l variants) | Pre-trained on COCO and fast enough on Apple M2 without CUDA |
| 🪪 **License plate detection** | Custom trained YOLO model (`best.pt`) | Off the shelf models were not trained on Nepali plates |
| 🔤 **OCR** | EasyOCR with English and Nepali support | Handles mixed Latin and Devanagari script and runs on CPU |
| ↕️ **Direction classification** | Virtual trip lines (a Y coordinate threshold) | Simple, robust, and easy to reason about, with no learned parts that could fail in surprising ways |
| 🗄️ **Logging** | SQLite plus CSV export | Needs no database server, survives crashes, and is easy to inspect |
| ⚡ **Fault tolerance** | RTSP reconnection with exponential backoff | Campus Wi-Fi dropped often, and a silent failure would ruin the log |
| 🍎 **Hardware** | Apple M2 through PyTorch MPS | The only hardware available, and no CUDA was needed |

### 3.2 Tech Stack

| Tool | Purpose |
|---|---|
| [Ultralytics YOLO11](https://docs.ultralytics.com/models/yolo11/) | Vehicle, pedestrian, and license plate detection plus tracking |
| [EasyOCR](https://github.com/JaidedAI/EasyOCR) | License plate text recognition |
| [OpenCV](https://opencv.org/) | Video input, RTSP stream handling, and frame rendering |
| [SQLite3](https://www.sqlite.org/) | Local event logging |
| [Pandas](https://pandas.pydata.org/) | CSV export of the vehicle log |

### 3.3 Project Structure

```
bird/
├── main.py               # Main detection + tracking + OCR pipeline
├── yolo11l.pt            # YOLO11 large model for vehicle detection (download separately)
├── best.pt               # Custom-trained YOLO model for license plates
├── requirements.txt      # Python dependencies
├── test_video.mp4        # Sample input video (not included in repo)
├── vehicle_log.db        # SQLite database (auto-created on first run)
└── vehicle_log.csv       # Exported crossing log (generated on exit)
```

---

## 4. Getting Started

### 4.1 Clone the repository

```bash
git clone https://github.com/puriiiii/bird.git
cd bird
```

### 4.2 Install dependencies

```bash
pip install -r requirements.txt
# or manually:
pip install ultralytics easyocr opencv-python pandas
```

> **Note.** EasyOCR downloads language model weights on first run. A GPU helps but is not required. The whole deployment ran on an Apple M2 through MPS.

### 4.3 Add model weights and video

- Place `yolo11l.pt` (YOLO11 large) in the project root. Download it from [Ultralytics](https://docs.ultralytics.com/models/yolo11/)
- Place your custom license plate model as `best.pt` in the project root
- Place your input video as `test_video.mp4`, or set up an RTSP stream (see [Configuration](#45-configuration))

### 4.4 Run

```bash
python main.py
```

Press `q` to quit. The vehicle log is exported to `vehicle_log.csv` on exit.

### 4.5 Configuration

Edit these variables at the top of `main.py` to match your camera and site.

```python
# RTSP stream from Hikvision or any IP camera (TCP mode recommended)
rtsp_url = "rtsp://<username>:<password>@<ip_address>:<port>/<stream_path>"

# Y-coordinate of the virtual crossing line (adjust to your frame resolution)
y_coordinate = 500

# IN region (left lane), adjust X range to match your video
cv2.line(frame, (100, y_coordinate), (550, y_coordinate), ...)

# OUT region (right lane), adjust X range to match your video
cv2.line(frame, (700, y_coordinate), (1050, y_coordinate), ...)
```

> **Tip.** Run with a recorded video first to find the right `y_coordinate` for your camera angle before switching to live RTSP. This is how I calibrated the trip lines at both deployment sites.

### 4.6 Fault Tolerance

The implementation handles several failure modes I hit in the Kathmandu deployment.

- **RTSP stream dropout.** A reconnection loop with exponential backoff keeps the system from failing silently when Wi-Fi drops. Without it I saw silent disconnects that would have invalidated the log.
- **SQLite crash safety.** Each event is committed to disk the moment it is logged. I saw no data loss during network interruptions.
- **OCR failure handling.** Plate OCR is wrapped in error handling so a failed read never interrupts the main tracking loop. A missed plate is logged as an empty string and the directional event is still recorded.

---

## 5. Deployment Observations

The system ran across two campus sites over roughly 14 hours of active logging in three sessions. The longest single uninterrupted session ran for about 18 hours.

| Condition | Liberty College | Global College |
|---|---|---|
| Camera type | Hikvision fixed mount | Hikvision fixed mount |
| Stream protocol | RTSP over TCP | RTSP over TCP |
| Network stability | Frequent dropouts | Frequent dropouts |
| Traffic density | Moderate | High at peak hours |
| Lighting | Daylight, some low light near the gate | Daylight, shaded entry |
| Hardware | Apple M2, no GPU | Apple M2, no GPU |

### 5.1 Logged Results

| Metric | Observed Value |
|---|---|
| Mean throughput | ~20.8 FPS |
| Max uninterrupted runtime | ~18 hours |
| Logged flow events | Thousands of crossings across both sites |
| Data loss events | 0 observed |
| Hardware | Apple M2, no CUDA |

> ⚠️ **Important.** These figures reflect what the system logged and what I observed while operating it. They are not metrics validated against an independently annotated ground truth dataset.

### 5.2 Known Limitations

This was a single operator deployment without a controlled experimental design. Keep the following in mind when reading any observation in this document.

- No annotated ground truth dataset was collected for validation
- OCR results were not independently verified
- The deployment ran on a single hardware configuration
- Results may not carry over to different camera placements, traffic mixes, or lighting

### 5.3 Documented Failure Modes

| Failure Mode | Conditions | Observed Behavior |
|---|---|---|
| Missed detections | Low light at dusk and dawn | YOLO missed or misclassified objects |
| OCR failures | Motion blur at the gate | EasyOCR returned empty or garbled text |
| Track fragmentation | Dense motorcycle clusters | Multiple track IDs assigned to one vehicle |
| Direction errors | Vehicles stopping on the trip line | Ambiguous crossing direction logged |
| Stream dropout | Wi-Fi congestion | Reconnection loop triggered and logging resumed |

### 5.4 Database Schema

Events are logged to `vehicle_log.db` in the `vehicle_log` table.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Auto incremented primary key |
| `track_id` | INTEGER | Unique ID assigned to each tracked object |
| `vehicle_type` | TEXT | Detected class such as `car`, `motorcycle`, or `person` |
| `direction` | TEXT | `IN` or `OUT` |
| `number_plate` | TEXT | OCR extracted plate text, empty if not detected |
| `timestamp` | TEXT | Event time in `YYYY-MM-DD HH:MM:SS` format |

Sample log output

```csv
id,track_id,vehicle_type,direction,number_plate,timestamp
1,4,car,IN,BA 1 KA 2345,2024-11-01 10:23:11
2,7,motorcycle,OUT,,2024-11-01 10:23:18
3,12,person,IN,,2024-11-01 10:24:05
```

### 5.5 OCR Language Support

EasyOCR starts with English by default. To add Nepali (Devanagari) support, update this line in `main.py`.

```python
reader = easyocr.Reader(['en', 'ne'])  # 'ne' = Nepali / Devanagari
```

Hindi (`hi`) and Newari are also supported.

---

## 6. Lessons Learned

### 6.1 What Worked Well

- **Virtual trip lines** were robust and easy to understand. They need no tuning of learned parts and their failure mode is predictable.
- **SQLite logging** was the right fit at this scale. I saw zero data loss and needed no database administration.
- **RTSP over TCP** was far more stable than UDP on campus Wi-Fi.
- **Running without CUDA** worked fine at this traffic density. The Apple M2 MPS backend was enough for a single camera.
- **EasyOCR** handled mixed Latin and Devanagari plate text without custom training, though accuracy on partly hidden plates was poor.

### 6.2 What I Would Do Differently

- **Collect ground truth.** Even a small annotated sample of 2 to 4 hours of reviewed footage would let me measure direction accuracy instead of estimating it by eye. Plan for this from day one.
- **Handle low light.** A preprocessing step such as histogram equalization or CLAHE would likely improve detection at dawn and dusk. I did not build this and recommend it for future deployments.
- **Improve tracking stability.** Track fragmentation in motorcycle clusters was a known weak point. A stronger tracker such as DeepSORT might reduce it at the cost of more compute.
- **Keep a field log.** Operator notes about weather, unusual events, and camera obstructions are hard to reconstruct from the database alone. Keep a structured field log next to the automated one.

### 6.3 Unexpected Challenges

- **RTSP authentication.** Some camera firmware versions needed slightly different URL formats. I only found this out after failed connection attempts on site.
- **Plate text normalization.** Nepali plate formats vary, for example "BA 1 KA 2345" versus "BA1KA2345". Downstream analysis of the log needed manual cleanup.
- **Clock drift.** The laptop clock drifted during long sessions without NTP sync. Treat timestamps in long sessions as accurate to about one minute.

### 6.4 Advice for New Deployments

1. **Start with a recorded video.** Testing on a file first reveals configuration issues without the added noise of network instability.
2. **Plan for network failure.** Campus Wi-Fi is unreliable. Any RTSP deployment needs a reconnection strategy.
3. **Expect imperfect OCR.** Real world plate OCR misses many plates and garbles others. Design the system to degrade gracefully and log the crossing even when OCR fails.
4. **Document as you go.** The event log alone does not capture context. Keep operator notes, especially for anomalies.
5. **Calibrate trip lines on site.** The real camera angle rarely matches the plan. Budget time for on site calibration.
6. **Check your camera angle.** The trip line approach needs an angle where crossing direction shows up as vertical movement in the frame. Verify with a short test capture before mounting anything permanently.

---

## 7. Reproducibility

This repository is published under the MIT License to support reproduction and reuse.

**Included**

- `main.py`, the complete detection, tracking, OCR, and logging pipeline
- `best.pt`, the custom trained license plate detection model
- `requirements.txt`, the full Python dependency list
- This documentation

**Not included**

- `yolo11l.pt`, the base YOLO11 model. Download it from [Ultralytics](https://docs.ultralytics.com/models/yolo11/)
- `test_video.mp4`, the sample deployment video, withheld for privacy
- The deployment log database, withheld to protect the privacy of people captured on camera

**To reproduce the deployment at a new site**

1. Follow the [Getting Started](#4-getting-started) steps
2. Calibrate the `y_coordinate` trip line position using a short static video of your entry point
3. Set the lane X ranges for the IN and OUT regions to match your camera frame
4. Run a short test session and inspect `vehicle_log.csv` to verify event logging
5. Switch to live RTSP and verify reconnection by briefly disconnecting the network

---

## 8. Sustainability and Maintenance

A deployment is only useful if it stays running.

**Hardware.** The deployment ran on a consumer laptop, which is fine for one camera but is a single point of failure. For production use, consider a dedicated low power inference machine such as a Raspberry Pi 5 or a mini PC with an NPU, a UPS for power stability, and physical security for the hardware.

**Software.** Pin the `ultralytics` version in `requirements.txt` to avoid surprise behavior changes when weights are updated. EasyOCR downloads its language models at runtime, so make sure internet access is available for first time setup or bundle the weights ahead of time. SQLite databases grow forever, so plan log rotation or archival for long term deployments.

**Operations.** Trip line positions need recalibration if the camera is moved or the mount shifts. The custom plate model (`best.pt`) was trained on a limited sample of Nepali plates and degrades on unusual formats, so review OCR output periodically. Designate an operator who can restart the system after a crash and review logs.

---

## 9. Ethical Considerations

Bird captures and logs visual data about people and vehicles.

**Data collected**

- Vehicle presence, direction, and timestamp (always logged)
- License plate text (logged when OCR succeeds)
- Person presence and direction (no biometric data and no face recognition)

**Privacy**

- License plate data is personally linkable in most places. Treat the log database as sensitive and restrict access to authorized personnel.
- Pedestrian tracking logs movement events, not identities. No face recognition or biometric identification is performed.
- Deployment sites should inform people that automated traffic monitoring is in operation, in line with local policy.

**Retention.** I recommend a defined retention policy, for example a 90 day rolling window. This repository contains no personal data from the deployment.

**Scope.** Bird was built for traffic management. Do not adapt this codebase for surveillance, law enforcement, or identity tracking without proper legal and ethical review.

---

## 10. Contribution Statement

The contribution of this work is not algorithmic. I did not design a new detector, tracker, or OCR model. Every component is off the shelf.

The contribution is infrastructural and documentary

1. A deployable, fault tolerant pipeline assembled from open source parts and documented for reproduction
2. An honest account of what was observed, what failed, and what was learned in a real deployment under real constraints
3. A blueprint for institutions in similar contexts who want a comparable system without a large infrastructure budget
4. Documentation of the gap between "the algorithm works on a benchmark" and "the system runs reliably on a Nepali campus"

Deployment reports like this one are rare in the computer vision literature. Benchmark results are common. Both are needed.

---

## 🔭 Roadmap

Bird is moving from a monitoring tool toward an autonomous traffic management system for Nepal. Planned work includes

- [ ] Pothole and road hazard detection tuned for Nepali road conditions
- [ ] Model fine tuning on Nepal specific vehicle classes such as e-rickshaws and tempos
- [ ] Public release of a Nepali license plate fine tuning dataset
- [ ] Multi camera fusion support
- [ ] Real time web dashboard (Flask or FastAPI)
- [ ] Low light enhancement preprocessing stage
- [ ] Annotated ground truth sample for direction classification validation
- [ ] Structured field log template for operator documentation
- [ ] Automated traffic flow control experiments at gates and intersections

---

## 📄 License

This project is open source under the [MIT License](LICENSE). Feel free to use, modify, and distribute it. Attribution is appreciated.

---

<p align="center">
  Built by <a href="https://github.com/puriiiii">Danish Puri</a> · NYU Tandon School of Engineering · Deployed in Kathmandu, Nepal
</p>
