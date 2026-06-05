import clsx from "clsx";

export default function ConfidenceIndicator({ score }: { score?: number }) {
  if (score == null) return null;
  const color = score >= 70 ? "bg-emerald-500" : score >= 40 ? "bg-yellow-400" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div className={clsx("h-full rounded-full transition-all", color)} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs text-slate-500">{score}% confidence</span>
    </div>
  );
}
