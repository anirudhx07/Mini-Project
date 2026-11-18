"""Benchmark and evaluate model weights against test datasets."""

import os
import argparse
import time
import torch
import numpy as np

from ..models.lightweight_unet import LightweightUNet
from ..datasets.dataset_loader import CamouflageDataset
from .metrics import evaluate_batch_metrics
from torch.utils.data import DataLoader


def evaluate_checkpoint(checkpoint_path: str, test_data_dir: str, batch_size: int = 4):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[EVAL] Evaluating checkpoint: {checkpoint_path} on {device}")

    images_dir = os.path.join(test_data_dir, "images")
    masks_dir = os.path.join(test_data_dir, "masks")

    if not os.path.exists(images_dir):
        print(f"[WARN] Test directory not found: {images_dir}. Please supply valid test imagery.")
        return

    test_ds = CamouflageDataset(images_dir, masks_dir)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    model = LightweightUNet(in_channels=3, num_classes=1, base_filters=16).to(device)
    if os.path.exists(checkpoint_path):
        model.load_state_dict(torch.load(checkpoint_path, map_location=device))
        print("[OK] Checkpoint weights loaded.")
    else:
        print("[WARN] Specified weights not found. Evaluating randomly initialized baseline.")

    model.eval()
    total_iou = 0.0
    total_precision = 0.0
    total_recall = 0.0
    latencies = []

    with torch.no_grad():
        for images, masks in test_loader:
            images, masks = images.to(device), masks.to(device)
            start_t = time.time()
            preds = model(images)
            latencies.append((time.time() - start_t) * 1000.0)

            res = evaluate_batch_metrics(preds, masks)
            total_iou += res["mean_iou"]
            total_precision += res["mean_precision"]
            total_recall += res["mean_recall"]

    n = max(1, len(test_loader))
    print("\n================ EVALUATION SUMMARY ================")
    print(f"Mean IoU:         {total_iou / n:.4f}  (Target: >= 0.50)")
    print(f"Mean Precision:   {total_precision / n:.4f}")
    print(f"Mean Recall:      {total_recall / n:.4f}")
    print(f"Avg Batch Latency:{np.mean(latencies):.2f} ms")
    print("====================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, default="ml/models/checkpoints/best_camouflage_unet.pt")
    parser.add_argument("--test-dir", type=str, default="ml/datasets/test")
    args = parser.parse_args()

    evaluate_checkpoint(args.checkpoint, args.test_dir)
