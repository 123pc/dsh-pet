/**
 * 桌面事件薄壳的实际衔接测试，不启动 Electron 或触碰真实工作状态。
 * @module dsh-pet/src/shared/work-sequence-runtime.test
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { join } from 'node:path';
import * as sequence from './work-sequence.ts';
import * as pickers from './pickers.ts';

function sprite() {
  const context = vm.createContext({
    navigator: { platform: 'Win32' },
    BASE: '',
    config: {},
    console: { log() {}, error() {} },
    window: { setTimeout: () => 1, clearTimeout() {} },
    BUBBLE_DURATION_MS: 10000,
    S: {
      ...sequence,
      ...pickers,
      WORK_STATUS_INDEX: { thinking: 0, working: 1, result: 2, waiting: 3, success: 4, error: 5 },
    },
  });
  const root = process.env.DSH_PET_SEQUENCE_TEST_RUNTIME;
  const source = (file: string) =>
    readFileSync(
      root
        ? join(root, 'runtime/electron-helper', file)
        : new URL('../../runtime/electron-helper/' + file, import.meta.url),
      'utf8',
    );
  vm.runInContext(source('sprite.js'), context);
  vm.runInContext(source('events.js'), context);
  const proto = vm.runInContext('PetSprite.prototype', context);
  const history: string[] = [];
  const value = Object.assign(Object.create(proto), {
    pet: { id: 'test-lean', workStatusEnabled: true },
    frozen: false,
    prevWorkTick: 0,
    workPhase: 'closed',
    workState: null,
    workTimer: null,
    anim: 'idle',
    playback: null,
    dragState: { active: false },
    animations: {
      idle: ['idle'],
      turn: [],
      drag: [],
      clicks: ['click'],
      workSequence: { enter: 'enter', loops: ['typing', 'thinking'], exit: 'exit' },
      events: {
        workStatus: [
          ['typing', 'thinking'],
          ['typing', 'thinking'],
          ['typing', 'thinking'],
          ['typing', 'thinking'],
          'done',
          'error',
        ],
      },
    },
    stopMove() {},
    renderBubble() {},
    playOnce(name: string) {
      this.anim = name;
      history.push(name);
    },
    switchTo(name: string) {
      this.anim = name;
      history.push(name);
    },
  });
  return { value, history };
}

test('desktop ticks and ended form enter → work variations → exit → idle', () => {
  const { value: s, history } = sprite();
  s.onWorkTick({ state: 'thinking' }, 1);
  s.onWorkTick({ state: 'working', task: 'new progress' }, 2);
  assert.deepEqual(history, ['enter']);
  s.handleEnded();
  assert.ok(['typing', 'thinking'].includes(s.anim));
  const current = s.anim;
  s.onWorkTick({ state: 'result' }, 3);
  assert.equal(s.anim, current);
  s.handleEnded();
  assert.notEqual(s.anim, current);
  s.onWorkTick({ state: 'success' }, 4);
  assert.equal(s.anim, 'exit');
  s.onWorkTick({ state: null }, 5);
  s.handleEnded();
  assert.equal(s.anim, 'idle');
  assert.equal(history.filter((n) => n === 'enter').length, 1);
  assert.equal(history.filter((n) => n === 'exit').length, 1);
});

test('desktop short tasks and user interruptions retain the sequence guards', () => {
  const { value: s } = sprite();
  s.onWorkTick({ state: 'working' }, 1);
  s.onWorkTick({ state: null }, 2);
  assert.equal(s.anim, 'enter');
  s.handleEnded();
  assert.equal(s.anim, 'exit');
  s.onWorkTick({ state: 'working' }, 3);
  s.handleEnded();
  assert.equal(s.anim, 'enter');
  s.handleEnded();
  s.anim = 'click';
  assert.equal(s.resumeWorkStatusAnim(), true);
  assert.ok(['typing', 'thinking'].includes(s.anim));
  s.frozen = true;
  const before = s.anim;
  s.handleEnded();
  assert.equal(s.anim, before);
});
