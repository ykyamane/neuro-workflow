import { createAuthHeaders } from "./authHeaders";

export type CatalogSource = "dandi" | "cbs" | "brainminds" | "bmb_human" | "aws";

export interface CatalogDataUrl {
  url: string;
  label: string;
  browse_url?: string;
  type?: string;
  size?: number;
  asset_id?: string;
  file_id?: string;
  path?: string;
  mime_type?: string;
}

export interface CatalogDataset {
  source: string;
  dataset_id: string;
  name: string;
  description?: string;
  synced_at?: string;
  landing_page?: string;
  data_url_count: number;
  data_url_total?: number;
  truncated?: boolean;
  data_urls?: CatalogDataUrl[];
  metadata?: Record<string, unknown>;
}

export interface CatalogSearchResponse {
  datasets: CatalogDataset[];
  count: number;
  query: string;
  source?: string | null;
}

export interface CatalogStatusResponse {
  mdb_available: boolean;
  mdb_base_url?: string;
  statistics?: {
    total_datasets?: number;
    source_counts?: Record<string, number>;
    sync_status?: Record<
      string,
      {
        datasets_count?: number;
        last_sync?: string;
        status?: string;
        error_message?: string | null;
      }
    >;
    timestamp?: string;
  };
  error?: string;
}

async function catalogFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = await createAuthHeaders();
  const response = await fetch(path, {
    ...init,
    headers: {
      ...headers,
      ...(init?.headers || {}),
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message =
      (data as { error?: string }).error ||
      `Catalog API error (${response.status})`;
    throw new Error(message);
  }

  return data as T;
}

export async function fetchCatalogStatus(): Promise<CatalogStatusResponse> {
  return catalogFetch<CatalogStatusResponse>("/api/catalog/status/");
}

export async function searchCatalog(
  query: string,
  source?: CatalogSource
): Promise<CatalogSearchResponse> {
  const params = new URLSearchParams({ q: query });
  if (source) {
    params.set("source", source);
  }
  return catalogFetch<CatalogSearchResponse>(
    `/api/catalog/search/?${params.toString()}`
  );
}

export async function fetchCatalogDataset(
  source: string,
  datasetId: string
): Promise<CatalogDataset> {
  const data = await catalogFetch<{ dataset: CatalogDataset }>(
    `/api/catalog/datasets/${encodeURIComponent(source)}/${encodeURIComponent(datasetId)}/`
  );
  return data.dataset;
}

export async function syncCatalog(): Promise<unknown> {
  return catalogFetch("/api/catalog/sync/", { method: "POST" });
}
