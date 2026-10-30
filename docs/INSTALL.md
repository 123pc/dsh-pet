# 安装 Claude 大肥鱼

## Windows 解压即用

1. 在[发布页](https://github.com/123pc/dsh-pet-claude/releases/tag/claude-v0.7.1)下载 `claude-dafeiyu-windows-x64.zip`。
2. 解压到自己可写的文件夹，双击 `启动桌宠.cmd`。第一次启动会在该文件夹的 `data/` 安装角色与配置。
3. 右键桌宠 → 换装，选择站立或托腮；右键可点播动作，托盘菜单可以退出。

不需要安装 DSH、Node.js 或另行下载 Electron。不要只复制内部的 EXE；整个文件夹需要一起保留。升级前先退出，将新版本解压到另一个文件夹，把旧版 `data/` 复制过去再启动即可。删除整个文件夹就是卸载；保留 `data/` 即可保留设置。

解压版自带日常活动；跟随 DSH 任务的办公状态需要下面的插件模式。角色不需要联网生成动画。对话能力需另行配置模型，未配置不会自动调用模型服务。

## 安装到已有 DSH

本分支与原版使用相同插件 ID `dsh-pet`，安装前先退出 DSH，并保存原有配置。请安装本分支的引擎，单独安装角色包不能为原版引擎增加动作链与办公衔接。

从同一发布页下载：

- `dsh-pet-0.3.8-claude.1.tgz`：插件引擎。
- `claude-dafeiyu-pet-pack.zip`：两种形态与完整动作、安装器。

Web 模式（Node.js 22.12+）：

```powershell
dsh plugin --profile web add file:D:/Downloads/dsh-pet-0.3.8-claude.1.tgz
```

桌面 DSH 使用应用内插件管理安装本地插件包，或使用桌面应用自带的 CLI 和对应 profile；不要误装到 `web` profile。

首次启动一次插件以创建素材目录，然后退出 DSH。解压角色包，进入解压目录：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -CheckOnly
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

默认素材目录为 `%USERPROFILE%\.dsh\dsh-pet\pet`。设置了 `DSH_HOME` 或使用其它目录时，两个命令都加上 `-PetRoot '你的实际素材目录'`。安装器校验 SHA256、备份被覆盖文件并保留已有实例偏好。

重启 DSH，右键原版桌宠 → 换装 → Claude-大肥鱼-站立 / Claude-大肥鱼-托腮。首次安装角色默认同时显示站立形态，可在显示位置菜单中隐藏不需要的实例。

卸载两种 Claude 形态可运行角色包的 `uninstall.ps1`；它会保护用户修改与无关文件。恢复原版引擎请重新安装上游插件。

## 从源码构建

```powershell
git clone https://github.com/123pc/dsh-pet-claude.git
cd dsh-pet-claude/dsh-pet
npm install
npm run build
dsh plugin --profile web add file:D:/你的路径/dsh-pet-claude/dsh-pet
```

随后运行仓库 `community-pets/claude-dafeiyu/install.ps1` 安装角色包。开发与接口资料见[上游文档](../UPSTREAM-README.md)、[换装](../dsh-pet/docs/outfits.md)、[动作扩展](../dsh-pet/docs/animation-extensions.md)。

Windows 发行包的重建方法：在插件目录完成 `npm run prepack` 和 `npm pack --ignore-scripts`，再从仓库根目录依次运行：

```powershell
python tools/release/collect_notices.py
python tools/release/build_release.py --electron '本机 Electron 解压目录' --plugin 'dsh-pet/dsh-pet-0.3.8-claude.1.tgz'
```

Python 依赖为 Pillow 与 imageio-ffmpeg；`collect_notices.py` 下载固定提交的第三方源码，打包脚本不会下载 Electron。README 动图可用 `python tools/release/build_release.py --media-only` 从已发布视频重新生成。
