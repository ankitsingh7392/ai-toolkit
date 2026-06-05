import { useQuery } from "@tanstack/react-query";
import { flakyApi } from "../api/client";

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = pct > 70 ? "bg-red-500" : pct > 40 ? "bg-yellow-400" : "bg-emerald-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-500">{pct}%</span>
    </div>
  );
}

export default function FlakyTracker() {
  const { data = [], isLoading } = useQuery({
    queryKey: ["flaky"],
    queryFn: flakyApi.list,
    refetchInterval: 30_000,
  });

  if (isLoading) return <p className="text-slate-500 text-sm">Loading flaky tests…</p>;
  if (!data.length) return <p className="text-slate-400 text-sm">No flaky tests detected yet.</p>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-500 border-b border-slate-200 dark:border-slate-700 text-xs">
            <th className="pb-2 pr-4 font-medium">Test</th>
            <th className="pb-2 pr-4 font-medium">Job</th>
            <th className="pb-2 pr-4 font-medium">Pass/Fail</th>
            <th className="pb-2 font-medium">Flakiness</th>
          </tr>
        </thead>
        <tbody>
          {data.map((f) => (
            <tr key={f.id} className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40">
              <td className="py-2.5 pr-4">
                <p className="text-slate-700 dark:text-slate-200 text-xs font-medium truncate max-w-xs">{f.test_name}</p>
                <p className="text-slate-400 text-xs truncate">{f.classname}</p>
              </td>
              <td className="py-2.5 pr-4 text-slate-500 dark:text-slate-400 text-xs">{f.job_name}</td>
              <td className="py-2.5 pr-4 text-xs">
                <span className="text-emerald-600 dark:text-emerald-400">{f.pass_count}✓</span>
                <span className="text-slate-300 dark:text-slate-600 mx-1">/</span>
                <span className="text-red-500 dark:text-red-400">{f.fail_count}✗</span>
              </td>
              <td className="py-2.5">
                <ScoreBar score={f.flakiness_score} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
