# 社区扩展（非官方）

这个分支收集「上游没有、但可以直接用」的社区内容。目前包括：

| 目录 | 内容 |
|---|---|
| [`community-pets/claude-dafeiyu/`](community-pets/claude-dafeiyu/) | 「Claude 工牌大肥鱼」dsh-pet 角色包：19 段透明动画、随机动作分类、一键安装脚本 |
| [`community-plugins/dsh-pet-panel/`](community-plugins/dsh-pet-panel/) | DSH 左侧栏「桌宠控制台」：形象切换（大肥鱼 ↔ Claude 工牌）、逐只显示位置、全部开关 |

## 安装角色包

```powershell
# 先按上游说明装好 dsh-pet（>= 0.3.0），然后：
powershell -NoProfile -ExecutionPolicy Bypass -File .\community-pets\claude-dafeiyu\install.ps1
```

默认装到 `%USERPROFILE%\.dsh\dsh-pet\pet\`，装完刷新 DSH 页面或在桌宠右键菜单里「重载配置」。

## 安装侧栏控制台

```powershell
dsh plugin --profile desktop add "link:<本仓库>/community-plugins/dsh-pet-panel"
```

装完重启 DSH，左侧栏底部会出现 🐋 按钮。

## 授权提醒

- 「大肥鱼」角色形象是社区二创：CC BY-NC-SA 4.0（署名、非商业、同协议）。参考来源：上善无形「溟月」、ZipZipPipe 的 DeepSeek 女仆版，以及 Claude 工牌工作服设定图（原作者未标注、授权未明）。
- 本目录素材为**个人自用**生成/整理，请勿商用或再分发；要发布请先联系原作者。
- 引擎与上游代码仍按上游许可证（MIT；素材另有约束）。

## 说明

- 本分支不修改上游运行时代码，只追加 `community-*` 目录；合并时不会和上游冲突。
- 动画由立绘程序化生成（呼吸、走、跳、转圈、托腮等），不是手绘逐帧，属于可用的第一版。
