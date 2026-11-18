"""Evaluation metrics for camouflaged anomaly detection and segmentation."""

import numpy as np
from typing import Dict, Any

try:
    import torch
except ImportError:
    torch = None


def calculate_iou(pred_mask: np.ndarray, target_mask: np.ndarray, threshold: float = 0.5) -> float:
    """Calculate Intersection-over-Union (IoU) between binary masks."""
    p = (pred_mask >= threshold).astype(bool)
    t = (target_mask >= threshold).astype(bool)

    intersection = np.logical_and(p, t).sum()
    union = np.logical_or(p, t).sum()

    if union == 0:
        return 1.0 if intersection == 0 else 0.0
    return float(intersection) / float(union)


def calculate_precision_recall(pred_mask: np.ndarray, target_mask: np.ndarray, threshold: float = 0.5) -> tuple[float, float, float]:
    """Calculate Precision, Recall, and F1-score for detected regions."""
    p = (pred_mask >= threshold).astype(bool)
    t = (target_mask >= threshold).astype(bool)

    tp = np.logical_and(p, t).sum()
    fp = np.logical_and(p, np.logical_not(t)).sum()
    fn = np.logical_and(np.logical_not(p), t).sum()

    precision = float(tp) / float(tp + fp) if (tp + fp) > 0 else 0.0
    recall = float(tp) / float(tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2.0 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return precision, recall, f1


def evaluate_batch_metrics(preds: Any, targets: Any, threshold: float = 0.5) -> Dict[str, float]:
    """Compute mean metrics across a batch tensor."""
    preds_np = preds.detach().cpu().numpy()
    targets_np = targets.detach().cpu().numpy()

    ious = []
    precisions = []
    recalls = []
    f1s = []

    for i in range(preds_np.shape[0]):
        iou = calculate_iou(preds_np[i, 0], targets_np[i, 0], threshold)
        prec, rec, f1 = calculate_precision_recall(preds_np[i, 0], targets_np[i, 0], threshold)
        ious.append(iou)
        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)

    return {
        "mean_iou": float(np.mean(ious)),
        "mean_precision": float(np.mean(precisions)),
        "mean_recall": float(np.mean(recalls)),
        "mean_f1": float(np.mean(f1s))
    }
