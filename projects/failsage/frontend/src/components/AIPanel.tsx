import { Lightbulb, ShieldAlert, Wrench } from "lucide-react";
import type { AIAnalysis } from "../api/client";
import ConfidenceIndicator from "./ConfidenceIndicator";

const CATEGORY_COLOR: Record<string, string> = {
  UI: "text-purple-500 dark:text-purple-400",
  API: "text-blue-500 dark:text-blue-400",
  Database: "text-yellow-600 dark:text-yellow-400",
  Performance: "text-orange-500 dark:text-orange-400",
  Infrastructure: "text-red-500 dark:text-red-400",
  TestIssue: "text-slate-500",
};

export default function AIPanel({ analysis }: { analysis: AIAnalysis }) {
  const catColor = CATEGORY_COLOR[analysis.failure_category] ?? "text-slate-500";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-4">
        <span className={`font-semibold text-sm ${catColor}`}>{analysis.failure_category}</span>
        <ConfidenceIndicator score={analysis.confidence_score} />
        {analysis.is_flaky && (
          <span className="text-xs bg-yellow-50 dark:bg-yellow-900/50 text-yellow-700 dark:text-yellow-300 border border-yellow-200 dark:border-yellow-600/40 px-2 py-0.5 rounded">
            ⚡ Possibly Flaky
          </span>
        )}
      </div>

      {/* Root cause */}
      <div className="bg-slate-100 dark:bg-slate-800/60 rounded-lg p-4 space-y-3">
        <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <ShieldAlert className="w-3.5 h-3.5" /> Root Cause
        </h4>
        <p className="text-slate-800 dark:text-slate-200 text-sm font-medium">{analysis.root_cause.summary}</p>

        {analysis.root_cause.observed_facts.length > 0 && (
          <div>
            <p className="text-xs text-slate-500 mb-1">Observed facts:</p>
            <ul className="space-y-0.5">
              {analysis.root_cause.observed_facts.map((f, i) => (
                <li key={i} className="text-xs text-slate-600 dark:text-slate-300 flex gap-2">
                  <span className="text-indigo-500 dark:text-indigo-400 mt-0.5">•</span>
                  {f}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div>
          <p className="text-xs text-slate-500 mb-1">Reasoning:</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 italic">{analysis.root_cause.inferred_reasoning}</p>
        </div>
      </div>

      {/* Debugging steps */}
      {analysis.debugging_steps.length > 0 && (
        <div className="bg-slate-100 dark:bg-slate-800/60 rounded-lg p-4">
          <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-3">
            <Wrench className="w-3.5 h-3.5" /> Debugging Steps
          </h4>
          <ol className="space-y-1.5">
            {analysis.debugging_steps.map((step, i) => (
              <li key={i} className="text-xs text-slate-700 dark:text-slate-300 flex gap-2">
                <span className="text-indigo-500 dark:text-indigo-400 font-mono font-bold shrink-0">{i + 1}.</span>
                {step}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Suggested fix */}
      {analysis.suggested_fix && (
        <div className="bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-700/30 rounded-lg p-4">
          <h4 className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <Lightbulb className="w-3.5 h-3.5" /> Suggested Fix
          </h4>
          <p className="text-xs text-emerald-800 dark:text-emerald-200 font-mono">{analysis.suggested_fix}</p>
        </div>
      )}

      {analysis.low_confidence_reasons.length > 0 && (
        <p className="text-xs text-slate-400 italic">
          Confidence limited: {analysis.low_confidence_reasons.join("; ")}
        </p>
      )}
    </div>
  );
}
