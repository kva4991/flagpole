/*
 * Создаёт и проверяет воспроизводимый SHA-256 manifest всего публикуемого дерева.
 * Build/cache-каталоги и сам manifest исключены. §checksum
 */
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readLfsPointer } from './lfsPointer.mjs';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const manifestPath = resolve(repoRoot, 'CHECKSUMS_SHA256.txt');
const ignoredDirectories = new Set(['.build', '.cache', '.git', '.gradle', '.pio', '__pycache__', 'build', 'node_modules']);
const textExtensions = new Set([
  '.bat', '.cpp', '.h', '.html', '.ini', '.ino', '.json', '.kt', '.kts',
  '.md', '.mjs', '.pro', '.properties', '.ps1', '.py', '.svg', '.txt',
  '.xml', '.yaml', '.yml',
]);
const textBasenames = new Set(['.gitattributes', '.gitignore', 'gradlew']);

function walk(root) {
  const files = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    // In a normal clone .git is a directory; in a linked worktree it is a
    // pointer file. Neither form belongs to the published project manifest.
    if (ignoredDirectories.has(entry.name)) continue;
    const path = join(root, entry.name);
    if (entry.isDirectory()) files.push(...walk(path));
    else if (resolve(path) !== manifestPath) files.push(path);
  }
  return files;
}

function manifest() {
  return walk(repoRoot)
    .map((path) => relative(repoRoot, path).replaceAll('\\', '/'))
    .sort((left, right) => (left < right ? -1 : left > right ? 1 : 0))
    .map((path) => {
      const absolutePath = resolve(repoRoot, path);
      const lfsPointer = readLfsPointer(absolutePath);
      if (lfsPointer) return `${lfsPointer.oid}  ${path}`;
      const extension = path.slice(path.lastIndexOf('.')).toLowerCase();
      const basename = path.split('/').at(-1);
      const content = textExtensions.has(extension) || textBasenames.has(basename)
        ? readFileSync(absolutePath, 'utf8').replaceAll('\r\n', '\n').replaceAll('\r', '\n')
        : readFileSync(absolutePath);
      const hash = createHash('sha256').update(content).digest('hex');
      return `${hash}  ${path}`;
    })
    .join('\n') + '\n';
}

const expected = manifest();
if (process.argv.includes('--update')) {
  writeFileSync(manifestPath, expected, 'utf8');
  console.log(`Обновлён ${relative(repoRoot, manifestPath)}.`);
} else if (!existsSync(manifestPath) || readFileSync(manifestPath, 'utf8').replaceAll('\r\n', '\n') !== expected) {
  console.error('CHECKSUMS_SHA256.txt не соответствует публикуемому дереву. Запустите npm run checksums:update.');
  process.exitCode = 1;
} else {
  console.log('Контрольные суммы публикуемого дерева совпадают.');
}
