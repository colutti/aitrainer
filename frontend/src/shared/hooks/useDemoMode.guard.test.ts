import { readdirSync, readFileSync } from 'node:fs';
import { join, relative } from 'node:path';

import { describe, expect, it } from 'vitest';

const FRONTEND_SRC = join(process.cwd(), 'src');
const ALLOWED_FILES = new Set([
  'shared/hooks/useAuth.ts',
  'shared/hooks/useDemoMode.ts',
]);

function readDirRecursive(root: string): string[] {
  const entries = readdirSync(root, { withFileTypes: true });
  const files: string[] = [];

  for (const entry of entries) {
    const fullPath = join(root, entry.name);
    if (entry.isDirectory()) {
      files.push(...readDirRecursive(fullPath));
      continue;
    }

    if (entry.isFile()) {
      files.push(fullPath);
    }
  }

  return files;
}

describe('demo mode guard', () => {
  it('keeps demo flag reads centralized in the shared hook', () => {
    const violations: string[] = [];
    const files = readDirRecursive(FRONTEND_SRC);

    for (const filePath of files) {
      if (!filePath.endsWith('.ts') && !filePath.endsWith('.tsx')) {
        continue;
      }

      const relativePath = relative(FRONTEND_SRC, filePath).replace(/\\/g, '/');
      if (ALLOWED_FILES.has(relativePath)) {
        continue;
      }

      if (relativePath.endsWith('.test.ts') || relativePath.endsWith('.test.tsx')) {
        continue;
      }

      const content = readFileSync(filePath, 'utf8');
      if (content.includes('userInfo?.is_demo') || content.includes('is_demo === true')) {
        violations.push(relativePath);
      }
    }

    expect(violations).toEqual([]);
  });
});
