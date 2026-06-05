import { useEffect, useRef, useState } from "react";
import { CalendarDays, ChevronDown, X } from "lucide-react";

export type DatePreset = "24h" | "3d" | "7d" | "15d" | "30d" | "custom" | "";

export interface DateRange {
  preset: DatePreset;
  from: string;
  to: string;
}

export const EMPTY_RANGE: DateRange = { preset: "", from: "", to: "" };

const PRESETS: { key: Exclude<DatePreset, "" | "custom">; label: string }[] = [
  { key: "24h", label: "Last 24 hours" },
  { key: "3d",  label: "Last 3 days"   },
  { key: "7d",  label: "Last 7 days"   },
  { key: "15d", label: "Last 15 days"  },
  { key: "30d", label: "Last 30 days"  },
];

function toISO(localValue: string) {
  if (!localValue) return "";
  return new Date(localValue).toISOString();
}

function presetToDates(preset: Exclude<DatePreset, "" | "custom">): { from: string; to: string } {
  const now = new Date();
  const days: Record<string, number> = { "24h": 1 / 24, "3d": 3, "7d": 7, "15d": 15, "30d": 30 };
  const ms = days[preset] * 24 * 60 * 60 * 1000;
  return {
    from: new Date(now.getTime() - ms).toISOString(),
    to: now.toISOString(),
  };
}

function labelFor(range: DateRange): string {
  if (!range.preset) return "All time";
  if (range.preset !== "custom")
    return PRESETS.find((p) => p.key === range.preset)?.label ?? "All time";
  if (range.from && range.to)
    return `${new Date(range.from).toLocaleDateString()} – ${new Date(range.to).toLocaleDateString()}`;
  if (range.from) return `From ${new Date(range.from).toLocaleDateString()}`;
  return "Custom range";
}

export default function DateRangePicker({
  value,
  onChange,
}: {
  value: DateRange;
  onChange: (r: DateRange) => void;
}) {
  const [open, setOpen] = useState(false);
  const [customFrom, setCustomFrom] = useState(
    value.preset === "custom" && value.from
      ? new Date(value.from).toISOString().slice(0, 16)
      : ""
  );
  const [customTo, setCustomTo] = useState(
    value.preset === "custom" && value.to
      ? new Date(value.to).toISOString().slice(0, 16)
      : ""
  );
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function selectPreset(preset: Exclude<DatePreset, "" | "custom">) {
    const { from, to } = presetToDates(preset);
    onChange({ preset, from, to });
    setOpen(false);
  }

  function clearRange() {
    setCustomFrom("");
    setCustomTo("");
    onChange(EMPTY_RANGE);
  }

  function handleCustomFrom(val: string) {
    setCustomFrom(val);
    if (val && customTo) {
      onChange({ preset: "custom", from: toISO(val), to: toISO(customTo) });
    }
  }

  function handleCustomTo(val: string) {
    setCustomTo(val);
    if (customFrom && val) {
      onChange({ preset: "custom", from: toISO(customFrom), to: toISO(val) });
    }
  }

  const active = value.preset !== "";

  return (
    <div className="flex flex-col gap-1 relative" ref={ref}>
      <label className="text-xs text-slate-500 uppercase tracking-wider font-medium">Date Range</label>

      <button
        onClick={() => setOpen((o) => !o)}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm transition-colors min-w-[180px]
          ${active
            ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-300"
            : "border-slate-300 dark:border-slate-700 bg-white dark:bg-[#0f1117] text-slate-500 dark:text-slate-400 hover:border-slate-400 dark:hover:border-slate-500"
          }`}
      >
        <CalendarDays className="w-3.5 h-3.5 shrink-0" />
        <span className="flex-1 text-left truncate">{labelFor(value)}</span>
        {active ? (
          <X
            className="w-3.5 h-3.5 shrink-0 hover:text-indigo-800 dark:hover:text-white"
            onClick={(e) => { e.stopPropagation(); clearRange(); setOpen(false); }}
          />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 shrink-0" />
        )}
      </button>

      {open && (
        <div className="absolute top-full mt-1 left-0 z-50 bg-white dark:bg-[#1a1d2e] border border-slate-200 dark:border-[#2a2d3e] rounded-xl shadow-lg dark:shadow-2xl overflow-hidden min-w-[220px]">
          {/* Presets */}
          <div className="p-2">
            {PRESETS.map((p) => (
              <button
                key={p.key}
                onClick={() => selectPreset(p.key)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors
                  ${value.preset === p.key
                    ? "bg-indigo-600 text-white"
                    : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700/60"
                  }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Custom */}
          <div className="border-t border-slate-100 dark:border-[#2a2d3e]">
            <button
              onClick={() => {
                if (value.preset !== "custom") onChange({ preset: "custom", from: "", to: "" });
              }}
              className={`w-full text-left px-5 py-2.5 text-sm transition-colors
                ${value.preset === "custom"
                  ? "bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-300 font-medium"
                  : "text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/40"
                }`}
            >
              Custom range
            </button>

            {value.preset === "custom" && (
              <div className="px-4 pb-4 pt-1 space-y-3">
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-slate-500">Start</label>
                  <input
                    type="datetime-local"
                    value={customFrom}
                    onChange={(e) => handleCustomFrom(e.target.value)}
                    className="bg-slate-50 dark:bg-[#0f1117] border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:border-indigo-500 dark:[color-scheme:dark] w-full"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-slate-500">End</label>
                  <input
                    type="datetime-local"
                    value={customTo}
                    onChange={(e) => handleCustomTo(e.target.value)}
                    className="bg-slate-50 dark:bg-[#0f1117] border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:border-indigo-500 dark:[color-scheme:dark] w-full"
                  />
                </div>
                {customFrom && customTo && (
                  <p className="text-xs text-emerald-600 dark:text-emerald-400">✓ Applied automatically</p>
                )}
                {(!customFrom || !customTo) && (
                  <p className="text-xs text-slate-400">Select both dates to apply</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
