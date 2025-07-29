"""AstrBot 状态插件"""

import hashlib
import importlib.util
import os
import subprocess
import sys
import time
from typing import Dict, Optional, Tuple

import astrbot.api.message_components as Comp
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register


def _check_and_install_dependencies():
    """检查并安装依赖包"""
    required_packages = {
        "psutil": "psutil>=5.9.0",
        "PIL": "Pillow>=9.0.0",
        "matplotlib": "matplotlib>=3.5.0",
        "cpuinfo": "py-cpuinfo>=9.0.0",
        # GPU相关包是可选的，不强制安装
        # "pynvml": "nvidia-ml-py3>=7.352.0",
        # "GPUtil": "GPUtil>=1.4.0",
    }

    missing_packages = []

    # 检查依赖是否存在
    for module_name, package_spec in required_packages.items():
        if importlib.util.find_spec(module_name) is None:
            missing_packages.append(package_spec)

    # 如果有缺失的依赖，尝试安装
    if missing_packages:
        logger.info(f"检测到缺失依赖: {', '.join(missing_packages)}")
        logger.info("正在自动安装依赖包...")

        try:
            # 获取requirements.txt路径
            requirements_file = os.path.join(
                os.path.dirname(__file__), "requirements.txt"
            )

            if os.path.exists(requirements_file):
                # 使用requirements.txt安装
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "-r", requirements_file]
                )
            else:
                # 逐个安装缺失的包
                for package in missing_packages:
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", package]
                    )

            logger.info("✅ 依赖包安装完成")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 依赖包安装失败: {e}")
            logger.error("请手动安装依赖包或检查网络连接")
            return False

    return True


