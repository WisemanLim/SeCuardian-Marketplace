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
    if (!form.name.trim()) { setError("이름을 입력하세요."); return; }
    try {
      const c = await createCollection(form);
      setShowCreate(false);
      setForm({ name: "", description: "", sensitivity: "general" });
      loadCollections();
      selectCollection(c);
    } catch (e) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "생성 실패");
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
    <div className="p-4 max-w-5xl mx-auto grid grid-cols-3 gap-4">
      <div className="col-span-1">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-lg font-semibold text-gray-800 dark:text-gray-100">{t("nav.rag") ?? "RAG"}</h1>
          <button onClick={() => setShowCreate((v) => !v)}
            className="text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700">
            {showCreate ? "닫기" : "+ 컬렉션"}
          </button>
        </div>
        <p className="text-xs text-gray-500 mb-3">문서 수집→임베딩→하이브리드(BM25+dense+RRF) 검색.</p>

        {showCreate && (
          <div className="mb-3 p-3 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 space-y-2">
            <input placeholder="이름" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className="w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
            <select value={form.sensitivity} onChange={(e) => setForm((f) => ({ ...f, sensitivity: e.target.value as "general" | "sensitive" }))}
              className="w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800">
              <option value="general">general</option>
              <option value="sensitive">sensitive</option>
            </select>
            {error && <p role="alert" className="text-xs text-red-500">{error}</p>}
            <button onClick={handleCreate} className="w-full text-sm px-2 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700">저장</button>
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
          {collections.length === 0 && <p className="text-xs text-gray-400">컬렉션이 없습니다.</p>}
        </div>
      </div>

      <div className="col-span-2">
        {!selected ? (
          <p className="text-sm text-gray-400 mt-8">좌측에서 컬렉션을 선택하세요.</p>
        ) : (
          <div className="space-y-4">
            <section className="p-3 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">문서 수집 — {selected.name}</h3>
              <input placeholder="제목(선택)" value={docText.title}
                onChange={(e) => setDocText((d) => ({ ...d, title: e.target.value }))}
                className="w-full text-sm px-2 py-1.5 mb-2 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
              <textarea placeholder="본문 텍스트" rows={4} value={docText.text}
                onChange={(e) => setDocText((d) => ({ ...d, text: e.target.value }))}
                className="w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
              <button disabled={busy} onClick={handleIngest}
                className="mt-2 text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">수집</button>
              <table className="w-full text-xs mt-3">
                <thead className="text-gray-400"><tr><th className="text-left font-normal py-1">제목</th><th className="text-left font-normal">청크</th></tr></thead>
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
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">하이브리드 검색</h3>
              <div className="flex gap-2">
                <input placeholder="검색어" value={query} onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  className="flex-1 text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
                <button disabled={busy} onClick={handleSearch}
                  className="text-xs px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">검색</button>
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
                {hits.length === 0 && <p className="text-xs text-gray-400">검색 결과가 없습니다.</p>}
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
