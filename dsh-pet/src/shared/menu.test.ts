/**
 * 动作菜单整理回归：重复槽位与触发方式只保留一个入口，不删减可点播动作。
 * @module dsh-pet/src/shared/menu.test
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildMenuTree, type MenuNode } from './menu.ts';
import { animationNames } from '../host/anim.ts';
import type { Animations } from './types';

function names(tree: MenuNode[]): string[] {
  return tree.flatMap((n) => ('children' in n ? names(n.children) : n.anim ? [n.anim] : []));
}

for (const form of ['claude-dafeiyu', 'claude-dafeiyu-lean']) {
  test(form + ': menu has exactly one entry per playable action and leaves config unchanged', () => {
    const config = JSON.parse(
      readFileSync(new URL('../../../community-pets/claude-dafeiyu/' + form + '-config.json', import.meta.url), 'utf8'),
    );
    const before = JSON.stringify(config);
    const actual = names(buildMenuTree(config.animations));
    assert.equal(actual.length, new Set(actual).size);
    assert.deepEqual([...actual].sort(), animationNames(config.animations).sort());
    assert.equal(JSON.stringify(config), before);
    if (form.endsWith('-lean')) {
      assert.equal(actual.length, 10);
      const tree = buildMenuTree(config.animations)[0];
      assert.ok('children' in tree);
      const office = tree.children.find((n) => n.label === '办公动作');
      assert.ok(office && 'children' in office);
      assert.equal(office.children.length, 5);
      assert.deepEqual(
        tree.children.map((n) => n.label),
        ['待机', '托腮小动作', '办公动作', '余额档位'],
      );
    }
  });
}

test('duplicates across categories and event slots merge; empty groups disappear', () => {
  const a: Animations = {
    idle: ['idle', 'idle'],
    turn: [],
    drag: ['tail'],
    clicks: ['tail'],
    moves: { default: {}, actions: [] },
    categories: [
      { id: '日常', weight: 1, actions: ['tail', 'tail'] },
      { id: '日常', weight: 1, actions: ['hair'] },
    ],
    events: {
      balance: ['reply', 'reply'],
      whisper: ['reply'],
      workStatus: [
        ['type', 'think'],
        ['type', 'think'],
      ],
    },
  };
  const tree = buildMenuTree(a);
  assert.deepEqual(names(tree), ['idle', 'tail', 'hair', 'reply', 'type', 'think']);
  assert.ok('children' in tree[0]);
  assert.equal(tree[0].children.filter((n) => n.label === '日常').length, 1);
  assert.deepEqual(buildMenuTree({ ...a, idle: [], drag: [], clicks: [], categories: [], events: {} }), []);
});
