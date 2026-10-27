# Claude 工牌大肥鱼 · 0.6 安静陪伴版

走路 v5 已获用户认可，保留原八帧、摆臂幅度与真实桌面位移。其余动作已对照原项目全部 106 个视频完成关键帧重制与 Codex 自查，当前完成数以 `sources/action-library/actions.json` 与 `preview/actions-index.json` 为准。

0.3 的 107 个分层动作已撤回，不能计作新动作完成。旧脚本与素材只用于追溯，不进入新版安装清单。新版使用内置 imagegen 生成完整人物画面：人物、四肢、衣服、道具均在每张图里一起绘制。后期只做整帧提取、配准、缩放和透明编码，没有关节拼贴、代码绘制道具、跨帧淡化或光流补帧。

## 查看动作

右键动作菜单按动画名去重；同一片段即使供多个工作档位或点击事件复用，也只显示一个入口。托腮菜单整理为待机、托腮小动作、办公动作与余额档位四组，共 10 个独立动作，工作状态联动和随机播放配置保留。

`/preview/companion.html` 是这次新增的交互预览：可开始办公、结束办公、逐项查看与慢放。托腮新增摇尾、拨发、无声哼歌；办公有拿出并打开电脑、打字、托腮思考、揉眼伸肩、合盖收起的完整过程。8 张新图板包含 64 张完整人物关键帧，保存在 `sources/lean-v2/`；精确内置 imagegen 提示词为 `requests.json` 与 `revisions.json`。

站立以 16 秒“安静站立·眨眼呼吸”为主要待机，按其余动作实际时长校准抽取权重。未被事件打断时预计占 64.99% 时间，固定模式为 65.95%；时间占比与每次抽中的概率不同。数值与适用范围记录在 `preview/ambient-timing.json`。

启动本目录的静态服务器，访问 `/preview/actions.html`。原 gallery 入口也跳转到动作库。可以搜索、分类、切换背景、慢放，并切换查看原视频四个时间点和新绘制的完整关键帧。`preview/keyframes.html` 保留走路 v4/v5 逐帧对照。

“用户已认可”只用于走路；“已检查”表示 Codex 完成源图与切帧检查，并不代表用户已验收。待制作或待复核动作不会用旧分层视频冒充，也不会自动进入安装清单。

## 素材与记录

- `sources/upstream-reference/`：原项目 106 个视频的截图和时长索引；已经核对配置与视频文件，没有遗漏素材。
- `sources/action-library/<id>/`：每个新动作的完整人物图、精确提示词与修订；生成方式为 builtin imagegen。
- `sources/action-library/actions.json`：名字、分类、帧数、时序、复核状态及源图 SHA256。
- `preview/actions/<id>/`：透明 PNG 关键帧、接触表、GIF 和 VP9 WebM。
- `sources/keyframes-v5/`：用户认可的走路源图与来源哈希；构建时禁止修改。

## 构建

在本目录运行（Python 需要 Pillow、numpy、imageio-ffmpeg）：

```powershell
python build.py --render action-024 action-027  # 生成指定动作预览，不自动验收
python build.py --accept action-024 action-027 --note "实际视觉复核发现与结果"
python build.py --pack                         # 仅收录已检查的动作
python verify.py
python verify_library.py          # 检查每张源帧与全部视频解码帧
python verify_companion.py        # 新托腮素材与待机时间占比
powershell -NoProfile -ExecutionPolicy Bypass -File tests/install.test.ps1
```

默认 `python build.py` 等同于 `--pack`。`build_keyframes.py --draft-only --revision v5` 可重建走路预览；旧撤回入口会保护已经认可的走路，不得退回静止包。`tests/test_full.py` 属于已撤回分层渲染器的历史测试。

从仓库根目录执行宿主和面板回归：

```powershell
node --experimental-strip-types --test community-pets/claude-dafeiyu/tests/runtime.test.mjs community-plugins/dsh-pet-panel/client.test.mjs
```

## 安装

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -CheckOnly
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\uninstall.ps1
```

安装器核对 SHA256、写入前备份，并保留实例名称、显示、尺寸、位置和功能偏好。支持 `-PetRoot`、`-WhatIf`。卸载保护用户修改和无关文件，不写 DSH profile。

托腮办公的入场／收尾需要本仓库新增的 `animations.workSequence` 双端支持。只运行素材安装器不会替换插件运行文件。当前机器已用 `deploy_companion_runtime.py` 对已安装的 0.3.8 版本制作增量补丁；它先在 `.tools/companion-runtime/<时间>/` 备份并构建，再替换四个运行文件，保留该版本其它行为。重建预览与逻辑：`python build_companion.py --render`，再 `python build.py --pack`；`--init` 会重置新增素材的复核状态，仅首次登记使用。

运行文件恢复：将记录中 `originalRuntimeBackup` 的四个文件按相对路径复制回对应插件目录，再重载桌宠。素材包可用原来的备份或卸载器恢复。插件升级可能覆盖本地运行补丁，之后需使用本仓库构建产物或重新部署兼容补丁。两端源码、状态机测试和配置校验均已纳入仓库工作区。

移动要按动作名称点播：`POST /dsh-pet-7340/anim?pet=claude-dafeiyu&surface=any`，例如 JSON `{"name":"自然走路","facing":"left"}`。裸视频 URL 不包含宿主移动语义。移动视频预留首尾各 0.5 秒与中间 4 秒行走窗口，向右由宿主镜像。

技术检查只证明引用、编码、透明、安装和接口工作；动画观感仍需在预览里检查。宿主实机验证使用 `verify_live.py --base-url http://127.0.0.1:<端口>`，结束后恢复位置、释放临时占用。
