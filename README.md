# AstrBot Status Plugin

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-Compatible-green.svg)](https://github.com/Soulter/AstrBot)

一个美观的 AstrBot 系统状态查看插件，提供实时的服务器状态监控和可视化展示。


## 🎯 使用方法

- `/status` - 查看系统状态（生成状态图片）
- `/状态` - 中文别名
- `/运行状态` - 中文别名

### 管理命令

- `/status_config` - 查看插件配置
- `/status_clear_cache` - 清理图片缓存

## ⚙️ 配置选项

在 AstrBot 配置中添加以下配置项：

```json
{
  "only_superuser": false,
  "cache_enabled": true,
  "cache_expire_minutes": 5,
  "theme": "light",
  "show_network": true,
  "show_process_count": true
}
```

### 配置说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `only_superuser` | boolean | `false` | 是否只允许超级用户使用状态命令 |
| `cache_enabled` | boolean | `true` | 是否启用图片缓存 |
| `cache_expire_minutes` | integer | `5` | 缓存过期时间（分钟） |
| `theme` | string | `"light"` | 主题样式（`light` 或 `dark`） |
| `show_network` | boolean | `true` | 是否显示网络信息 |
| `show_process_count` | boolean | `true` | 是否显示进程数量 |

## 📊 状态信息

插件会显示以下系统信息：

## 🔧 依赖项

插件会自动检测并安装以下依赖：

- `psutil>=5.9.0` - 系统信息获取
- `Pillow>=9.0.0` - 图像处理
- `matplotlib>=3.5.0` - 图表绘制
- `py-cpuinfo>=9.0.0` - CPU 信息获取

**注意**：插件首次加载时会自动安装缺失的依赖包，这可能需要几分钟时间。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 参考了 [nonebot-plugin-kawaii-status](https://github.com/KomoriDev/nonebot-plugin-kawaii-status) 的设计思路
- 感谢 AstrBot 项目提供的优秀框架
