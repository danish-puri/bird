<h1 align="center">Bird</h1>

<p align="center">🚗🚶 Vehicle and pedestrian counting from campus CCTV in Kathmandu</p>

<p align="center">
<a href="https://docs.ultralytics.com/models/yolo11/"><img src="https://img.shields.io/badge/YOLO-11l-darkgreen?logo=ultralytics" alt="YOLO11l"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
<a href="https://osf.io/6s7aw/files/9kch3"><img src="https://img.shields.io/badge/Paper-Case%20study-red" alt="Deployment case study"></a>
<img src="https://img.shields.io/badge/Field%20study-Kathmandu%2C%20Nepal-orange" alt="Kathmandu field study">
</p>

> **This is version 1.** I rebuilt it as **[GateWatch](https://github.com/danish-puri/GateWatch)**, a tested, headless service with stream reconnects, per-stream calibration, and an HTTP API. Start there for the current system. This repo stays up as the prototype I ran in the field and wrote my case study about.

Bird watches a CCTV feed, tracks people and vehicles, tries to read number plates, and logs every IN and OUT crossing to SQLite. I built it for two college campuses in Kathmandu, where traffic is dense and mixed, lighting changes through the day, the network drops often, and the only hardware was a laptop with no GPU.

## How it works

`main.py` is a single script.

1. **YOLO11l** detects and tracks people, bicycles, cars, motorcycles, buses, and trucks with persistent track IDs.
2. **A custom plate detector** (`best.pt`) looks for a plate inside each tracked vehicle, and **EasyOCR** reads it.
3. **Two lanes on a horizontal line** decide direction. A track whose center moves down across the line in the left lane is IN, and one moving up in the right lane is OUT. Each track counts at most once per direction.
4. **SQLite** stores every crossing with its track ID, class, direction, plate text, and time. On exit the whole log is exported to `vehicle_log.csv`.

## Running it

```bash
git clone https://github.com/danish-puri/bird.git
cd bird
python3.10 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Download `yolo11l.pt` from [Ultralytics](https://docs.ultralytics.com/models/yolo11/) into the repo root, put your video next to it as `test_video.mp4`, and run

```bash
python main.py
```

An OpenCV window shows the tracks and counts. Press `q` to stop. To use a live camera, set `rtsp_url` in `main.py` and pass it to `cv2.VideoCapture` instead of the file name. Keep real credentials out of commits.

The line position (`y_coordinate = 500`) and the two lane ranges are hardcoded for my camera angle. Adjust them to your footage before trusting any counts.

## What I learned in the field

I ran Bird at Liberty College and Global College in Kathmandu on fixed Hikvision cameras over RTSP, on an Apple M2 laptop. From my own logs, the deployed build averaged about 20.8 FPS, ran for up to about 18 hours without stopping, and recorded thousands of crossings with no data loss I could see. These are single-operator observations, not a benchmark against labelled ground truth. The deployed build also had stream recovery that this script does not.

The failures taught me more than the successes.

- Detection drops in low light, and clusters of motorcycles break into fragmented tracks.
- Vehicles that stop on the line make direction ambiguous.
- Plate OCR came back empty or garbled under motion blur. Later, on the cameras I used for GateWatch, I measured why. Plate characters were only 8 to 15 pixels tall, and reliable reading needs about 30, so it was a camera problem more than a model problem.
- Laptop clock drift made timestamps unreliable, so the time source has to be recorded.

Every one of these shaped GateWatch. It uses a dwell filter for parked vehicles, a cooldown for vehicles that turn at the gate, a segment test instead of a line, stream reconnects, and it turns plate reading off until a suitable camera exists.

## Case study

Bird was first called **LibertyTrack**, the name used in the paper.

> **LibertyTrack: A Deployment Case Study for Real-Time Vehicle and Pedestrian Tracking in a Resource-Constrained Campus Environment**<br>
> Danish Puri, New York University, Tandon School of Engineering

**[Read the case study (PDF)](https://osf.io/6s7aw/files/9kch3)**

The contribution is integrating existing detection, tracking, and OCR components under real constraints, plus the custom plate-detector weights. I do not claim a new detector, tracker, or OCR method.

## Privacy

The log can hold movement records and plate text, so I keep deployment footage and logs out of this repository. The script does no face recognition. Anyone running it should tell people at the site, restrict access to the logs, and decide how long to keep them.

## License

[MIT](LICENSE)
