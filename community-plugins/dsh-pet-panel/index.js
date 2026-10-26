/**
 * dsh-pet-panel —— 宿主半侧。
 *
 * 这个插件的能力全在浏览器半侧（左侧栏的桌宠控制台），宿主这边不需要注册
 * 任何服务或路由：它只是 bundle 的一条加载入口，让 DSH 的客户端模块系统
 * 把 ./client.js 作为浏览器插件挂到页面上。
 *
 * 控制台直接调用两个桌宠插件自己暴露的本地接口：
 *   - dsh-pet      GET  /dsh-pet-7340/config         读当前显示位置
 *                  POST /dsh-pet-7340/pet-display    写 web / desktop / both / none
 *   - dsh-dafeiyu  GET   /plugins/dsh-dafeiyu/config  读 enabled
 *                  PATCH /plugins/dsh-dafeiyu/config  写 enabled
 * 因此宿主侧保持空实现，避免与它们的配置层产生第二套真相。
 */

export const name = 'dsh-pet-panel'

export const inject = []

export function apply(ctx) {
  // 什么都不做：本插件没有宿主侧能力。
  // 保留一个可诊断的启动痕迹（logger 在部分宿主里可能不存在，故可选链）。
  ctx?.logger?.debug?.('[dsh-pet-panel] host half loaded (UI only)')
}
