import assert from 'node:assert/strict'
import { readFileSync, existsSync } from 'node:fs'
import { test } from 'node:test'
import { isEventAnim, rollKind } from '../../../dsh-pet/src/shared/pickers.ts'

const root = new URL('../', import.meta.url)
for (const [name, folder] of [['claude-dafeiyu', 'animation'], ['claude-dafeiyu-lean', 'lean-animation']]) {
  const config = JSON.parse(readFileSync(new URL(name + '-config.json', root)))
  const a = config.animations
  test(name + ': random idle cannot be trapped in an event or interaction loop', () => {
    for (const idle of a.idle) {
      assert.equal(isEventAnim(a.events, idle), false)
      assert.equal(a.drag.includes(idle) || a.clicks.includes(idle), false)
    }
    for (const category of a.categories) {
      for (const action of category.actions) assert.equal(isEventAnim(a.events, action), false)
    }
  })
  test(name + ': every configured animation exists', () => {
    const names = [a.idle, a.turn, a.drag, a.clicks, a.moves.actions.map(x => x.name),
      ...a.categories.map(c => c.actions), ...Object.values(a.events)].flat(2)
    for (const anim of names) assert.ok(existsSync(new URL(folder + '/' + anim + '.webm', root)), anim)
  })
}

test('runtime can roam with approved walking and only selects populated action pools', () => {
  const config = JSON.parse(readFileSync(new URL('claude-dafeiyu-config.json', root)))
  const counts = { idle: 0, turn: 0, move: 0, action: 0 }
  for (let i = 0; i < 100; i++) counts[rollKind((i + 0.5) / 100, config.animationWeights)]++
  assert.ok(counts.idle > 0)
  assert.ok(counts.move > 0)
  assert.ok(config.animations.moves.actions.some(row=>row.name==='自然走路'))
  assert.equal(counts.action > 0, config.animations.categories.length > 0)
})

test('106 upstream actions are tracked and pending artwork never enters runtime pools', () => {
  const upstream = JSON.parse(readFileSync(new URL('sources/action-catalogue.json', root)))
  const config = JSON.parse(readFileSync(new URL('claude-dafeiyu-config.json', root)))
  const a = config.animations
  const names = new Set([a.idle,a.turn,a.drag,a.clicks,a.moves.actions.map(x=>x.name),
    ...a.categories.map(c=>c.actions),...Object.values(a.events)].flat(2))
  assert.equal(upstream.count, 106)
  const registry = JSON.parse(readFileSync(new URL('sources/action-library/actions.json',root)))
  assert.equal(registry.actions.length,106)
  for (const { name,status } of registry.actions) assert.equal(names.has(name), ['self-reviewed','user-approved'].includes(status),name)
  assert.equal(names.has('自然走路'), true)
  assert.equal(registry.walk.status,'user-approved')
  assert.equal(a.events.balance.length,6)
  assert.equal(a.events.workStatus.length,6)
})

test('installed action media matches reviewed renders, excluding pending drafts and retired rig files', () => {
  const manifest = JSON.parse(readFileSync(new URL('manifest.json', root)))
  const status = JSON.parse(readFileSync(new URL('sources/review-status.json', root)))
  assert.equal(status.draftsInstalled, false)
  assert.ok(status.approvedActions.includes('自然走路'))
  const registry=JSON.parse(readFileSync(new URL('sources/action-library/actions.json',root)))
  const reviewed=new Map(registry.actions.filter(row=>['self-reviewed','user-approved'].includes(row.status)).map(row=>[row.name,row]))
  const companion=JSON.parse(readFileSync(new URL('sources/lean-v2/registry.json',root)))
  for(const row of companion.actions)reviewed.set(row.name,{...row,folder:'lean-animation'})
  reviewed.set('托腮·轻声回应',{id:'lean-hum',folder:'lean-animation'})
  reviewed.set('安静站立·眨眼呼吸',{id:'standing-rest'})
  for (const file of manifest.files) {
    const name=file.source.split('/').at(-1).replace(/\.webm$/,'')
    assert.ok(file.source.endsWith('-config.json') || /\/review\w+\.webm$/.test(file.source) || name==='自然走路' || reviewed.has(name), file.source)
    if(reviewed.has(name))assert.deepEqual(readFileSync(new URL(file.source,root)),readFileSync(new URL('preview/actions/'+reviewed.get(name).id+'/clip.webm',root)))
    assert.equal(file.source.includes('keyframes'), false)
  }
})
