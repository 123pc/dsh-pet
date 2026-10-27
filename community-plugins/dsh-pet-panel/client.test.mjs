import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import vm from 'node:vm'
import { test } from 'node:test'

const source = readFileSync(new URL('./client.js', import.meta.url), 'utf8')

function harness({ failId, failFeiyu = false } = {}) {
  let component, cursor = 0, effects = [], slots = [], tree
  const calls = []
  const config = { main: { pets: [{ id: 'main', display: 'web' }] },
    claude: { pets: [{ id: 'claude-dafeiyu', display: 'none' }] },
    lean: { pets: [{ id: 'claude-dafeiyu-lean', display: 'none' }] },
    other: { pets: [{ id: 'unrelated', display: 'desktop' }] } }
  config.claude.animations = { idle: ['待机呼吸休闲'], turn: ['东张西望'], drag: ['被鼠标拖拽悬空反馈'],
    clicks: ['点击回应-元气挥手'], moves: { actions: [{ name: '自然走路' }] },
    categories: [{ id: '小动作', actions: ['写代码'] }], events: { balance: ['余额-钱袋满溢'] } }
  let feiyu = true
  const React = {
    createElement: (type, props, ...children) => ({ type, props: props || {}, children: children.flat(Infinity).filter(x => x !== null && x !== undefined) }),
    useState(value) {
      const index = cursor++
      if (!slots[index]) slots[index] = { value }
      return [slots[index].value, next => { slots[index].value = typeof next === 'function' ? next(slots[index].value) : next }]
    },
    useRef(value) { const index = cursor++; return slots[index] ||= { current: value } },
    useCallback(fn, deps) {
      const index = cursor++, previous = slots[index]
      if (!previous || deps.some((d, i) => !Object.is(d, previous.deps[i]))) slots[index] = { fn, deps }
      return slots[index].fn
    },
    useEffect(fn, deps) {
      const index = cursor++, previous = slots[index]
      if (!previous || deps.some((d, i) => !Object.is(d, previous.deps[i]))) {
        slots[index] = { deps }; effects.push(fn)
      }
    },
  }
  const fetch = async (url, init = {}) => {
    const method = init.method || 'GET', body = init.body && JSON.parse(init.body)
    calls.push({ url, method, body })
    let data
    if (url.endsWith('/pet-display')) {
      if (body.id === failId && body.display !== 'none') data = { ok: false, message: 'simulated disk failure' }
      else {
        const pet = Object.values(config).flatMap(c => c.pets).find(p => p.id === body.id)
        pet.display = body.display; data = config
      }
    } else if (url.includes('/plugins/')) {
      if (method === 'PATCH' && failFeiyu) data = { ok: false, message: 'failure' }
      else { if (body) feiyu = body.enabled; data = { enabled: feiyu } }
    } else if (url.includes('/anim?')) data = url.includes('&surface=any') ? { ok: true, playbackId: 'test-playback' } : { ok: false, message: 'surface required' }
    else if (url.endsWith('/reload')) data = { reloading: true }
    else data = config
    return { ok: true, status: 200, text: async () => JSON.stringify(data) }
  }
  const document = { querySelector: () => null, getElementById: () => null,
    addEventListener() {}, removeEventListener() {}, createElement: () => ({}), head: { appendChild() {} } }
  const window = { localStorage: { getItem() {}, setItem() {} }, innerWidth: 1000, innerHeight: 800,
    __ModuleLoader__: { load({ factory }) {
      factory(name => { assert.equal(name, 'react'); return React }).apply({ slots: {
        inject(_, fn) { fn() }, register(_, value) { component = value },
      } })
    } } }
  vm.runInNewContext(source, { window, document, fetch, AbortController, setTimeout, clearTimeout })
  const render = () => { cursor = 0; tree = component({ wide: true }); const pending = effects; effects = []; pending.forEach(fn => fn()); return tree }
  const flatten = node => typeof node === 'object' ? [node, ...node.children.flatMap(flatten)] : []
  const text = node => typeof node === 'object' ? node.children.map(text).join('') : String(node)
  const button = label => flatten(tree).find(n => n.type === 'button' && (text(n) === label || n.props['aria-label'] === label))
  const settle = async () => { for (let i = 0; i < 4; i++) { await new Promise(setImmediate); render() } }
  const click = async label => { const b = button(label); assert.ok(b, label); b.props.onClick(); await settle() }
  const start = async () => { render(); await settle(); await click('桌宠控制台') }
  return { start, click, button, settle, calls, config, text: () => text(tree), feiyu: () => feiyu }
}

test('switch form preserves web-only mode and unrelated pets', async () => {
  const h = harness(); await h.start(); await h.click('Claude·托腮')
  assert.equal(h.config.main.pets[0].display, 'none')
  assert.equal(h.config.lean.pets[0].display, 'web')
  assert.equal(h.config.other.pets[0].display, 'desktop')
  assert.match(h.text(), /已切换为「Claude·托腮」/)
})

test('HTTP 200 business failure rolls back and never reports success', async () => {
  const h = harness({ failId: 'claude-dafeiyu-lean' }); await h.start(); await h.click('Claude·托腮')
  assert.equal(h.config.main.pets[0].display, 'web')
  assert.equal(h.config.lean.pets[0].display, 'none')
  assert.match(h.text(), /simulated disk failure/)
  assert.doesNotMatch(h.text(), /已切换为/)
})

test('rapid clicks cannot interleave two display transactions', async () => {
  const h = harness(); await h.start()
  h.button('Claude·托腮').props.onClick()
  h.button('Claude·站立').props.onClick()
  await h.settle()
  assert.equal(h.config.lean.pets[0].display, 'web')
  assert.equal(h.config.claude.pets[0].display, 'none')
})

test('all off includes standalone dafeiyu and reload posts to the existing API', async () => {
  const h = harness(); await h.start(); await h.click('全部关掉')
  assert.equal(h.feiyu(), false)
  assert.ok(Object.values(h.config).flatMap(c => c.pets).every(p => p.display === 'none'))
  await h.click('重载角色包')
  assert.ok(h.calls.some(c => c.url.endsWith('/reload') && c.method === 'POST'))
})

test('standalone failure is surfaced during all off', async () => {
  const h = harness({ failFeiyu: true }); await h.start(); await h.click('全部关掉')
  assert.match(h.text(), /独立大肥鱼开关失败/)
  assert.doesNotMatch(h.text(), /已全部关掉/)
})

test('left/right controls use name-based animation requests so the host really moves', async () => {
  const h = harness(); await h.start(); await h.click('Claude·站立'); await h.click('向左走'); await h.click('向右走')
  const cues=h.calls.filter(c=>c.url.includes('/anim?'))
  assert.deepEqual(cues.map(c=>c.body),[
    { name: '自然走路', facing: 'left' }, { name: '自然走路', facing: 'right' },
  ])
  assert.ok(cues.every(c=>c.url.includes('pet=claude-dafeiyu&surface=any') && c.method==='POST'))
  assert.ok(cues.every(c=>!('url' in c.body)))
})