@register(
    "status",
    "System",
    "AstrBot 服务器状态查看插件",
    "1.0.0",
    "https://github.com/example/astrbot_plugin_status",
)
class StatusPlugin(Star):
    """状态插件"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

        # 检查并安装依赖
        if not _check_and_install_dependencies():
            logger.error("依赖安装失败，插件可能无法正常工作")
            # 不抛出异常，让插件继续加载，但功能可能受限

        # 延迟导入，确保依赖已安装
        try:
            from .kawaii_renderer import KawaiiStatusRenderer
            from .system_info import get_all_status_info

            self.KawaiiStatusRenderer = KawaiiStatusRenderer
            self.get_all_status_info = get_all_status_info
        except ImportError as e:
            logger.error(f"导入模块失败: {e}")
            logger.error("请检查依赖是否正确安装")
            # 设置为None，在使用时进行检查
            self.KawaiiStatusRenderer = None
            self.get_all_status_info = None

        # 配置项
        self.only_superuser = config.get("only_superuser", False)
        self.cache_enabled = config.get("cache_enabled", True)
        self.cache_expire = config.get("cache_expire_minutes", 5) * 60  # 转换为秒
        self.theme = config.get("theme", "light")
        self.show_network = config.get("show_network", True)
        self.show_process_count = config.get("show_process_count", True)

        # 初始化渲染器
        if self.KawaiiStatusRenderer:
            self.renderer = self.KawaiiStatusRenderer()
        else:
            self.renderer = None

        # 缓存系统
        self.cache: Dict[str, Tuple[bytes, float]] = {}

        logger.info("Status 插件已加载")

    def get_cache_key(self, *args) -> str:
        """生成缓存键"""
        content = "|".join(str(arg) for arg in args)
        return hashlib.md5(content.encode()).hexdigest()

    def get_cached_image(self, cache_key: str) -> Optional[bytes]:
        """获取缓存的图片"""
        if not self.cache_enabled or cache_key not in self.cache:
            return None

        image_data, timestamp = self.cache[cache_key]
        if time.time() - timestamp > self.cache_expire:
            del self.cache[cache_key]
            return None

        return image_data

    def cache_image(self, cache_key: str, image_data: bytes):
        """缓存图片"""
        if self.cache_enabled:
            self.cache[cache_key] = (image_data, time.time())

    def clean_expired_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.cache_expire
        ]
        for key in expired_keys:
            del self.cache[key]

    def is_authorized(self, event: AstrMessageEvent) -> bool:
        """检查用户是否有权限使用状态命令"""
        if not self.only_superuser:
            return True

        # 这里需要根据AstrBot的实际权限系统来实现
        # 暂时返回True，实际使用时需要根据具体的权限检查方式修改
        return True

    @filter.command("status")
    async def status_command(self, event: AstrMessageEvent):
        """查看系统状态"""
        try:
            # 检查依赖是否可用
            if not self.renderer or not self.get_all_status_info:
                yield event.plain_result("❌ 插件依赖未正确安装，请检查依赖包")
                return

            # 权限检查
            if not self.is_authorized(event):
                yield event.plain_result("❌ 权限不足，仅管理员可查看系统状态")
                return

            # 生成缓存键
            cache_key = self.get_cache_key(
                "status", self.theme, self.show_network, self.show_process_count
            )

            # 尝试获取缓存
            cached_image = self.get_cached_image(cache_key)
            if cached_image:
                logger.info("使用缓存的状态图片")
                yield event.chain_result([Comp.Image.fromBytes(cached_image)])
                return

            # 收集系统信息
            logger.info("收集系统状态信息...")
            status_info = self.get_all_status_info()

            # 根据配置过滤信息
            if not self.show_network:
                status_info.pop("network", None)

            # 渲染状态图片
            logger.info("渲染状态图片...")
            image_data = self.renderer.render(status_info)

            # 缓存图片
            self.cache_image(cache_key, image_data)

            # 清理过期缓存
            self.clean_expired_cache()

            # 发送图片
            yield event.chain_result([Comp.Image.fromBytes(image_data)])

        except Exception as e:
            logger.error(f"生成状态图片失败: {e}")
            yield event.plain_result("❌ 生成状态图片时出现错误")

    @filter.command("状态")
    async def status_alias(self, event: AstrMessageEvent):
        """状态命令的中文别名"""
        async for result in self.status_command(event):
            yield result

    @filter.command("运行状态")
    async def running_status_alias(self, event: AstrMessageEvent):
        """运行状态命令别名"""
        async for result in self.status_command(event):
            yield result

    @filter.command("status_config")
    async def status_config_command(self, event: AstrMessageEvent):
        """查看状态插件配置"""
        try:
            # 权限检查
            if not self.is_authorized(event):
                yield event.plain_result("❌ 权限不足")
                return

            config_text = f"""📊 Status 插件配置
🔒 仅管理员: {'✅' if self.only_superuser else '❌'}
💾 缓存启用: {'✅' if self.cache_enabled else '❌'}
⏰ 缓存过期: {self.cache_expire // 60} 分钟
🎨 主题: {self.theme}
🌐 显示网络: {'✅' if self.show_network else '❌'}
📈 显示进程数: {'✅' if self.show_process_count else '❌'}
🗂️ 缓存数量: {len(self.cache)}"""

            yield event.plain_result(config_text)

        except Exception as e:
            logger.error(f"查看配置失败: {e}")
            yield event.plain_result("❌ 查看配置失败")

    @filter.command("status_clear_cache")
    async def clear_cache_command(self, event: AstrMessageEvent):
        """清理状态插件缓存"""
        try:
            # 权限检查
            if not self.is_authorized(event):
                yield event.plain_result("❌ 权限不足")
                return

            cache_count = len(self.cache)
            self.cache.clear()
            yield event.plain_result(f"✅ 已清理 {cache_count} 个缓存图片")

        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            yield event.plain_result("❌ 清理缓存失败")

    async def terminate(self):
        """插件卸载时的清理工作"""
        self.cache.clear()
        logger.info("Status 插件已卸载")
