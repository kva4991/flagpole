import fs from 'node:fs';
import path from 'node:path';

const pointerPattern = /^version https:\/\/git-lfs\.github\.com\/spec\/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n?$/;

export function readLfsPointer(file) {
  const stats = fs.statSync(file);
  if (stats.size > 1024) return null;
  const match = fs.readFileSync(file, 'utf8').replaceAll('\r\n', '\n').match(pointerPattern);
  if (!match) return null;
  return { oid: match[1], size: Number(match[2]) };
}

const canonicalTextExtensions = new Set([
  '.html', '.json', '.md', '.svg', '.txt', '.xml', '.yaml', '.yml',
]);

export function readPortableFileSize(file) {
  const lfsPointer = readLfsPointer(file);
  if (lfsPointer) return lfsPointer.size;
  if (!canonicalTextExtensions.has(path.extname(file).toLowerCase())) return fs.statSync(file).size;
  const canonicalText = fs.readFileSync(file, 'utf8').replace(/\r\n?/g, '\n');
  return Buffer.byteLength(canonicalText, 'utf8');
}
