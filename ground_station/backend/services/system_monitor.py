"""System hardware and compute resource monitor for COCKPIT."""

import platform
import socket
import subprocess
from typing import Any, Dict

import psutil


def get_local_ip() -> str:
    """Detect the laptop's active LAN IP address."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.3)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def detect_gpu_info() -> Dict[str, Any]:
    """Detect CUDA availability via PyTorch and query NVIDIA GPU details if present."""
    cuda_available = False
    torch_installed = False
    device_name = "None"
    active_compute = "CPU"

    try:
        import torch

        torch_installed = True
        cuda_available = bool(torch.cuda.is_available())
        if cuda_available:
            device_name = torch.cuda.get_device_name(0)
            active_compute = f"CUDA ({device_name})"
    except ImportError:
        pass

    # If PyTorch is missing or CPU-only, still report physical NVIDIA hardware honestly without claiming CUDA active
    physical_gpu = device_name
    if not cuda_available:
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                stderr=subprocess.DEVNULL,
                timeout=1.5,
                text=True,
            ).strip()
            if out:
                physical_gpu = out.splitlines()[0].strip()
        except Exception:
            pass

    return {
        "torch_installed": torch_installed,
        "cuda_available": cuda_available,
        "gpu_device_name": device_name if cuda_available else physical_gpu,
        "active_compute": active_compute,
    }


class SystemMonitor:
    """Collects CPU, memory, network, and GPU diagnostics."""

    def __init__(self):
        self._gpu_cache = detect_gpu_info()

    def refresh_gpu(self) -> Dict[str, Any]:
        self._gpu_cache = detect_gpu_info()
        return self._gpu_cache

    def get_info(self) -> Dict[str, Any]:
        vm = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=None)
        return {
            "os": f"{platform.system()} {platform.release()}",
            "python_version": platform.python_version(),
            "local_ip": get_local_ip(),
            "cpu_percent": round(cpu_pct, 1),
            "memory_percent": round(vm.percent, 1),
            "memory_used_gb": round(vm.used / (1024 ** 3), 2),
            "memory_total_gb": round(vm.total / (1024 ** 3), 2),
            "gpu": self._gpu_cache,
        }
