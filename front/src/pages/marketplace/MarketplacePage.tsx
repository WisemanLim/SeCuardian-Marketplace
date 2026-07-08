import { useEffect, useState } from "react";
import {
  MarketplaceAsset, ASSET_KINDS, listCatalog, registerAsset, installAsset, uninstallAsset,
} from "../../api/marketplace";
import { useLocale } from "../../hooks/useLocale";

export default function MarketplacePage() {
  const { t } = useLocale();
  const [assets, setAssets] = useState<MarketplaceAsset[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ asset_key: "", name: "", kind: "agent", description: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  function load() {
    listCatalog().then(setAssets).catch(() => {});
  }
  useEffect(load, []);

  async function handleRegister() {
    setError("");
    if (!form.asset_key.trim() || !form.name.trim()) { setError("asset_key/name 필수"); return; }
    try {
      await registerAsset(form);
      setShowCreate(false);
      setForm({ asset_key: "", name: "", kind: "agent", description: "" });
      load();
    } catch (e) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "등록 실패");
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
    <div className="p-4 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-lg font-semibold text-gray-800 dark:text-gray-100">{t("nav.marketplace") ?? "마켓플레이스"}</h1>
          <p className="text-xs text-gray-500 mt-0.5">에이전트·워크플로우·RAG 파이프라인을 탐색·설치·버전관리합니다.</p>
        </div>
        <button onClick={() => setShowCreate((v) => !v)}
          className="text-sm px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700">
          {showCreate ? "닫기" : "+ 자산 등록"}
        </button>
      </div>

      {showCreate && (
        <div className="mb-6 p-4 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 grid grid-cols-2 gap-3">
          <label className="text-xs text-gray-500">
            asset_key
            <input value={form.asset_key} onChange={(e) => setForm((f) => ({ ...f, asset_key: e.target.value }))}
              className="mt-0.5 w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
          </label>
          <label className="text-xs text-gray-500">
            name
            <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className="mt-0.5 w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
          </label>
          <label className="text-xs text-gray-500">
            kind
            <select value={form.kind} onChange={(e) => setForm((f) => ({ ...f, kind: e.target.value }))}
              className="mt-0.5 w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800">
              {ASSET_KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
          </label>
          <label className="text-xs text-gray-500 col-span-2">
            description
            <input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              className="mt-0.5 w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
          </label>
          {error && <p role="alert" className="text-xs text-red-500 col-span-2">{error}</p>}
          <button onClick={handleRegister}
            className="col-span-2 text-sm px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700">등록</button>
        </div>
      )}

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
        {assets.length === 0 && !showCreate && (
          <p className="text-sm text-gray-400 col-span-2">등록된 자산이 없습니다.</p>
        )}
      </div>
    </div>
  );
}
