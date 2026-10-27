# dsh-pet-panel · 侧栏桌宠控制台

给 DSH 左侧栏底部加一个 🐋 按钮，用于控制 dsh-pet 桌宠：

- **形象切换**：`大肥鱼` / `Claude·站立` / `Claude·托腮`，保留当前网页/桌面模式，只切换这三个形态
- 逐只宠物的显示位置：显示 / 仅网页 / 仅桌面 / 关
- 全部关掉 / 全部显示
- 小鲸鱼网页挂件（dsh-whale-widget）显示 / 隐藏
- 若装了 dsh-dafeiyu，还能开关它的 `enabled`
- 重载角色包：调用现有 `/reload`，重载桌面 helper；网页仍需刷新
- Claude 动作：向左走／向右走，按分类选择并点播站立形态全部 107 个动作
- 名称经 `/anim?pet=claude-dafeiyu&surface=any` 点播，保留宿主真实走位；不使用裸视频 URL 冒充走位
- 正确处理 HTTP 200 + `ok:false`；写入互斥，形态切换失败会尝试恢复原显示状态
- 全部开关也涵盖独立 dsh-dafeiyu；任何部分失败都会明确提示

## 安装

```powershell
dsh plugin --profile desktop add "link:<本目录绝对路径>"
```

安装/卸载插件前先完全退出 DSH，执行后再启动；不要在 DSH 运行时通过 CLI 修改 profile。已经链接过本目录时，替换 `client.js` 后先刷新网页；若宿主缓存客户端 bundle，再重启 DSH。

## 说明

- 控制台通过两个桌宠插件自己的本地 HTTP 接口操作，不直接改配置文件；
- 代码 MIT；不含任何角色素材。
- 浮层支持滚动和系统浅色/深色配色。宿主没有已验证的打开文件夹接口，因此未添加执行本地路径的按钮。
- 本目录 `client.js` 为手写入口。可在仓库根目录运行 `node --test community-plugins/dsh-pet-panel/client.test.mjs` 验证事务、回滚、并发与重载行为。
