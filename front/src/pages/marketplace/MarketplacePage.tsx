import { useEffect, useState } from "react";
import {
  MarketplaceAsset, listCatalog, installAsset, uninstallAsset,
} from "../../api/marketplace";
import { RemoteAsset, remoteCatalog, remoteInstall } from "../../api/marketplaceRemote";
import { useLocale } from "../../hooks/useLocale";

export default function MarketplacePage() {
  const { t } = useLocale();
  const [assets, setAssets] = useState<MarketplaceAsset[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  // 원격 레지스트리(E1.5) — MARKETPLACE_REMOTE_ENABLED=false 면 409 → 섹션 숨김
  const [remoteAssets, setRemoteAssets] = useState<RemoteAsset[]>([]);
  const [remoteEnabled, setRemoteEnabled] = useState(false);

  function load() {
    listCatalog().then(setAssets).catch(() => {});
  }
  function loadRemote() {
    remoteCatalog().then((r) => { setRemoteAssets(r.assets); setRemoteEnabled(true); })
      .catch(() => setRemoteEnabled(false));
  }
  useEffect(() => { load(); loadRemote(); }, []);

  async function handleRemoteInstall(a: RemoteAsset) {
    setBusy(`remote:${a.asset_key}`);
    try {
      await remoteInstall(a.asset_key, a.checksum);
      load();
    } catch (e) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "원격 설치 실패");
    } finally {
      setBusy(null);
    }
  }

  async function handleInstall(a: MarketplaceAsset) {
    setBusy(a.asset_key);
    try {
      await installAsset(a.asset_key, a.version);
      load();
    } finally {
      setBusy(null);
    }
  }

  async function handleUninstall(a: MarketplaceAsset) {
    setBusy(a.asset_key);
    try {
      await uninstallAsset(a.asset_key);
      load();
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300">{t("agent.assetCatalog")}</h2>
        <p className="text-xs text-gray-500 mt-0.5">에이전트·워크플로우·RAG 파이프라인을 탐색·설치·버전관리합니다. (등록은 상단 ‘{t("agent.registerAsset")}’)</p>
      </div>

      {error && <p role="alert" className="mb-3 text-xs text-red-500">{error}</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {assets.map((a) => (
          <div key={`${a.asset_key}-${a.version}`} className="p-3 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
            <div className="flex items-start justify-between">
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">{a.name}</p>
                <p className="text-xs text-gray-400">{a.asset_key} · {a.kind} · v{a.version}</p>
              </div>
              <span className={`text-[10px] px-1.5 py-0.5 rounded shrink-0 ${
                a.installed ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                            : "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"}`}>
                {a.installed ? `설치됨 (${a.active_version})` : "미설치"}
              </span>
            </div>
            {a.description && <p className="text-xs text-gray-500 mt-1.5 line-clamp-2">{a.description}</p>}
            <div className="mt-2 flex gap-2">
              {a.installed ? (
                <button disabled={busy === a.asset_key} onClick={() => handleUninstall(a)}
                  className="text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-600 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40">
                  해제
                </button>
              ) : (
                <button disabled={busy === a.asset_key} onClick={() => handleInstall(a)}
                  className="text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">
                  설치
                </button>
              )}
            </div>
          </div>
        ))}
        {assets.length === 0 && (
          <p className="text-sm text-gray-400 col-span-2">등록된 자산이 없습니다.</p>
        )}
      </div>

      {remoteEnabled && (
        <section className="mt-8">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            원격 레지스트리 <span className="text-xs font-normal text-gray-400">(다운로드→체크섬 검증→로컬 편입)</span>
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {remoteAssets.map((a) => {
              const localHas = assets.some((la) => la.asset_key === a.asset_key);
              return (
                <div key={`${a.asset_key}-${a.version}`} className="p-3 rounded border border-dashed border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
                  <div className="flex items-start justify-between">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">{a.name}</p>
                      <p className="text-xs text-gray-400">{a.asset_key} · {a.kind} · v{a.version} · 원격</p>
                    </div>
                  </div>
                  {a.description && <p className="text-xs text-gray-500 mt-1.5 line-clamp-2">{a.description}</p>}
                  <button disabled={busy === `remote:${a.asset_key}` || localHas} onClick={() => handleRemoteInstall(a)}
                    className="mt-2 text-xs px-2 py-1 rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40">
                    {localHas ? "로컬에 편입됨" : "다운로드·편입"}
                  </button>
                </div>
              );
            })}
            {remoteAssets.length === 0 && <p className="text-sm text-gray-400 col-span-2">원격 자산이 없습니다.</p>}
          </div>
        </section>
      )}
    </div>
  );
}
