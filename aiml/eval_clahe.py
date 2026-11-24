"""
==============================================================================
Team SkyForge-87: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing
Module: eval_clahe.py
Description: Quantitative Evaluation of U-Net segmentation on CAMO dataset:
             Plain Image vs. CLAHE at clipLimit 1.0, 2.0, and 4.0.
==============================================================================
"""

import os
import csv
import cv2
import torch
import numpy as np
from datetime import datetime

# Import teammate's predict module without modifying it
import predict as pred_mod

# Task 1: Import preprocessing functions from preprocess.py instead of local duplicate
from preprocess import apply_clahe, enhance


def get_predicted_mask(frame: np.ndarray) -> np.ndarray:
    """
    Compute binary prediction mask exactly as done in predict.py:
    - Resize to SIZE x SIZE (256x256)
    - Normalise using ImageNet MEAN and STD
    - Pass through U-Net model and apply Sigmoid
    - Resize probability map back to original frame size (w, h)
    - Threshold at 0.30
    """
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(cv2.resize(frame, (pred_mod.SIZE, pred_mod.SIZE)), cv2.COLOR_BGR2RGB)
    x = (rgb.astype(np.float32) / 255.0 - pred_mod.MEAN) / pred_mod.STD
    x = torch.from_numpy(x.transpose(2, 0, 1))[None].to(pred_mod.device)
    
    with torch.no_grad():
        prob = torch.sigmoid(pred_mod._model(x))[0, 0].cpu().numpy()
        
    prob = cv2.resize(prob, (w, h))
    pred_binary = (prob > 0.30)
    return pred_binary


def compute_metrics(pred_mask: np.ndarray, gt_mask: np.ndarray):
    """
    Calculate IoU (Jaccard Index), Precision, and Recall between binary masks.
    Handles edge cases (empty masks) safely.
    """
    intersection = np.logical_and(pred_mask, gt_mask).sum()
    union = np.logical_or(pred_mask, gt_mask).sum()
    pred_pos = pred_mask.sum()
    gt_pos = gt_mask.sum()

    # IoU
    if union == 0:
        iou = 1.0 if gt_pos == 0 else 0.0
    else:
        iou = float(intersection) / float(union)

    # Precision = TP / (TP + FP)
    if pred_pos == 0:
        precision = 1.0 if gt_pos == 0 else 0.0
    else:
        precision = float(intersection) / float(pred_pos)

    # Recall = TP / (TP + FN)
    if gt_pos == 0:
        recall = 1.0 if pred_pos == 0 else 0.0
    else:
        recall = float(intersection) / float(gt_pos)

    return iou, precision, recall


