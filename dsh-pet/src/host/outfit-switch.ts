/**
 * 一次换装只切换两个现有实例的显示状态；先准备所有文件，失败时恢复原文。
 * 与配置请求共用宿主串行队列，成功后由调用方统一发配置信号和重载。
 * @module dsh-pet/src/host/outfit-switch
 */
import * as fs from 'node:fs/promises';
import { dirname } from 'node:path';
import { randomUUID } from 'node:crypto';
import { readAllConfig, userConfigUnparsable, findPetInstance, type ConfigPaths } from './config.ts';
import { resolveConfigLayer } from './routes/config/layer.ts';
import { listOutfits } from './outfit-catalog.ts';

type Merged = Record<string, Record<string, unknown>>;
/** 单层改动：文件路径由配置扫描定位，绝不由请求体拼接。 */
export interface OutfitLayer {
  path: string;
  value: Record<string, unknown>;
}
export type OutfitFailureReason =
  | 'pet-required'
  | 'unknown-pet'
  | 'unknown-outfit'
  | 'pet-not-displayed'
  | 'config-unparsable'
  | 'config-changed'
  | 'rollback-error';

/** 路由可直接转成现有业务失败格式。 */
export class OutfitError extends Error {
  declare reason: OutfitFailureReason;
  constructor(reason: OutfitFailureReason, message: string) {
    super(message);
    this.reason = reason;
  }
}

/** 多文件提交：暂存文件与目标同目录；正常异常回滚，不能宣称抗进程崩溃的数据库事务。 */
export async function writeOutfitLayers(layers: OutfitLayer[], io = fs): Promise<void> {
  const staged: Array<{ path: string; temp: string; before: Buffer | null }> = [];
  const committed: typeof staged = [];
  try {
    for (const layer of layers) {
      let before: Buffer | null;
      try {
        before = await io.readFile(layer.path);
      } catch (e) {
        if ((e as NodeJS.ErrnoException).code !== 'ENOENT') throw e;
        before = null;
      }
      await io.mkdir(dirname(layer.path), { recursive: true });
      const item = { path: layer.path, temp: layer.path + '.outfit-' + randomUUID() + '.tmp', before };
      staged.push(item);
      await io.writeFile(item.temp, JSON.stringify(layer.value, null, 2) + '\n', 'utf8');
    }
    // 手工编辑也不能被准备阶段读到的旧版本覆盖。
    for (const item of staged) {
      let current: Buffer | null;
      try {
        current = await io.readFile(item.path);
      } catch (e) {
        if ((e as NodeJS.ErrnoException).code !== 'ENOENT') throw e;
        current = null;
      }
      if (current === null ? item.before !== null : item.before === null || !current.equals(item.before))
        throw new OutfitError('config-changed', '配置刚被其它操作修改，请重试');
    }
    for (const item of staged) {
      await io.rename(item.temp, item.path);
      committed.push(item);
    }
  } catch (error) {
    let rollbackFailed = false;
    for (const item of committed.reverse()) {
      try {
        if (item.before === null) await io.unlink(item.path);
        else await io.writeFile(item.path, item.before);
      } catch {
        rollbackFailed = true;
      }
    }
    if (rollbackFailed) throw new OutfitError('rollback-error', '换装失败，部分配置未能恢复，请检查配置文件');
    throw error;
  } finally {
    for (const item of staged) {
      try {
        await io.unlink(item.temp);
      } catch {
        /* 已提交或准备失败时可能不存在 */
      }
    }
  }
}

/** 验证候选后切换；保留名称、独立记忆、完整动作库和无关实例配置。 */
export async function switchOutfit(
  paths: ConfigPaths,
  petId: string,
  targetId: string,
): Promise<{ merged: Merged; changed: boolean }> {
  if (!petId || !targetId) throw new OutfitError('pet-required', '需要指定当前桌宠与目标形态');
  const merged = readAllConfig(paths),
    source = findPetInstance(merged, petId),
    target = findPetInstance(merged, targetId);
  if (!source) throw new OutfitError('unknown-pet', '找不到当前桌宠');
  if (!target || !listOutfits(merged, petId).some((choice) => choice.id === targetId))
    throw new OutfitError('unknown-outfit', '目标形态未安装或不属于这组换装');
  if (petId === targetId) return { merged, changed: false };
  if (!['web', 'desktop', 'both'].includes(String(source.pet.display)))
    throw new OutfitError('pet-not-displayed', '当前桌宠未显示，不能从它发起换装');
  const edits = new Map<string, { existing: Record<string, unknown>; pets: Record<string, unknown>[] }>();
  const layerFor = (hit: typeof source) => {
    if (hit.entry === 'main' && userConfigUnparsable(paths))
      throw new OutfitError('config-unparsable', '主配置无法解析，未执行换装');
    const resolved = resolveConfigLayer(
      {
        configPaths: paths,
        userConfigPath: paths.userFile,
        userRoot: dirname(paths.userFile),
        petConfigDir: paths.petDir,
      },
      hit.entry,
    );
    if (!resolved.ok || (hit.entry !== 'main' && !resolved.layer.existing))
      throw new OutfitError('config-unparsable', '形态配置无法解析，未执行换装');
    const { path, existing } = resolved.layer;
    if (!edits.has(path)) {
      const rawPets = Array.isArray(existing?.pets) ? existing.pets : hit.conf.pets;
      const pets = (rawPets as Record<string, unknown>[]).map((p) => {
        const copy = { ...p };
        delete copy.outfits;
        return copy;
      });
      edits.set(path, { existing: existing ?? {}, pets });
    }
    const layer = edits.get(path)!;
    const i = layer.pets.findIndex((p) => p.id === hit.pet.id);
    if (i < 0) throw new OutfitError('config-changed', '桌宠配置已变化，请重试');
    return { layer, i };
  };
  const from = layerFor(source),
    to = layerFor(target);
  from.layer.pets[from.i] = { ...from.layer.pets[from.i], display: 'none' };
  const targetVisible = ['web', 'desktop', 'both'].includes(String(target.pet.display));
  const display = targetVisible && target.pet.display !== source.pet.display ? 'both' : source.pet.display;
  to.layer.pets[to.i] = {
    ...to.layer.pets[to.i],
    display,
    ...(!targetVisible ? { size: source.pet.size, position: source.pet.position } : {}),
  };
  await writeOutfitLayers(
    [...edits].map(([path, layer]) => ({ path, value: { ...layer.existing, pets: layer.pets } })),
  );
  return { merged: readAllConfig(paths), changed: true };
}
