import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { Activity, AlertTriangle, CheckCircle2, Filter, X, Zap, Database } from "lucide-react";
import { runsApi } from "../api/client";
import BuildOverview from "../components/BuildOverview";
import FlakyTracker from "../components/FlakyTracker";
import ThemeToggle from "../components/ThemeToggle";
import DateRangePicker, { EMPTY_RANGE, type DateRange } from "../components/DateRangePicker";
import { useTheme } from "../hooks/useTheme";

// ── Filter state (single source of truth — every change auto-applies) ─────────
interface Filters {
  job_name: string;
  branch: string;
  environment: string;
  status: string;
  risk: "" | "true" | "false";
  dateRange: DateRange;
}

const EMPTY: Filters = {
  job_name: "",
  branch: "",
  environment: "",
  status: "",
  risk: "",
  dateRange: EMPTY_RANGE,
};

function activeCount(f: Filters) {
  return [f.job_name, f.branch, f.environment, f.status, f.risk, f.dateRange.preset].filter(Boolean).length;
}

function toApiParams(f: Filters) {
  const p: Record<string, string | boolean | number> = { limit: 1000 };
  if (f.job_name) p.job_name = f.job_name;
  if (f.branch) p.branch = f.branch;
  if (f.environment) p.environment = f.environment;
  if (f.status) p.status = f.status;
  if (f.risk !== "") p.build_at_risk = f.risk === "true";
  if (f.dateRange.from) p.date_from = f.dateRange.from;
  if (f.dateRange.to) p.date_to = f.dateRange.to;
  return p;
}

// ── Sub-components ────────────────────────────────────────────────────────────
function FilterSelect({
  label,
  value,
  onChange,
  options,
  placeholder = "All",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
  placeholder?: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-slate-500 dark:text-slate-500 uppercase tracking-wider font-medium">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-white dark:bg-[#0f1117] border border-slate-300 dark:border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 cursor-pointer min-w-[140px] transition-colors"
      >
        <option value="">{placeholder}</option>
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </div>
  );
}

