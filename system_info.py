"""系统信息收集模块"""

import logging
import os
import platform
import time
from dataclasses import dataclass
from typing import Dict, Optional

import cpuinfo
import psutil

logger = logging.getLogger(__name__)


@dataclass
class CPUInfo:
    """CPU信息"""

    usage: float  # CPU使用率百分比
    freq: float  # CPU频率 (GHz)
    cores: int  # CPU核心数
    brand: str  # CPU品牌型号
    temperature: Optional[float] = None  # CPU温度（如果可用）


@dataclass
class MemoryInfo:
    """内存信息"""

    total: float  # 总内存 (GB)
    used: float  # 已使用内存 (GB)
    available: float  # 可用内存 (GB)
    usage: float  # 使用率百分比


@dataclass
class SwapInfo:
    """交换分区信息"""

    total: float  # 总交换分区 (GB)
    used: float  # 已使用交换分区 (GB)
    usage: float  # 使用率百分比


@dataclass
class DiskInfo:
    """磁盘信息"""

    total: float  # 总磁盘空间 (GB)
    used: float  # 已使用磁盘空间 (GB)
    free: float  # 可用磁盘空间 (GB)
    usage: float  # 使用率百分比


@dataclass
class NetworkInfo:
    """网络信息"""

    bytes_sent: int  # 发送字节数
    bytes_recv: int  # 接收字节数
    packets_sent: int  # 发送包数
    packets_recv: int  # 接收包数
    upload_speed: float  # 上传速度 (MB/s)
    download_speed: float  # 下载速度 (MB/s)


@dataclass
class GPUInfo:
    """GPU信息"""

    name: str  # GPU名称
    usage: float  # GPU使用率百分比
    memory_used: float  # 已使用显存 (GB)
    memory_total: float  # 总显存 (GB)
    temperature: Optional[float] = None  # GPU温度（如果可用）


@dataclass
class SystemInfo:
    """系统信息"""

    hostname: str
    system: str
    release: str
    architecture: str
    boot_time: float
    uptime: str
    process_count: int


def bytes_to_gb(bytes_value: int) -> float:
    """将字节转换为GB"""
    return round(bytes_value / (1024**3), 2)


def is_docker_environment() -> bool:
    """检测是否在Docker环境中运行"""
    try:
        # 检查/.dockerenv文件
        if os.path.exists("/.dockerenv"):
            return True

        # 检查/proc/1/cgroup文件
        if os.path.exists("/proc/1/cgroup"):
            with open("/proc/1/cgroup", "r") as f:
                content = f.read()
                if "docker" in content or "containerd" in content:
                    return True

        # 检查/proc/self/mountinfo文件
        if os.path.exists("/proc/self/mountinfo"):
            with open("/proc/self/mountinfo", "r") as f:
                content = f.read()
                if "docker" in content:
                    return True

        return False
    except (OSError, IOError, PermissionError):
        return False


def get_cpu_info() -> CPUInfo:
    """获取CPU信息"""
    # CPU使用率
    cpu_percent = psutil.cpu_percent(interval=1)

    # CPU频率
    cpu_freq = psutil.cpu_freq()
    freq_ghz = round(cpu_freq.current / 1000, 2) if cpu_freq else 0.0

    # CPU核心数
    cores = psutil.cpu_count(logical=True)

    # CPU品牌信息
    cpu_brand = cpuinfo.get_cpu_info().get("brand_raw", "Unknown CPU")

    # 尝试获取CPU温度（可能不可用）
    temperature = None
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            # 尝试获取CPU温度
            for name, entries in temps.items():
                if "cpu" in name.lower() or "core" in name.lower():
                    if entries:
                        temperature = entries[0].current
                        break
    except (AttributeError, OSError):
        pass

    return CPUInfo(
        usage=cpu_percent,
        freq=freq_ghz,
        cores=cores,
        brand=cpu_brand,
        temperature=temperature,
    )


def get_memory_info() -> MemoryInfo:
    """获取内存信息"""
    memory = psutil.virtual_memory()

    return MemoryInfo(
        total=bytes_to_gb(memory.total),
        used=bytes_to_gb(memory.used),
        available=bytes_to_gb(memory.available),
        usage=memory.percent,
    )


