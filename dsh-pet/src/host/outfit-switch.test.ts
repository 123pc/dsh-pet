/**
 * 原生换装回归：独立形态动作、两层写入回滚、旧配置与多宠物隔离。
 * @module dsh-pet/src/host/outfit-switch.test
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readAllConfig, readUserConfig, type ConfigPaths } from './config.ts';
import { listOutfits } from './outfit-catalog.ts';
import { switchOutfit, writeOutfitLayers } from './outfit-switch.ts';

const pet = (id: string, display = 'web', size = 240) => ({
  id,
  name: id,
  size,
  display,
  balanceEnabled: false,
  whisperEnabled: false,
  workStatusEnabled: false,
  fixedEnabled: false,
  position: { corner: 'top-right', marginX: 20, marginY: 40 },
});
function setup() {
  const dir = mkdtempSync(join(tmpdir(), 'dsh-outfit-test-'));
  const paths: ConfigPaths = {
    defaultFile: fileURLToPath(new URL('../../assets/config.jsonc', import.meta.url)),
    userFile: join(dir, 'main-config.jsonc'),
    petDir: join(dir, 'pet'),
  };
  mkdirSync(paths.petDir);
  const animations = {
    idle: ['skin-idle'],
    turn: [],
    drag: [],
    clicks: [],
    moves: { default: {}, actions: [] },
    categories: [],
    events: { balance: ['balance'] },
  };
  const main = { pets: [pet('original'), pet('other')], whisperPrompt: 'keep main', extraField: { keep: true } };
  const pack = {
    pets: [pet('costume', 'none', 330), pet('costume-other', 'none')],
    outfit: { base: 'main', label: 'Costume' },
    animations,
    whisperPrompt: 'keep costume',
  };
  const packFile = join(paths.petDir, 'costume-config.jsonc');
  writeFileSync(paths.userFile, JSON.stringify(main));
  writeFileSync(packFile, JSON.stringify(pack));
  return {
    dir,
    paths,
    packFile,
    main,
    pack,
    cleanup() {
      assert.ok(resolve(dir).startsWith(resolve(tmpdir())));
      rmSync(dir, { recursive: true, force: true });
    },
  };
}

test('only explicitly related installed shapes enter the native outfit menu; legacy pets stay unchanged', () => {
  const f = setup();
  try {
    const legacy = { main: { pets: [pet('original')] }, unrelated: { pets: [pet('unrelated')] } };
    assert.deepEqual(listOutfits(legacy, 'original'), []);
    writeFileSync(join(f.paths.petDir, 'unrelated-config.json'), JSON.stringify({ pets: [pet('unrelated')] }));
    const merged = readAllConfig(f.paths),
      choices = listOutfits(merged, 'original');
    assert.deepEqual(
      choices.map((c) => c.id),
      ['original', 'other', 'costume', 'costume-other'],
    );
    assert.equal(choices.filter((c) => c.current).length, 1);
    assert.ok((merged.main.pets as Array<{ outfits: unknown }>)[0].outfits);
    assert.deepEqual(
      listOutfits({ ...legacy, loop: { outfit: { base: 'loop', label: 'Loop' }, pets: [pet('loop')] } }, 'loop'),
      [],
    );
  } finally {
    f.cleanup();
  }
});

test('switch and return retain names, independent animation pools, unrelated pets and advanced settings', async () => {
  const f = setup();
  try {
    const result = await switchOutfit(f.paths, 'original', 'costume');
    assert.equal(result.changed, true);
    const main = readUserConfig(f.paths)!;
    const pack = JSON.parse(readFileSync(f.packFile, 'utf8'));
    assert.equal((main.pets as ReturnType<typeof pet>[])[0].display, 'none');
    assert.deepEqual((main.pets as unknown[])[1], f.main.pets[1]);
    assert.equal(pack.pets[0].display, 'web');
    assert.equal(pack.pets[0].name, 'costume');
    assert.equal(pack.pets[0].size, 240);
    assert.deepEqual(pack.animations, f.pack.animations);
    assert.deepEqual(pack.pets[1], f.pack.pets[1]);
    assert.deepEqual(main.extraField, { keep: true });
    assert.equal(pack.whisperPrompt, 'keep costume');
    assert.equal('outfits' in pack.pets[0], false);
    await switchOutfit(f.paths, 'costume', 'original');
    const returned = readUserConfig(f.paths)!;
    assert.equal((returned.pets as ReturnType<typeof pet>[])[0].display, 'web');
    assert.equal(JSON.parse(readFileSync(f.packFile, 'utf8')).pets[0].display, 'none');
  } finally {
    f.cleanup();
  }
});

test('same choice is a no-op, cross-group and hidden-source changes cannot modify files', async () => {
  const f = setup();
  try {
    const before = [readFileSync(f.paths.userFile), readFileSync(f.packFile)];
    assert.equal((await switchOutfit(f.paths, 'original', 'original')).changed, false);
    for (const [source, target] of [
      ['original', 'missing'],
      ['costume', 'original'],
      ['../bad', 'original'],
    ])
      await assert.rejects(switchOutfit(f.paths, source, target));
    assert.deepEqual(readFileSync(f.paths.userFile), before[0]);
    assert.deepEqual(readFileSync(f.packFile), before[1]);
  } finally {
    f.cleanup();
  }
});

test('an already visible destination retains its own size and merges display surfaces', async () => {
  const f = setup();
  try {
    f.pack.pets[0].display = 'desktop';
    writeFileSync(f.packFile, JSON.stringify(f.pack));
    await switchOutfit(f.paths, 'original', 'costume');
    const actual = JSON.parse(readFileSync(f.packFile, 'utf8')).pets[0];
    assert.equal(actual.display, 'both');
    assert.equal(actual.size, 330);
  } finally {
    f.cleanup();
  }
});

test('failure committing the second layer restores the first file byte-for-byte and removes staging files', async () => {
  const f = setup();
  try {
    const before = [readFileSync(f.paths.userFile), readFileSync(f.packFile)];
    let renames = 0;
    const io = {
      ...fs,
      rename: async (from: Parameters<typeof fs.rename>[0], to: Parameters<typeof fs.rename>[1]) => {
        if (++renames === 2) throw new Error('injected write failure');
        return fs.rename(from, to);
      },
    };
    await assert.rejects(
      writeOutfitLayers(
        [
          { path: f.paths.userFile, value: { changed: true } },
          { path: f.packFile, value: { changed: true } },
        ],
        io,
      ),
      /injected/,
    );
    assert.deepEqual(readFileSync(f.paths.userFile), before[0]);
    assert.deepEqual(readFileSync(f.packFile), before[1]);
    assert.equal(
      [...readdirSync(f.dir), ...readdirSync(f.paths.petDir)].some((n) => n.endsWith('.tmp')),
      false,
    );
  } finally {
    f.cleanup();
  }
});
