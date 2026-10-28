/**
 * 已安装形态的换装目录；角色包通过可选 outfit 元数据关联原版条目。
 * 不识别角色 ID，不把无关种类或未安装形态加入菜单。
 * @module dsh-pet/src/host/outfit-catalog
 */

/** 角色包声明的换装关系；base 是已安装配置的条目 key。 */
export interface OutfitMetadata {
  base: string;
  label: string;
}
/** 由宿主派生的菜单候选，不写回角色文件。 */
export interface OutfitChoice {
  id: string;
  label: string;
  current: boolean;
}
type Merged = Record<string, Record<string, unknown>>;

/** 与文件条目标识同口径；不允许路径、控制字符或超长标识。 */
export function outfitMetadata(value: unknown): OutfitMetadata | undefined {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return;
  const o = value as Record<string, unknown>;
  // eslint-disable-next-line no-control-regex -- 禁止控制字符进入配置条目标识。
  if (typeof o.base !== 'string' || !o.base || o.base.length > 64 || /[<>:"/\\|?*\x00-\x1f]/.test(o.base)) return;
  if (typeof o.label !== 'string' || !o.label.trim() || o.label.length > 80) return;
  return { base: o.base, label: o.label.trim() };
}

/** 仅一层 base 关系，拒绝循环或多层换装继承；旧种类没有关联时不出现入口。 */
export function listOutfits(merged: Merged, petId: string): OutfitChoice[] {
  const current = Object.entries(merged).find(
    ([, conf]) => Array.isArray(conf.pets) && conf.pets.some((p) => p && String(p.id) === petId),
  );
  if (!current) return [];
  const [entry, conf] = current;
  const own = outfitMetadata(conf.outfit);
  const base = own?.base ?? entry;
  if (!merged[base] || merged[base].outfit !== undefined) return [];
  const related = Object.entries(merged).filter(([key, c]) => key === base || outfitMetadata(c.outfit)?.base === base);
  if (related.length < 2) return [];
  return related.flatMap(([key, c]) => {
    const pets = Array.isArray(c.pets) ? (c.pets as Record<string, unknown>[]) : [];
    const label = key === base ? '原版形态' : outfitMetadata(c.outfit)!.label;
    return pets
      .filter((p) => typeof p.id === 'string' && p.id)
      .map((p) => ({
        id: String(p.id),
        label: pets.length > 1 ? `${label} · ${String(p.name || p.id)}` : label,
        current: p.id === petId,
      }));
  });
}