def get_swap_info() -> SwapInfo:
    """获取交换分区信息"""
    is_docker = is_docker_environment()

    try:
        swap = psutil.swap_memory()

        # 检查是否在docker环境或swap不可用的情况下
        if swap.total == 0:
            if is_docker:
                logger.info("检测到Docker环境，swap不可用，返回0值数据")
            else:
                logger.info("系统未配置swap分区，返回0值数据")
            return SwapInfo(total=0.0, used=0.0, usage=0.0)

        return SwapInfo(
            total=bytes_to_gb(swap.total),
            used=bytes_to_gb(swap.used),
            usage=swap.percent,
        )
    except (OSError, AttributeError, PermissionError) as e:
        # 在docker环境或权限不足时，psutil可能抛出异常
        if is_docker:
            logger.warning(f"Docker环境下获取swap信息失败: {e}，返回0值数据")
        else:
            logger.warning(f"获取swap信息失败: {e}，返回0值数据")
        return SwapInfo(total=0.0, used=0.0, usage=0.0)


def get_disk_info() -> DiskInfo:
    """获取磁盘信息"""
    disk = psutil.disk_usage("/")

    return DiskInfo(
        total=bytes_to_gb(disk.total),
        used=bytes_to_gb(disk.used),
        free=bytes_to_gb(disk.free),
        usage=round((disk.used / disk.total) * 100, 1),
    )


def get_network_info() -> NetworkInfo:
    """获取网络信息"""
    net_io = psutil.net_io_counters()

    # 简单的速度计算（这里返回0，实际应用中可以通过两次采样计算）
    # 在实际使用中，可以存储上次的数据并计算差值来得到速度
    upload_speed = 0.0  # MB/s
    download_speed = 0.0  # MB/s

    return NetworkInfo(
        bytes_sent=net_io.bytes_sent,
        bytes_recv=net_io.bytes_recv,
        packets_sent=net_io.packets_sent,
        packets_recv=net_io.packets_recv,
        upload_speed=upload_speed,
        download_speed=download_speed,
    )


def get_gpu_info() -> GPUInfo:
    """获取GPU信息"""
    try:
        # 尝试使用nvidia-ml-py获取NVIDIA GPU信息
        try:
            import pynvml

            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)

            # GPU名称
            name = pynvml.nvmlDeviceGetName(handle).decode("utf-8")

            # GPU使用率
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            usage = utilization.gpu

            # 显存信息
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory_total = bytes_to_gb(memory_info.total)
            memory_used = bytes_to_gb(memory_info.used)

            # GPU温度
            try:
                temperature = pynvml.nvmlDeviceGetTemperature(
                    handle, pynvml.NVML_TEMPERATURE_GPU
                )
            except:
                temperature = None

            return GPUInfo(
                name=name,
                usage=float(usage),
                memory_used=memory_used,
                memory_total=memory_total,
                temperature=temperature,
            )

        except ImportError:
            # 如果没有pynvml，尝试其他方法
            pass

        # 尝试使用GPUtil
        try:
            import GPUtil

            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # 获取第一个GPU
                return GPUInfo(
                    name=gpu.name,
                    usage=gpu.load * 100,
                    memory_used=gpu.memoryUsed / 1024,  # 转换为GB
                    memory_total=gpu.memoryTotal / 1024,  # 转换为GB
                    temperature=gpu.temperature,
                )
        except ImportError:
            pass

        # 如果都没有，返回默认值
        return GPUInfo(
            name="Unknown GPU",
            usage=0.0,
            memory_used=0.0,
            memory_total=0.0,
            temperature=None,
        )

    except Exception:
        # 出现任何错误都返回默认值
        return GPUInfo(
            name="No GPU",
            usage=0.0,
            memory_used=0.0,
            memory_total=0.0,
            temperature=None,
        )


def format_uptime(uptime_seconds: float) -> str:
    """格式化运行时间"""
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)

    if days > 0:
        return f"{days}天 {hours}小时 {minutes}分钟"
    elif hours > 0:
        return f"{hours}小时 {minutes}分钟"
    else:
        return f"{minutes}分钟"


def get_system_info() -> SystemInfo:
    """获取系统信息"""
    system = platform.uname()
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time

    return SystemInfo(
        hostname=system.node,
        system=system.system,
        release=system.release,
        architecture=system.machine,
        boot_time=boot_time,
        uptime=format_uptime(uptime_seconds),
        process_count=len(psutil.pids()),
    )


def get_all_status_info() -> Dict:
    """获取所有状态信息"""
    return {
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "swap": get_swap_info(),
        "disk": get_disk_info(),
        "network": get_network_info(),
        "gpu": get_gpu_info(),
        "system": get_system_info(),
    }
