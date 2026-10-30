# 第三方组件与源码

本项目源代码保留上游与本分支的 MIT 许可，见 [LICENSE](LICENSE)。

Windows 组合发行包包含 GPL-3.0-only 组件 `@andresaya/edge-tts` 1.9.1；该组合二进制分发遵循随附的 GPL v3 条款，原 MIT 部分的版权与许可继续保留。完整条款在 [docs/licenses/edge-tts-LICENSE.txt](docs/licenses/edge-tts-LICENSE.txt)。

- 引擎与发布脚本的对应源码：本仓库 `claude-v0.7.1` 标签（发布页自带 Source code 下载）。构建说明见 [docs/INSTALL.md](docs/INSTALL.md)。
- Edge TTS 对应源码：`andresayac/edge-tts` 的 `v1.9.1`，提交 `93f6dbc5905293402ebf4b6dc162d31f7e61136e`；[发布页](https://github.com/123pc/dsh-pet-claude/releases/tag/claude-v0.7.1)附有 `THIRD-PARTY-SOURCE.zip`，包含该提交的源文件、构建配置与许可证。
- Electron 及 Chromium 许可证随 Windows 包的 `runtime/LICENSE`、`runtime/LICENSES.chromium.html` 保留；其它依赖许可证汇集在 `licenses/`。这些组件的名称、版本与源码仓库地址见 `licenses/components.json`。

角色图片与视频保留在源码仓库的 `community-pets/claude-dafeiyu/`，视频及配置校验清单见该目录的 `manifest.json`。
