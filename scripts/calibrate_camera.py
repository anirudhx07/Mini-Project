"""Camera calibration script using standard chessboard calibration targets."""

import os
import glob
import argparse
import cv2
import numpy as np


def calibrate_camera(image_dir: str, pattern_size: tuple[int, int] = (9, 6), square_size_mm: float = 25.0):
    print(f"[CALIB] Calibrating camera using images from '{image_dir}'...")
    # Prepare 3D object points
    objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2) * square_size_mm

    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane

    images = glob.glob(os.path.join(image_dir, "*.jpg")) + glob.glob(os.path.join(image_dir, "*.png"))
    if not images:
        print(f"[WARN] No calibration images found in '{image_dir}'. Capture 10-20 checkerboard photos first.")
        return

    gray = None
    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, pattern_size, None)

        if ret:
            objpoints.append(objp)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)
            print(f" -> Pattern detected in {os.path.basename(fname)}")

    if len(objpoints) > 0 and gray is not None:
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
        print("\n============= CALIBRATION RESULTS =============")
        print(f"Reprojection Error: {ret:.4f} pixels")
        print("Camera Intrinsic Matrix:\n", mtx)
        print("Distortion Coefficients:\n", dist.ravel())
        print("===============================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=str, default="ground_station/results/calibration")
    args = parser.parse_args()

    calibrate_camera(args.image_dir)
