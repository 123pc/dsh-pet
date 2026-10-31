/**
 * @generated 素材目录的构建入口：校验社区角色清单并复制运行所需文件，不触碰用户目录。
 * 由 npm run build 调用，assets/bundled-claude/ 可随时从源清单重建。
 * @module dsh-pet/scripts/prepare-pet-pack
 */
import { createHash } from 'node:crypto';
import { copyFileSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const source = join(root, '..', 'community-pets', 'claude-dafeiyu');
const destination = join(root, 'assets', 'bundled-claude');
const manifest = JSON.parse(readFileSync(join(source, 'manifest.json'), 'utf8'));
if (manifest.files.length !== 121) throw new Error('角色清单必须包含两份配置与 119 段视频');
for (const item of manifest.files) {
  const valid =
    /^claude-dafeiyu(-lean)?-config\.json$/.test(item.source) ||
    /^(animation|lean-animation)\/[\p{L}\p{N} _·，-]+\.webm$/u.test(item.source);
  if (
    !valid ||
    createHash('sha256')
      .update(readFileSync(join(source, item.source)))
      .digest('hex') !== item.sha256
  )
    throw new Error('角色素材无效：' + item.source);
}
for (const name of ['manifest.json', ...manifest.files.map((item) => item.source)]) {
  mkdirSync(dirname(join(destination, name)), { recursive: true });
  copyFileSync(join(source, name), join(destination, name));
}
console.log('[prepare-pet-pack] verified and bundled 119 transparent animations and 2 configs');
