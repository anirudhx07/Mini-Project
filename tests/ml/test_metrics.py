import numpy as np
import pytest

from ml.evaluation.metrics import calculate_iou, calculate_precision_recall


def test_iou_calculation():
    mask_a = np.zeros((50, 50), dtype=np.uint8)
    mask_b = np.zeros((50, 50), dtype=np.uint8)

    mask_a[10:30, 10:30] = 1 # Area 400
    mask_b[10:30, 10:30] = 1 # Exact match

    iou = calculate_iou(mask_a, mask_b)
    assert iou == pytest.approx(1.0, 0.01)

    # Disjoint masks
    mask_c = np.zeros((50, 50), dtype=np.uint8)
    mask_c[35:45, 35:45] = 1
    assert calculate_iou(mask_a, mask_c) == pytest.approx(0.0, 0.01)


def test_precision_recall():
    target = np.zeros((20, 20), dtype=np.uint8)
    pred = np.zeros((20, 20), dtype=np.uint8)

    target[5:15, 5:15] = 1 # 100 pixels true
    pred[5:15, 5:15] = 1 # 100 pixels pred

    prec, rec, f1 = calculate_precision_recall(pred, target)
    assert prec == pytest.approx(1.0, 0.01)
    assert rec == pytest.approx(1.0, 0.01)
    assert f1 == pytest.approx(1.0, 0.01)


def test_lightweight_unet_forward():
    torch = pytest.importorskip("torch")
    from ml.models.lightweight_unet import LightweightUNet

    model = LightweightUNet(in_channels=3, num_classes=1, base_filters=8)
    dummy_input = torch.randn(2, 3, 64, 64)
    output = model(dummy_input)
    assert output.shape == (2, 1, 64, 64)
    # Output should be sigmoid probability [0, 1]
    assert (output >= 0.0).all() and (output <= 1.0).all()

