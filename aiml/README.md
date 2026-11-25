## Camouflage Segmentation Model (Plan A)

Model: U-Net, ResNet18 encoder (ImageNet pretrained), segmentation_models_pytorch.
Input 256x256 RGB, output 1-channel mask. Loss: BCE + Dice. Adam, lr 3e-4,
cosine decay, batch 16, flip augmentation, 30 epochs on a Colab T4 GPU.
(Training was resumed once from epoch 3 after a session change.)

Dataset: CAMO (CVIU 2019), 1250 images. Official Train (1000) split into
850 train / 150 val (seed 42); official Test (250) used only for final evaluation.
Licence: [README se likho]

Results (test set, 250 images, IoU = mean per-image IoU at 256x256):
  threshold 0.50: IoU 0.4965, precision 0.7304, recall 0.6229
  threshold 0.30: IoU 0.5049, precision 0.7140, recall 0.6491  (55.2% images IoU >= 0.5)
  Best validation IoU: 0.5952 (epoch 26)
  Threshold 0.30 was chosen on the validation set; the test set was used once.
  CLAHE at inference: no meaningful change (IoU 0.4922 with CLAHE vs 0.4965 without).

Observations:
  - Validation IoU plateaued after about epoch 11 while train loss kept falling
    (overfitting on a small dataset). Val (0.60) and test (0.50) differ; the cause
    is not confirmed.
  - Precision is higher than recall: the model tends to under-segment objects.
  - The model was never trained on images with no camouflaged object, so it may
    mark regions on ordinary frames.

Speed: [CPU ms / GPU ms, results_log.csv se, warm-up ke baad]
Weights: [Drive link]
