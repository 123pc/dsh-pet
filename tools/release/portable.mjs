// Isolate portable data before the app locks its profile or creates any window.
// Electron waits for this module's top-level await before emitting app.ready;
// a fire-and-forget CJS import would apply the DPI switch too late.
import { createRequire } from 'node:module';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mkdirSync } from 'node:fs';

const require = createRequire(import.meta.url);
const { app } = require('electron');
const data = resolve(dirname(fileURLToPath(import.meta.url)), '../../../data');
process.env.DSH_HOME = data;
for (const [name, relative] of [['appData', 'appdata'], ['userData', 'electron'], ['sessionData', 'session']]) {
  const directory = join(data, relative);
  mkdirSync(directory, { recursive: true });
  app.setPath(name, directory);
}
if (process.env.DSH_PET_DPI_PROBE === '1') {
  require('./runtime/electron-helper/main.js');
} else {
  await import('./lib/app.js');
}
