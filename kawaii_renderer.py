"""Kawaii Status 渲染器"""

import io
from pathlib import Path
from typing import Dict

import cpuinfo
from PIL import Image, ImageDraw, ImageFont

from .system_info import (
    CPUInfo,
    DiskInfo,
    GPUInfo,
    MemoryInfo,
    NetworkInfo,
    SwapInfo,
    SystemInfo,
)


class KawaiiStatusRenderer:
    """Kawaii Status 渲染器"""

    def __init__(self):
        self.setup_paths()
        self.setup_colors()
        self.setup_fonts()

    def setup_paths(self):
        """设置资源路径"""
        self.resources_dir = Path(__file__).parent / "resources"
        self.bg_img_path = self.resources_dir / "images" / "background.png"

        # 字体路径
        self.baotu_font_path = self.resources_dir / "fonts" / "baotu.ttf"
        self.spicy_font_path = self.resources_dir / "fonts" / "SpicyRice-Regular.ttf"
        self.dingtalk_font_path = self.resources_dir / "fonts" / "DingTalk-JinBuTi.ttf"
        self.adlam_font_path = self.resources_dir / "fonts" / "ADLaMDisplay-Regular.ttf"

    def setup_colors(self):
        """设置颜色"""
        # 原项目的颜色配置 (RGBA)
        self.cpu_color = (84, 173, 255, 255)
        self.ram_color = (255, 179, 204, 255)
        self.swap_color = (251, 170, 147, 255)
        self.disk_color = (184, 170, 159, 255)
        # 新增的颜色配置
        self.gpu_color = (144, 238, 144, 255)  # 浅绿色
        self.network_upload_color = (255, 165, 0, 255)  # 橙色
        self.network_download_color = (135, 206, 235, 255)  # 天蓝色
        self.transparent_color = (0, 0, 0, 0)
        self.details_color = (184, 170, 159, 255)
        self.nickname_color = (84, 173, 255, 255)

    def setup_fonts(self):
        """设置字体"""
        try:
            self.adlam_fnt = ImageFont.truetype(str(self.adlam_font_path), 36)
            self.spicy_fnt = ImageFont.truetype(str(self.spicy_font_path), 38)
            self.baotu_fnt = ImageFont.truetype(str(self.baotu_font_path), 64)
            self.dingtalk_fnt = ImageFont.truetype(str(self.dingtalk_font_path), 38)
            self.baotu_small_fnt = ImageFont.truetype(str(self.baotu_font_path), 28)
        except (OSError, IOError):
            self.adlam_fnt = ImageFont.load_default()
            self.spicy_fnt = ImageFont.load_default()
            self.baotu_fnt = ImageFont.load_default()
            self.dingtalk_fnt = ImageFont.load_default()
            self.baotu_small_fnt = ImageFont.load_default()

    def render(self, status_info: Dict) -> bytes:
        """渲染状态图片 样式"""
        # 加载背景图片
        try:
            base_img = Image.open(self.bg_img_path).convert("RGBA")
        except (OSError, IOError):
            # 如果背景图片不存在，创建一个默认背景 (原项目尺寸)
            base_img = Image.new("RGBA", (1080, 1920), (255, 255, 255, 255))

        # 创建透明图层用于绘制内容
        img = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 获取系统信息
        cpu_info: CPUInfo = status_info["cpu"]
        memory_info: MemoryInfo = status_info["memory"]
        disk_info: DiskInfo = status_info["disk"]
        system_info: SystemInfo = status_info["system"]
        network_info: NetworkInfo = status_info.get("network")
        swap_info: SwapInfo = status_info.get("swap")
        gpu_info: GPUInfo = status_info.get("gpu")

        # 绘制昵称
        nickname = "AstrBot"
        draw.text((103, 581), nickname, font=self.baotu_fnt, fill=self.nickname_color)

        # 左侧项目
        draw.text((251, 737), "CPU", font=self.adlam_fnt, fill=self.cpu_color)
        cpu_text = f"{cpu_info.usage:.1f}% - {cpu_info.freq}GHz [{cpu_info.cores} core]"
        draw.text((251, 772), cpu_text, font=self.spicy_fnt, fill=self.cpu_color)

        draw.text((251, 892), "RAM", font=self.adlam_fnt, fill=self.ram_color)
        ram_text = f"{memory_info.used:.1f} / {memory_info.total:.1f} GB"
        draw.text((251, 927), ram_text, font=self.spicy_fnt, fill=self.ram_color)

        draw.text((251, 1046), "SWAP", font=self.adlam_fnt, fill=self.swap_color)
        if swap_info and swap_info.total > 0:
            swap_text = f"{swap_info.used:.1f} / {swap_info.total:.1f} GB"
            draw.text((251, 1081), swap_text, font=self.spicy_fnt, fill=self.swap_color)

        draw.text(
            (251, 1200),
            "download",
            font=self.adlam_fnt,
            fill=self.network_download_color,
        )
        if network_info:
            download_text = f"{self.format_bytes(network_info.bytes_recv)}"
            draw.text(
                (251, 1235),
                download_text,
                font=self.spicy_fnt,
                fill=self.network_download_color,
            )

        # 右侧项目
        draw.text((720, 892), "GPU", font=self.adlam_fnt, fill=self.gpu_color)
        if gpu_info:
            if gpu_info.memory_total > 0:
                gpu_text = (
                    f"{gpu_info.memory_used:.1f} / {gpu_info.memory_total:.1f} GB"
                )
            else:
                gpu_text = f"{gpu_info.usage:.1f}%"
            draw.text((720, 927), gpu_text, font=self.spicy_fnt, fill=self.gpu_color)

        draw.text((720, 1046), "DISK", font=self.adlam_fnt, fill=self.disk_color)
        disk_text = f"{disk_info.used:.1f} / {disk_info.total:.1f} GB"
        draw.text((720, 1081), disk_text, font=self.spicy_fnt, fill=self.disk_color)

        draw.text(
            (720, 1195), "upload", font=self.adlam_fnt, fill=self.network_upload_color
        )
        if network_info:
            upload_text = f"{self.format_bytes(network_info.bytes_sent)}"
            draw.text(
                (720, 1235),
                upload_text,
                font=self.spicy_fnt,
                fill=self.network_upload_color,
            )

        # 绘制圆形进度条
        self._draw_progress_arcs(
            draw, cpu_info, memory_info, swap_info, disk_info, gpu_info, network_info
        )

        # 绘制系统详细信息
        self._draw_system_details(draw, system_info, cpu_info)

        # 合成最终图片
        final_img = Image.alpha_composite(base_img, img)

        # 保存为字节流
        buf = io.BytesIO()
        final_img.save(buf, format="PNG")
        buf.seek(0)
        return buf.getvalue()

    def _draw_progress_arcs(
        self,
        draw: ImageDraw.Draw,
        cpu_info: CPUInfo,
        memory_info: MemoryInfo,
        swap_info: SwapInfo,
        disk_info: DiskInfo,
        gpu_info: GPUInfo,
        network_info: NetworkInfo,
    ):
        """绘制圆形进度条 坐标"""

        # CPU进度条
        cpu_usage_angle = cpu_info.usage * 3.6 - 90
        draw.arc(
            (103, 724, 217, 838),
            start=-90,
            end=cpu_usage_angle,
            width=15,
            fill=self.cpu_color,
        )

        # 内存进度条
        ram_usage_angle = (memory_info.used / memory_info.total) * 360 - 90
        draw.arc(
            (103, 878, 217, 992),
            start=-90,
            end=ram_usage_angle,
            width=15,
            fill=self.ram_color,
        )

        # 交换分区进度条
        if swap_info and swap_info.total > 0:
            swap_usage_angle = (swap_info.used / swap_info.total) * 360 - 90
            draw.arc(
                (103, 1032, 217, 1146),
                start=-90,
                end=swap_usage_angle,
                width=15,
                fill=self.swap_color,
            )

        # 网络下载进度条
        if network_info:
            # 使用接收字节数的对数比例来显示进度
            import math

            if network_info.bytes_recv > 0:
                max_bytes = 1024**4  # 1TB
                download_percentage = min(
                    100,
                    (math.log10(network_info.bytes_recv + 1) / math.log10(max_bytes))
                    * 100,
                )
            else:
                download_percentage = 0
            download_angle = download_percentage * 3.6 - 90
            draw.arc(
                (103, 1186, 217, 1300),
                start=-90,
                end=download_angle,
                width=15,
                fill=self.network_download_color,
            )

        # GPU进度条
        if gpu_info:
            if gpu_info.memory_total > 0:
                gpu_usage_angle = (
                    gpu_info.memory_used / gpu_info.memory_total
                ) * 360 - 90
            else:
                gpu_usage_angle = gpu_info.usage * 3.6 - 90
            draw.arc(
                (560, 878, 674, 992),
                start=-90,
                end=gpu_usage_angle,
                width=15,
                fill=self.gpu_color,
            )

        # 磁盘进度条
        disk_usage_angle = (disk_info.used / disk_info.total) * 360 - 90
        draw.arc(
            (560, 1032, 674, 1146),
            start=-90,
            end=disk_usage_angle,
            width=15,
            fill=self.disk_color,
        )

        # 网络上传进度条
        if network_info:
            # 使用发送字节数的对数比例来显示进度
            import math

            if network_info.bytes_sent > 0:
                max_bytes = 1024**4  # 1TB
                upload_percentage = min(
                    100,
                    (math.log10(network_info.bytes_sent + 1) / math.log10(max_bytes))
                    * 100,
                )
            else:
                upload_percentage = 0
            upload_angle = upload_percentage * 3.6 - 90
            draw.arc(
                (560, 1186, 674, 1300),
                start=-90,
                end=upload_angle,
                width=15,
                fill=self.network_upload_color,
            )

        # 绘制中心透明圆形 (挖空效果)
        draw.ellipse((108, 729, 212, 833), fill=self.transparent_color)  # CPU
        draw.ellipse((108, 883, 212, 987), fill=self.transparent_color)  # RAM
        draw.ellipse((108, 1037, 212, 1141), fill=self.transparent_color)  # SWAP
        draw.ellipse((108, 1192, 212, 1295), fill=self.transparent_color)  # 网络下载

        # 右侧圆形的挖空效果 (右移10个点与环形图对应)
        draw.ellipse((565, 883, 669, 987), fill=self.transparent_color)  # GPU
        draw.ellipse((565, 1037, 669, 1141), fill=self.transparent_color)  # DISK
        draw.ellipse((565, 1192, 669, 1295), fill=self.transparent_color)  # 网络上传

        # CPU百分比 (环形图中心: 103+114/2=160, 724+109/2=778.5)
        cpu_percent_text = f"{cpu_info.usage:.0f}%"
        draw.text(
            (135, 760),
            cpu_percent_text,
            font=self.spicy_fnt,
            fill=self.cpu_color,
        )

        # RAM百分比 (环形图中心: 103+114/2=160, 878+109/2=932.5)
        ram_percent = (memory_info.used / memory_info.total) * 100
        ram_percent_text = f"{ram_percent:.0f}%"
        draw.text(
            (135, 915),
            ram_percent_text,
            font=self.spicy_fnt,
            fill=self.ram_color,
        )

        # SWAP百分比 (环形图中心: 103+114/2=160, 1032+109/2=1086.5)
        if swap_info and swap_info.total > 0:
            swap_percent = (swap_info.used / swap_info.total) * 100
            swap_percent_text = f"{swap_percent:.0f}%"
            draw.text(
                (135, 1069),
                swap_percent_text,
                font=self.spicy_fnt,
                fill=self.swap_color,
            )

        # 网络下载百分比 (使用下载与上传总量的比例)
        if network_info:
            total_network = network_info.bytes_sent + network_info.bytes_recv
            if total_network > 0:
                download_percentage = (network_info.bytes_recv / total_network) * 100
            else:
                download_percentage = 0
            download_percent_text = f"{download_percentage:.0f}%"
            draw.text(
                (135, 1223),
                download_percent_text,
                font=self.spicy_fnt,
                fill=self.network_download_color,
            )

        # GPU百分比 (环形图中心: 560+114/2=617, 878+109/2=932.5)
        if gpu_info:
            if gpu_info.memory_total > 0:
                gpu_percent = (gpu_info.memory_used / gpu_info.memory_total) * 100
            else:
                gpu_percent = gpu_info.usage
            gpu_percent_text = f"{gpu_percent:.0f}%"
            draw.text(
                (592, 915),
                gpu_percent_text,
                font=self.spicy_fnt,
                fill=self.gpu_color,
            )

        # DISK百分比 (环形图中心: 560+114/2=617, 1032+109/2=1086.5)
        disk_percent = (disk_info.used / disk_info.total) * 100
        disk_percent_text = f"{disk_percent:.0f}%"
        draw.text(
            (592, 1069),
            disk_percent_text,
            font=self.spicy_fnt,
            fill=self.disk_color,
        )

        # 网络上传百分比 (使用上传与下载总量的比例)
        if network_info:
            total_network = network_info.bytes_sent + network_info.bytes_recv
            if total_network > 0:
                upload_percentage = (network_info.bytes_sent / total_network) * 100
            else:
                upload_percentage = 0
            upload_percent_text = f"{upload_percentage:.0f}%"
            draw.text(
                (592, 1223),
                upload_percent_text,
                font=self.spicy_fnt,
                fill=self.network_upload_color,
            )

    def _draw_system_details(
        self, draw: ImageDraw.Draw, system_info: SystemInfo, cpu_info: CPUInfo
    ):
        """绘制系统详细信息 坐标"""
        # 获取CPU信息
        try:
            cpu_brand = cpuinfo.get_cpu_info().get("brand_raw", "Unknown CPU")
            # 截断过长的CPU名称
            cpu_brand = self.truncate_string(cpu_brand)
        except Exception:
            cpu_brand = "Unknown CPU"

        # 系统信息
        draw.text((352, 1378), cpu_brand, font=self.adlam_fnt, fill=self.details_color)

        # 系统版本
        system_text = f"{system_info.system} {system_info.release}"
        system_text = self.truncate_string(system_text)
        draw.text(
            (352, 1431), system_text, font=self.adlam_fnt, fill=self.details_color
        )

        # AstrBot版本信息
        version_text = "AstrBot v3.5.22"
        draw.text(
            (352, 1484), version_text, font=self.adlam_fnt, fill=self.details_color
        )

        # 插件数量
        plugin_count = self._get_plugin_count()
        plugin_text = f"{plugin_count} plugins"
        draw.text(
            (352, 1537), plugin_text, font=self.adlam_fnt, fill=self.details_color
        )

        # 运行时间标签
        uptime_label = "运行时间"
        draw.text(
            (400, 1680),
            uptime_label,
            font=self.baotu_small_fnt,
            fill=self.details_color,
        )

        # 运行时间
        uptime_text = system_info.uptime
        draw.text(
            (957, 1703),
            uptime_text,
            font=self.dingtalk_fnt,
            fill=self.details_color,
            anchor="ra",
        )

    def _get_plugin_count(self) -> int:
        """获取插件数量"""
        try:
            plugins_dir = Path(__file__).parent.parent.parent / "plugins"
            if not plugins_dir.exists():
                return 0

            # 统计插件目录数量（排除隐藏目录和文件）
            plugin_count = 0
            for item in plugins_dir.iterdir():
                if (
                    item.is_dir()
                    and not item.name.startswith(".")
                    and not item.name.startswith("__")
                ):
                    # 检查是否包含main.py或__init__.py
                    if (item / "main.py").exists() or (item / "__init__.py").exists():
                        plugin_count += 1
            return plugin_count
        except Exception:
            return 0

    def truncate_string(self, text: str, max_length: int = 30) -> str:
        """截断过长的字符串"""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def format_bytes(self, bytes_value: int) -> str:
        """格式化字节数"""
        value = float(bytes_value)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if value < 1024.0:
                return f"{value:.1f}{unit}"
            value /= 1024.0
        return f"{value:.1f}PB"
