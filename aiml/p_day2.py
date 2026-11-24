import cv2, csv, os, time
import numpy as np
from datetime import datetime

SOURCE = "test_images"   # folder, ya 0 (webcam), ya "test.mp4"
USE_CLAHE = False         # CLAHE on/off test ke liye True/False badlo
EVERY_N = 3              # video/webcam mein har 3rd frame pe model chalao

try:
    from predict import predict, load_model
    load_model("best_model.pth")
    print("Model loaded")
except Exception as e:
    print("Model nahi mila, dummy mode:", e)
    def predict(frame):
        out = frame.copy()
        cv2.putText(out, "DUMMY", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return out, 0.0

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
def enhance(frame):
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    return cv2.cvtColor(cv2.merge((clahe.apply(l), a, b)), cv2.COLOR_LAB2BGR)

is_folder = isinstance(SOURCE, str) and os.path.isdir(SOURCE)
if is_folder:
    EVERY_N = 1
    def frames():
        for f in sorted(os.listdir(SOURCE)):
            img = cv2.imread(os.path.join(SOURCE, f))
            if img is not None:
                yield img
    gen = frames()
else:
    cap = cv2.VideoCapture(SOURCE)
    if not cap.isOpened():
        raise SystemExit(f"ERROR: source open nahi hua: {SOURCE}")
    def frames():
        while True:
            ok, fr = cap.read()
            if not ok:
                return
            yield fr
    gen = frames()

os.makedirs("results", exist_ok=True)
new_log = not os.path.exists("results_log.csv")
logf = open("results_log.csv", "a", newline="")
w = csv.writer(logf)
if new_log:
    w.writerow(["timestamp", "source", "clahe", "latency_ms", "confidence", "file"])

n, last = 0, None
for frame in gen:
    n += 1
    frame = cv2.resize(frame, (320, 240))
    if last is None or n % EVERY_N == 0:
        inp = enhance(frame) if USE_CLAHE else frame
        t0 = time.perf_counter()
        out, conf = predict(inp)
        ms = (time.perf_counter() - t0) * 1000
        last = (out, conf, ms)
    out, conf, ms = last

    show = out.copy()
    cv2.putText(show, f"conf {conf:.2f} | {ms:.0f} ms", (5, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.imshow("Original | Result", np.hstack([frame, show]))

    key = cv2.waitKey(1000 if is_folder else 1)
    if key == ord('s'):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fn = f"results/{ts}.jpg"
        cv2.imwrite(fn, show)
        w.writerow([ts, SOURCE, USE_CLAHE, round(ms, 1), round(conf, 3), fn])
        logf.flush()
        print("Saved:", fn)
    elif key == 27:
        break

logf.close()
cv2.destroyAllWindows()