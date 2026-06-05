import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Globe, Loader2 } from "lucide-react";
import { runsApi, failuresApi } from "../api/client";
import FailureList from "../components/FailureList";
import RegressionInsights from "../components/RegressionInsights";
import ThemeToggle from "../components/ThemeToggle";
import { useTheme } from "../hooks/useTheme";

function MetaChip({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return (
    <div className="flex flex-col">
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-xs text-slate-600 dark:text-slate-300 font-mono">{value}</span>
    </div>
  );
}

export default function RunDetail() {
  const { theme, toggle: toggleTheme } = useTheme();
  const { runId } = useParams<{ runId: string }>();

  const { data: run, isLoading: runLoading } = useQuery({
    queryKey: ["run", runId],
    queryFn: () => runsApi.get(runId!),
    refetchInterval: (q) =>
      q.state.data?.status === "completed" || q.state.data?.status === "failed" ? false : 3000,
    enabled: !!runId,
  });

  const { data: failures = [], isLoading: failLoading } = useQuery({
    queryKey: ["failures", runId],
    queryFn: () => failuresApi.list(runId!),
    enabled: run?.status === "completed",
  });

  if (runLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-[#0f1117] flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
      </div>
    );
  }

  if (!run) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-[#0f1117] flex items-center justify-center">
        <p className="text-slate-500">Run not found.</p>
      </div>
    );
  }

  const totalFailed = run.failed_tests + run.error_tests;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0f1117] transition-colors duration-200">
      <header className="bg-white dark:bg-[#0f1117] border-b border-slate-200 dark:border-[#2a2d3e] px-8 py-4 flex items-center justify-between shadow-sm dark:shadow-none">
        <Link to="/" className="flex items-center gap-2 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 text-sm transition-colors">
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </Link>
        <ThemeToggle theme={theme} onToggle={toggleTheme} />
      </header>

      <main className="px-8 py-8 max-w-5xl mx-auto space-y-8">
        {/* Run header */}
        <div className="bg-white dark:bg-[#1a1d2e] border border-slate-200 dark:border-[#2a2d3e] rounded-xl p-6 shadow-sm dark:shadow-none">
          <div className="flex flex-wrap items-start justify-between gap-4 mb-5">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">{run.job_name}</h1>
                <span className="text-slate-400">#{run.build_id}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded">{run.branch}</span>
                <span>{run.environment}</span>
                {run.jenkins_url && (
                  <a href={run.jenkins_url} target="_blank" rel="noreferrer" className="text-indigo-500 dark:text-indigo-400 flex items-center gap-1">
                    <Globe className="w-3 h-3" /> Jenkins
                  </a>
                )}
              </div>
            </div>
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium
              ${run.status === "completed" ? "bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800"
              : run.status === "processing" ? "bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800"
              : run.status === "failed" ? "bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800"
              : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700"}`}>
              {run.status === "processing" && <Loader2 className="w-4 h-4 animate-spin" />}
              {run.status.charAt(0).toUpperCase() + run.status.slice(1)}
            </div>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-5">
            <div className="text-center">
              <p className="text-2xl font-bold text-slate-700 dark:text-slate-200">{run.total_tests}</p>
              <p className="text-xs text-slate-500">Total</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-emerald-500 dark:text-emerald-400">{run.passed_tests}</p>
              <p className="text-xs text-slate-500">Passed</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-500 dark:text-red-400">{totalFailed}</p>
              <p className="text-xs text-slate-500">Failed</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-slate-400">{run.skipped_tests}</p>
              <p className="text-xs text-slate-500">Skipped</p>
            </div>
          </div>

          {/* Meta */}
          <div className="flex flex-wrap gap-6 pt-4 border-t border-slate-100 dark:border-slate-800">
            <MetaChip label="Commit" value={run.git_commit?.slice(0, 8)} />
            <MetaChip label="Run ID" value={run.run_id} />
          </div>
        </div>

        {/* Processing state */}
        {(run.status === "pending" || run.status === "processing") && (
          <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-700/30 rounded-xl p-6 flex items-center gap-4">
            <Loader2 className="w-5 h-5 text-blue-500 dark:text-blue-400 animate-spin shrink-0" />
            <div>
              <p className="text-sm text-blue-700 dark:text-blue-300 font-medium">AI analysis in progress…</p>
              <p className="text-xs text-slate-500 mt-1">This page auto-refreshes every 3s</p>
            </div>
          </div>
        )}

        {/* Regression insight */}
        {run.status === "completed" && run.build_insight && (
          <div>
            <h2 className="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-3">AI Build Assessment</h2>
            <RegressionInsights insight={run.build_insight as any} />
          </div>
        )}

        {/* Failures */}
        {run.status === "completed" && (
          <div>
            <h2 className="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-3">
              Failures ({failures.length})
            </h2>
            {failLoading ? (
              <p className="text-slate-500 text-sm">Loading failures…</p>
            ) : failures.length === 0 ? (
              <div className="text-center py-8 text-slate-500 border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-transparent">
                No failures — all tests passed! ✓
              </div>
            ) : (
              <FailureList failures={failures} />
            )}
          </div>
        )}
      </main>
    </div>
  );
}
