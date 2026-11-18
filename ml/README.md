# SkyForge Machine Learning & Detection Models

This package provides the data pipeline, model architectures, loss formulations, and evaluation routines for aerial camouflage segmentation and anomaly detection.

---

## 1. Directory Structure

```
ml/
├── datasets/
│   ├── dataset_loader.py       # PyTorch Dataset for COD10K / CAMO and custom aerial frames
│   └── README.md               # Dataset sourcing, annotation guidelines & splits
├── models/
│   ├── lightweight_unet.py     # Compact U-Net for low-latency CPU/edge inference
│   └── README.md               # Architecture details, parameter count & latency profile
├── training/
│   ├── train.py                # Supervised training loop with model checkpointing
│   └── loss_functions.py       # Hybrid BCE + Soft Dice Loss for imbalanced masks
├── evaluation/
│   ├── metrics.py              # Mean IoU, Precision, Recall, and F1 calculations
│   └── evaluate.py             # Evaluation benchmark runner
└── README.md
```

---

## 2. Model Architecture & Target Performance

- **Backbone:** 4-stage encoder-decoder U-Net with skip connections and batch normalization.
- **Input Dimensions:** $3 \times 224 \times 224$ (Normalized RGB tensor).
- **Target Performance Benchmarks (from Approved Synopsis):**
  - **Mean IoU:** $\ge 0.50$ on camouflaged test partition.
  - **Inference Latency:** $\le 500\text{ ms}$ on ground-station laptop CPU.
