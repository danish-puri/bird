<h1 align="center">Bird</h1>

<p align="center">🚗🚶 Vehicle and pedestrian monitoring for Nepali roads</p>

<p align="center">
<a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-target%203.10-blue?logo=python" alt="Python 3.10 target"></a>
<a href="https://docs.ultralytics.com/models/yolo11/"><img src="https://img.shields.io/badge/YOLO-11l-darkgreen?logo=ultralytics" alt="YOLO11l"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
<a href="https://osf.io/6s7aw/files/9kch3"><img src="https://img.shields.io/badge/Paper-Case%20study-red" alt="Deployment case study"></a>
<img src="https://img.shields.io/badge/Field%20study-Kathmandu%2C%20Nepal-orange" alt="Kathmandu field study">
</p>

Bird combines object tracking, license-plate recognition, and directional crossing logs. I built it around the conditions encountered at two campuses in Kathmandu: mixed traffic, inconsistent lighting, constrained hardware, and unreliable networks. Its longer-term goal is autonomous traffic management for Nepal.

**Current status:** this checkout contains a single-script monitoring prototype. The [source audit and implementation plan](docs/AUDIT.md) documents its reliability gaps and proposed fixes. Application changes, automated tests, and runtime validation in that plan remain pending. Historical deployment observations appear separately below.

https://github.com/user-attachments/assets/a2079247-0f05-41ec-9d38-801f72050072

## Current implementation

[`main.py`](main.py) reads `test_video.mp4`, tracks selected object classes, attempts plate recognition, displays an OpenCV window, and stores qualifying IN/OUT crossings in SQLite. Source, model names, and counting geometry are configured by editing the script; there is no command-line configuration or headless mode.

| Layer | Current configuration | Source evidence |
| --- | --- | --- |
| Runtime | Python 3.10 is the documented target; no enforced version or verified dependency lock is supplied | [`requirements.txt`](requirements.txt) lists unpinned direct dependencies |
| Detection and tracking | Ultralytics YOLO11 large, `yolo11l.pt`; persistent tracking of COCO classes 0, 1, 2, 3, 5, 6, and 7 | `YOLO('yolo11l.pt')` and `vehicle_model.track(..., persist=True, classes=...)` in [`main.py`](main.py) |
| Plate detection | Custom `best.pt` model applied to tracked-object crops | [`best.pt`](best.pt) is included; loaded with `YOLO('best.pt')` |
| OCR | EasyOCR initialized with English only | `easyocr.Reader(['en'])` in [`main.py`](main.py) |
| Video and display | OpenCV capture, drawing, and an operator window | `cv2.VideoCapture('test_video.mp4')`, `cv2.imshow`, and keyboard polling |
| Persistence | SQLite event insert and commit for each qualifying crossing | `vehicle_log.db`, table `vehicle_log` |
| Export | pandas exports the entire event table on normal shutdown | `read_sql_query` and `to_csv` write `vehicle_log.csv` |

The four direct third-party dependencies are `opencv-python`, `pandas`, `ultralytics`, and `easyocr`. The model libraries use PyTorch; the script leaves CPU, CUDA, or MPS selection to the installed libraries' defaults. It enables English-only OCR, and no particular device configuration has been validated for this checkout.

```text
bird/
├── main.py               # Detection, tracking, OCR, display, and logging
├── best.pt               # Included custom plate-detection weights
├── requirements.txt      # Unpinned direct Python dependencies
├── docs/AUDIT.md         # Source findings and proposed implementation plan
├── LICENSE               # MIT license
├── yolo11l.pt            # Base detector weights; obtain separately
├── test_video.mp4        # Your input video; not included
├── vehicle_log.db        # Generated SQLite event history
└── vehicle_log.csv       # Generated export of the event history
```

## Getting started

### 1. Clone and install

Use an isolated Python environment. Python 3.10 is the existing project target; a tested package/version combination has not been established.

```bash
# Clone the canonical repository and enter its root directory.
git clone https://github.com/danish-puri/bird.git
cd bird

# Create and activate an isolated environment on macOS or Linux.
python3.10 -m venv .venv
source .venv/bin/activate

# Install the repository's direct dependencies into that environment.
python -m pip install -r requirements.txt
```

### 2. Supply weights and input

