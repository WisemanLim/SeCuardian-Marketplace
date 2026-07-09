import { useEffect, useState } from "react";
import {
  RagCollection, RagDocument, RagSearchHit,
  listCollections, createCollection, listDocuments, ingestDocument, search,
} from "../../api/rag";
import { useLocale } from "../../hooks/useLocale";

export default function RagPage() {
  const { t } = useLocale();
  const [collections, setCollections] = useState<RagCollection[]>([]);
  const [selected, setSelected] = useState<RagCollection | null>(null);
  const [documents, setDocuments] = useState<RagDocument[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", sensitivity: "general" as "general" | "sensitive" });
  const [docText, setDocText] = useState({ title: "", text: "" });
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<RagSearchHit[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function loadCollections() {
    listCollections().then(setCollections).catch(() => {});
  }
  useEffect(loadCollections, []);

  function selectCollection(c: RagCollection) {
    setSelected(c);
    setHits([]);
    listDocuments(c.id).then(setDocuments).catch(() => {});
  }

  async function handleCreate() {
    setError("");
    if (!form.name.trim()) { setError(t("rag.nameRequired")); return; }
    try {
      const c = await createCollection(form);
      setShowCreate(false);
      setForm({ name: "", description: "", sensitivity: "general" });
      loadCollections();
      selectCollection(c);
    } catch (e) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || t("rag.createFailed"));
    }
  }

  async function handleIngest() {
    if (!selected || !docText.text.trim()) return;
    setBusy(true);
    try {
      await ingestDocument(selected.id, docText);
      setDocText({ title: "", text: "" });
      const docs = await listDocuments(selected.id);
      setDocuments(docs);
    } finally {
      setBusy(false);
    }
  }

  async function handleSearch() {
    if (!selected || !query.trim()) return;
    setBusy(true);
    try {
      setHits(await search(selected.id, query));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page grid grid-cols-3 gap-4">
      <div className="col-span-1">
        {/* 타이틀은 상단 헤더(AppLayout)에 표시 — 본문에는 설명만 (R18 표준) */}
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-gray-500">{t("rag.pageDesc")}</p>
          <button onClick={() => setShowCreate((v) => !v)}
            className="text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 shrink-0">
            {showCreate ? t("common.close") : t("rag.addCollection")}
          </button>
        </div>

        {showCreate && (
          <div className="mb-3 p-3 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 space-y-2">
            <input placeholder={t("rag.namePh")} value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className="w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
            <select value={form.sensitivity} onChange={(e) => setForm((f) => ({ ...f, sensitivity: e.target.value as "general" | "sensitive" }))}
              className="w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800">
              <option value="general">general</option>
              <option value="sensitive">sensitive</option>
            </select>
            {error && <p role="alert" className="text-xs text-red-500">{error}</p>}
            <button onClick={handleCreate} className="w-full text-sm px-2 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700">{t("common.save")}</button>
          </div>
        )}

        <div className="space-y-1.5">
          {collections.map((c) => (
            <button key={c.id} onClick={() => selectCollection(c)}
              className={`w-full text-left p-2 rounded border text-sm ${
                selected?.id === c.id
                  ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                  : "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800"}`}>
              <span className="font-medium text-gray-800 dark:text-gray-100">{c.name}</span>
              <span className={`ml-1.5 text-[10px] px-1 py-0.5 rounded ${
                c.sensitivity === "sensitive" ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                                               : "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"}`}>
                {c.sensitivity}
              </span>
            </button>
          ))}
          {collections.length === 0 && <p className="text-xs text-gray-400">{t("rag.noCollections")}</p>}
        </div>
      </div>

      <div className="col-span-2">
        {!selected ? (
          <p className="text-sm text-gray-400 mt-8">{t("rag.selectPrompt")}</p>
        ) : (
          <div className="space-y-4">
            <section className="p-3 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">{t("rag.ingestTitle")}{selected.name}</h3>
              <input placeholder={t("rag.titleOptionalPh")} value={docText.title}
                onChange={(e) => setDocText((d) => ({ ...d, title: e.target.value }))}
                className="w-full text-sm px-2 py-1.5 mb-2 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
              <textarea placeholder={t("rag.bodyPh")} rows={4} value={docText.text}
                onChange={(e) => setDocText((d) => ({ ...d, text: e.target.value }))}
                className="w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
              <button disabled={busy} onClick={handleIngest}
                className="mt-2 text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">{t("rag.ingest")}</button>
              <table className="w-full text-xs mt-3">
                <thead className="text-gray-400"><tr><th className="text-left font-normal py-1">{t("rag.thTitle")}</th><th className="text-left font-normal">{t("rag.thChunks")}</th></tr></thead>
                <tbody>
                  {documents.map((d) => (
                    <tr key={d.id} className="border-t border-gray-200 dark:border-gray-800">
                      <td className="py-1">{d.title || `#${d.id}`}</td><td>{d.chunks}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <section className="p-3 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">{t("rag.hybridSearch")}</h3>
              <div className="flex gap-2">
                <input placeholder={t("rag.queryPh")} value={query} onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  className="flex-1 text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
                <button disabled={busy} onClick={handleSearch}
                  className="text-xs px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">{t("rag.search")}</button>
              </div>
              <div className="mt-2 space-y-2">
                {hits.map((h) => (
                  <div key={h.chunk_id} className="p-2 rounded border border-gray-200 dark:border-gray-800 text-xs">
                    <p className="text-gray-700 dark:text-gray-300">{h.text}</p>
                    <p className="text-gray-400 mt-1">
                      rrf={h.rrf_score} · dense={h.dense_score}(#{h.dense_rank ?? "-"}) · bm25={h.bm25_score}(#{h.bm25_rank ?? "-"})
                    </p>
                  </div>
                ))}
                {hits.length === 0 && <p className="text-xs text-gray-400">{t("rag.noResults")}</p>}
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
