# SkyForge Computer Vision Subsystem

The `vision` package houses the image ingestion, spatial preprocessing, camouflage/anomaly detection, target tracking, and aerospace HUD visualization modules.

---

## 1. Directory Structure

```
vision/
├── capture/
│   ├── frame_buffer.py          # Thread-safe ring buffer with drop rate monitoring
│   └── stream_receiver.py       # Wi-Fi video stream & synthetic test generator
├── preprocessing/
│   ├── filters.py               # Bilateral filtering, noise reduction & morphology
│   ├── contrast_enhancement.py  # CLAHE & illumination normalization
│   └── edge_detection.py        # Sobel gradient magnitude & Canny edge detection
├── detection/
│   ├── camouflage_detector.py   # Plan A: Anomaly & texture discrepancy detector
│   ├── anomaly_detector.py      # Statistical Gaussian background subtraction
│   └── person_detector.py       # Plan B (Fallback): Pretrained human detector
├── tracking/
│   └── tracker.py               # Centroid Euclidean distance multi-frame tracker
├── visualization/
│   ├── overlay.py               # Aerospace HUD targeting reticles & telemetry
│   └── heatmap.py               # Pseudo-color confidence heatmap alpha blending
└── README.md
```

---

## 2. Dual-Mode Operation (Plan A vs. Plan B)

- **Plan A (`CamouflageDetector`):** Operates on high-frequency texture gradients and localized standard-deviation variance to isolate camouflaged targets embedded in natural ground foliage.
- **Plan B (`PersonDetector`):** Documented contingency fallback activated if camera resolution limits subtle texture preservation. Leverages HOG+SVM feature pyramids to detect and track human subjects.
