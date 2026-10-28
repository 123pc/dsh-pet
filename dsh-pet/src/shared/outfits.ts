/**
 * 两端共用的换装请求；一次宿主操作完成，不在客户端分两次切显示。
 * @module dsh-pet/src/shared/outfits
 */
export async function requestOutfitChange(
  baseUrl: string,
  id: string,
  target: string,
  fetcher: typeof fetch = fetch,
): Promise<Record<string, Record<string, unknown>>> {
  const response = await fetcher(baseUrl + '/pet-outfit', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ id, target }),
  });
  if (!response.ok) throw new Error('换装请求失败：HTTP ' + response.status);
  const value = await response.json();
  if (!value || typeof value !== 'object' || value.ok === false)
    throw new Error(value?.message || '换装未成功，请重试');
  return value as Record<string, Record<string, unknown>>;
}
