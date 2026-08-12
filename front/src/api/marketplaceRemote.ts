import client from "./client";

export interface RemoteAsset {
  asset_key: string;
  version: string;
  kind: string;
  name: string;
  name_en?: string;
  description?: string;
  category?: string;
  checksum?: string;
}

export interface RemotePing {
  ok: boolean;
  mode: string;
  host: string;
}

export async function remotePing(): Promise<RemotePing> {
  const { data } = await client.get<RemotePing>("/marketplace-remote/ping");
  return data;
}

export async function remoteCatalog(refresh = false): Promise<{ assets: RemoteAsset[]; cached: boolean }> {
  const { data } = await client.get<{ assets: RemoteAsset[]; cached: boolean }>("/marketplace-remote/catalog", {
    params: refresh ? { refresh: true } : undefined,
  });
  return data;
}

// R22-7: force=true 는 hot-deploy 중복(기등록 키) 사용자 확인 후에만
export async function remoteInstall(
  assetKey: string, expectedChecksum?: string, force = false
): Promise<{ registered: boolean; checksum: string }> {
  const { data } = await client.post<{ registered: boolean; checksum: string }>(
    `/marketplace-remote/install/${assetKey}`,
    { expected_checksum: expectedChecksum, force },
  );
  return data;
}
