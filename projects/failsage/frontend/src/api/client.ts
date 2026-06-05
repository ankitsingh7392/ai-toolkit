import axios from "axios";

export const api = axios.create({ baseURL: "/api" });

export interface Run {
  id: string;
  run_id: string;
  status: string;
  build_id: string;
  job_name: string;
  git_commit: string;
  branch: string;
  environment: string;
  jenkins_url?: string;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  error_tests: number;
  skipped_tests: number;
  build_at_risk: boolean;
  risk_level?: string;
  regression_commit?: string;
  build_insight?: BuildInsight;
  created_at: string;
  completed_at?: string;
}

export interface BuildInsight {
  build_at_risk: boolean;
  risk_level: string;
  risk_rationale: string;
  likely_regression_commit?: string;
  regression_reasoning?: string;
  affected_components: string[];
  recommended_action: string;
  action_rationale: string;
  confidence_score: number;
  patterns_detected: string[];
}

export interface RootCause {
  observed_facts: string[];
  inferred_reasoning: string;
  summary: string;
}

export interface AIAnalysis {
  failure_category: string;
  root_cause: RootCause;
  severity: string;
  severity_rationale: string;
  is_flaky: boolean;
  flakiness_indicators: string[];
  debugging_steps: string[];
  confidence_score: number;
  low_confidence_reasons: string[];
  suggested_fix?: string;
  related_components: string[];
}

export interface TestCase {
  id: string;
  run_id: string;
  suite_name: string;
  classname: string;
  name: string;
  duration: number;
  status: string;
  failure_message?: string;
  failure_type?: string;
  stack_trace?: string;
  failure_category?: string;
  root_cause_summary?: string;
  severity?: string;
  is_flaky: boolean;
  confidence_score?: number;
  ai_analysis?: AIAnalysis;
  cluster_id?: string;
  created_at: string;
}

export interface FlakyTest {
  id: string;
  test_name: string;
  classname: string;
  job_name: string;
  fail_count: number;
  pass_count: number;
  total_runs: number;
  flakiness_score: number;
  indicators: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface RunFilters {
  limit?: number;
  offset?: number;
  job_name?: string;
  branch?: string;
  environment?: string;
  status?: string;
  build_at_risk?: boolean;
  date_from?: string;
  date_to?: string;
}

export interface RunsMeta {
  jobs: string[];
  branches: string[];
  environments: string[];
}

export const runsApi = {
  list: (params?: RunFilters) =>
    api.get<Run[]>("/runs", { params }).then((r) => r.data),
  get: (runId: string) => api.get<Run>(`/runs/${runId}`).then((r) => r.data),
  meta: () => api.get<RunsMeta>("/runs/meta").then((r) => r.data),
};

export const failuresApi = {
  list: (runId: string, params?: { severity?: string; flaky_only?: boolean }) =>
    api.get<TestCase[]>(`/failures/${runId}`, { params }).then((r) => r.data),
};

export const flakyApi = {
  list: () => api.get<FlakyTest[]>("/flaky-tests").then((r) => r.data),
};

export const feedbackApi = {
  submit: (data: {
    test_case_id: string;
    is_helpful: boolean;
    correct_category?: string;
    correct_severity?: string;
    feedback_notes?: string;
    engineer_email?: string;
  }) => api.post("/feedback", data).then((r) => r.data),
};
