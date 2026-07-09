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
  category: string;
  min_platform_version: string;
  governance: string;
  required_env: string;
  checksum: string;
  source: "local" | "remote";
  installed: boolean;
  active_version: string | null;
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
  asset_key: string;
  version?: string;
  kind?: string;
  name: string;
  name_en?: string;
  description?: string;
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

export async function installAsset(assetKey: string, version?: string): Promise<MarketplaceInstall> {
  const { data } = await client.post<MarketplaceInstall>(
    `/marketplace/install/${assetKey}`,
    {},
    { params: version ? { version } : undefined },
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
