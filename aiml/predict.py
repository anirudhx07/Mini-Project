import cv2, torch, numpy as np
import segmentation_models_pytorch as smp

SIZE = 256
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)
device = "cuda" if torch.cuda.is_available() else "cpu"
_model = None

def load_model(path="best_model.pth"):
    global _model
    m = smp.Unet(encoder_name="resnet18", encoder_weights=None,
                 in_channels=3, classes=1)
    m.load_state_dict(torch.load(path, map_location=device))
    _model = m.to(device).eval()

def predict(frame):
    """frame: OpenCV BGR image. Returns (annotated_frame, confidence)."""
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(cv2.resize(frame, (SIZE, SIZE)), cv2.COLOR_BGR2RGB)
    x = (rgb.astype(np.float32) / 255.0 - MEAN) / STD
    x = torch.from_numpy(x.transpose(2, 0, 1))[None].to(device)
    with torch.no_grad():
        prob = torch.sigmoid(_model(x))[0, 0].cpu().numpy()
    prob = cv2.resize(prob, (w, h))
    mask = prob > 0.30
    conf = float(prob[mask].mean()) if mask.any() else 0.0

    out = frame.copy()
    out[mask] = (0.5 * out[mask] + 0.5 * np.array([0, 0, 255])).astype(np.uint8)
    cnts, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(out, cnts, -1, (0, 255, 0), 2)
    return out, conf