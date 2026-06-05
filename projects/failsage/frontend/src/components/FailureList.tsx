import { useState } from "react";
import { ChevronDown, ChevronRight, Zap } from "lucide-react";
import type { TestCase } from "../api/client";
import { feedbackApi } from "../api/client";
import AIPanel from "./AIPanel";
import SeverityBadge from "./SeverityBadge";
import StackTraceViewer from "./StackTraceViewer";

function FailureCard({ tc }: { tc: TestCase }) {
  const [open, setOpen] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState(false);

  const handleFeedback = async (helpful: boolean) => {
    await feedbackApi.submit({ test_case_id: tc.id, is_helpful: helpful });
    setFeedbackSent(true);
  };

  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-start gap-3 p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors text-left"
      >
        <span className="mt-0.5">
          {open ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <SeverityBadge severity={tc.severity} />
            {tc.is_flaky && (
              <span className="text-xs text-yellow-600 dark:text-yellow-400 flex items-center gap-0.5">
                <Zap className="w-3 h-3" /> Flaky
              </span>
            )}
            {tc.failure_category && (
              <span className="text-xs text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">{tc.failure_category}</span>
            )}
          </div>
          <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">{tc.name}</p>
          <p className="text-xs text-slate-500 truncate">{tc.classname}</p>
          {tc.root_cause_summary && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate italic">{tc.root_cause_summary}</p>
          )}
        </div>
        <span className="text-xs text-slate-400 shrink-0">{tc.duration.toFixed(2)}s</span>
      </button>

      {open && (
        <div className="border-t border-slate-200 dark:border-slate-700 p-4 space-y-4 bg-slate-50 dark:bg-slate-900/40">
          {tc.ai_analysis && <AIPanel analysis={tc.ai_analysis} />}
          <StackTraceViewer stackTrace={tc.stack_trace} failureMessage={tc.failure_message} />

          {!feedbackSent ? (
            <div className="flex items-center gap-3 text-xs text-slate-500">
              <span>Was this analysis helpful?</span>
              <button
                onClick={() => handleFeedback(true)}
                className="px-3 py-1 rounded bg-emerald-50 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/50 hover:bg-emerald-100 dark:hover:bg-emerald-800/50 transition-colors"
              >
                👍 Yes
              </button>
              <button
                onClick={() => handleFeedback(false)}
                className="px-3 py-1 rounded bg-red-50 dark:bg-red-900/50 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800/50 hover:bg-red-100 dark:hover:bg-red-800/50 transition-colors"
              >
                👎 No
              </button>
            </div>
          ) : (
            <p className="text-xs text-emerald-600 dark:text-emerald-500">Thanks for the feedback!</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function FailureList({ failures }: { failures: TestCase[] }) {
  const clusters: Record<string, TestCase[]> = {};
  for (const tc of failures) {
    const key = tc.cluster_id || tc.id;
    if (!clusters[key]) clusters[key] = [];
    clusters[key].push(tc);
  }

  return (
    <div className="space-y-3">
      {Object.entries(clusters).map(([cid, tcs]) => (
        <div key={cid}>
          {tcs.length > 1 && (
            <p className="text-xs text-slate-400 mb-1.5 ml-1">
              Cluster of {tcs.length} similar failures
            </p>
          )}
          {tcs.map((tc) => (
            <div key={tc.id} className="mb-2">
              <FailureCard tc={tc} />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
