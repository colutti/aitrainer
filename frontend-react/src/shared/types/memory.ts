export interface Memory {
  id: string;
  memory: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface MemoryListResponse {
  memories: Memory[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