def evaluate():
    # 1. Load trained model weights
    model_path = "best_model.pth"
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    print(f"[Eval] Loading model from '{model_path}' onto {pred_mod.device}...")
    pred_mod.load_model(model_path)
    print("[Eval] Model loaded successfully!\n")

    # 2. Find images and ground-truth masks
    img_dir = "test_images"
    mask_dir = "test_masks"
    if not os.path.exists(img_dir) or not os.path.exists(mask_dir):
        raise FileNotFoundError(f"Required folders {img_dir}/ or {mask_dir}/ not found!")

    image_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    print(f"[Eval] Found {len(image_files)} test images in '{img_dir}'.\n")

    settings = [
        ("Plain (No CLAHE)", None),
        ("CLAHE (clip=1.0)", 1.0),
        ("CLAHE (clip=2.0)", 2.0),
        ("CLAHE (clip=4.0)", 4.0),
    ]

    # Store detailed per-image and aggregate results
    results_per_image = []
    setting_metrics = {name: {"iou": [], "precision": [], "recall": []} for name, _ in settings}

    # 3. Process each image
    for idx, fname in enumerate(image_files, start=1):
        img_path = os.path.join(img_dir, fname)
        base_name = os.path.splitext(fname)[0]
        mask_path = os.path.join(mask_dir, base_name + ".png")

        if not os.path.exists(mask_path):
            print(f"[Warning] Mask missing for {fname} at {mask_path}, skipping.")
            continue

        raw_img = cv2.imread(img_path)
        h, w = raw_img.shape[:2]

        # Load matching ground-truth mask, resize with nearest-neighbour, and binarise at >127
        raw_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        gt_resized = cv2.resize(raw_mask, (w, h), interpolation=cv2.INTER_NEAREST)
        gt_binary = (gt_resized > 127)

        row_data = {"image": fname}

        for setting_name, clip_val in settings:
            if clip_val is None:
                # Plain image
                input_frame = raw_img
            else:
                # CLAHE enhanced frame
                input_frame = apply_clahe(raw_img, clip_limit=clip_val, tile_grid_size=(8, 8))

            pred_binary = get_predicted_mask(input_frame)
            iou, prec, rec = compute_metrics(pred_binary, gt_binary)

            setting_metrics[setting_name]["iou"].append(iou)
            setting_metrics[setting_name]["precision"].append(prec)
            setting_metrics[setting_name]["recall"].append(rec)

            row_data[f"{setting_name}_iou"] = round(iou, 4)
            row_data[f"{setting_name}_prec"] = round(prec, 4)
            row_data[f"{setting_name}_rec"] = round(rec, 4)

        results_per_image.append(row_data)

    # 4. Print Per-Image Table
    print("=" * 105)
    print(f"{'Image':<24} | {'Plain IoU':<10} | {'CLAHE 1.0':<10} | {'CLAHE 2.0':<10} | {'CLAHE 4.0':<10}")
    print("-" * 105)
    for r in results_per_image:
        print(f"{r['image']:<24} | {r['Plain (No CLAHE)_iou']:<10.4f} | {r['CLAHE (clip=1.0)_iou']:<10.4f} | {r['CLAHE (clip=2.0)_iou']:<10.4f} | {r['CLAHE (clip=4.0)_iou']:<10.4f}")
    print("=" * 105)

    # 5. Print Summary Table
    print("\n" + "=" * 65)
    print("          OVERALL PERFORMANCE SUMMARY (Mean over 12 CAMO Images) ")
    print("=" * 65)
    print(f"{'Preprocessing Setting':<25} | {'Mean IoU':<10} | {'Precision':<10} | {'Recall':<10}")
    print("-" * 65)
    summary_rows = []
    for setting_name, _ in settings:
        m_iou = float(np.mean(setting_metrics[setting_name]["iou"]))
        m_prec = float(np.mean(setting_metrics[setting_name]["precision"]))
        m_rec = float(np.mean(setting_metrics[setting_name]["recall"]))
        summary_rows.append({
            "setting": setting_name,
            "mean_iou": round(m_iou, 4),
            "mean_precision": round(m_prec, 4),
            "mean_recall": round(m_rec, 4)
        })
        print(f"{setting_name:<25} | {m_iou:<10.4f} | {m_prec:<10.4f} | {m_rec:<10.4f}")
    print("=" * 65)

    # 6. Save results to eval_results.csv
    csv_file = "eval_results.csv"
    with open(csv_file, "w", newline="") as f:
        # Write Per-Image section
        fieldnames = ["image"]
        for sname, _ in settings:
            fieldnames.extend([f"{sname}_iou", f"{sname}_prec", f"{sname}_rec"])
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results_per_image:
            writer.writerow(r)

        # Blank row separator
        writer.writerow({k: "" for k in fieldnames})
        
        # Write Summary rows
        f.write("# SUMMARY AVERAGES\n")
        f.write("Setting,Mean_IoU,Mean_Precision,Mean_Recall\n")
        for s in summary_rows:
            f.write(f"{s['setting']},{s['mean_iou']},{s['mean_precision']},{s['mean_recall']}\n")

    print(f"\n[Eval Complete] Full results saved to '{csv_file}'.")


if __name__ == "__main__":
    evaluate()
