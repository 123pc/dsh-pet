/**
 * 动作菜单整理回归：重复槽位与触发方式只保留一个入口，不删减可点播动作。
 * @module dsh-pet/src/shared/menu.test
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildMenuTree, type MenuNode } from './menu.ts';
import type { Animations } from './types.ts';

function names(tree: MenuNode[]): string[] {
  return tree.flatMap((n) => ('children' in n ? names(n.children) : n.anim ? [n.anim] : []));
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
