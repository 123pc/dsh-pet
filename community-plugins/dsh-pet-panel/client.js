/**
 * dsh-pet-panel —— 浏览器半侧：左侧栏「桌宠控制台」。
 *
 * 形态：sidebar.footer.action 里的一个图标按钮（宽栏时带文字）。
 * 点开是一个小浮层，能：
 *   - 逐只切换 dsh-pet 的显示位置：显示(web+desktop) / 仅网页 / 仅桌面 / 关
 *   - 开关 dsh-dafeiyu（若其接口可用）
 *   - 一键全部关掉 / 全部显示
 *
 * 数据来源是桌宠插件自己的本地 HTTP 接口（同源），不读写它们的配置文件：
 *   GET/POST /dsh-pet-7340/config、/dsh-pet-7340/pet-display
 *   GET/PATCH /plugins/dsh-dafeiyu/config
 *
 * 注意：本文件是「浏览器端副作用脚本」，不能有顶层 import/export；
 * 必须通过 DSH 注入的 window.__ModuleLoader__.load 注册 factory。
 */
;(() => {
  function makeFactory() {
    return (require) => {
      const module = { exports: {} }
      const React = require('react')
      const h = React.createElement
      const { useState, useEffect, useRef, useCallback } = React

      const PET_API = '/dsh-pet-7340'
      const FEIYU_API = '/plugins/dsh-dafeiyu/config'
      // dsh-whale-widget（小鲸鱼挂件）是往页面里注入的网页挂件，没有开关接口，
      // 只能按它自己的根节点做显隐——这是纯前端操作，不碰它的数据。
      const WIDGET_SELECTOR = '.dshwv-root'
      const WIDGET_STYLE_ID = 'dsh-pet-panel-hide-whale'
      const WIDGET_KEY = 'dsh-pet-panel:whale-hidden'

      function readWhaleHidden() {
        try {
          return window.localStorage.getItem(WIDGET_KEY) === '1'
        } catch {
          return false
        }
      }

      /** 用一条注入的样式表隐藏挂件根节点：它重绘/重建根节点也不会把显隐状态弄丢。 */
      function applyWhaleHidden(hidden) {
        try {
          window.localStorage.setItem(WIDGET_KEY, hidden ? '1' : '0')
        } catch {
          /* 隐私模式下可能不可写 */
        }
        if (typeof document === 'undefined') return
        const existing = document.getElementById(WIDGET_STYLE_ID)
        if (hidden) {
          if (existing) return
          const style = document.createElement('style')
          style.id = WIDGET_STYLE_ID
          style.textContent = '.dshwv-root{display:none !important}'
          document.head.appendChild(style)
        } else if (existing) {
          existing.remove()
        }
      }

      const DISPLAY_MODES = [
        ['both', '显示'],
        ['web', '仅网页'],
        ['desktop', '仅桌面'],
        ['none', '关'],
      ]

      async function request(url, init) {
        try {
          const res = await fetch(url, init)
          const text = await res.text()
          let data = text
          try {
            data = text ? JSON.parse(text) : null
          } catch {
            /* 保留原文 */
          }
          return { ok: res.ok, status: res.status, data }
        } catch (error) {
          return { ok: false, status: 0, data: String(error) }
        }
      }

      function petRows(cfg) {
        const rows = []
        if (!cfg || typeof cfg !== 'object') return rows
        for (const entry of Object.keys(cfg)) {
          const conf = cfg[entry]
          if (!conf || !Array.isArray(conf.pets)) continue
          for (const pet of conf.pets) {
            if (!pet || typeof pet.id !== 'string' || !pet.id) continue
            rows.push({
              entry,
              id: pet.id,
              name: typeof pet.name === 'string' && pet.name ? pet.name : pet.id,
              display: typeof pet.display === 'string' ? pet.display : 'both',
            })
          }
        }
        return rows
      }

      const S = {
        button: {
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 6,
          minWidth: 32,
          height: 32,
          padding: '0 8px',
          border: 'none',
          borderRadius: 8,
          background: 'transparent',
          color: 'inherit',
          font: 'inherit',
          fontSize: 13,
          cursor: 'pointer',
          position: 'relative',
        },
        dot: {
          position: 'absolute',
          top: 5,
          right: 5,
          width: 6,
          height: 6,
          borderRadius: 3,
          background: '#3ecf8e',
        },
        popover: {
          position: 'fixed',
          zIndex: 10000,
          width: 268,
          padding: 12,
          borderRadius: 12,
          background: 'rgba(30,30,32,0.97)',
          color: '#f2f2f2',
          border: '1px solid rgba(255,255,255,0.14)',
          boxShadow: '0 12px 32px rgba(0,0,0,0.45)',
          fontSize: 12,
          lineHeight: 1.5,
        },
        title: { fontSize: 12, opacity: 0.65, marginBottom: 8 },
        row: { marginBottom: 10 },
        rowHead: {
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 8,
          marginBottom: 5,
        },
        label: { fontWeight: 600, fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
        seg: { display: 'flex', gap: 3, background: 'rgba(255,255,255,0.07)', borderRadius: 8, padding: 2 },
        segBtn: {
          flex: 1,
          padding: '3px 0',
          border: 'none',
          borderRadius: 6,
          background: 'transparent',
          color: 'inherit',
          fontSize: 11,
          cursor: 'pointer',
          opacity: 0.72,
        },
        segBtnOn: { background: 'rgba(62,207,142,0.9)', color: '#0b1f16', opacity: 1, fontWeight: 700 },
        note: { minHeight: 16, fontSize: 11, opacity: 0.75, marginTop: 6, wordBreak: 'break-all' },
        links: { display: 'flex', gap: 8, marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(255,255,255,0.12)' },
        link: {
          flex: 1,
          padding: '5px 0',
          border: '1px solid rgba(255,255,255,0.18)',
          borderRadius: 8,
          background: 'transparent',
          color: 'inherit',
          fontSize: 11,
          cursor: 'pointer',
        },
        unavailable: { fontSize: 11, opacity: 0.6, padding: '2px 0' },
      }

      function PetPanel(props) {
        const wide = props && props.wide !== false
        const [open, setOpen] = useState(false)
        const [pets, setPets] = useState([])
        const [feiyu, setFeiyu] = useState({ available: false, enabled: false })
        const [widget, setWidget] = useState({ available: false, hidden: readWhaleHidden() })
        const [busy, setBusy] = useState('')
        const [note, setNote] = useState('')
        const [pos, setPos] = useState({ left: 16, bottom: 64 })
        const containerRef = useRef(null)
        const buttonRef = useRef(null)

        const refresh = useCallback(async () => {
          const cfg = await request(PET_API + '/config')
          if (cfg.ok && cfg.data) setPets(petRows(cfg.data))
          else setPets([])
          const fy = await request(FEIYU_API)
          if (fy.ok && fy.data && typeof fy.data === 'object') {
            setFeiyu({ available: true, enabled: fy.data.enabled !== false })
          } else {
            setFeiyu({ available: false, enabled: false })
          }
          const el = typeof document !== 'undefined' ? document.querySelector(WIDGET_SELECTOR) : null
          setWidget({ available: !!el, hidden: readWhaleHidden() })
        }, [])

        // 页面刚加载时就把上次的隐藏状态补上（挂件脚本可能比本插件晚注入）
        useEffect(() => {
          applyWhaleHidden(readWhaleHidden())
        }, [])

        useEffect(() => {
          if (!open) return undefined
          void refresh()
          const el = buttonRef.current
          if (el) {
            const rect = el.getBoundingClientRect()
            const width = 268
            let left = rect.left
            if (left + width > window.innerWidth - 8) left = Math.max(8, window.innerWidth - width - 8)
            setPos({ left, bottom: Math.max(8, window.innerHeight - rect.top + 8) })
          }
          const onPointerDown = (event) => {
            const root = containerRef.current
            if (root && root.contains(event.target)) return
            setOpen(false)
          }
          const onKeyDown = (event) => {
            if (event.key === 'Escape') setOpen(false)
          }
          document.addEventListener('mousedown', onPointerDown)
          document.addEventListener('keydown', onKeyDown)
          return () => {
            document.removeEventListener('mousedown', onPointerDown)
            document.removeEventListener('keydown', onKeyDown)
          }
        }, [open, refresh])

        const setDisplay = useCallback(
          async (id, display) => {
            setBusy('pet:' + id)
            setNote('')
            const result = await request(PET_API + '/pet-display', {
              method: 'POST',
              headers: { 'content-type': 'application/json' },
              body: JSON.stringify({ id, display }),
            })
            setBusy('')
            if (!result.ok) {
              setNote('切换失败：HTTP ' + result.status)
            } else if (result.data && result.data.ok === false) {
              setNote(result.data.message || '切换失败')
            } else {
              const label = DISPLAY_MODES.find((m) => m[0] === display)
              setNote('已切换为「' + (label ? label[1] : display) + '」')
              await refresh()
            }
          },
          [refresh],
        )

        const swapTo = useCallback(
          async (targetId) => {
            if (!pets.some((p) => p.id === targetId)) {
              setNote('没找到这只宠物：' + targetId)
              return
            }
            setBusy('swap:' + targetId)
            setNote('')
            for (const pet of pets) {
              const display = pet.id === targetId ? 'both' : 'none'
              await request(PET_API + '/pet-display', {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({ id: pet.id, display }),
              })
            }
            setBusy('')
            setNote(targetId === 'main' ? '已切换为「大肥鱼」' : '已切换为「Claude 工牌」')
            await refresh()
          },
          [pets, refresh],
        )

        const setFeiyuEnabled = useCallback(
          async (enabled) => {
            setBusy('feiyu')
            setNote('')
            const result = await request(FEIYU_API, {
              method: 'PATCH',
              headers: { 'content-type': 'application/json' },
              body: JSON.stringify({ enabled }),
            })
            setBusy('')
            if (!result.ok) {
              setNote('大肥鱼接口不可用（插件未启用？）')
              return
            }
            setFeiyu({ available: true, enabled })
            setNote(enabled ? '已打开大肥鱼' : '已关闭大肥鱼')
          },
          [],
        )

        const setWidgetHidden = useCallback((hidden) => {
          applyWhaleHidden(hidden)
          const el = typeof document !== 'undefined' ? document.querySelector(WIDGET_SELECTOR) : null
          setWidget({ available: !!el, hidden })
          setNote(
            hidden
              ? el
                ? '已隐藏小鲸鱼挂件（刷新后仍保持）'
                : '设置已保存，挂件加载后会隐藏'
              : '已显示小鲸鱼挂件',
          )
        }, [])

        const allDisplay = useCallback(
          async (display) => {
            setBusy('all')
            setNote('')
            for (const pet of pets) {
              // 串行，避免同时触发多次桌面 helper 重启
              await request(PET_API + '/pet-display', {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({ id: pet.id, display }),
              })
            }
            setBusy('')
            setNote(display === 'none' ? '已全部关掉' : '已全部显示')
            await refresh()
          },
          [pets, refresh],
        )

        const allToggle = useCallback(
          async (display) => {
            await allDisplay(display)
            applyWhaleHidden(display === 'none')
            setWidget((prev) => Object.assign({}, prev, { hidden: display === 'none' }))
          },
          [allDisplay],
        )

        const active = pets.some((pet) => pet.display !== 'none') || feiyu.enabled || (widget.available && !widget.hidden)

        return h(
          'div',
          { ref: containerRef, style: { position: 'relative', display: 'inline-flex' } },
          h(
            'button',
            {
              ref: buttonRef,
              type: 'button',
              title: '桌宠控制台',
              'aria-label': '桌宠控制台',
              onClick: () => setOpen((value) => !value),
              style: S.button,
            },
            h('span', { 'aria-hidden': 'true', style: { fontSize: 15 } }, '🐋'),
            wide ? h('span', null, '桌宠') : null,
            active ? h('span', { style: S.dot }) : null,
          ),
          open
            ? h(
                'div',
                { style: Object.assign({}, S.popover, { left: pos.left, bottom: pos.bottom }) },
                h(
                  'div',
                  { style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 } },
                  h('strong', { style: { fontSize: 12 } }, '桌宠控制台'),
                  h(
                    'button',
                    {
                      type: 'button',
                      onClick: () => void refresh(),
                      style: Object.assign({}, S.link, { flex: '0 0 auto', padding: '2px 8px' }),
                    },
                    '刷新',
                  ),
                ),
                h(
                  'div',
                  { style: S.row },
                  h('div', { style: S.rowHead }, h('span', { style: S.label }, '形象切换')),
                  h(
                    'div',
                    { style: S.seg },
                    [
                      ['main', '大肥鱼'],
                      ['claude-dafeiyu', 'Claude 工牌'],
                    ].map(([id, label]) => {
                      const pet = pets.find((p) => p.id === id)
                      const on = !!pet && pet.display !== 'none'
                      return h(
                        'button',
                        {
                          key: id,
                          type: 'button',
                          disabled: !pet || busy === 'swap:' + id,
                          onClick: () => void swapTo(id),
                          style: Object.assign({}, S.segBtn, on ? S.segBtnOn : null),
                        },
                        label,
                      )
                    }),
                  ),
                ),
                pets.length === 0
                  ? h('div', { style: S.unavailable }, 'dsh-pet 未安装（当前用小鲸鱼挂件代替）')
                  : pets.map((pet) =>
                      h(
                        'div',
                        { key: pet.entry + ':' + pet.id, style: S.row },
                        h(
                          'div',
                          { style: S.rowHead },
                          h('span', { style: S.label, title: pet.name }, pet.name),
                          h('span', { style: { fontSize: 10, opacity: 0.5 } }, pet.entry),
                        ),
                        h(
                          'div',
                          { style: S.seg },
                          DISPLAY_MODES.map(([value, label]) =>
                            h(
                              'button',
                              {
                                key: value,
                                type: 'button',
                                disabled: busy === 'pet:' + pet.id || busy === 'all',
                                onClick: () => void setDisplay(pet.id, value),
                                style: Object.assign({}, S.segBtn, pet.display === value ? S.segBtnOn : null),
                              },
                              label,
                            ),
                          ),
                        ),
                      ),
                    ),
                h(
                  'div',
                  { style: S.row },
                  h('div', { style: S.rowHead }, h('span', { style: S.label }, '大肥鱼（dsh-dafeiyu）')),
                  feiyu.available
                    ? h(
                        'div',
                        { style: S.seg },
                        [
                          [true, '开'],
                          [false, '关'],
                        ].map(([value, label]) =>
                          h(
                            'button',
                            {
                              key: label,
                              type: 'button',
                              disabled: busy === 'feiyu',
                              onClick: () => void setFeiyuEnabled(value),
                              style: Object.assign({}, S.segBtn, feiyu.enabled === value ? S.segBtnOn : null),
                            },
                            label,
                          ),
                        ),
                      )
                    : h('div', { style: S.unavailable }, '未启用（当前 profile 未加载该插件）'),
                ),
                h('div', { style: S.note }, busy ? '处理中…' : note),
                h(
                  'div',
                  { style: S.row },
                  h(
                    'div',
                    { style: S.rowHead },
                    h('span', { style: S.label }, '小鲸鱼挂件（网页）'),
                    h('span', { style: { fontSize: 10, opacity: 0.5 } }, widget.available ? '已检测到' : '未加载'),
                  ),
                  h(
                    'div',
                    { style: S.seg },
                    [
                      [false, '显示'],
                      [true, '隐藏'],
                    ].map(([value, label]) =>
                      h(
                        'button',
                        {
                          key: label,
                          type: 'button',
                          onClick: () => setWidgetHidden(value),
                          style: Object.assign({}, S.segBtn, widget.hidden === value ? S.segBtnOn : null),
                        },
                        label,
                      ),
                    ),
                  ),
                ),
                h(
                  'div',
                  { style: S.links },
                  h(
                    'button',
                    { type: 'button', style: S.link, onClick: () => void allToggle('none') },
                    '全部关掉',
                  ),
                  h(
                    'button',
                    { type: 'button', style: S.link, onClick: () => void allToggle('both') },
                    '全部显示',
                  ),
                ),
              )
            : null,
        )
      }

      const name = 'pet-panel'
      const inject = ['slots']

      function apply(ctx) {
        ctx.slots.inject('sidebar.footer.action', () =>
          ctx.slots.register(
            {
              name: 'sidebar.footer.action',
              id: 'pet-panel',
              order: 90,
            },
            PetPanel,
          ),
        )
      }

      module.exports = { name, inject, apply }
      return module.exports
    }
  }

  window.__ModuleLoader__.load({
    id: 'dsh-pet-panel',
    factory: makeFactory(),
  })
})()
