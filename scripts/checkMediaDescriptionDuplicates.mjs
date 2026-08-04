import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { loadAndValidateMediaDescriptions } from './mediaDescriptions.mjs';

const root = process.cwd();
const media = JSON.parse(fs.readFileSync(path.join(root, 'catalog', 'drawings.json'), 'utf8'));
const { descriptions } = loadAndValidateMediaDescriptions(root, media);
const ignoredDirectories = new Set([
  '.build', '.cache', '.git', '.gradle', '.pio', '__pycache__', 'archive', 'build',
  'node_modules', 'catalog/media-descriptions',
]);
const ignoredFiles = new Set([
  'catalog/catalog.html',
  'CHECKSUMS_SHA256.txt',
  'SNAPSHOT_FILES_SHA256.txt',
]);
const textExtensions = new Set(['.html', '.json', '.md', '.mjs', '.py', '.txt']);

function normalizedRelative(absolutePath) {
  return path.relative(root, absolutePath).split(path.sep).join('/');
}

function walk(directory) {
  const files = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const absolutePath = path.join(directory, entry.name);
    const relativePath = normalizedRelative(absolutePath);
    if (entry.isDirectory()) {
      if ([...ignoredDirectories].some(ignored => relativePath === ignored || relativePath.startsWith(`${ignored}/`))) continue;
      files.push(...walk(absolutePath));
    } else if (textExtensions.has(path.extname(entry.name).toLowerCase()) && !ignoredFiles.has(relativePath)) {
      files.push({ absolutePath, relativePath });
    }
  }
  return files;
}

function rationaleParagraphs(body) {
  return body
    .replaceAll('\r\n', '\n')
    .split(/\n\s*\n/)
    .map(paragraph => paragraph.replaceAll(/\s+/g, ' ').trim())
    .filter(paragraph => paragraph.length >= 350)
    .filter(paragraph => !paragraph.startsWith('> **Статус:**'))
    .filter(paragraph => !paragraph.startsWith('При любом изменении карточки'))
    .filter(paragraph => !paragraph.startsWith('Минимальная цифровая проверка'));
}

const candidates = walk(root).map(file => ({
  ...file,
  normalizedText: fs.readFileSync(file.absolutePath, 'utf8').replaceAll(/\s+/g, ' '),
}));
const failures = [];
for (const [id, description] of descriptions) {
  const summary = description.metadata.summary.replaceAll(/\s+/g, ' ').trim();
  for (const file of candidates) {
    if (file.normalizedText.includes(summary)) {
      failures.push(`#${id}: summary продублирован в ${file.relativePath}`);
    }
  }
  for (const paragraph of rationaleParagraphs(description.body)) {
    for (const file of candidates) {
      if (file.normalizedText.includes(paragraph)) {
        failures.push(`#${id}: подробный rationale-фрагмент продублирован в ${file.relativePath}`);
      }
    }
  }
}

if (failures.length) {
  console.error(`Найдены дубли подробных медиа-описаний вне ID-папки:\n- ${[...new Set(failures)].join('\n- ')}`);
  process.exit(1);
}
console.log(`Дубли подробных медиа-описаний вне ID-папки не найдены: проверено ${descriptions.size} ID и ${candidates.length} редактируемых текстовых файлов.`);
