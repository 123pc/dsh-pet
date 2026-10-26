# dsh-pet-panel · 侧栏桌宠控制台

给 DSH 左侧栏底部加一个 🐋 按钮，用于控制 dsh-pet 桌宠：

- **形象切换**：`大肥鱼` / `Claude 工牌`（调用 dsh-pet 的 `/pet-display` 接口，一只显示、另一只隐藏）
- 逐只宠物的显示位置：显示 / 仅网页 / 仅桌面 / 关
- 全部关掉 / 全部显示
- 小鲸鱼网页挂件（dsh-whale-widget）显示 / 隐藏
- 若装了 dsh-dafeiyu，还能开关它的 `enabled`

## 安装

```powershell
dsh plugin --profile desktop add "link:<本目录绝对路径>"
```

装完重启 DSH（客户端插件在启动时装配）。

## 说明

- 控制台通过两个桌宠插件自己的本地 HTTP 接口操作，不直接改配置文件；
- 代码 MIT；不含任何角色素材。
