/**
 * 浏览器半侧：经同源接口控制桌宠，不直接写配置或 profile。
 * 依赖 DSH 的模块加载器、React 与侧栏插槽；本文件是手写入口。
 * 多步写入串行执行，业务失败回滚已完成的显示变更。
 * @module dsh-pet-panel/client
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
      const FORMS = [
        ['main', '大肥鱼'],
        ['claude-dafeiyu', 'Claude·站立'],
        ['claude-dafeiyu-lean', 'Claude·托腮'],
      ]
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
        const controller = new AbortController()
        const timer = setTimeout(() => controller.abort(), 10000)
        try {
          const res = await fetch(url, { ...init, signal: controller.signal })
          const text = await res.text()
          let data = text
          try {
            data = text ? JSON.parse(text) : null
          } catch {
            /* 保留原文 */
          }
          return { ok: res.ok && data !== null && typeof data === 'object' && data.ok !== false, status: res.status, data }
        } catch (error) {
          return { ok: false, status: 0, data: String(error) }
        } finally {
          clearTimeout(timer)
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
              animations: conf.animations,
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
          maxWidth: 'calc(100vw - 16px)',
          maxHeight: 'calc(100vh - 80px)',
          overflowY: 'auto',
          colorScheme: 'light dark',
          background: 'Canvas',
          color: 'CanvasText',
          border: '1px solid color-mix(in srgb, CanvasText 18%, transparent)',
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
        seg: { display: 'flex', gap: 3, background: 'color-mix(in srgb, CanvasText 7%, transparent)', borderRadius: 8, padding: 2 },
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
        const [actionGroup, setActionGroup] = useState('moves')
        const [actionName, setActionName] = useState('自然走路')
        const containerRef = useRef(null)
        const buttonRef = useRef(null)
        const busyRef = useRef(false)

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

        /** 互斥操作入口；无论业务失败或请求异常都解锁并重新读服务端状态。 */
        const runOperation = useCallback(async (key, action, message) => {
          if (busyRef.current) return false
          busyRef.current = true
          setBusy(key)
          setNote('')
          try {
            await action()
            setNote(message)
            return true
          } catch (error) {
            setNote(error.message || String(error))
            return false
          } finally {
            await refresh()
            busyRef.current = false
            setBusy('')
          }
        }, [refresh])

        /** 多步变更失败时恢复先前显示模式；回滚失败也必须明确报告。 */
        const changeDisplays = useCallback(async (changes) => {
          const applied = []
          const write = (id, display) => request(PET_API + '/pet-display', {
            method: 'POST', headers: { 'content-type': 'application/json' },
            body: JSON.stringify({ id, display }),
          })
          for (const [pet, display] of changes) {
            if (pet.display === display) continue
            const result = await write(pet.id, display)
            if (!result.ok) {
              // 超时可能发生在服务端写入后；失败的这一步也要尝试恢复。
              const restored = await write(pet.id, pet.display)
              let rollbackFailed = !restored.ok
              for (const previous of applied.reverse()) {
                if (!(await write(previous.id, previous.display)).ok) rollbackFailed = true
              }
              const detail = result.data?.message || result.data?.error || ('HTTP ' + result.status)
              throw new Error('切换失败：' + detail + (rollbackFailed ? '；部分状态未恢复，请刷新后检查' : '；已恢复原显示设置'))
            }
            applied.push(pet)
          }
        }, [])

        // 页面刚加载时就把上次的隐藏状态补上（挂件脚本可能比本插件晚注入）
        useEffect(() => {
          applyWhaleHidden(readWhaleHidden())
          void refresh()
        }, [refresh])

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
            const pet = pets.find(p => p.id === id)
            if (!pet) return
            const label = DISPLAY_MODES.find(m => m[0] === display)?.[1] || display
            return runOperation('pet:' + id, () => changeDisplays([[pet, display]]), '已切换为「' + label + '」')
          },
          [pets, changeDisplays, runOperation],
        )

        const swapTo = useCallback(
          async (targetId) => {
            if (!pets.some((p) => p.id === targetId)) {
              setNote('没找到这只宠物：' + targetId)
              return
            }
            const family = pets.filter(p => FORMS.some(([id]) => id === p.id))
            const target = family.find(p => p.id === targetId)
            const display = family.find(p => p.display !== 'none')?.display || 'both'
            const changes = family.filter(p => p.id !== targetId).map(p => [p, 'none'])
            changes.push([target, display])
            return runOperation('swap:' + targetId, () => changeDisplays(changes),
              '已切换为「' + FORMS.find(([id]) => id === targetId)[1] + '」')
          },
          [pets, runOperation, changeDisplays],
        )

        const setFeiyuEnabled = useCallback(
          async (enabled) => {
            return runOperation('feiyu', async () => {
              const result = await request(FEIYU_API, {
                method: 'PATCH', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ enabled }),
              })
              if (!result.ok) throw new Error('大肥鱼接口不可用或保存失败')
            }, enabled ? '已打开大肥鱼' : '已关闭大肥鱼')
          },
          [runOperation],
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
            return runOperation('all', async () => {
              await changeDisplays(pets.map(pet => [pet, display]))
              if (feiyu.available) {
                const result = await request(FEIYU_API, { method: 'PATCH', headers: { 'content-type': 'application/json' },
                  body: JSON.stringify({ enabled: display !== 'none' }) })
                if (!result.ok) throw new Error('dsh-pet 已更新；独立大肥鱼开关失败，请检查')
              }
            }, display === 'none' ? '已全部关掉' : '已全部显示')
          },
          [pets, feiyu.available, runOperation, changeDisplays],
        )

        const allToggle = useCallback(
          async (display) => {
            if (!await allDisplay(display)) return
            applyWhaleHidden(display === 'none')
            setWidget((prev) => Object.assign({}, prev, { hidden: display === 'none' }))
          },
          [allDisplay],
        )

        const active = pets.some((pet) => pet.display !== 'none') || feiyu.enabled || (widget.available && !widget.hidden)
        const standing = pets.find(p => p.id === 'claude-dafeiyu')
        const a = standing?.animations
        const groups = a ? [
          ['moves', '移动', (a.moves?.actions || []).map(item => item.name)],
          ['clicks', '点击回应', a.clicks || []],
          ['idle', '待机', a.idle || []],
          ['turn', '转向', a.turn || []],
          ['drag', '拖拽反馈', a.drag || []],
          ...(a.categories || []).map(c => [c.id, c.id, c.actions]),
          ...Object.entries(a.events || {}).map(([key, names]) => [key,
            { balance: '余额六档', whisper: '碎碎念', workStatus: '工作状态六档' }[key] || key, names.flat()]),
        ].filter(group => group[2].length > 0) : []
        const selectedGroup = groups.find(g => g[0] === actionGroup) || groups[0]
        const options = selectedGroup?.[2] || []
        const selectedAction = options.includes(actionName) ? actionName : options[0]
        const canPlay = !!standing && standing.display !== 'none'

        /** 名称点播保留宿主的移动语义；不能改成裸素材 URL，否则只会原地播放。 */
        const playAction = (name, facing) => runOperation('action', async () => {
          if (!canPlay || !name) throw new Error('请先切换至 Claude·站立')
          const result = await request(PET_API + '/anim?pet=' + encodeURIComponent(standing.id) + '&surface=any', {
            method: 'POST', headers: { 'content-type': 'application/json' },
            body: JSON.stringify({ name, ...(facing ? { facing } : {}) }),
          })
          if (!result.ok) throw new Error(result.data?.message || '动作请求失败')
        }, '已请求「' + name + '」' + (facing ? '，到屏幕边缘会停止' : ''))

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
                    FORMS.map(([id, label]) => {
                      const pet = pets.find((p) => p.id === id)
                      const on = !!pet && pet.display !== 'none'
                      return h(
                        'button',
                        {
                          key: id,
                          type: 'button',
                          disabled: !pet || !!busy,
                          onClick: () => void swapTo(id),
                          style: Object.assign({}, S.segBtn, on ? S.segBtnOn : null),
                        },
                        label,
                      )
                    }),
                  ),
                ),
                standing ? h('div', { style: S.row },
                  h('div', { style: S.rowHead }, h('span', { style: S.label }, 'Claude 动作')),
                  h('div', { style: S.seg },
                    h('button', { type: 'button', disabled: !!busy || !canPlay || !a?.moves?.actions?.length, style: S.segBtn,
                      onClick: () => void playAction(a?.moves?.actions?.[0]?.name, 'left') }, '向左走'),
                    h('button', { type: 'button', disabled: !!busy || !canPlay || !a?.moves?.actions?.length, style: S.segBtn,
                      onClick: () => void playAction(a?.moves?.actions?.[0]?.name, 'right') }, '向右走')),
                  groups.length ? h('div', { style: { display: 'flex', gap: 4, marginTop: 6 } },
                    h('select', { 'aria-label': '动作分类', value: selectedGroup?.[0], disabled: !!busy,
                      style: { width: 86, minWidth: 0, background: 'Canvas', color: 'CanvasText', borderRadius: 5 },
                      onChange: event => { setActionGroup(event.target.value); setActionName('') } },
                      groups.map(([key, label]) => h('option', { key, value: key }, label))),
                    h('select', { 'aria-label': '动作名称', value: selectedAction, disabled: !!busy,
                      style: { flex: 1, minWidth: 0, background: 'Canvas', color: 'CanvasText', borderRadius: 5 },
                      onChange: event => setActionName(event.target.value) },
                      options.map(name => h('option', { key: name, value: name }, name)))) : null,
                  h('button', { type: 'button', disabled: !!busy || !canPlay || !selectedAction,
                    style: { ...S.link, width: '100%', marginTop: 6 },
                    onClick: () => void playAction(selectedAction) }, '播放选中动作'),
                  !canPlay ? h('div', { style: S.unavailable }, '先切换至 Claude·站立以点播动作') : null,
                  !a?.moves?.actions?.length ? h('div', { style: S.unavailable }, '走路正在重绘，样片验收后开放') : null,
                ) : null,
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
                                disabled: !!busy,
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
                              disabled: !!busy,
                              onClick: () => void setFeiyuEnabled(value),
                              style: Object.assign({}, S.segBtn, feiyu.enabled === value ? S.segBtnOn : null),
                            },
                            label,
                          ),
                        ),
                      )
                    : h('div', { style: S.unavailable }, '未启用（当前 profile 未加载该插件）'),
                ),
                h('div', { style: S.note, role: 'status', 'aria-live': 'polite' }, busy ? '处理中…' : note),
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
                          disabled: !!busy,
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
                    { type: 'button', disabled: !!busy, style: S.link, onClick: () => void allToggle('none') },
                    '全部关掉',
                  ),
                  h(
                    'button',
                    { type: 'button', disabled: !!busy, style: S.link, onClick: () => void allToggle('both') },
                    '全部显示',
                  ),
                ),
                h('button', {
                  type: 'button', disabled: !!busy || pets.length === 0, style: { ...S.link, width: '100%', marginTop: 8 },
                  onClick: () => void runOperation('reload', async () => {
                    const result = await request(PET_API + '/reload', { method: 'POST' })
                    if (!result.ok) throw new Error('重载请求失败')
                  }, '已请求重载桌面；网页请刷新。若新角色仍缺失，请重启 DSH。'),
                }, '重载角色包'),
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
