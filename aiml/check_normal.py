import cv2, os, numpy as np, torch
import predict as P

P.load_model("best_model.pth")
THR = 0.30   # predict.py wala threshold

def prob_map(img):
    rgb = cv2.cvtColor(cv2.resize(img, (P.SIZE, P.SIZE)), cv2.COLOR_BGR2RGB)
    x = (rgb.astype(np.float32) / 255.0 - P.MEAN) / P.STD
    x = torch.from_numpy(x.transpose(2, 0, 1))[None].to(P.device)
    with torch.no_grad():
        return torch.sigmoid(P._model(x))[0, 0].cpu().numpy()

def scores(folder):
    rows = []
    for f in sorted(os.listdir(folder)):
        img = cv2.imread(os.path.join(folder, f))
        if img is None:
            continue
        conf = P.predict(img)[1]
        area = float((prob_map(img) > THR).mean())   # mask ne kitni image gheri
        rows.append((f, conf, area))
    return rows

normal = scores("normal_frames")
camo = scores("test_images")

for name, rows in [("NORMAL", normal), ("CAMOUFLAGE", camo)]:
    print(f"\n{name} ({len(rows)} images)")
    for f, c, a in rows:
        print(f"  {f:28s} conf {c:.2f} | mask area {a*100:5.1f}%")
    cs = [r[1] for r in rows]
    ar = [r[2] for r in rows]
    print(f"  conf  mean {np.mean(cs):.3f} (min {min(cs):.2f}, max {max(cs):.2f})")
    print(f"  area  mean {np.mean(ar)*100:.1f}% (min {min(ar)*100:.1f}%, max {max(ar)*100:.1f}%)")

nc = [r[1] for r in normal]; cc = [r[1] for r in camo]
na = [r[2] for r in normal]; ca = [r[2] for r in camo]
print("\nconf se alag hote hain?", max(nc) < min(cc))
print("area se alag hote hain?", max(na) < min(ca) or min(na) > max(ca))