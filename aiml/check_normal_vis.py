import cv2, os
import predict as P

P.load_model("best_model.pth")
os.makedirs("normal_check", exist_ok=True)
for i, f in enumerate(sorted(os.listdir("normal_frames"))):
    img = cv2.imread(os.path.join("normal_frames", f))
    if img is None:
        continue
    out, conf = P.predict(img)
    h, w = out.shape[:2]
    out = cv2.resize(out, (480, int(480 * h / w)))
    cv2.putText(out, f"conf {conf:.2f}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imwrite(f"normal_check/{i+1:02d}.jpg", out)
print("done")