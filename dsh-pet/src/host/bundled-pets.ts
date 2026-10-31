/**
 * 内置角色首次初始化：校验发行清单，只补充用户目录中缺失的配置与视频。
 * 不覆盖已有文件，不运行安装脚本，不访问网络；配置仍由现有配置层读取和编辑。
 * 新目录默认显示站立形态，已有配置的用户通过换装自行选择新增形态。
 * @module dsh-pet/src/host/bundled-pets
 */
import { createHash, randomUUID } from 'node:crypto';
import {
  existsSync,
  linkSync,
  lstatSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  unlinkSync,
  writeFileSync,
} from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { readAllConfig, type ConfigPaths } from './config.ts';

/** 完成校验的发行文件；内容仅来自包内清单。 */
interface PreparedFile {
  /** 用户目录中的相对目标。 */
  target: string;
  /** 校验后的源内容。 */
  data: Buffer;
}

/** 初始化结果，不包含用户配置内容。 */
export interface BundledPetResult {
  /** 本次新增的文件数。 */
  added: number;
  /** 本次保留的已有文件数。 */
  preserved: number;
  /** 是否为没有用户主配置和文件宠物的新目录。 */
  fresh: boolean;
}

/** 拒绝通过用户素材目录内的符号链接写到其它目录。 */
function safeTarget(root: string, relative: string): string {
  let path = resolve(root);
  for (const part of ['', ...relative.split('/')]) {
    path = part ? join(path, part) : path;
    if (lstatSync(path, { throwIfNoEntry: false })?.isSymbolicLink()) throw new Error('角色目标包含目录链接：' + path);
  }
  return path;
}

/** 完整校验所有源文件后才允许向用户目录写入。 */
function prepareFiles(sourceRoot: string): PreparedFile[] {
  const manifest = JSON.parse(readFileSync(join(sourceRoot, 'manifest.json'), 'utf8')) as {
    files?: { source: string; target: string; sha256: string }[];
  };
  if (!Array.isArray(manifest.files) || manifest.files.length === 0) throw new Error('内置角色清单为空');
  const seen = new Set<string>();
  return manifest.files.map((file) => {
    const config = /^claude-dafeiyu(-lean)?-config\.json$/.test(file.source);
    const media = /^(animation|lean-animation)\/[\p{L}\p{N} _·，-]+\.webm$/u.test(file.source);
    const expected = file.source
      .replace(/^animation\//, 'claude-dafeiyu-animation/')
      .replace(/^lean-animation\//, 'claude-dafeiyu-lean-animation/');
    if ((!config && !media) || file.target !== expected || seen.has(file.target)) throw new Error('内置角色路径无效');
    seen.add(file.target);
    const data = readFileSync(join(sourceRoot, file.source));
    if (createHash('sha256').update(data).digest('hex') !== file.sha256)
      throw new Error('内置角色校验失败：' + file.source);
    if (config) {
      const parsed = JSON.parse(data.toString('utf8')) as { pets?: unknown[] };
      if (!Array.isArray(parsed.pets) || parsed.pets.length === 0) throw new Error('内置角色配置无效：' + file.source);
    }
    return { target: file.target, data };
  });
}

/** 用同目录临时文件及排他硬链接发布完整内容；已有目标永不替换。 */
function addFile(path: string, data: Buffer | string): boolean {
  if (existsSync(path)) return false;
  mkdirSync(dirname(path), { recursive: true });
  const temporary = path + '.claude-' + randomUUID() + '.tmp';
  try {
    writeFileSync(temporary, data, { flag: 'wx' });
    try {
      linkSync(temporary, path);
      return true;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'EEXIST') return false;
      throw error;
    }
  } finally {
    if (existsSync(temporary)) unlinkSync(temporary);
  }
}

/** 检查用户是否已经配置主角色或安装其它文件宠物。 */
function isFresh(paths: ConfigPaths): boolean {
  if (existsSync(paths.userFile) || (paths.legacyUserFile && existsSync(paths.legacyUserFile))) return false;
  return !existsSync(paths.petDir) || !readdirSync(paths.petDir).some((name) => /-config\.(json|jsonc)$/.test(name));
}

/**
 * 补齐内置角色；新目录隐藏原版并启用站立，已有目录保留现状且不自动增加可见角色。
 * @param paths - 现有宿主配置路径。
 * @param sourceRoot - 由发布流程生成的包内角色目录。
 * @returns 新增和保留文件数；源码尚未构建角色目录时返回零。
 * @throws {Error} 发行清单损坏、路径含链接或用户目录不可写时抛出。
 */
export function ensureBundledPets(paths: ConfigPaths, sourceRoot: string): BundledPetResult {
  if (!existsSync(join(sourceRoot, 'manifest.json'))) return { added: 0, preserved: 0, fresh: false };
  const files = prepareFiles(sourceRoot);
  for (const file of files) safeTarget(paths.petDir, file.target);
  const fresh = isFresh(paths);
  const main = fresh ? readAllConfig(paths).main : undefined;
  const result = { added: 0, preserved: 0, fresh };
  // 最后发布配置：复制视频中途失败不会留下指向不完整角色的新增配置。
  files.sort((a, b) => Number(a.target.endsWith('.json')) - Number(b.target.endsWith('.json')));
  for (const file of files) {
    let data = file.data;
    if (file.target.endsWith('-config.json')) {
      const config = JSON.parse(data.toString('utf8')) as { pets: Record<string, unknown>[] };
      for (const pet of config.pets) {
        if (!fresh) pet.display = 'none';
        pet.whisperEnabled = false;
        pet.balanceEnabled = false;
      }
      data = Buffer.from(JSON.stringify(config, null, 2) + '\n');
    }
    const path = safeTarget(paths.petDir, file.target);
    if (addFile(path, data)) result.added++;
    else result.preserved++;
  }
  if (main) {
    const pets = (main.pets as Record<string, unknown>[]).map((pet) => ({
      ...pet,
      display: 'none',
      whisperEnabled: false,
      balanceEnabled: false,
    }));
    addFile(paths.userFile, JSON.stringify({ pets }, null, 2) + '\n');
  }
  return result;
}
