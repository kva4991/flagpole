import fs from 'node:fs';

const pointerPattern = /^version https:\/\/git-lfs\.github\.com\/spec\/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n?$/;

export function readLfsPointer(file) {
  const stats = fs.statSync(file);
  if (stats.size > 1024) return null;
  const match = fs.readFileSync(file, 'utf8').replaceAll('\r\n', '\n').match(pointerPattern);
  if (!match) return null;
  return { oid: match[1], size: Number(match[2]) };
}