- Obtain `yolo11l.pt` from the [Ultralytics YOLO11 model page](https://docs.ultralytics.com/models/yolo11/) and place it in the repository root.
- Keep the included `best.pt` in the repository root, or replace it with a compatible custom plate detector.
- Supply your own video as `test_video.mp4`. Deployment footage and logs are withheld for privacy.
- Allow for [first-use EasyOCR model downloads](https://github.com/JaidedAI/EasyOCR#usage). Prepare model files before an offline deployment; no dependency or EasyOCR model cache is bundled here.

The script resolves these filenames relative to the working directory. Run it from the repository root with a graphical desktop available for the OpenCV window.

### 3. Calibrate and run

Start with a recorded video and adjust the geometry in [`main.py`](main.py) to fit its resolution and camera angle.

| Setting | Default | Where to edit |
| --- | --- | --- |
| Horizontal crossing line | `y_coordinate = 500` | The assignment before the processing loop |
| IN lane | `100 < cx < 550`, downward crossing | Both the IN `cv2.line` call and IN detection condition |
| OUT lane | `700 < cx < 1050`, upward crossing | Both the OUT `cv2.line` call and OUT detection condition |

Changing the drawn lane alone does not change counting. The fixed defaults may lie outside a small frame; the application does not validate them.

```bash
# Start processing with the source and geometry configured in main.py.
python main.py
```

Press `q` while the display window has focus to stop. File EOF or `q` leads to the normal cleanup and CSV-export path. An unhandled exception or interruption can bypass it. The final export message alone does not prove frames were processed: a source that fails to open can also reach that message.

### Optional: select an RTSP source

In the capture section of `main.py`, replace the existing `rtsp_url` assignment and active `cap = cv2.VideoCapture('test_video.mp4')` line with your stream configuration:

```python
# Configure the camera address and credentials for your authorized stream.
rtsp_url = "rtsp://<username>:<password>@<ip_address>:<port>/<stream_path>"

# Open the configured URL value instead of the recorded-video filename.
cap = cv2.VideoCapture(rtsp_url)
```

Changing `rtsp_url` alone has no effect on the active file input. The existing commented example uses the literal string `'rtsp_url'`; use the variable without quotes as shown above. Keep camera credentials out of commits and shared logs.

**There is no RTSP reconnection or exponential backoff in the current script.** A failed read ends processing. The script also does not explicitly configure RTSP transport; TCP use in the field study does not establish transport settings for this checkout.

## Counting and output semantics

The tracked classes are person, bicycle, car, motorcycle, bus, train, and truck. A crossing compares the previous and current vertical center of the tracked bounding box:

- **IN:** the center moves from above the line to on or below it, with the current center X strictly inside the IN lane.
- **OUT:** the center moves from below the line to on or above it, with the current center X strictly inside the OUT lane.
- Each track ID can produce at most one event in each direction during one process. Repeat passages by the same track in the same direction are suppressed.
- Lane eligibility uses the current center X, not the movement segment's intersection with the line. Detection misses, fragmented tracks, and diagonal movement can affect counts.

Each qualifying event is inserted and committed to the `vehicle_log` table in `vehicle_log.db`. Commits retain completed writes across many failure scenarios, but this is not a guarantee against every crash or storage failure. The script neither rotates the database nor clears it between runs.

| Column | Type | Meaning |
| --- | --- | --- |
| `id` | INTEGER | Auto-incremented event primary key |
| `track_id` | INTEGER | Tracker-assigned ID; no run/source identifier distinguishes reuse across runs |
| `vehicle_type` | TEXT | Detected class, including `person` |
| `direction` | TEXT | `IN` or `OUT` |
| `number_plate` | TEXT | Accepted OCR text from the crossing frame, or an empty string |
| `timestamp` | TEXT | Local processing time in `YYYY-MM-DD HH:MM:SS` format; no timezone or recording offset |

On normal shutdown, `vehicle_log.csv` is overwritten with **all rows in the database**, including earlier runs. Earlier successful plate reads are not retained across frames. OCR errors inside the guarded helper call are skipped, so a crossing can still be logged with empty plate text; failures elsewhere in plate processing can stop the application.

Illustrative CSV rows, not published deployment records:

```csv
id,track_id,vehicle_type,direction,number_plate,timestamp
1,4,car,IN,BA 1 KA 2345,2024-11-01 10:23:11
2,7,motorcycle,OUT,,2024-11-01 10:23:18
3,12,person,IN,,2024-11-01 10:24:05
```

## Known gaps and implementation plan

The [audit](docs/AUDIT.md) supplies evidence and acceptance criteria for ten findings. Application implementation and runtime validation remain pending:

1. Add an import-safe entry point, validated configuration, and offline tests. Importing the current `main.py` initializes models, opens outputs/capture, and starts processing.
2. Handle missing tracker IDs, failed startup, bounded stream reconnection, and exception-safe resource cleanup/export.
3. Preserve clean inference images and useful plate reads, validate crops, and bound repeated OCR work. Plate inference currently also runs for tracked people.
4. Unify drawing/counting geometry, define track-state lifetimes, and add compatible event context. State currently grows without eviction.
5. Improve operator status, frame-aware overlays, and headless/text alternatives. The present window uses fixed positions and has only the `q` control.
6. Validate the changes with offline checks, visual inspection, and a controlled clip comparison when suitable footage is available.

No test suite or benchmark for this checkout is supplied. The historical figures below are not a performance or accuracy baseline for those changes.

## Kathmandu deployment case study

Bird was previously called **LibertyTrack**, the name used in the accompanying paper:

> **LibertyTrack: A Deployment Case Study for Real-Time Vehicle and Pedestrian Tracking in a Resource-Constrained Campus Environment**<br>
> Danish Puri, New York University, Tandon School of Engineering<br>
> Prepared for IEEE style submission

**[Read the case study (PDF)](https://osf.io/6s7aw/files/9kch3)**

The following preserves the author's historical deployment account. These observations were not reproduced during the source audit and do not establish the behavior of the checked-in script.

| Condition | Liberty College | Global College |
| --- | --- | --- |
| Camera | Fixed Hikvision CCTV | Fixed Hikvision CCTV |
| Reported transport | RTSP over TCP | RTSP over TCP |
| Network | Campus Wi-Fi with frequent dropouts | Campus Wi-Fi with frequent dropouts |
| Traffic | Moderate mixed traffic | High density at peak hours |
| Lighting | Daylight and low light near the gate | Daylight and shaded entry |
| Hardware | Apple M2 laptop, no CUDA | Apple M2 laptop, no CUDA |

| Historical observation | Reported result |
| --- | --- |
| Mean throughput | Approximately 20.8 FPS |
| Longest uninterrupted runtime | Approximately 18 hours |
| Flow events | Thousands of crossings across both sites |
| Data loss | None observed by the operator |
| Directional behavior | Qualitatively consistent during live operation |

The earlier account also reports approximately 14 hours of active logging across three sessions. A verified timeline reconciling that total with the separately reported 18-hour session is unavailable. Both figures are preserved as reported, with their relationship unresolved.

This was a single-operator deployment on one hardware configuration, without independently annotated ground truth or independently verified OCR. Throughput, direction accuracy, and reliability cannot be assumed to carry over to another camera, environment, or software version.

### Reported failure modes and lessons

The field account describes missed detections in low light, empty or garbled OCR under motion blur, fragmented identities in motorcycle clusters, and ambiguous direction for vehicles stopping on the line. It also reports stream recovery, MPS use, and mixed Latin/Devanagari OCR in the deployment. The current script has English-only OCR, no explicit device selection, and no stream recovery.

The practical lessons remain useful:

- Calibrate trip lines on recorded footage from the actual camera angle, and repeat calibration after camera movement.
- Collect manually reviewed examples before making accuracy claims. Keep operator notes about lighting, occlusion, weather, and outages alongside event logs.
- Preserve crossings when a plate is unreadable, and review OCR before downstream use. The field account describes inconsistent plate formatting and manual normalization.
- Treat network recovery, resource cleanup, and output checks as requirements to implement and validate. A long field session alone does not demonstrate every failure path.
- Record timestamp provenance. The field account reported laptop clock drift; current video-file timestamps are processing times.

The contribution is the integration and documentation of existing detection, tracking, and OCR components in a constrained deployment, including custom plate-detector weights. No new detector, tracker, or OCR architecture is claimed.

## Vision and longer-term roadmap

Nepali roads combine dense motorcycle traffic, mixed Latin and Devanagari plates, unusual vehicle classes, dust, rain, and power/network interruptions. Bird aims to support affordable monitoring and eventually traffic management suited to those conditions. Beyond the immediate audit work, planned directions include:

- [ ] Nepali plate recognition and a publishable plate-training dataset
- [ ] Vehicle-class adaptation for e-rickshaws and tempos
- [ ] Pothole/road-hazard detection and low-light processing
- [ ] Multi-camera support and a real-time dashboard
- [ ] Annotated direction-validation footage and a structured field-log template
- [ ] Traffic-flow control experiments at gates and intersections

These capabilities are aspirations, not features of the current script. The audit covers the existing Python/OpenCV application; it excludes the separate `neoBird` repository and webapp work.

## Operations and privacy

The event database can contain vehicle/person movement and plate text. The script does not perform face recognition or biometric identification. Restrict access to logs, inform people at deployment sites, and define an appropriate retention policy. The script does not implement access controls or automated retention, and its generated `vehicle_log.db` and `vehicle_log.csv` files are not currently excluded by `.gitignore`; review files before committing.

For ongoing operation, record the dependency versions, model files, device, and camera configuration used; review outputs after restarts; and plan database archival and recovery from power/network failures. Private deployment footage and logs are not included in this repository.

## License

This project is published under the [MIT License](LICENSE).

<p align="center">
  Built by <a href="https://github.com/danish-puri">Danish Puri</a> · NYU Tandon School of Engineering · Kathmandu field study
</p>
