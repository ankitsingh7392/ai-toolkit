import { useState } from "react";
import { ChevronDown, ChevronRight, Terminal } from "lucide-react";

export default function StackTraceViewer({
  stackTrace,
  failureMessage,
}: {
  stackTrace?: string;
  failureMessage?: string;
}) {
  const [open, setOpen] = useState(false);

  if (!stackTrace && !failureMessage) return null;

  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center gap-2 px-4 py-2.5 bg-slate-100 dark:bg-slate-800/80 text-xs text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
      >
        <Terminal className="w-3.5 h-3.5" />
        <span className="font-medium">Stack Trace</span>
        {open ? <ChevronDown className="w-3.5 h-3.5 ml-auto" /> : <ChevronRight className="w-3.5 h-3.5 ml-auto" />}
      </button>

      {open && (
        <div className="bg-slate-50 dark:bg-[#0a0c14] p-4 overflow-x-auto">
          {failureMessage && (
            <p className="text-red-500 dark:text-red-400 text-xs font-medium mb-3 font-mono">{failureMessage}</p>
          )}
          {stackTrace && (
            <pre className="text-xs text-slate-600 dark:text-slate-400 font-mono whitespace-pre-wrap leading-relaxed">
              {stackTrace}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
