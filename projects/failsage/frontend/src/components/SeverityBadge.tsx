import clsx from "clsx";

const map: Record<string, string> = {
  P0: "bg-red-600 text-white",
  P1: "bg-orange-500 text-white",
  P2: "bg-yellow-500 text-black",
  P3: "bg-slate-500 text-white",
};

export default function SeverityBadge({ severity }: { severity?: string }) {
  if (!severity) return null;
  return (
    <span className={clsx("px-2 py-0.5 rounded text-xs font-bold", map[severity] ?? "bg-slate-600 text-white")}>
      {severity}
    </span>
  );
}
