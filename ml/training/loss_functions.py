"""Loss functions for camouflaged object segmentation."""

import torch
import torch.nn as nn


class DiceLoss(nn.Module):
    """Computes continuous Dice loss for binary segmentation masks."""

    def __init__(self, smooth: float = 1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        pred_flat = pred.contiguous().view(-1)
        target_flat = target.contiguous().view(-1)

        intersection = (pred_flat * target_flat).sum()
        dice = (2.0 * intersection + self.smooth) / (pred_flat.sum() + target_flat.sum() + self.smooth)
        return 1.0 - dice


class CombinedBCEDiceLoss(nn.Module):
    """Hybrid loss combining BCE with Dice loss to handle foreground/background imbalance."""

    def __init__(self, bce_weight: float = 0.5, dice_weight: float = 0.5):
        super().__init__()
        self.bce = nn.BCELoss()
        self.dice = DiceLoss()
        self.bce_weight = bce_weight
        self.dice_weight = dice_weight

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        loss_bce = self.bce(pred, target)
        loss_dice = self.dice(pred, target)
        return self.bce_weight * loss_bce + self.dice_weight * loss_dice
