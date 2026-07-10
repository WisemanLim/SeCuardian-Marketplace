import { useState } from "react";
import { registerAssetZips, ASSET_KINDS } from "../../api/marketplace";
import { useLocale } from "../../hooks/useLocale";

// 마켓플레이스 자산 등록 모달 (§7.6.2·§7.6.3) — 두 진입점:
//  - 상단 '자산 등록' 버튼(category 미지정): 카탈로그(신규 category 자유 입력) 생성 + 자산 등록
//  - 카탈로그 카테고리 섹션 '+ 추가' 버튼(category 프리셋): 해당 카탈로그에 에이전트 추가
// asset_key 는 서버 자동부여(name 슬러그). addon ZIP 다중 첨부 시 ZIP 별 meta 로 등록·설치 시 hot-deploy.
export default function AssetRegisterModal({ category, onClose }: Readonly<{
  category?: string;
  onClose: () => void;
}>) {
  const { t } = useLocale();
  const [form, setForm] = useState({
    name: "", name_en: "", kind: "agent", description: "", description_en: "",
    category: category ?? "general",
  });
  const [zipFiles, setZipFiles] = useState<File[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    setError("");
    // 필수값: 자산명·설명·ZIP(§7.6.6 — 메타-only 빈 자산 등록 차단)
    if (!form.name.trim()) { setError(t("agent.assetNameRequired")); return; }
    if (!form.description.trim()) { setError(t("agent.assetDescRequired")); return; }
    if (zipFiles.length === 0) { setError(t("agent.assetZipRequired")); return; }
    setBusy(true);
    try {
      const cat = form.category.trim() || "general";
      await registerAssetZips(zipFiles, cat); // ZIP 별 자산 등록 + 블롭 저장 (다중)
      window.dispatchEvent(new CustomEvent("marketplaceChanged")); // 카탈로그 즉시 갱신
      onClose();
    } catch (e) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || t("agent.assetRegisterFailed"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="w-full max-w-lg rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100">
            {t("agent.registerAsset")}
            {category && (
              <span className="ml-2 text-xs font-normal px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                {category}
              </span>
            )}
          </h2>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-sm">✕</button>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {/* §7.6.3: category 프리셋(카테고리별 추가) 시 입력 숨김, 상단 등록은 자유 입력 = 카탈로그 생성.
              입력 순서: 카탈로그 → name → 종류 → 이름(영문) … (사용자 요구 2026-07-10) */}
          {!category && (
            <label className="text-xs text-gray-500 col-span-2">
              {t("agent.assetCategory")}
              <input value={form.category} onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
                placeholder="general"
                className="mt-0.5 w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
              <span className="block mt-0.5 text-[11px] text-gray-400">{t("agent.assetCategoryHint")}</span>
            </label>
          )}
          <label className="text-xs text-gray-500">
            {t("agent.assetName")}<span className="ml-0.5 text-red-500 font-bold">*</span>
            <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder={t("agent.assetNamePlaceholder")}
              className="mt-0.5 w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
            {/* §7.6.2: asset_key 는 name 슬러그로 자동부여 */}
            <span className="block mt-0.5 text-[11px] text-gray-400">{t("agent.assetKeyAuto")}</span>
          </label>
          <label className="text-xs text-gray-500">
            {t("agent.assetKind")}
            <select value={form.kind} onChange={(e) => setForm((f) => ({ ...f, kind: e.target.value }))}
              className="mt-0.5 w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800">
              {ASSET_KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
          </label>
          {/* R18-7: 다국어 — name(ko)/name_en, description(ko)/description_en */}
          <label className="text-xs text-gray-500 col-span-2">
            {t("agent.assetNameEn")}
            <input value={form.name_en} onChange={(e) => setForm((f) => ({ ...f, name_en: e.target.value }))}
              className="mt-0.5 w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
          </label>
          <label className="text-xs text-gray-500 col-span-2">
            {t("agent.assetDesc")}<span className="ml-0.5 text-red-500 font-bold">*</span>
            <input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              className="mt-0.5 w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
          </label>
          <label className="text-xs text-gray-500 col-span-2">
            {t("agent.assetDescEn")}
            <input value={form.description_en} onChange={(e) => setForm((f) => ({ ...f, description_en: e.target.value }))}
              className="mt-0.5 w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
          </label>
          {/* §7.6.2·§7.6.6: addon ZIP 다중 첨부(필수) — ZIP 별 meta.json 으로 자산 등록, 설치 시 hot-deploy */}
          <label className="text-xs text-gray-500 col-span-2">
            {t("agent.assetZip")}<span className="ml-0.5 text-red-500 font-bold" title={t("agent.assetZipRequired")}>*</span>
            <input type="file" accept=".zip" multiple
              onChange={(e) => setZipFiles(Array.from(e.target.files ?? []))}
              className="mt-0.5 w-full text-sm text-gray-500 file:mr-2 file:text-xs file:px-2 file:py-1 file:rounded file:border file:border-gray-300 dark:file:border-gray-600 file:bg-gray-50 dark:file:bg-gray-800 file:text-gray-600 dark:file:text-gray-300" />
            <span className="block mt-0.5 text-[11px] text-gray-400">{t("agent.assetZipHint")}</span>
            {zipFiles.length > 0 && (
              <span className="block mt-1 text-[11px] text-blue-500">
                {zipFiles.map((f) => f.name).join(", ")} ({zipFiles.length})
              </span>
            )}
          </label>
          {error && <p role="alert" className="text-xs text-red-500 col-span-2">{error}</p>}
          <button onClick={submit} disabled={busy}
            className="col-span-2 text-sm px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">
            {t("agent.assetRegisterSubmit")}
          </button>
        </div>
      </div>
    </div>
  );
}
