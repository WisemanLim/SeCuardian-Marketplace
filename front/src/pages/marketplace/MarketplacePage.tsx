import { useEffect, useState } from "react";
import {
  MarketplaceAsset, listCatalog, installAsset, uninstallAsset,
} from "../../api/marketplace";
import { RemoteAsset, remoteCatalog, remoteInstall } from "../../api/marketplaceRemote";
import { useLocale } from "../../hooks/useLocale";
import { parseLangMap, pickDescription } from "../../store/locale";
import { getAuth } from "../../store/auth";
import AssetRegisterModal from "./AssetRegisterModal";

export default function MarketplacePage() {
  const { t } = useLocale();
  // R18-7: 카탈로그 카드 이름·설명 다국어 — names/descriptions JSON({"ko":…,"en":…,…}) 을
  // 공통함수(parseLangMap+pickDescription)로 해석, 레거시 컬럼은 폴백만. 언어 확장 시 데이터만 추가.
  const assetName = (a: { name: string; name_en?: string | null; names?: string | null }) =>
    pickDescription(parseLangMap(a.names), a.name, a.name_en) || a.name;
  const assetDesc = (a: { description?: string | null; descriptions?: string | null }) =>
    pickDescription(parseLangMap(a.descriptions), a.description, null);
  const user = getAuth();
  const isAdmin = user?.role === "supervisor" || user?.role === "admin";
  const [assets, setAssets] = useState<MarketplaceAsset[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  // §7.6.3: 카테고리별 추가 등록 — '+ 추가' 클릭 시 해당 category 프리셋 모달
  const [addCategory, setAddCategory] = useState<string | null>(null);
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
  useEffect(() => {
    load(); loadRemote();
    // §7.6.2: 자산 등록/ZIP 등록 완료 시 카탈로그 즉시 갱신
    window.addEventListener("marketplaceChanged", load);
    return () => window.removeEventListener("marketplaceChanged", load);
  }, []);

  // §7.6.2: category(security·utilities·general …) 별 그룹 표시 — 알려진 순서 우선
  const CATEGORY_ORDER = ["security", "utilities", "general"];
  const grouped = assets.reduce<Record<string, MarketplaceAsset[]>>((acc, a) => {
    const cat = a.category || "general";
    (acc[cat] ??= []).push(a);
    return acc;
  }, {});
  const categories = Object.keys(grouped).sort((x, y) => {
    const ix = CATEGORY_ORDER.indexOf(x), iy = CATEGORY_ORDER.indexOf(y);
    return (ix === -1 ? CATEGORY_ORDER.length : ix) - (iy === -1 ? CATEGORY_ORDER.length : iy) || x.localeCompare(y);
  });

  async function handleRemoteInstall(a: RemoteAsset) {
    setBusy(`remote:${a.asset_key}`);
    try {
      await remoteInstall(a.asset_key, a.checksum);
      window.dispatchEvent(new CustomEvent("marketplaceChanged"));
    } catch (e) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || t("mp.remoteInstallFailed"));
    } finally {
      setBusy(null);
    }
  }

  async function handleInstall(a: MarketplaceAsset) {
    setBusy(a.asset_key);
    try {
      await installAsset(a.asset_key, a.version);
      // §7.6.4: 설치됨 탭·카탈로그 동시 갱신 (자기 자신도 리스너로 load)
      window.dispatchEvent(new CustomEvent("marketplaceChanged"));
      window.dispatchEvent(new CustomEvent("agentConfigChanged")); // §7.6.5: 좌측 네비 즉시 동기화
    } finally {
      setBusy(null);
    }
  }

  async function handleUninstall(a: MarketplaceAsset) {
    setBusy(a.asset_key);
    try {
      await uninstallAsset(a.asset_key);
      window.dispatchEvent(new CustomEvent("marketplaceChanged"));
      window.dispatchEvent(new CustomEvent("agentConfigChanged")); // §7.6.5: 좌측 네비 즉시 동기화
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300">{t("agent.assetCatalog")}</h2>
        <p className="text-xs text-gray-500 mt-0.5">{t("mp.catalogDesc")} ({t("mp.registerHint")} ‘{t("agent.registerAsset")}’)</p>
      </div>

      {error && <p role="alert" className="mb-3 text-xs text-red-500">{error}</p>}

      {/* §7.6.2: 카테고리별 섹션 — security·utilities·general … */}
      {categories.map((cat) => (
        <section key={cat} className="mb-5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500">
              {t(`mp.cat.${cat}`) === `mp.cat.${cat}` ? cat : t(`mp.cat.${cat}`)}
              <span className="ml-1.5 font-normal">({grouped[cat].length})</span>
            </h3>
            {/* §7.6.3: 카테고리별 추가 등록 — category 프리셋 자산 등록 모달 */}
            {isAdmin && (
              <button type="button" onClick={() => setAddCategory(cat)}
                className="text-[11px] px-2 py-0.5 rounded border border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:text-blue-600 hover:border-blue-300 dark:hover:border-blue-700 transition-colors">
                + {t("mp.addToCatalog")}
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {grouped[cat].map((a) => (
              <div key={`${a.asset_key}-${a.version}`} className="p-3 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
                <div className="flex items-start justify-between">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">{assetName(a)}</p>
                    <p className="text-xs text-gray-400">{a.asset_key} · {a.kind} · v{a.version}</p>
                  </div>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded shrink-0 ${
                    a.installed ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                                : "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"}`}>
                    {a.installed ? `${t("mp.installed")} (${a.active_version})` : t("mp.notInstalled")}
                  </span>
                </div>
                {assetDesc(a) && <p className="text-xs text-gray-500 mt-1.5 line-clamp-2">{assetDesc(a)}</p>}
                <div className="mt-2 flex gap-2">
                  {a.installed ? (
                    <button disabled={busy === a.asset_key} onClick={() => handleUninstall(a)}
                      className="text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-600 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40">
                      {t("mp.uninstall")}
                    </button>
                  ) : (
                    <button disabled={busy === a.asset_key} onClick={() => handleInstall(a)}
                      className="text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">
                      {t("mp.install")}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      ))}
      {assets.length === 0 && (
        <p className="text-sm text-gray-400">{t("mp.noAssets")}</p>
      )}

      {/* §7.6.3: 카테고리 프리셋 자산 등록 모달 — 등록 완료 시 marketplaceChanged 로 자동 갱신 */}
      {addCategory && (
        <AssetRegisterModal category={addCategory} onClose={() => setAddCategory(null)} />
      )}

      {remoteEnabled && (
        <section className="mt-8">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            {t("mp.remoteTitle")} <span className="text-xs font-normal text-gray-400">{t("mp.remoteSub")}</span>
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {remoteAssets.map((a) => {
              const localHas = assets.some((la) => la.asset_key === a.asset_key);
              return (
                <div key={`${a.asset_key}-${a.version}`} className="p-3 rounded border border-dashed border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
                  <div className="flex items-start justify-between">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">{assetName(a)}</p>
                      <p className="text-xs text-gray-400">{a.asset_key} · {a.kind} · v{a.version} · {t("mp.remoteTag")}</p>
                    </div>
                  </div>
                  {assetDesc(a) && <p className="text-xs text-gray-500 mt-1.5 line-clamp-2">{assetDesc(a)}</p>}
                  <button disabled={busy === `remote:${a.asset_key}` || localHas} onClick={() => handleRemoteInstall(a)}
                    className="mt-2 text-xs px-2 py-1 rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40">
                    {localHas ? t("mp.importedLocal") : t("mp.downloadImport")}
                  </button>
                </div>
              );
            })}
            {remoteAssets.length === 0 && <p className="text-sm text-gray-400 col-span-2">{t("mp.noRemote")}</p>}
          </div>
        </section>
      )}
    </div>
  );
}
