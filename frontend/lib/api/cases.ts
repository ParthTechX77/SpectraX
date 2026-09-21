import { apiGet, apiPost } from "../api";

export type Case = {
  id: string;
  case_number: string;
  title: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type CreateCaseInput = {
  title: string;
  description?: string;
};

export function createCase(
  data: CreateCaseInput,
): Promise<Case> {
  return apiPost<Case>("/api/v1/cases", data);
}

export function getCases(): Promise<Case[]> {
  return apiGet<Case[]>("/api/v1/cases");
}

export function getCase(caseId: string): Promise<Case> {
  return apiGet<Case>(`/api/v1/cases/${caseId}`);
}