function StatCard({ icon, label, value, sub, accent }: {
  icon: React.ReactNode; label: string; value: string | number; sub?: string; accent?: string;
}) {
  return (
    <div className="bg-white dark:bg-[#1a1d2e] border border-slate-200 dark:border-[#2a2d3e] rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="text-slate-500 text-xs uppercase tracking-wider font-medium">{label}</span>
        <span className={accent ?? "text-slate-400"}>{icon}</span>
      </div>
      <p className={`text-3xl font-bold ${accent ?? "text-slate-800 dark:text-slate-200"}`}>{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
    </div>
  );
}

function Chip({ label, value, onRemove }: { label: string; value: string; onRemove: () => void }) {
  return (
    <span className="flex items-center gap-1.5 text-xs bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/50 px-2.5 py-1 rounded-full font-medium">
      <span className="text-indigo-400">{label}:</span>
      {value}
      <button onClick={onRemove} className="hover:text-indigo-900 dark:hover:text-white transition-colors ml-0.5">
        <X className="w-3 h-3" />
      </button>
    </span>
  );
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { theme, toggle: toggleTheme } = useTheme();
  const [filters, setFilters] = useState<Filters>(EMPTY);
  const [filtersOpen, setFiltersOpen] = useState(true);

  const set = <K extends keyof Filters>(key: K, val: Filters[K]) =>
    setFilters((f) => ({ ...f, [key]: val }));

  const clear = () => setFilters(EMPTY);
  const numActive = activeCount(filters);

  const { data: meta } = useQuery({
    queryKey: ["runs-meta"],
    queryFn: runsApi.meta,
    staleTime: 30_000,
  });

  // Auto-applies: filters is the query key — every change triggers a fetch
  const { data: runs = [], isLoading, error } = useQuery({
    queryKey: ["runs", filters],
    queryFn: () => runsApi.list(toApiParams(filters) as any),
    refetchInterval: 15_000,
  });

  const totalTests = runs.reduce((s, r) => s + r.total_tests, 0);
  const totalPassed = runs.reduce((s, r) => s + r.passed_tests, 0);
  const totalFailed = runs.reduce((s, r) => s + r.failed_tests + r.error_tests, 0);
  const atRisk = runs.filter((r) => r.build_at_risk).length;
  const completed = runs.filter((r) => r.status === "completed").length;
  const passRate = totalTests ? Math.round((totalPassed / totalTests) * 100) : null;

  const chartData = useMemo(
    () =>
      [...runs].slice(0, 15).reverse().map((r) => ({
        name: `#${r.build_id}`,
        job: r.job_name,
        passed: r.passed_tests,
        failed: r.failed_tests + r.error_tests,
      })),
    [runs]
  );

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0f1117] transition-colors duration-200">

      {/* Header */}
      <header className="bg-white dark:bg-[#0f1117] border-b border-slate-200 dark:border-[#2a2d3e] px-8 py-4 flex items-center justify-between sticky top-0 z-20 shadow-sm dark:shadow-none">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🔬</span>
          <div>
            <h1 className="text-base font-bold text-slate-900 dark:text-slate-100">FailSage</h1>
            <p className="text-xs text-slate-400">AI reads your failures, so you don't have to</p>
          </div>
        </div>
        <div className="flex items-center gap-2.5">
          <span className="flex items-center gap-1.5 text-xs text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/40 px-2 py-1 rounded-lg font-medium">
            <Database className="w-3 h-3" /> {runs.length} runs
          </span>
          <ThemeToggle theme={theme} onToggle={toggleTheme} />
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer"
            className="text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 border border-indigo-200 dark:border-indigo-800 px-3 py-1.5 rounded-lg transition-colors">
            API Docs →
          </a>
        </div>
      </header>

      <main className="px-8 py-6 space-y-5 max-w-7xl mx-auto">

        {/* ── Filter bar ── */}
        <div className="bg-white dark:bg-[#1a1d2e] border border-slate-200 dark:border-[#2a2d3e] rounded-xl shadow-sm dark:shadow-none overflow-visible">
          <button
            onClick={() => setFiltersOpen((o) => !o)}
            className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors rounded-xl"
          >
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-indigo-500" />
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">Filters</span>
              {numActive > 0 && (
                <span className="bg-indigo-600 text-white text-xs px-1.5 py-0.5 rounded-full font-medium">
                  {numActive}
                </span>
              )}
            </div>
            <span className="text-slate-400 text-xs">{filtersOpen ? "▲" : "▼"}</span>
          </button>

          {filtersOpen && (
            <div className="border-t border-slate-100 dark:border-[#2a2d3e] px-5 py-4">
              {/* Controls row */}
              <div className="flex flex-wrap gap-3 items-end">
                <FilterSelect
                  label="Job"
                  value={filters.job_name}
                  onChange={(v) => set("job_name", v)}
                  options={meta?.jobs ?? []}
                />
                <FilterSelect
                  label="Branch"
                  value={filters.branch}
                  onChange={(v) => set("branch", v)}
                  options={meta?.branches ?? []}
                />
                <FilterSelect
                  label="Environment"
                  value={filters.environment}
                  onChange={(v) => set("environment", v)}
                  options={meta?.environments ?? []}
                />
                <FilterSelect
                  label="Status"
                  value={filters.status}
                  onChange={(v) => set("status", v)}
                  options={["completed", "processing", "pending", "failed"]}
                />
                <FilterSelect
                  label="Risk"
                  value={filters.risk}
                  onChange={(v) => set("risk", v as Filters["risk"])}
                  options={["true", "false"]}
                  placeholder="All"
                />
                <DateRangePicker
                  value={filters.dateRange}
                  onChange={(r) => set("dateRange", r)}
                />
                {numActive > 0 && (
                  <div className="flex items-end pb-0.5">
                    <button
                      onClick={clear}
                      className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-slate-500 dark:text-slate-400 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 border border-slate-200 dark:border-slate-700 transition-colors"
                    >
                      <X className="w-3.5 h-3.5" /> Clear all
                    </button>
                  </div>
                )}
              </div>

              {/* Active chips */}
              {numActive > 0 && (
                <div className="flex flex-wrap gap-2 mt-3.5 pt-3 border-t border-slate-100 dark:border-slate-800">
                  {filters.job_name && <Chip label="Job" value={filters.job_name} onRemove={() => set("job_name", "")} />}
                  {filters.branch && <Chip label="Branch" value={filters.branch} onRemove={() => set("branch", "")} />}
                  {filters.environment && <Chip label="Env" value={filters.environment} onRemove={() => set("environment", "")} />}
                  {filters.status && <Chip label="Status" value={filters.status} onRemove={() => set("status", "")} />}
                  {filters.risk && <Chip label="Risk" value={filters.risk === "true" ? "At Risk" : "OK"} onRemove={() => set("risk", "")} />}
                  {filters.dateRange.preset && (
                    <Chip
                      label="Date"
                      value={filters.dateRange.preset !== "custom"
                        ? { "24h": "Last 24h", "3d": "Last 3 days", "7d": "Last 7 days", "15d": "Last 15 days", "30d": "Last 30 days" }[filters.dateRange.preset] ?? filters.dateRange.preset
                        : `${new Date(filters.dateRange.from).toLocaleDateString()} – ${new Date(filters.dateRange.to).toLocaleDateString()}`
                      }
                      onRemove={() => set("dateRange", EMPTY_RANGE)}
                    />
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Stats ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard icon={<Activity className="w-4 h-4" />} label="Runs" value={runs.length} sub={`${completed} completed`} />
          <StatCard icon={<CheckCircle2 className="w-4 h-4" />} label="Pass Rate" value={passRate !== null ? `${passRate}%` : "—"} accent="text-emerald-500" />
          <StatCard icon={<AlertTriangle className="w-4 h-4" />} label="At-Risk" value={atRisk} accent={atRisk > 0 ? "text-red-500" : "text-slate-400"} />
          <StatCard icon={<Zap className="w-4 h-4" />} label="Failures" value={totalFailed} accent={totalFailed > 0 ? "text-orange-500" : "text-slate-400"} />
        </div>

        {/* ── Trend chart ── */}
        {chartData.length > 1 && (
          <div className="bg-white dark:bg-[#1a1d2e] border border-slate-200 dark:border-[#2a2d3e] rounded-xl p-5 shadow-sm dark:shadow-none">
            <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">
              Build Trend
              <span className="text-slate-400 font-normal ml-2 text-xs">{chartData.length} builds</span>
            </h2>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={chartData} barSize={14} barGap={2}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: theme === "dark" ? "#1a1d2e" : "#fff", border: `1px solid ${theme === "dark" ? "#2a2d3e" : "#e2e8f0"}`, borderRadius: 8 }}
                  itemStyle={{ color: theme === "dark" ? "#cbd5e1" : "#334155" }}
                  formatter={(val, name) => [val, name === "passed" ? "Passed ✓" : "Failed ✗"]}
                  labelFormatter={(label, payload) => `${label}  ${payload?.[0]?.payload?.job ?? ""}`}
                />
                <Bar dataKey="passed" fill="#34d399" radius={[3, 3, 0, 0]} />
                <Bar dataKey="failed" fill="#f87171" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* ── Build table ── */}
        <div className="bg-white dark:bg-[#1a1d2e] border border-slate-200 dark:border-[#2a2d3e] rounded-xl p-6 shadow-sm dark:shadow-none">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Jenkins Builds</h2>
            <span className="text-xs text-slate-400">{runs.length} result{runs.length !== 1 ? "s" : ""}</span>
          </div>
          {isLoading ? (
            <p className="text-slate-400 text-sm">Loading…</p>
          ) : error ? (
            <p className="text-red-500 text-sm">Failed to load. Is the backend running?</p>
          ) : (
            <BuildOverview runs={runs} />
          )}
        </div>

        {/* ── Flaky tests ── */}
        <div className="bg-white dark:bg-[#1a1d2e] border border-slate-200 dark:border-[#2a2d3e] rounded-xl p-6 shadow-sm dark:shadow-none">
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-5 flex items-center gap-2">
            <Zap className="w-4 h-4 text-yellow-500" /> Flaky Test Tracker
          </h2>
          <FlakyTracker />
        </div>

      </main>
    </div>
  );
}
