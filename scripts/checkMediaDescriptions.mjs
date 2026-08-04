import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { loadAndValidateMediaDescriptions } from './mediaDescriptions.mjs';

const root = process.cwd();
const media = JSON.parse(fs.readFileSync(path.join(root, 'catalog', 'drawings.json'), 'utf8'));
const { descriptions, records } = loadAndValidateMediaDescriptions(root, media);
const characters = [...descriptions.values()].reduce((sum, item) => sum + item.body.length, 0);
console.log(`Подробные медиа-описания и критические контракты синхронизированы: ${descriptions.size}/${records.length} файлов, ${characters.toLocaleString('ru-RU')} символов.`);
