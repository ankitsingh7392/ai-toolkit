import { AlertTriangle, GitCommit, ShieldCheck } from "lucide-react";
import type { BuildInsight } from "../api/client";
import ConfidenceIndicator from "./ConfidenceIndicator";

const ACTION_COLOR: Record<string, string> = {
  BLOCK_MERGE: "border-red-300 dark:border-red-600/50 bg-red-50 dark:bg-red-950/30",
  INVESTIGATE: "border-orange-300 dark:border-orange-600/50 bg-orange-50 dark:bg-orange-950/30",
  MONITOR: "border-yellow-300 dark:border-yellow-600/50 bg-yellow-50 dark:bg-yellow-950/30",
  PASS: "border-emerald-300 dark:border-emerald-600/50 bg-emerald-50 dark:bg-emerald-950/30",
};

const ACTION_TEXT: Record<string, string> = {
  BLOCK_MERGE: "text-red-600 dark:text-red-400",
  INVESTIGATE: "text-orange-600 dark:text-orange-400",
  MONITOR: "text-yellow-600 dark:text-yellow-400",
  PASS: "text-emerald-600 dark:text-emerald-400",
};

export default function RegressionInsights({ insight }: { insight: BuildInsight }) {
  const borderClass = ACTION_COLOR[insight.recommended_action] ?? "border-slate-200 dark:border-slate-700";
  const textClass = ACTION_TEXT[insight.recommended_action] ?? "text-slate-500";

  return (
    <div className={`rounded-xl border p-5 space-y-4 ${borderClass}`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {insight.build_at_risk ? (
            <AlertTriangle className="w-5 h-5 text-red-500 dark:text-red-400" />
          ) : (
            <ShieldCheck className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          )}
          <span className={`font-bold text-base ${textClass}`}>{insight.recommended_action.replace("_", " ")}</span>
          <span className="text-xs text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">{insight.risk_level} RISK</span>
        </div>
        <ConfidenceIndicator score={insight.confidence_score} />
      </div>

      <p className="text-sm text-slate-600 dark:text-slate-300">{insight.risk_rationale}</p>

      {insight.likely_regression_commit && (
        <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800/60 rounded-lg px-3 py-2">
          <GitCommit className="w-4 h-4 text-indigo-500 dark:text-indigo-400 shrink-0" />
          <div>
            <p className="text-xs text-slate-500">Likely regression introduced in</p>
            <p className="text-xs font-mono text-indigo-600 dark:text-indigo-300">{insight.likely_regression_commit}</p>
            {insight.regression_reasoning && (
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{insight.regression_reasoning}</p>
            )}
          </div>
        </div>
      )}

      {insight.patterns_detected.length > 0 && (
        <div>
          <p className="text-xs text-slate-500 mb-1.5">Patterns detected:</p>
          <ul className="space-y-1">
            {insight.patterns_detected.map((p, i) => (
              <li key={i} className="text-xs text-slate-600 dark:text-slate-300 flex gap-2">
                <span className="text-indigo-500 dark:text-indigo-400">•</span> {p}
              </li>
            ))}
          </ul>
        </div>
      )}

      {insight.affected_components.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {insight.affected_components.map((c) => (
            <span key={c} className="text-xs bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded">{c}</span>
          ))}
        </div>
      )}
    </div>
  );
}
