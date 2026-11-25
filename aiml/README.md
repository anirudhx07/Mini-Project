# Camouflage Segmentation Model (Plan A)

U-Net with a ResNet18 encoder (ImageNet pretrained, `segmentation_models_pytorch`).
Input: 256x256 RGB image. Output: 1-channel mask. Loss: BCE + Dice.
Adam, lr 3e-4, cosine decay, batch 16, horizontal-flip augmentation, 30 epochs on a Colab T4 GPU.
Training was resumed once from epoch 3 after a Colab session change.

**Weights (`best_model.pth`, epoch 26, about 55 MB):** [Google Drive](https://drive.google.com/file/d/1dMYxk4Us9onZsJbcDoRSpmKK-jOYLajK/view?usp=sharing)
The weights are not stored in this repo. Download the file and place it next to `predict.py`.

## Dataset

CAMO (release "CAMO-V.1.0-CVIU2019"), 1250 images with masks, obtained from a Kaggle upload by Ivan Omelchenko.
Citation: see the README shipped with the dataset.
Licence: [CC BY-NC-SA 3.0 IGO](https://creativecommons.org/licenses/by-nc-sa/3.0/igo/) (Attribution-NonCommercial-ShareAlike).
This model was trained for an academic, non-commercial project.

Split: official Train (1000) divided into 850 train / 150 validation (seed 42).
Official Test (250) was used only for the final evaluation.

## Results (test set, 250 images)

IoU is the mean per-image IoU at 256x256.

| Threshold | IoU | Precision | Recall | Images with IoU >= 0.5 |
|---|---|---|---|---|
| 0.50 | 0.4965 | 0.7304 | 0.6229 | 52.0% |
| 0.30 (used in `predict.py`) | 0.5049 | 0.7140 | 0.6491 | 55.2% |

- Best validation IoU: 0.5952 (epoch 26).
- Threshold 0.30 was chosen on the validation set; the test set was evaluated once with it.
- CLAHE at inference gave no meaningful change (IoU 0.4922 with CLAHE vs 0.4965 without, threshold 0.50).

## Observations and limitations

- Validation IoU plateaued after about epoch 11 while train loss kept falling (overfitting on a small dataset). Validation (0.60) and test (0.50) IoU differ; the cause is not confirmed.
- Precision is higher than recall: the model tends to under-segment objects.
- The model was never trained on images without a camouflaged object. On 29 ordinary phone photos (no camouflaged object) it produced a non-empty mask on 26 of them. Its confidence (mean probability inside the mask) overlapped with that on camouflage test images (mean 0.73 vs 0.88), and neither confidence nor mask area separated the two groups. It therefore cannot be used to decide whether an object is present. Small samples (29 and 12 images) from different sources; treat this as an indication only.
- Results are at 256x256 resolution. Performance on low-quality ESP32 camera frames has not been tested.

## Speed (CPU only)

Pushkar's laptop, Intel64 Family 6 Model 183, `pipeline.py` on `test.mp4`, 140 benchmarked frames after 10 warm-up frames.

| Power state | Heatmap | Latency | FPS |
|---|---|---|---|
| Plugged in, Best performance | off | 31.2 ms | 32.0 |
| Plugged in, Best performance | on | 32.5 ms | 30.8 |
| Battery, Eco | on | 162.5 ms | 6.2 |

Latency depends strongly on the laptop power mode, so run demos plugged in.
All measured runs, including Priyanshu's laptop, are in `benchmark_summary.csv`. GPU speed is not benchmarked in this README.

## Usage

    from predict import predict, load_model
    load_model("best_model.pth")
    annotated, confidence = predict(frame)   # frame: OpenCV BGR image

`predict(frame)` takes a BGR numpy array of any size and returns an annotated BGR image of the same size
and a float in 0..1 (mean probability inside the mask, 0.0 if nothing is detected).
The confidence is the model's score, not an accuracy.

## Files

- `predict.py`: inference wrapper (threshold 0.30)
- `p_day2.py`: simple folder/webcam/video test script
- `training/`: training notebook, `train_log.csv`, `test_results_thr0.3.csv`, `training_curves.png`, `test_examples.png`
- `benchmark_summary.csv`: speed runs
