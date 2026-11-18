"""Centroid-based multi-frame target tracker for visual object persistence."""

import numpy as np
from collections import OrderedDict
from typing import List, Tuple, Dict


class CentroidTracker:
    """Tracks detected objects across sequential video frames using Euclidean distance matching."""

    def __init__(self, max_disappeared: int = 15, max_distance: float = 60.0):
        self.next_object_id = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, centroid: Tuple[int, int]):
        """Register a newly detected target centroid."""
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.next_object_id += 1

    def deregister(self, object_id: int):
        """Purge tracking ID when target lost for too many frames."""
        del self.objects[object_id]
        del self.disappeared[object_id]

    def update(self, rects: List[List[int]]) -> Dict[int, Tuple[int, int]]:
        """Update tracked centroids given a list of bounding boxes [x, y, w, h]."""
        if len(rects) == 0:
            for obj_id in list(self.disappeared.keys()):
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    self.deregister(obj_id)
            return self.objects

        input_centroids = np.zeros((len(rects), 2), dtype="int")
        for i, (x, y, w, h) in enumerate(rects):
            input_centroids[i] = (int(x + w / 2.0), int(y + h / 2.0))

        if len(self.objects) == 0:
            for i in range(len(input_centroids)):
                self.register(tuple(input_centroids[i]))
        else:
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            # Distance matrix between current tracks and new centroids
            D = np.linalg.norm(np.array(object_centroids)[:, np.newaxis] - input_centroids, axis=2)

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                if D[row, col] > self.max_distance:
                    continue

                obj_id = object_ids[row]
                self.objects[obj_id] = tuple(input_centroids[col])
                self.disappeared[obj_id] = 0

                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(0, D.shape[0])).difference(used_rows)
            unused_cols = set(range(0, D.shape[1])).difference(used_cols)

            for row in unused_rows:
                obj_id = object_ids[row]
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    self.deregister(obj_id)

            for col in unused_cols:
                self.register(tuple(input_centroids[col]))

        return self.objects
