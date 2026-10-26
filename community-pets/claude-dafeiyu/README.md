# Claude 工牌大肥鱼 · dsh-pet 角色包

一只穿 Claude 工牌的蓝发鲸鱼娘，Q 版，带 19 段透明动画。

## 内容

- `claude-dafeiyu-config.json`：角色配置（宠物实例、动画池、分类权重）
- `animation/*.webm`：19 段 VP9-alpha 透明动画，640×360 / 24fps
- `install.ps1`：复制到 `~/.dsh/dsh-pet/pet/`

## 动画一览

| 用途 | 动画 |
|---|---|
| 基础 | `idle` 待机、`walk` 走路、`click` 点击回应、`drag` 被拎起 |
| 小动作 | `stretch` 伸懒腰、`squat` 蹲下、`shake` 抖一抖、`wag` 摇尾、`peek` 探头 |
| 玩耍 | `spin` 转圈、`jump` 蹦跳、`dance` 摇摆舞、`dash` 小跑 |
| 干饭 | `eat` 干饭、`eatHappy` 干饭蹦 |
| 休息 | `sleep` 趴睡、`sleepDeep` 熟睡、`lean` 托腮、`leanSway` 托腮晃 |

随机链权重：`idle 10 / turn 5 / move 5`，剩余 80% 会在四类动作池里按权重抽：
小动作 30、玩耍 20、干饭 15、休息 15。

## 安装

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
# 可选：指定宠物目录
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -PetRoot "D:\你的\dsh-pet\pet"
```

装完：
- 浏览器里：刷新 DSH 页面；
- 桌面上：右键任意桌宠 →「重载配置」。

## 卸载

删掉以下两项即可（先备份你改过的文件）：

```
%USERPROFILE%\.dsh\dsh-pet\pet\claude-dafeiyu-config.json
%USERPROFILE%\.dsh\dsh-pet\pet\claude-dafeiyu-animation\
```

## 授权

角色二创，个人自用；大肥鱼本体 CC BY-NC-SA 4.0；参考素材来自社区档案（授权未明）。**请勿商用或再分发。**
