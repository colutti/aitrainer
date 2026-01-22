export interface ImportResult {
  imported: number;
  skipped: number;
  failed: number;
  errors?: number; // Some endpoints use 'errors', others use 'failed'
  created?: number;
  updated?: number;
}
