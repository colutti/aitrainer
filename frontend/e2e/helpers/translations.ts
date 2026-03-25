import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load translation file synchronously for E2E usage
const localesPath = path.resolve(__dirname, '../../src/locales/pt-BR.json');
const ptBR = JSON.parse(fs.readFileSync(localesPath, 'utf-8'));

/**
 * E2E Translation Helper
 * 
 * Provides access to real application strings during tests.
 * Supports nested keys using dot notation (e.g., 'common.save').
 */
export function t(pathStr: string, params?: Record<string, string | number>): string {
  const keys = pathStr.split('.');
  let current: any = ptBR;

  for (const key of keys) {
    if (current && typeof current === 'object' && key in current) {
      current = current[key];
    } else {
      console.warn(`QA Warning: Translation key not found: ${pathStr} (failed at ${key})`);
      return pathStr;
    }
  }

  let result = String(current);

  // Simple interpolation for {{count}}, {{name}}, etc.
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      result = result.replace(`{{${key}}}`, String(value));
    });
  }

  return result;
}
