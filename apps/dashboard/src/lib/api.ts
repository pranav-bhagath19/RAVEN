/**
 * RAVEN Next.js Frontend REST API Client
 * Connects directly to RAVEN FastAPI Control Plane endpoints (defaulting to http://localhost:8000/api/v1).
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface UserSession {
  apiKey: string;
  tenantId: string;
  role: string;
}

export function getStoredAuth(): UserSession {
  if (typeof window === "undefined") {
    return { apiKey: "admin_dev_key", tenantId: "tenant_demo", role: "ADMIN" };
  }
  const apiKey = localStorage.getItem("raven_api_key") || "admin_dev_key";
  const tenantId = localStorage.getItem("raven_tenant_id") || "tenant_demo";
  const role = localStorage.getItem("raven_role") || "ADMIN";
  return { apiKey, tenantId, role };
}

export function setStoredAuth(apiKey: string, tenantId: string, role: string = "ADMIN") {
  if (typeof window !== "undefined") {
    localStorage.setItem("raven_api_key", apiKey);
    localStorage.setItem("raven_tenant_id", tenantId);
    localStorage.setItem("raven_role", role);
  }
}

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const { apiKey, tenantId } = getStoredAuth();
  const headers = new Headers(options.headers || {});
  headers.set("X-API-Key", apiKey);
  headers.set("X-Tenant-ID", tenantId);
  headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData?.error?.message || errorData?.detail || `API error (${response.status})`;
    throw new Error(message);
  }

  return response.json();
}
