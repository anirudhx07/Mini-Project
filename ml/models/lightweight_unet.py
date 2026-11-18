"""Lightweight U-Net architecture for efficient camouflage segmentation."""

import torch
import torch.nn as nn
import torch.nn.functional as F


class ConvBlock(nn.Module):
    """Two-layer convolution block with Batch Normalization and ReLU."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(x)


class LightweightUNet(nn.Module):
    """Compact 4-stage U-Net designed for real-time aerial terrain segmentation."""

    def __init__(self, in_channels: int = 3, num_classes: int = 1, base_filters: int = 16):
        super().__init__()
        # Encoder (Downsampling)
        self.enc1 = ConvBlock(in_channels, base_filters)
        self.pool1 = nn.MaxPool2d(2, 2)

        self.enc2 = ConvBlock(base_filters, base_filters * 2)
        self.pool2 = nn.MaxPool2d(2, 2)

        self.enc3 = ConvBlock(base_filters * 2, base_filters * 4)
        self.pool3 = nn.MaxPool2d(2, 2)

        # Bottleneck
        self.bottleneck = ConvBlock(base_filters * 4, base_filters * 8)

        # Decoder (Upsampling with skip connections)
        self.up3 = nn.ConvTranspose2d(base_filters * 8, base_filters * 4, kernel_size=2, stride=2)
        self.dec3 = ConvBlock(base_filters * 8, base_filters * 4)

        self.up2 = nn.ConvTranspose2d(base_filters * 4, base_filters * 2, kernel_size=2, stride=2)
        self.dec2 = ConvBlock(base_filters * 4, base_filters * 2)

        self.up1 = nn.ConvTranspose2d(base_filters * 2, base_filters, kernel_size=2, stride=2)
        self.dec1 = ConvBlock(base_filters * 2, base_filters)

        # 1x1 Final Convolution for probability mask
        self.final_conv = nn.Conv2d(base_filters, num_classes, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        e3 = self.enc3(self.pool2(e2))

        b = self.bottleneck(self.pool3(e3))

        d3 = self.up3(b)
        d3 = torch.cat([d3, e3], dim=1)
        d3 = self.dec3(d3)

        d2 = self.up2(d3)
        d2 = torch.cat([d2, e2], dim=1)
        d2 = self.dec2(d2)

        d1 = self.up1(d2)
        d1 = torch.cat([d1, e1], dim=1)
        d1 = self.dec1(d1)

        out = self.final_conv(d1)
        return torch.sigmoid(out)
