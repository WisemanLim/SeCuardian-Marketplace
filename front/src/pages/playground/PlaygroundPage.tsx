import { useEffect, useState } from "react";
import { PlaygroundRun, runPlayground, listRuns } from "../../api/playground";
import { RagCollection, listCollections } from "../../api/rag";
import { useLocale } from "../../hooks/useLocale";

interface VariantState {
  system: string;
  model: string;
  result: PlaygroundRun | null;
  busy: boolean;
}

const emptyVariant: VariantState = { system: "", model: "", result: null, busy: false };

function VariantPanel({
  label, variant, onChange, onRun,
}: {
  label: string;
  variant: VariantState;
  onChange: (patch: Partial<VariantState>) => void;
  onRun: () => void;
}) {
  const { t } = useLocale();
  return (
    <div className="p-3 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      <p className="text-xs font-semibold text-gray-500 mb-2">{label}</p>
      <input
        placeholder={t("pg.systemPh")}
        value={variant.system}
        onChange={(e) => onChange({ system: e.target.value })}
        className="w-full text-xs px-2 py-1.5 mb-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
      />
      <input
        placeholder={t("pg.modelPh")}
        value={variant.model}
        onChange={(e) => onChange({ model: e.target.value })}
        className="w-full text-xs px-2 py-1.5 mb-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
      />
      <button onClick={onRun} disabled={variant.busy}
        className="w-full text-xs px-2 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">
        {variant.busy ? t("pg.running") : t("pg.runWith")}
      </button>
      {variant.result && (
        <div className="mt-2 p-2 rounded bg-gray-50 dark:bg-gray-800 text-xs">
          <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{variant.result.response_text}</p>
          <p className="text-gray-400 mt-1.5">
            {variant.result.provider} · {variant.result.latency_ms}ms
            {variant.result.citations_json !== "[]" && ` · ${t("pg.cit1")}${JSON.parse(variant.result.citations_json).length}${t("pg.cit2")}`}
          </p>
        </div>
      )}
    </div>
  );
}

export default function PlaygroundPage() {
  const { t } = useLocale();
  const [prompt, setPrompt] = useState("");
  const [collections, setCollections] = useState<RagCollection[]>([]);
  const [ragCollectionId, setRagCollectionId] = useState<number | "">("");
  const [compareMode, setCompareMode] = useState(false);
  const [a, setA] = useState<VariantState>(emptyVariant);
  const [b, setB] = useState<VariantState>(emptyVariant);
  const [history, setHistory] = useState<PlaygroundRun[]>([]);

  useEffect(() => {
    listCollections().then(setCollections).catch(() => {});
    loadHistory();
  }, []);

  function loadHistory() {
    listRuns(10).then(setHistory).catch(() => {});
  }

  async function runVariant(variant: VariantState, setVariant: (v: VariantState) => void) {
    if (!prompt.trim()) return;
    setVariant({ ...variant, busy: true });
    try {
      const result = await runPlayground({
        prompt,
        system: variant.system || undefined,
        model: variant.model || undefined,
        rag_collection_id: ragCollectionId === "" ? undefined : ragCollectionId,
      });
      setVariant({ ...variant, busy: false, result });
      loadHistory();
    } catch {
      setVariant({ ...variant, busy: false });
    }
  }

  return (
    <div className="page">
      <div className="flex items-center justify-between mb-2">
        {/* 타이틀은 상단 헤더(AppLayout)에 표시 — 본문에는 설명만 (R18 표준) */}
        <p className="text-sm text-gray-500 dark:text-gray-400">{t("pg.pageDesc")}</p>
        <label className="flex items-center gap-1.5 text-xs text-gray-500">
          <input type="checkbox" checked={compareMode} onChange={(e) => setCompareMode(e.target.checked)} />
          {t("pg.abCompare")}
        </label>
      </div>

      <div className="mb-3 space-y-2">
        <textarea
          placeholder={t("pg.promptPh")}
          rows={3}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
        />
        <select
          value={ragCollectionId}
          onChange={(e) => setRagCollectionId(e.target.value === "" ? "" : Number(e.target.value))}
          className="text-xs px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
        >
          <option value="">{t("pg.noRagCollection")}</option>
          {collections.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>

      <div className={`grid gap-3 ${compareMode ? "grid-cols-2" : "grid-cols-1"}`}>
        <VariantPanel label="A" variant={a} onChange={(p) => setA({ ...a, ...p })} onRun={() => runVariant(a, setA)} />
        {compareMode && (
          <VariantPanel label="B" variant={b} onChange={(p) => setB({ ...b, ...p })} onRun={() => runVariant(b, setB)} />
        )}
      </div>

      <div className="mt-6">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">{t("pg.historyTitle")}</h3>
        <table className="w-full text-xs">
          <thead className="text-gray-400">
            <tr><th className="text-left font-normal py-1">{t("pg.thPrompt")}</th><th className="text-left font-normal">provider</th><th className="text-left font-normal">{t("pg.thLatency")}</th><th className="text-left font-normal">{t("pg.thTokens")}</th></tr>
          </thead>
          <tbody>
            {history.map((r) => (
              <tr key={r.id} className="border-t border-gray-200 dark:border-gray-800">
                <td className="py-1 truncate max-w-[240px]">{r.prompt}</td>
                <td>{r.provider}</td>
                <td>{r.latency_ms}ms</td>
                <td>{r.input_tokens}/{r.output_tokens}</td>
              </tr>
            ))}
            {history.length === 0 && <tr><td colSpan={4} className="text-gray-400 py-2">{t("pg.noHistory")}</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
