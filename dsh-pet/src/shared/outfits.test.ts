/** @module dsh-pet/src/shared/outfits.test */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { outfitMenuBranch } from './menu.ts';
import { requestOutfitChange } from './outfits.ts';

test('outfit menu hides when unavailable and marks the current installed choice', () => {
  assert.equal(outfitMenuBranch(), null);
  assert.equal(outfitMenuBranch([{ id: 'a', label: 'A', current: true }]), null);
  const menu = outfitMenuBranch([
    { id: 'a', label: 'Original', current: true },
    { id: 'b', label: 'Costume', current: false },
  ])!;
  assert.equal(menu.label, '换装');
  assert.deepEqual(menu.children, [
    { label: 'Original', action: 'set-outfit', outfit: 'a', hint: '当前' },
    { label: 'Costume', action: 'set-outfit', outfit: 'b' },
  ]);
});

test('one native request performs the complete switch and HTTP 200 business failures are surfaced', async () => {
  const calls: unknown[] = [];
  const result = await requestOutfitChange('/plugin', 'a', 'b', async (input, init) => {
    calls.push({ input, body: JSON.parse(String(init?.body)) });
    return new Response(JSON.stringify({ main: { pets: [] } }));
  });
  assert.deepEqual(calls, [{ input: '/plugin/pet-outfit', body: { id: 'a', target: 'b' } }]);
  assert.ok(result.main);
  await assert.rejects(
    requestOutfitChange(
      '/plugin',
      'a',
      'b',
      async () => new Response(JSON.stringify({ ok: false, message: 'not installed' })),
    ),
    /not installed/,
  );
  await assert.rejects(
    requestOutfitChange('/plugin', 'a', 'b', async () => new Response('', { status: 500 })),
    /500/,
  );
});
