import client from "./client";

export interface MarketplaceAsset {
  id: number;
  tenant_id: string;
  asset_key: string;
  version: string;
  kind: "agent" | "workflow" | "rag-pipeline" | "tool-proxy";
  name: string;
  name_en: string;
  description: string;
  /** 다국어 JSON TEXT {"ko":…, "en":…, …} — parseLangMap 으로 파싱 (R18-7) */
  names: string;
  descriptions: string;
  category: string;
  min_platform_version: string;
  governance: string;
  required_env: string;
  checksum: string;
  source: "local" | "remote";
  installed: boolean;
  active_version: string | null;
  deletable?: boolean;           // §7.6.6: 사용자 등록 자산(디스크 미보유)만 true
}

export interface MarketplaceInstall {
  id: number;
  asset_key: string;
  version: string;
  status: string;
  active: boolean;
  installed_by: string;
  error: string;
  agent_config_key: string | null;
  created_at: string;
}

export async function listCatalog(): Promise<MarketplaceAsset[]> {
  const { data } = await client.get<{ assets: MarketplaceAsset[] }>("/marketplace/catalog");
  return data.assets ?? [];
}

export async function registerAsset(body: {
  asset_key?: string; // §7.6.2: 미지정 시 서버가 name 슬러그로 자동부여
  version?: string;
  kind?: string;
  name: string;
  name_en?: string;
  description?: string;
  description_en?: string;
  /** 다국어 dict 직접 지정 — 지정 시 레거시 필드보다 우선 (R18-7) */
  names?: Record<string, string>;
  descriptions?: Record<string, string>;
  category?: string;
  required_env?: string;
}): Promise<MarketplaceAsset> {
  const { data } = await client.post<MarketplaceAsset>("/marketplace/catalog", body);
  return data;
}

// §7.6.1: 자산 등록 시 addon ZIP(스캐폴드 형식) 첨부 — 설치 시 hot-deploy 에 사용
export async function uploadAssetZip(assetKey: string, file: File, version?: string): Promise<{
  asset_key: string; version: string; checksum: string; size: number;
}> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post(`/marketplace/catalog/${assetKey}/zip`, form, {
    params: version ? { version } : undefined,
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

// §7.6.2: ZIP 다중 등록 — 각 ZIP 의 {key}-meta.json 기반 자산 등록 + 블롭 저장
export async function registerAssetZips(
  files: File[],
  category?: string,
  // §7.6.6: 단일 ZIP 등록 시 폼 입력(name/description/kind)이 ZIP meta 를 덮어씀
  fields?: { name?: string; name_en?: string; description?: string; description_en?: string; kind?: string },
  // §7.6.6 v0.47: 기존 등록 key 존재 시 confirm 없이는 409 duplicate — 사용자 확인 후 true 로 재요청
  confirm = false,
): Promise<MarketplaceAsset[]> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  Object.entries(fields ?? {}).forEach(([k, v]) => { if (v?.trim()) form.append(k, v.trim()); });
  const { data } = await client.post<{ assets: MarketplaceAsset[] }>("/marketplace/catalog/zip", form, {
    params: { ...(category ? { category } : {}), ...(confirm ? { confirm: true } : {}) },
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data.assets ?? [];
}

// §7.6.6 v0.47: 중복 등록 409 detail — {"code":"duplicate","assets":[…]}
export interface DuplicateAssetInfo {
  asset_key: string;
  name: string;
  category: string;
}

// §7.6.6: 사용자 등록 자산 삭제 (디스크 미보유·비설치만 — 서버 검증)
export async function deleteAsset(assetKey: string): Promise<{ deleted: string }> {
  const { data } = await client.delete(`/marketplace/catalog/${assetKey}`);
  return data;
}

// §7.6.6: 사용자 카탈로그(카테고리) 일괄 삭제 — 전 자산 deletable·비설치일 때만
export async function deleteCategory(category: string): Promise<{ deleted_category: string; deleted_assets: string[] }> {
  const { data } = await client.delete(`/marketplace/catalog-category/${encodeURIComponent(category)}`);
  return data;
}

// R22-7: force=true 는 중복(기존 에이전트 키 점유·동일 버전 활성 설치) 사용자 확인 후에만
export async function installAsset(
  assetKey: string, version?: string, force = false
): Promise<MarketplaceInstall> {
  const params: Record<string, string | boolean> = {};
  if (version) params.version = version;
  if (force) params.force = true;
  const { data } = await client.post<MarketplaceInstall>(
    `/marketplace/install/${assetKey}`,
    {},
    { params: Object.keys(params).length ? params : undefined },
  );
  return data;
}

export async function uninstallAsset(assetKey: string): Promise<{ uninstalled: string }> {
  const { data } = await client.delete<{ uninstalled: string }>(`/marketplace/install/${assetKey}`);
  return data;
}

export async function listInstalls(assetKey?: string): Promise<MarketplaceInstall[]> {
  const { data } = await client.get<{ installs: MarketplaceInstall[] }>("/marketplace/installs", {
    params: assetKey ? { asset_key: assetKey } : undefined,
  });
  return data.installs ?? [];
}

export const ASSET_KINDS = ["agent", "workflow", "rag-pipeline", "tool-proxy"] as const;
