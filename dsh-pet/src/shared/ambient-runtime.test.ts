/**
 * 用假时钟驱动桌面真实播放薄壳，验证待机中途触发和办公抢占。
 * @module dsh-pet/src/shared/ambient-runtime.test
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import vm from 'node:vm';
import { AmbientDirector } from './ambient.ts';
import * as work from './work-sequence.ts';
import * as pickers from './pickers.ts';
import { isNoMirrorAnimation } from './menu.ts';
import type { Animations } from './types.ts';

function setup(office = false, legacy = false) {
  let now = 0;
  const animations: Animations = {
    idle: ['idle'],
    turn: [],
    drag: [],
    clicks: ['click'],
    moves: { default: {}, actions: [] },
    categories: [{ id: 'play', weight: 1, actions: ['A', 'B'] }],
    events: {
      balance: ['event'],
      workStatus: [
        ['typing', 'thinking'],
        ['typing', 'thinking'],
        ['typing', 'thinking'],
        ['typing', 'thinking'],
        'done',
        'error',
      ],
    },
    workSequence: { enter: 'enter', loops: ['typing', 'thinking'], exit: 'exit' },
    ambient: {
      windowSec: 180,
      minEpisodes: 1,
      maxEpisodes: 1,
      minGapSec: 25,
      edgeSec: 12,
      chainChance: 1,
      chains: [
        {
          id: 'test',
          label: 'test',
          weight: 1,
          steps: (office ? ['enter', 'typing', 'exit'] : ['A', 'B']).map((name) => ({ name })),
        },
      ],
    },
  };
  if (legacy) {
    delete animations.ambient;
    delete animations.workSequence;
  }
  const ctx = vm.createContext({
    navigator: { platform: 'Win32' },
    BASE: '',
    config: {},
    console: { log() {}, error() {} },
    performance: { now: () => now },
    window: { setTimeout: () => 1, clearTimeout() {} },
    BUBBLE_DURATION_MS: 10000,
    S: {
      AmbientDirector,
      ...work,
      ...pickers,
      isNoMirrorAnimation,
      WORK_STATUS_INDEX: { thinking: 0, working: 1, result: 2, waiting: 3, success: 4, error: 5 },
    },
  });
  const root = process.env.DSH_PET_SEQUENCE_TEST_RUNTIME;
  for (const file of ['sprite.js', 'sprite/playback.js', 'sprite/motion.js', 'events.js'])
    vm.runInContext(
      readFileSync(
        root
          ? join(root, 'runtime/electron-helper', file)
          : new URL('../../runtime/electron-helper/' + file, import.meta.url),
        'utf8',
      ),
      ctx,
    );
  const history: Array<{ name: string; once: boolean }> = [];
  const s = Object.assign(Object.create(vm.runInContext('PetSprite.prototype', ctx)), {
    pet: { id: 'test', workStatusEnabled: true, fixedEnabled: false },
    animations,
    ambient: legacy ? null : new AmbientDirector(animations, 0, () => 0.05),
    ambientDispatch: false,
    workPhase: 'closed',
    workState: null,
    prevWorkTick: 0,
    workTimer: null,
    frozen: false,
    anim: 'idle',
    once: true,
    throwRef: null,
    moveRef: null,
    moveToken: 0,
    pending: null,
    menuOpen: false,
    chatOpen: false,
    dragState: { active: false },
    playback: null,
    stopPosFollow() {},
    renderBubble() {},
    switchTo(name: string, once: boolean) {
      this.anim = name;
      this.once = once;
      history.push({ name, once });
    },
  });
  return {
    s,
    history,
    setTime: (time: number) => {
      now = time;
    },
  };
}

test('the clock interrupts a looping idle at 19.8s and finishes exactly one ordered activity', () => {
  const { s, history, setTime } = setup();
  s.playIdle();
  assert.equal(s.once, false);
  setTime(s.ambient.snapshot().due[0]);
  s.tickAmbient();
  assert.equal(s.anim, 'A');
  s.handleEnded();
  assert.equal(s.anim, 'B');
  s.handleEnded();
  assert.equal(s.anim, 'idle');
  assert.equal(s.once, false);
  assert.deepEqual(
    history.map((x) => x.name),
    ['idle', 'A', 'B', 'idle'],
  );
  s.tickAmbient();
  assert.equal(history.length, 4);
});

test('a real manual stop cancels the remaining chain and never resumes its next step', () => {
  const { s, setTime } = setup();
  setTime(s.ambient.snapshot().due[0]);
  s.tickAmbient();
  s.stopMove();
  assert.equal(s.ambient.running, false);
  assert.equal(s.ambient.ended('A', 22000, false), null);
});

test('autonomous laptop steps retain props; real work takes over without reopening the computer', () => {
  const { s, history, setTime } = setup(true);
  setTime(s.ambient.snapshot().due[0]);
  s.tickAmbient();
  assert.equal(s.anim, 'enter');
  assert.equal(s.workPhase, 'opening');
  s.handleEnded();
  assert.equal(s.anim, 'typing');
  assert.equal(s.workPhase, 'open');
  s.onWorkTick({ state: 'working' }, 1);
  assert.equal(s.ambient.running, false);
  assert.equal(s.anim, 'typing');
  s.handleEnded();
  assert.ok(['typing', 'thinking'].includes(s.anim));
  assert.equal(history.filter((x) => x.name === 'enter').length, 1);
  s.onWorkTick({ state: null }, 2);
  assert.equal(s.anim, 'exit');
  s.handleEnded();
  assert.equal(s.workPhase, 'closed');
});

test('an unmodified legacy pet keeps work-status rotation and event return without an ambient director', () => {
  const { s, history } = setup(false, true);
  assert.equal(s.ambient, null);
  s.onWorkTick({ state: 'working' }, 1);
  assert.ok(['typing', 'thinking'].includes(s.anim));
  assert.equal(s.once, true);
  const first = s.anim;
  s.handleEnded();
  assert.ok(['typing', 'thinking'].includes(s.anim));
  assert.notEqual(s.anim, first);
  s.onWorkTick({ state: 'success' }, 2);
  assert.equal(s.anim, 'done');
  s.handleEnded();
  assert.equal(s.anim, 'idle');
  assert.equal(s.once, true);
  assert.equal(
    history.some(({ name }) => name === 'enter' || name === 'exit'),
    false,
  );
});
