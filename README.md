
### LibertyTrack: Real-Time Vehicle and Pedestrian Tracking system 

🚗🚶 *Engineering Documentation & Deployment Report*

[![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)](https://www.python.org/)
[![YOLOv11](https://img.shields.io/badge/YOLO-11n%20%2F%2011l-darkgreen?logo=ultralytics)](https://docs.ultralytics.com/models/yolo11/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![arXiv](https://img.shields.io/badge/Paper-arXiv-red)](https://arxiv.org/)
[![Deployment](https://img.shields.io/badge/Deployed%20at-Liberty%20College%2C%20Nepal-orange)]()

> This repository documents a real-world deployment of a computer vision–based campus traffic monitoring system at two institutions in Kathmandu, Nepal. It is offered as an engineering case study to support reproducibility and technology transfer to similar resource-constrained institutions.


---


https://github.com/user-attachments/assets/424e83c7-0f66-4583-8f43-618ea3ced993


---

## 📄 Case Study Paper

This repository accompanies the case study paper:

> **LibertyTrack: A Deployment Case Study for Real-Time Vehicle and Pedestrian Tracking in a Resource-Constrained Campus Environment**  
> Danish Puri — New York University, Tandon School of Engineering  
> *Prepared for IEEE-style submission*

The paper documents the full deployment process, pragmatic design choices, real-world observations, and lessons learned, including:
- 20.8 FPS sustained throughput on Apple M2 (no CUDA required)
- Observed directional flow consistency during operational deployment (qualitative observation, not validated against annotated ground truth)
- 18-hour uninterrupted runtime with zero data loss
- Documented failure modes: low-light conditions, motion blur, motorcycle clustering


📥 **[Download the paper (PDF)](https://osf.io/6s7aw/files/9kch3)** ·

---

## 📋 Abstract

This case study documents the deployment of a real-time vehicle and pedestrian directional tracking system at Liberty College and Global College, Kathmandu, Nepal — two institutions operating under infrastructure constraints typical of developing-country campuses: low-resolution CCTV cameras, intermittent Wi-Fi, heterogeneous traffic, and no on-site GPU hardware.
This work documents the practical challenges encountered, the design choices made to address them, and the lessons learned from sustained real-world operation. We describe how off-the-shelf tools (YOLO11, EasyOCR, OpenCV, SQLite) were assembled into a fault-tolerant pipeline that appears to operate reliably under these conditions. The system logged traffic flow events over approximately 18 hours across two campus sites. We observed consistent directional classification behaviour, though we did not validate these observations against an annotated ground-truth dataset.

The primary contribution of this work is a reproducible deployment blueprint and an honest account of what worked, what failed, and what should be considered by similar institutions attempting to implement comparable systems.

---

## 1. Introduction

Campus traffic monitoring in developing countries faces a different set of challenges than those addressed by most published computer vision pipelines. The majority of computer vision research assumes high-resolution cameras, stable network infrastructure, GPU-based inference hardware, and controlled lighting — none of which are reliably present at institutions like Liberty College or Global College in Kathmandu, Nepal.

This work documents what happened when we deployed an off-the-shelf computer vision stack in such an environment. The goal was not to design a novel system or to improve upon existing algorithms. The goal was to get something working, document what we learned, and make the experience reproducible for other institutions facing the same constraints.

The research questions that guided this deployment were:
1. Can an off-the-shelf computer vision stack be deployed in a resource-constrained campus environment without GPU hardware?
2. What practical challenges arise, and how can they be addressed with minimal infrastructure investment?
3. What does the deployed system actually log, and what patterns appear in that data?
4. What would we do differently, and what should other institutions know before attempting a similar deployment?

This document is structured as a case study. We describe the deployment context, the design choices we made for this specific environment, what we observed during operation, what failed, and what we recommend for future deployments of similar systems.

---

## 2. Related Work: Deployment Challenges in Developing Countries

Most published work on vehicle detection and traffic monitoring focuses on algorithmic improvements evaluated on benchmark datasets (COCO, BDD100K, CARLA). These contributions are valuable, but they rarely address the practical barriers faced by institutions in resource-constrained settings.

Several threads of work are relevant to this deployment:

**Technology transfer and resource constraints.** Work on TinyML and edge inference has documented the gap between laboratory performance and real-world deployment *(citations to be added upon arXiv submission)*. For computer vision specifically, reduced-resolution inputs, lighting variance, and network instability are known to degrade performance — but these degradations are rarely characterised in field conditions comparable to a developing-country campus.

**Infrastructure-constrained deployment.** Researchers working in sub-Saharan Africa and South/Southeast Asia have noted that assumptions baked into standard pipelines — stable power, dedicated hardware, expert maintenance staff — often do not hold *(citations to be added upon arXiv submission)*. Fault tolerance and graceful degradation become primary design concerns, not performance optimisation.

**Documenting real-world deployments.** A recurring observation in the ML systems community is that deployment reports are underrepresented in the literature relative to benchmark results. This work attempts to address that gap specifically for the context of a Nepali campus, with mixed-script license plates, dense motorcycle traffic, and consumer-grade CCTV hardware.

---

## 3. Implementation & Deployment

This section describes the design choices we made for this specific deployment context. Each choice reflects a pragmatic decision given the constraints of the Kathmandu campus environment, not an optimal or generalised solution.

### 3.1 Deployment Context

LibertyTrack was implemented and operated at **Liberty College and Global College, Kathmandu, Nepal**. The physical environment is characterised by:

- Low-resolution Hikvision CCTV cameras (consumer-grade, fixed-mount) over RTSP/TCP
- Congested campus Wi-Fi with frequent intermittent dropouts
- Mixed traffic: pedestrians, cars, and dense motorcycle clusters
- No on-site GPU hardware — a consumer laptop (Apple M2) served as the inference machine

These constraints shaped every design decision described below.

### 3.2 Design Choices

| Feature | Implementation | Why this choice |
|---|---|---|
| 🔍 **Object Detection** | YOLO11 (n/l variants) | Pre-trained on COCO; runs at acceptable speed on Apple M2 MPS without CUDA |
| 🪪 **License Plate Detection** | Custom-trained YOLO model (`best.pt`) | Off-the-shelf models were not trained on Nepali plates |
| 🔤 **OCR** | EasyOCR with English support | Handles mixed Latin/Devanagari script; runs on CPU without GPU dependency |
| ↕️ **Directional Classification** | Virtual trip lines (Y-coordinate threshold) | Simple, robust, and interpretable; no learned components that could degrade unexpectedly |
| 🗄️ **Logging** | SQLite + CSV export | Requires no database server; crash-safe; easy to inspect without specialist tools |
| ⚡ **Fault Tolerance** | RTSP reconnection with exponential back-off | Campus Wi-Fi drops were frequent; silent failure would invalidate the log |
| 🍎 **Hardware** | Apple M2 via PyTorch MPS | The only available hardware; no CUDA required |

### 3.3 Tech Stack

| Tool | Purpose |
|---|---|
| [Ultralytics YOLO11](https://docs.ultralytics.com/models/yolo11/) | Vehicle, pedestrian & license plate detection + tracking |
| [EasyOCR](https://github.com/JaidedAI/EasyOCR) | License plate text recognition |
| [OpenCV](https://opencv.org/) | Video I/O, RTSP stream handling, frame rendering |
| [SQLite3](https://www.sqlite.org/) | Local event logging |
| [Pandas](https://pandas.pydata.org/) | CSV export of vehicle log |

### 3.4 Project Structure

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

## 4. Deployment Strategy

### 4.1 Getting Started

#### 1. Clone the repository

```bash
git clone https://github.com/puriiiii/realtime-vehicle-person-detection-ocr.git
cd realtime-vehicle-person-detection-ocr
```

#### 2. Install dependencies

```bash
pip install -r requirements.txt
# or manually:
pip install ultralytics easyocr opencv-python pandas
```

> **Note:** EasyOCR downloads language model weights on first run. GPU is helpful but not required — the system was operated on Apple M2 via MPS throughout this deployment.

#### 3. Add model weights and video

- Place `yolo11l.pt` (YOLO11 large) in the project root — download from [Ultralytics](https://docs.ultralytics.com/models/yolo11/)
- Place your custom license plate model as `best.pt` in the project root
- Place your input video as `test_video.mp4`, **or** configure an RTSP stream (see [Configuration](#configuration))

#### 4. Run

```bash
python main.py
```

Press `q` to quit. The vehicle log will be automatically exported to `vehicle_log.csv` on exit.

### 4.2 Configuration

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

> **Tip:** Run with a static video first to find the right `y_coordinate` for your camera angle before switching to live RTSP. This was how we calibrated the trip lines at both deployment sites.

### 4.3 Fault Tolerance Considerations

The implementation addresses several failure modes observed in the Kathmandu deployment:

- **RTSP stream dropout**: The reconnection loop with exponential back-off prevents the system from silently failing when campus Wi-Fi drops. Without this, we observed silent disconnection that would invalidate the log.
- **SQLite crash safety**: Each event is committed immediately after logging. We did not observe data loss during network interruptions.
- **OCR failure handling**: The `try/except` around plate OCR ensures a detection failure does not interrupt the main tracking loop. A missed plate is logged as an empty string; the directional event is still recorded.

---

## 5. Deployment Context & Observations

### 5.1 Operational Conditions

The deployment ran across two campus sites over approximately 14 hours of active logging across three sessions. The longest single uninterrupted session ran for approximately 18 hours:

| Condition | Liberty College | Global College |
|---|---|---|
| Camera type | Hikvision fixed-mount | Hikvision fixed-mount |
| Stream protocol | RTSP/TCP | RTSP/TCP |
| Network stability | Frequent dropouts | Frequent dropouts |
| Traffic density | Moderate | High (peak hours) |
| Lighting | Daylight; some low-light near gate | Daylight; shaded entry |
| Hardware | Apple M2 (no GPU) | Apple M2 (no GPU) |

### 5.2 Known Limitations of the Deployment

This was a single-site, single-operator deployment conducted without a controlled experimental design. The following limitations apply to all observations:

- No annotated ground-truth dataset was collected for validation
- OCR results were not independently verified
- The deployment ran on a single hardware configuration
- Results may not generalise to different camera placements, traffic compositions, or lighting conditions

---

## 6. Observed System Behaviour

The following observations are drawn from the deployment log and operator notes. They are presented as observations from a real deployment, not as validated experimental results.

### 6.1 Logged Flow Events

| Metric | Observed Value |
|---|---|
| Mean throughput | ~20.8 FPS |
| Max uninterrupted runtime | ~18 hours |
| Logged flow events | Thousands of crossings across both sites |
| Data loss events | 0 observed |
| Hardware | Apple M2 (no CUDA) |

> ⚠️ **Important:** The above figures reflect what the system logged and what the operator observed during operation. They are not metrics validated against an independently annotated ground-truth dataset.

### 6.2 Directional Classification Behaviour

The virtual trip-line approach appeared to produce consistent directional assignments for vehicles traversing the camera's field of view under normal daytime conditions. Directional consistency was assessed qualitatively by the operator watching live output — not by comparing system labels to manually annotated ground truth.

### 6.3 Documented Failure Modes

The following failure modes were encountered and documented during the deployment:

| Failure Mode | Conditions | Observed Behaviour |
|---|---|---|
| Missed detections | Low-light (dusk/dawn) | YOLO appeared to miss or mis-classify objects |
| OCR failures | Motion blur at gate entry | EasyOCR returned empty strings or garbled text |
| Track fragmentation | Dense motorcycle clusters | Multiple track IDs assigned to a single vehicle |
| Direction mis-assignment | Vehicles stopping on trip line | Ambiguous crossing direction logged |
| Stream dropout | Wi-Fi congestion | Reconnection loop triggered; logging resumed |

### 6.4 Database Schema

Events are logged to `vehicle_log.db` under the `vehicle_log` table:

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Auto-incremented primary key |
| `track_id` | INTEGER | Unique ID assigned to each tracked object |
| `vehicle_type` | TEXT | Detected class (`car`, `motorcycle`, `person`, etc.) |
| `direction` | TEXT | `IN` or `OUT` |
| `number_plate` | TEXT | OCR-extracted plate text (empty if not detected) |
| `timestamp` | TEXT | Event time (`YYYY-MM-DD HH:MM:SS`) |

### 6.5 Sample Log Output

```csv
id,track_id,vehicle_type,direction,number_plate,timestamp
1,4,car,IN,BA 1 KA 2345,2024-11-01 10:23:11
2,7,motorcycle,OUT,,2024-11-01 10:23:18
3,12,person,IN,,2024-11-01 10:24:05
```

### 6.6 OCR Language Support

EasyOCR is initialised for English by default. To add Nepali (Devanagari) support, update this line in `main.py`:

```python
reader = easyocr.Reader(['en', 'ne'])  # 'ne' = Nepali / Devanagari
```

Other supported South Asian scripts: Hindi (`hi`), Newari.

---

## 7. Lessons Learned & Deployment Insights

### 7.1 What Worked Well

- **Virtual trip lines** proved robust and interpretable. They do not require tuning of learned components and their failure mode is predictable.
- **SQLite logging** was appropriate for this scale. Zero data loss was observed. No database server administration was required.
- **RTSP/TCP mode** was significantly more stable than RTSP/UDP for the campus Wi-Fi environment.
- **Running without CUDA** was entirely feasible at this traffic density. The Apple M2 MPS backend appeared sufficient for single-camera deployment.
- **EasyOCR** handled mixed Latin/Devanagari plate text without requiring custom training, though accuracy for partially occluded plates was poor.

### 7.2 What Should Be Done Differently

- **Ground truth collection**: Even a small annotated sample (e.g. 2–4 hours of independently reviewed footage) would allow directional consistency to be measured rather than estimated qualitatively. Future deployments should plan for this from the start.
- **Low-light handling**: A pre-processing step (e.g. histogram equalisation or CLAHE) would likely improve detection at dawn and dusk. We did not implement this; it is recommended for similar deployments.
- **Multi-object tracking stability**: Track fragmentation for motorcycle clusters was a known limitation. A more sophisticated tracker (e.g. DeepSORT) might reduce this, at the cost of increased compute.
- **Operator documentation**: We recommend maintaining a structured field log alongside the automated event log. Operator observations (weather, unusual events, camera obstructions) are difficult to reconstruct from the database alone.

### 7.3 Unexpected Challenges

- **RTSP authentication handling**: Some camera firmware versions required slightly different URL formatting. This was discovered only after failed connection attempts on-site.
- **Plate text normalisation**: Nepali plate formats vary (e.g. "BA 1 KA 2345" vs "BA1KA2345"). Downstream analysis of the log required manual normalisation.
- **Time synchronisation**: The laptop clock drifted during extended sessions without NTP sync. Timestamps in the log should be treated with ~1-minute uncertainty for long sessions.

### 7.4 Adapting for Different Contexts

This deployment was calibrated for a single fixed-angle camera with a defined entry/exit lane structure. Institutions adapting this system should consider:

- **Camera placement**: The virtual trip-line approach requires a camera angle where crossing direction is distinguishable from vertical movement in the frame. Verify this with a short test capture before committing to a permanent mount.
- **Traffic composition**: Dense motorcycle traffic was a persistent challenge. Contexts with primarily car traffic may find tracking much more stable.
- **Lighting schedule**: If the deployment must cover night hours, a lighting pre-processing step is essential.
- **Network infrastructure**: RTSP/TCP mode is strongly recommended. Budget time for RTSP authentication and firewall configuration before the deployment date.

---

## 8. Reproducibility & Open Source

This repository is published under the MIT License to support reproducibility and reuse. All code required to reproduce the deployment is included.

### 8.1 What is included

- `main.py` — the complete detection, tracking, OCR, and logging pipeline
- `best.pt` — the custom-trained license plate detection model
- `requirements.txt` — full Python dependency list
- This documentation

### 8.2 What is not included

- `yolo11l.pt` — the base YOLO11 model (download from [Ultralytics](https://docs.ultralytics.com/models/yolo11/))
- `test_video.mp4` — the sample deployment video (not included for privacy reasons)
- The deployment log database — not included to protect privacy of individuals captured

### 8.3 Reproducing the deployment

To reproduce the deployment on a new site:

1. Follow the [Getting Started](#4-deployment-strategy) steps
2. Calibrate the `y_coordinate` trip-line position using a short static video of your entry/exit point
3. Set lane X-ranges for IN/OUT regions to match your camera frame
4. Run a short test session and inspect `vehicle_log.csv` to verify event logging
5. Switch to RTSP for live operation; verify reconnection behaviour by briefly disconnecting the network

---

## 9. Lessons for Technology Transfer

This deployment demonstrates that off-the-shelf computer vision tools can be made to operate in resource-constrained environments without specialised hardware or expertise — but the path from working code to working deployment involves challenges that are rarely documented in published research.

Key takeaways for institutions considering a similar deployment:

1. **Start with a static video test.** Running on a recorded video before connecting to live RTSP reveals configuration issues without the added complexity of network instability.
2. **Expect and plan for network failures.** Campus Wi-Fi is unreliable. Any deployment relying on RTSP must have a reconnection strategy.
3. **Plan for OCR imperfection.** Plate OCR in real-world conditions will miss many plates and produce garbled text for others. Design the system to degrade gracefully — log the directional event even when OCR fails.
4. **Document as you go.** The deployment log alone does not capture context. Maintain a parallel field log with operator notes, especially for anomalies.
5. **Calibrate trip lines on-site.** Camera placement in practice rarely matches the planned angle. Budget time for on-site calibration before declaring the system operational.
6. **Open source lowers the barrier.** Making the full implementation available (as this repository does) allows institutions to adapt and deploy without reimplementing from scratch.

---

## 10. Sustainability & Maintenance Considerations

A deployment is only useful if it remains operational. Several factors affect the long-term sustainability of a system like this:

### 10.1 Hardware

The deployment ran on a consumer laptop (Apple M2). This is adequate for single-camera operation but creates a single point of failure. For production use, consider:
- A dedicated low-power inference machine (e.g. Raspberry Pi 5 or a mini-PC with NPU)
- UPS backup for power stability
- Physical security for the inference hardware

### 10.2 Software maintenance

- YOLO model weights may be updated by Ultralytics. Pin the `ultralytics` version in `requirements.txt` to avoid unexpected behaviour changes.
- EasyOCR language models are downloaded at runtime. Ensure internet access for first-time setup, or pre-download and bundle the weights.
- SQLite databases grow indefinitely. Implement a log rotation or archival strategy for long-term deployments.

### 10.3 Operational maintenance

- Trip-line positions may need recalibration if the camera is physically moved or the mounting shifts.
- The custom plate detection model (`best.pt`) was trained on a limited sample of Nepali plates. Its performance appears to degrade for unusual plate formats; periodic review of OCR output is recommended.
- Designate a responsible operator who can restart the system after a crash and review logs periodically.

---

## 11. Ethical Considerations

This system captures and logs visual data about individuals (pedestrians) and vehicles (with license plates) in a campus environment. The following ethical considerations apply:

### 11.1 Data collected

- Vehicle presence, direction, and timestamp (always logged)
- License plate text (logged when OCR succeeds)
- Person presence and direction (no biometric data; no face recognition)

### 11.2 Privacy

- **License plate data** is personally linkable in most jurisdictions. The log database should be treated as sensitive data and access should be restricted to authorised personnel.
- **Pedestrian tracking** logs directional movement events, not identities. No face recognition or biometric identification is performed.
- Deployment sites should inform campus users that automated traffic monitoring is in operation, consistent with local institutional policy.

### 11.3 Data retention

- We recommend a defined data retention policy (e.g. 90-day rolling window) for operational deployments.
- This repository does not include any personal data collected during the deployment.

### 11.4 Scope limitations

This system was deployed for campus traffic management purposes only. The codebase should not be adapted for surveillance, law enforcement, or identity tracking applications without appropriate legal and ethical review.

---

## 12. Contribution Statement

This work's contribution is **not algorithmic**. We did not design a novel object detector, tracking algorithm, or OCR model. All components used are off-the-shelf.

The contribution of this work is **infrastructural and documentary**:

1. A deployable, fault-tolerant pipeline assembled from open-source components and documented for reproducibility
2. An honest account of what was observed, what failed, and what was learned during a real-world deployment in a resource-constrained environment
3. A blueprint for similar institutions in developing-country contexts who wish to implement comparable systems without significant infrastructure investment
4. Documentation of a deployment gap: the gap between "the algorithm works on a benchmark" and "the system runs reliably in a Nepali campus"

This work addresses an underrepresented category in computer vision literature: honest deployment documentation for resource-constrained, developing-country contexts.

---

## 13. Conclusion

LibertyTrack documents what happened when a standard computer vision pipeline was deployed in a resource-constrained campus environment in Kathmandu, Nepal. The system appeared to operate reliably under these conditions: it logged traffic flow events over approximately 18 hours without data loss, demonstrated consistent directional classification behaviour under normal daytime conditions, and recovered from network failures.

These observations are offered as deployment documentation, not as validated experimental results. We did not collect annotated ground truth. We cannot claim a specific accuracy figure. What we can say is that the system logged events consistently, the operator-observed directional classifications appeared correct in the cases reviewed, and the failure modes we encountered were predictable and documentable.

We hope this case study is useful to other institutions facing similar constraints. The most important thing we can offer is not the code (though it is freely available) but the documentation of what to expect: what works, what fails, and what to plan for before deployment day.

We encourage similar case studies from other institutions in developing-country contexts. The computer vision literature is rich in benchmark results; it is sparse in honest deployment reports. Both are needed.

---

## 🔭 Roadmap

- [ ] Nepali licence plate fine-tuning dataset (public release)
- [ ] Multi-camera fusion support
- [ ] Real-time web dashboard (Flask/FastAPI)
- [ ] Model fine-tuning on Nepal-specific vehicle classes (e-rickshaws, tempos)
- [ ] Low-light enhancement pre-processing stage
- [ ] Annotated ground-truth sample for directional classification validation
- [ ] Structured field log template for operator documentation

---

## 📄 License

This project is open source under the [MIT License](LICENSE). Feel free to use, modify, and distribute it — attribution appreciated.

---

<p align="center">
  Built by <a href="https://github.com/puriiiii">Danish Puri</a> · NYU Tandon School of Engineering · Deployed in Kathmandu, Nepal
</p>ments/assets/ce535cb5-f73e-4b00-a2cd-c05fda4381b2


---

