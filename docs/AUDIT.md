# Bird source audit and implementation plan

Status: planning complete; application implementation and execution have not started.

## Scope and baseline

- Repository: [danish-puri/bird](https://github.com/danish-puri/bird).
- Audited revision: [`dfbc32f733ea27918aeb8f360b50ee400409a837`](https://github.com/danish-puri/bird/tree/dfbc32f733ea27918aeb8f360b50ee400409a837), `main` at checkout time.
- Implementation branch: `feat/bird-audit-improvements`, created from that revision.
- Local checkout: `/Users/danishpuri/CS/Programming/bird/bird-audit`.
- Review method: static source and documentation inspection, with an independent second source review. No application imports, model loading, camera connections, dependency installation, tests, or benchmarks were performed.
- Reviewed files: `main.py`, `README.md`, `requirements.txt`, and `.gitignore`. The presence of `best.pt` was verified; its contents and accuracy were not evaluated.
- The separate `neoBird` repository and all webapp work are excluded.

Bird at this revision is a single Python script with an OpenCV operator window, YOLO tracking, plate recognition, and SQLite/CSV event logging. This audit covers reliability and correctness as prerequisites for usability, plus performance, accessibility, and visual quality of that existing interface. It does not propose a web dashboard.

The repository tracks six files. There is no test suite, test configuration, or CI workflow at the audited revision. `best.pt` is included; `yolo11l.pt` and input footage are not. The README describes the footage as withheld. Missing private deployment footage is a validation constraint, not a request to publish it.

## Priority summary

P1 means address in the first implementation pass because the behavior can stop operation, lose useful event information, or mislead operators. P2 means address next for sustained operation and usability. These priorities are engineering judgments, not measured incident rates.

| ID | Priority | Area | Finding |
| --- | --- | --- | --- |
| B01 | P1 | Reliability | Tracker IDs are dereferenced without checking availability. |
| B02 | P1 | Usability/reliability | Unusable inputs can appear successful; RTSP reconnection is absent. |
| B03 | P1 | Reliability | Exceptions bypass explicit cleanup and CSV export. |
| B04 | P1 | Event quality | Earlier plate reads are discarded; rendering changes inference input. |
| B05 | P1 | Reproducibility | Importing starts the pipeline, and no automated checks are supplied. |
| B06 | P2 | Performance | Plate detection/OCR runs repeatedly inside the frame loop. |
| B07 | P2 | Counting | Fixed geometry and lifetime deduplication limit crossing semantics. |
| B08 | P2 | Sustained operation | Track state grows without eviction and events lack run/source context. |
| B09 | P2 | Accessibility/visual quality | Fixed overlays lack clear status, scalable layout, and textual alternatives. |
| B10 | P2 | Documentation | Operational instructions conflict with the shipped implementation. |

## Findings and proposed fixes

### B01 — Missing tracker IDs can terminate processing

Evidence: [main.py, lines 76–82][tracking]. The condition checks `boxes.data` and then calls `boxes.id.int()` without checking `id`. Ultralytics documents [tracking IDs as optional](https://docs.ultralytics.com/reference/engine/results/#ultralytics.engine.results.Boxes.id). Checking the data tensor does not establish that IDs are present.

Impact: a result with boxes but no IDs raises an exception instead of letting the pipeline continue. The branch defect is visible in source; how frequently it occurs with the eventual installed dependency versions has not been measured.

Proposed fix: validate the result, boxes, and ID availability before track-dependent work. Treat empty/untracked frames as valid input; continue reporting status and accepting operator controls. Do not invent persistent IDs for untracked detections.

Acceptance: synthetic results with empty boxes, missing IDs, and normal tracks are handled without unexpected termination; an empty frame cannot create a crossing event.

### B02 — Startup and end-of-input need explicit outcomes

Evidence: [main.py, lines 55–74][capture] hard-codes `test_video.mp4`, while the unused RTSP example passes the literal string `'rtsp_url'`. If capture never opens, the loop is skipped and processing reaches the normal export/success message. Every failed read breaks out; there is no reconnection loop. This conflicts with [README.md, lines 167–173][fault-tolerance].

Impact: operators cannot distinguish a missing/unreadable source from a completed run using the final success message. Enabling RTSP by following the commented example does not pass the configured URL, and an interrupted stream ends processing.

Proposed fix: add a documented command-line/configuration entry point for source, weights, output locations, device, and trip lines. Validate configuration before loading expensive models. Report capture-open failure clearly and return a failure status. Distinguish expected file EOF from live-stream failure; implement bounded, cancellable reconnect/backoff for streams, with explicit tracker-state handling after reconnect.

Acceptance: missing files and failed opens report failure; file EOF exits normally; mocked live disconnects exercise retry, recovery, exhaustion, and cancellation. No test needs access to a real camera.

### B03 — Shutdown and export are not exception-safe

Evidence: [main.py, lines 147–153][shutdown] releases the camera, closes the primary database connection, exports the entire table through a second unclosed connection, and destroys windows only after normal loop exit. No outer `try/finally` protects these operations. [The bare OCR exception handler][plate-loop] also catches interruption exceptions raised inside that block.

Impact: an inference, database, or display error, or interruption outside that OCR block, skips the explicit cleanup/export path. Previously committed SQLite records are not thereby proven lost; the supported finding is missing finalization and CSV output. An export error can also prevent window cleanup.

Proposed fix: own resources in a small runner with guaranteed finalization, isolate export errors from other cleanup, explicitly close every connection, and catch expected OCR errors without swallowing shutdown signals. Preserve immediate event commits until measurement justifies a documented durability tradeoff. Use streaming CSV export and replacement of a completed temporary export to avoid loading the entire historical table into memory or leaving a partial final CSV.

Acceptance: injected inference, write, export, and interruption failures release acquired resources; committed rows remain readable in temporary test databases; a failed export reports its error and leaves a previous completed export intact.

### B04 — Plate evidence is lost between frames and altered before inference

Evidence: [main.py, lines 84–114][plate-loop] draws trip lines before cropping from the same frame, then draws each object's annotations before processing the next object. Plate detection therefore receives pixels that can already contain overlays. `plate_text` is reset to an empty string for every track on every frame. [Crossing writes][counting] use only the current frame's result.

[The OCR helper, lines 16–26][ocr], keeps the last accepted text fragment, applies no confidence threshold when exactly one fragment is returned, and uses `COLOR_RGB2GRAY` for the captured image. OpenCV distinguishes RGB and BGR conversions and documents its [default BGR color ordering](https://docs.opencv.org/4.12.0/d8/d01/group__imgproc__color__conversions.html). The full vehicle crop is not clamped/checked before plate inference, while only the inner OCR call is guarded.

Impact: a plate read just before a crossing is discarded if the crossing frame is blurred or unreadable. Overlay pixels can affect overlapping crops. Multi-part OCR results are not assembled into a complete plate. The source demonstrates these data paths; accuracy loss has not been quantified.

Proposed fix: retain an untouched inference frame and render on a separate display frame; clamp and validate vehicle and plate crops; use the matching color conversion; aggregate text fragments in a documented order with consistent confidence filtering; cache the best accepted read for the current track lifecycle. Keep counting independent of OCR success and surface OCR failures without exposing source credentials.

Acceptance: a good read followed by an empty crossing-frame read retains the earlier accepted text; out-of-bounds/empty crops are skipped; multi-fragment and low-confidence OCR outputs behave as specified; enabling overlays does not change the image supplied to plate inference; OCR failure still permits a crossing event.

### B05 — Imports have operational side effects and setup is not reproducible

Evidence: [main.py][full-source] loads models/readers, opens SQLite, opens capture, and enters processing at module scope. [requirements.txt][requirements] lists four packages without version constraints. The tracked file inventory contains no tests or CI configuration.

Impact: importing application functions for tests also starts expensive operational work, potentially including model downloads and local file writes. A fresh installation cannot reproduce a known dependency set from this repository alone.

Proposed fix: introduce an explicit entry point, keep imports free of operational effects, and extract only the boundaries needed to test configuration, counting, OCR selection, capture, and persistence. Record a supported Python/dependency combination after compatibility verification; do not invent pins. Add a small offline test suite before broader behavioral changes. Add CI only after those checks are reliable locally.

Acceptance: importing modules or requesting CLI help does not load weights, connect to cameras, or create output files; focused tests use fake models/readers and temporary outputs; a documented isolated environment reproduces the selected checks.

### B06 — Repeated inference is a strong performance candidate, not a benchmark result

Evidence: [main.py, lines 76–109][plate-loop] invokes vehicle tracking once per frame, then plate detection for every tracked object, including people, and OCR for each detected plate until a read succeeds. There is no class eligibility check, cooldown, best-read cache, or stage timing. `yolo11l.pt` is fixed at [model initialization][initialization].

Impact: plate work scales with the number of tracks in each frame and blocks progress through capture/display. It is a likely optimization target; this audit cannot establish the dominant bottleneck, current FPS, latency, or a percentage speedup.

Proposed fix: first instrument capture, detection/tracking, plate detection/OCR, persistence, and rendering. Then restrict plate work to eligible vehicle classes and schedule bounded attempts per track, retaining useful reads. Make model/device settings explicit while keeping the initial default stable. Prefer these bounded changes before adding worker queues, dropping frames, or replacing the tracker/model.

Acceptance: a fake-reader test demonstrates fewer repeated OCR calls while preserving known plate reads and crossing events. A later fixed-clip comparison records dependency versions, weights, device, resolution, warm-up, elapsed processing time, stage timings, and event/OCR outcomes. Any improvement claim must report both speed and quality observations.

### B07 — Crossing geometry and deduplication need an explicit contract

Evidence: [main.py, lines 62–69 and 116–129][counting] stores only previous Y positions, uses fixed pixel ranges, and allows each track at most one IN and one OUT event for its entire process lifetime. The lane test uses the current X position rather than the X position where the movement segment intersects the line. Drawing uses separately hard-coded copies of the ranges.

Impact: a diagonal movement can be accepted or rejected based on the endpoint rather than the crossing location. Changing frame resolution can place lanes outside the image. A repeat crossing by the same track in the same direction is suppressed. That last behavior could be intentional unique-track counting; it is not automatically a defect until the counting contract is chosen.

Proposed fix: make one validated geometry configuration drive drawing and counting. Track both prior coordinates and use finite-segment crossing logic. Initially preserve/document unique-track-per-direction behavior; introduce cooldown/hysteresis and repeat-crossing behavior only as an explicit event-counting option. Treat tracker resets as lifecycle boundaries.

Acceptance: synthetic paths cover IN, OUT, no crossing, crossing outside the segment, diagonal movement, line jitter, repeat crossings, and boundary coordinates. Configuration checks cover multiple frame sizes. The tests state whether the expected unit is a unique track or a passage event.

### B08 — Long runs accumulate state and mix event provenance

Evidence: [main.py, lines 64–69 and 116–129][counting] grows `previous_y`, `in_ids`, and `out_ids` without eviction. [The schema and logger, lines 29–53][logging], contain no run/source identifier, and assign `datetime.now()` at processing time. [Shutdown export][shutdown] selects all rows from the same fixed database. `.gitignore` excludes Django's `db.sqlite3`, but not the actual `vehicle_log.db` or `vehicle_log.csv` outputs.

Impact: memory use grows with observed identities. Reused track IDs across runs are indistinguishable in aggregated logs; processing timestamps can be mistaken for recording times. Output files can be accidentally included in a later broad Git add. Growth rate and memory impact remain unmeasured.

Proposed fix: scope track/OCR state to documented session and expiry rules, retaining any metadata required by the selected deduplication contract. Keep process timestamps explicitly labeled; add source/run metadata and recording offsets only through a backward-compatible logging design. Make run-versus-history export scope explicit and ignore the generated outputs by exact names. Do not delete or replace existing databases.

Acceptance: simulated long sessions evict stale state without resetting active tracks; tracker restart/reuse does not attach a stale plate to another vehicle; export scope and timestamp meaning are documented; existing database rows remain usable if metadata is added.

### B09 — The operator window needs clearer, adaptable information

Evidence: [main.py, lines 84–85 and 111–144][display] draws thin colored lines and text directly over arbitrary video. Trip lines have no on-image IN/OUT labels or direction arrows. Counts use fixed X positions of 50 and 800, share a Y cursor between the two columns, and appear only for classes already counted. Labels at `y1 - 10` can lie above the image. The only built-in key control is `q`, and the window shows no source state, elapsed time, processing speed, or help.

Impact: small frames can clip counts; dense or bright scenes can obscure text; an empty count area is ambiguous. Red/green trip lines require remembered color meaning even though count text separately names directions. OpenCV-drawn text is raster content rather than a semantic status interface. The source supports these limitations; no visual, keyboard, screen-reader, contrast, or usability test was performed.

Proposed fix: add a compact status/count panel with a consistent opaque background; use frame-aware layout, bounded label positions, stable class order, explicit zero counts, and labeled IN/OUT arrows. Use color as an additional cue. Show source type, connection/processing state, and operator help. Add a headless mode with readable terminal status and accessible text/CSV outputs; these alternatives improve access without claiming the OpenCV canvas becomes screen-reader accessible.

Acceptance: after execution is authorized, inspect synthetic and representative frames at small and large sizes and in grayscale, check keyboard quit/interruption and headless behavior, and ensure status remains visible without detections. Confirm readable text against the actual panel background. No WCAG compliance or visual-quality score is asserted by this static audit.

### B10 — Align usage instructions with what is shipped

Evidence: [README.md setup][setup] uses the historical `puriiiii/bird` URL. [The fault-tolerance section][fault-tolerance] claims reconnect/backoff that does not exist in the current source. [The design table][design-table] describes Nepali OCR, but initialization is English-only; the newer technical-stack section already clarifies this. Device usage described in deployment observations is not explicitly selected in the script. The [project/reproducibility sections][reproducibility] correctly identify the missing base weights and footage.

Impact: a reader can follow instructions and expect capabilities the checked-in version does not supply. Deployment observations cannot establish runtime behavior or performance for this checkout.

Proposed fix: update the canonical clone URL, consolidate setup and configuration instructions, document first-use model requirements and actual OCR languages/device selection, and distinguish historical deployment observations from verified current behavior. Describe reconnect as implemented only after B02's tests pass. Verify language support against the eventual dependency version before expanding the language configuration.

Acceptance: every quickstart option maps to the implemented interface; missing-input instructions explain the actual failure path; each operational claim names the behavior or check that supports it. Historical 20.8 FPS and 18-hour observations remain clearly attributed and are not reused as this audit's baseline.

## Implementation sequence on this branch

The branch currently contains this report only. The steps below are proposed implementation work for a subsequent instruction to begin coding.

| Order | Work package | Findings | Reviewable outcome |
| --- | --- | --- | --- |
| 1 | Entry point, configuration, and offline test seams | B02, B05 | Predictable startup and isolated tests without model/camera side effects. |
| 2 | Processing reliability and finalization | B01, B02, B03 | Missing IDs, capture failures, reconnect, and shutdown handled explicitly. |
| 3 | Plate quality and bounded repeated work | B04, B06 | Clean inference images, retained plate evidence, controlled OCR attempts, stage timings. |
| 4 | Geometry, state lifecycle, and event context | B07, B08 | One calibration source, tested crossing contract, bounded state, compatible log/export behavior. |
| 5 | Operator display and documentation | B09, B10 | Readable status/counts, text alternatives, and accurate setup instructions. |
| 6 | Controlled validation and handoff | All | Results from the authorized checks, annotated before/after evidence, and remaining limitations. |

Keep the design proportional to a single-script application. Preserve the SQLite event store, current vehicle/person counting scope, and model choices initially. Document any deliberate behavior change. Every new or modified function and logical section must include explanatory comments/docstrings, following the user's persistent coding preference.

## Verification plan — not executed

There are no existing repository tests to run at the baseline. Future validation should begin with the focused tests below and expand only when a change requires it.

| Layer | Planned coverage | Prerequisites |
| --- | --- | --- |
| Offline unit tests | Missing IDs, OCR selection/caching, crop validity, geometry, state expiry, configuration. | Import-safe components; fake model/OCR outputs. |
| Offline integration tests | Failed startup, EOF, stream retry, interruption, logging/export failures. | Fake capture and clock; temporary output directory and SQLite database. |
| Static checks | Syntax/lint and any newly introduced project checks. | A documented supported environment; no model loading. |
| Visual/operator checks | Label clipping, zero counts, status visibility, color-independent direction, headless/keyboard behavior. | Authorization to render; synthetic frames first, representative footage later. |
| Performance/accuracy comparison | Stage timings, elapsed time, OCR calls, crossing output, plate-read quality. | Authorized recorded clip, model files, fixed configuration/device, and manual reference annotations. |

Do not infer detection accuracy from passing mocked tests. Do not claim speedups from reduced call counts alone. Compare the same clip and hardware for any measured before/after result; report that operational footage and historical field observations are not an independently labeled benchmark.

## Current handoff

Completed: repository identity and base revision verified; local implementation branch created; source audit, priorities, and acceptance criteria documented.

Deferred by the user's planning constraint: application edits, new tests, dependency installation, pipeline/model execution, benchmarks, and runtime/visual validation. No camera access, deployment, remote push, or pull request is part of this preparation.

[full-source]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/main.py
[initialization]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/main.py#L9-L13
[ocr]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/main.py#L16-L26
[logging]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/main.py#L29-L53
[capture]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/main.py#L55-L74
[tracking]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/main.py#L76-L82
[plate-loop]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/main.py#L76-L114
[counting]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/main.py#L62-L129
[display]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/main.py#L84-L144
[shutdown]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/main.py#L147-L153
[requirements]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/requirements.txt
[setup]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/README.md#L114-L165
[fault-tolerance]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/README.md#L167-L173
[design-table]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/README.md#L71-L97
[reproducibility]: https://github.com/danish-puri/bird/blob/dfbc32f733ea27918aeb8f360b50ee400409a837/README.md#L289-L312
