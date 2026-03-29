import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const fixturesDir = path.resolve(__dirname, '../fixtures/imports');

const fixturePaths = {
  mfp: path.resolve(fixturesDir, 'mfp-sample.csv'),
  zepp: path.resolve(fixturesDir, 'zepp-life-sample.csv'),
} as const;

type FixtureKind = keyof typeof fixturePaths;

export function loadImportFixture(kind: FixtureKind, replacements: Record<string, string> = {}) {
  let content = fs.readFileSync(fixturePaths[kind], 'utf-8');

  for (const [from, to] of Object.entries(replacements)) {
    content = content.replaceAll(from, to);
  }

  return {
    name: path.basename(fixturePaths[kind]),
    mimeType: 'text/csv',
    buffer: Buffer.from(content, 'utf-8'),
  };
}
