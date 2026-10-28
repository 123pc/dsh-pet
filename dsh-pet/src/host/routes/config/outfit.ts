/**
 * 原生换装：宿主串行执行两层可见性切换，成功后统一广播与重载。
 * @module dsh-pet/src/host/routes/config/outfit
 */
import { switchOutfit, OutfitError } from '../../outfit-switch.ts';
import type { RouteResult } from '../../http.ts';
import type { PetRouteDeps, RouteInput } from '../types.ts';
import { failResult, invalidJson, methodNotAllowed, okResult } from '../result.ts';

/** 仅接受宿主目录中同组已安装实例；请求不提供磁盘路径。 */
export async function setPetOutfit(deps: PetRouteDeps, input: RouteInput): Promise<RouteResult> {
  if (input.method !== 'POST') return methodNotAllowed();
  let value: unknown;
  try {
    value = JSON.parse(input.body ?? '');
  } catch {
    return invalidJson();
  }
  if (!value || typeof value !== 'object' || Array.isArray(value))
    return failResult('bad-request', '需要 id 与 target');
  const payload = value as Record<string, unknown>;
  const id = typeof payload.id === 'string' ? payload.id.trim() : '';
  const target = typeof payload.target === 'string' ? payload.target.trim() : '';
  try {
    const result = await switchOutfit(deps.configPaths, id, target);
    if (result.changed) {
      deps.lock.release({ petId: id, force: true });
      deps.lock.release({ petId: target, force: true });
      deps.state.writeSection('config', {});
      void deps.requestRestart();
    }
    return okResult(result.merged);
  } catch (error) {
    if (error instanceof OutfitError) return failResult(error.reason, error.message);
    return failResult('generate-error', '换装配置写入失败，请重试');
  }
}
