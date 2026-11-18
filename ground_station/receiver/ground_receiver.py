"""Ground-station socket listener and frame stream ingestion manager."""

import time
import socket
from typing import Optional
import numpy as np
import cv2

from vision.capture.frame_buffer import FrameBuffer


class GroundReceiver:
    """Listens for inbound UDP/TCP JPEG datagrams transmitted from the drone's ESP32."""

    def __init__(self, port: int = 8080, host: str = "0.0.0.0", buffer_size: int = 15):
        self.port = port
        self.host = host
        self.buffer = FrameBuffer(maxsize=buffer_size)
        self.sock: Optional[socket.socket] = None
        self._running = False

    def bind(self):
        """Bind network socket."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(1.0)
        print(f"[RECV] Ground receiver listening on UDP {self.host}:{self.port}")

    def ingest_packet(self) -> bool:
        """Receive single datagram, decode JPEG payload, and enqueue in frame buffer."""
        if not self.sock:
            return False
        try:
            data, addr = self.sock.recvfrom(65536)
            if data:
                np_arr = np.frombuffer(data, dtype=np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if frame is not None:
                    self.buffer.put(frame, time.time())
                    return True
        except socket.timeout:
            return False
        except Exception as e:
            print(f"[RECV-ERR] Packet read failed: {e}")
            return False
        return False

    def close(self):
        """Release socket."""
        if self.sock:
            self.sock.close()
            self.sock = None
