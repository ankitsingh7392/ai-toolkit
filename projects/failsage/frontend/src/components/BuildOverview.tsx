import { formatDistanceToNow } from "date-fns";
import { AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import type { Run } from "../api/client";

const statusIcon = {
  completed: <CheckCircle2 className="w-4 h-4 text-emerald-500" />,
  processing: <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />,
  pending: <Loader2 className="w-4 h-4 text-slate-400 animate-spin" />,
  failed: <AlertTriangle className="w-4 h-4 text-red-500" />,
};

export default function BuildOverview({ runs }: { runs: Run[] }) {
  if (!runs.length) {
    return (
      <div className="text-center py-20 text-slate-400">
        No runs yet. Send a Jenkins webhook to{" "}
        <code className="text-indigo-500 dark:text-indigo-400">/api/ci/jenkins/test-results</code>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-500 border-b border-slate-200 dark:border-slate-700 text-xs">
            <th className="pb-2 pr-4 font-medium">Job / Build</th>
            <th className="pb-2 pr-4 font-medium">Branch</th>
            <th className="pb-2 pr-4 font-medium">Env</th>
            <th className="pb-2 pr-4 font-medium">Tests</th>
            <th className="pb-2 pr-4 font-medium">Risk</th>
            <th className="pb-2 pr-4 font-medium">Status</th>
            <th className="pb-2 font-medium">Age</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.run_id} className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
              <td className="py-3 pr-4">
                <Link to={`/runs/${run.run_id}`} className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium">
                  {run.job_name}
                </Link>
                <span className="text-slate-400 text-xs ml-2">#{run.build_id}</span>
              </td>
              <td className="py-3 pr-4">
                <span className="text-xs bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded">{run.branch}</span>
              </td>
              <td className="py-3 pr-4 text-slate-500 dark:text-slate-400">{run.environment}</td>
              <td className="py-3 pr-4">
                <div className="flex gap-3 text-xs">
                  <span className="text-emerald-600 dark:text-emerald-400">{run.passed_tests}✓</span>
                  <span className="text-red-500 dark:text-red-400">{run.failed_tests + run.error_tests}✗</span>
                  <span className="text-slate-400">{run.skipped_tests}⊘</span>
                </div>
              </td>
              <td className="py-3 pr-4">
                {run.build_at_risk ? (
                  <span className="flex items-center gap-1 text-red-500 dark:text-red-400 text-xs">
                    <AlertTriangle className="w-3 h-3" /> {run.risk_level}
                  </span>
                ) : (
                  <span className="text-emerald-600 dark:text-emerald-500 text-xs">OK</span>
                )}
              </td>
              <td className="py-3 pr-4">
                <span className="flex items-center gap-1.5">
                  {statusIcon[run.status as keyof typeof statusIcon] ?? null}
                  <span className="text-slate-600 dark:text-slate-300 capitalize">{run.status}</span>
                </span>
              </td>
              <td className="py-3 text-slate-400 text-xs whitespace-nowrap">
                {formatDistanceToNow(new Date(run.created_at), { addSuffix: true })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
