/*
 * Проверяет всю документацию: репозиторий небольшой, поэтому полный локальный
 * проход быстрее и надёжнее сложной выборки по Git. §docqa01
 */
import { readdirSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { auditDocumentation, formatDocumentationAudit } from '../tools/quality/documentationAudit.mjs';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const ignoredDirectories = new Set(['.build', '.git', '.gradle', '.pio', 'build', 'node_modules']);

function markdownTree(root) {
  const files = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    if (entry.isDirectory() && ignoredDirectories.has(entry.name)) continue;
    const path = join(root, entry.name);
    if (entry.isDirectory()) files.push(...markdownTree(path));
    else if (entry.name.endsWith('.md')) files.push(relative(repoRoot, path).replaceAll('\\', '/'));
  }
  return files;
}

const report = auditDocumentation(markdownTree(repoRoot), { repoRoot });
console.log(formatDocumentationAudit(report));
if (report.brokenLinks.length || report.unknownTags.length || report.missingNpmScripts.length) {
  process.exitCode = 1;
}
