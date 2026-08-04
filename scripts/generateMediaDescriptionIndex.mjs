import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import crypto from 'node:crypto';
import { loadAndValidateMediaDescriptions } from './mediaDescriptions.mjs';

const root = process.cwd();
const mediaPath = path.join(root, 'catalog', 'drawings.json');
const outputPath = path.join(root, 'catalog', 'media-descriptions', 'INDEX_RU.md');
const media = JSON.parse(fs.readFileSync(mediaPath, 'utf8'));
const { descriptions, records } = loadAndValidateMediaDescriptions(root, media);

const typeLabel = new Map([
  ['drawing', '2D-чертёж/схема'],
  ['model', 'интерактивная 3D-модель'],
  ['print-layout', 'раскладка/очередь печати'],
]);

const rows = records
  .slice()
  .sort((a, b) => a.id.localeCompare(b.id, 'ru'))
  .map(item => {
    const description = descriptions.get(item.id);
    const bytes = fs.statSync(description.absolutePath).size;
    const sha256 = crypto.createHash('sha256').update(fs.readFileSync(description.absolutePath)).digest('hex');
    return `| [#${item.id}](${item.id}.md) | ${typeLabel.get(item.kind) ?? item.kind} | ${item.title.replaceAll('|', '\\|')} | \`${item.file}\` | \`${description.metadata.sourceOfTruth}\` | ${bytes.toLocaleString('ru-RU')} | \`${sha256.slice(0, 12)}…\` |`;
  });

const counts = Object.fromEntries(['drawings', 'models', 'experimentalModels', 'printSessions'].map(section => [section, records.filter(item => item.catalogSection === section).length]));
const body = `# Индекс подробных описаний чертежей и 3D-моделей\n\n<!-- generated: scripts/generateMediaDescriptionIndex.mjs -->\n\nЭтот файл генерируется из \`catalog/drawings.json\` и одноимённых Markdown-файлов. Вручную его не редактировать. Полный контракт находится в [README_RU.md](README_RU.md), решение — в [ADR-0032](../../docs/architecture/decisions/0032-one-media-id-one-rationale-file.ru.md). §mediarationale1\n\n## Сводка\n\n- всего медиа-ID: **${records.length}**;\n- карточек 2D: **${counts.drawings}**;\n- текущих карточек 3D: **${counts.models}**;\n- экспериментальных карточек CAD: **${counts.experimentalModels}**;\n- операционных карточек очередей: **${counts.printSessions}**;\n- каждый ID имеет ровно один файл, а подробный текст в \`catalog/drawings.json\` отсутствует.\n\n## Реестр\n\n| ID | Тип | Название | Основной файл | Источник истины | Байт | SHA-256 файла |\n| --- | --- | --- | --- | --- | ---: | --- |\n${rows.join('\n')}\n\n## Как пользоваться\n\nПеред изменением конкретного рисунка или модели открыть файл по его ID и прочитать его полностью. После изменения обновить этот файл, первичный CAD/SVG-источник, производные медиа, запись каталога и проверки в одной правке. Затем выполнить \`npm.cmd run media:descriptions:check\`.\n`;

if (process.argv.includes('--check')) {
  const current = fs.existsSync(outputPath) ? fs.readFileSync(outputPath, 'utf8') : '';
  if (current !== body) {
    console.error('catalog/media-descriptions/INDEX_RU.md не соответствует карточкам и описаниям. Запустите npm run media:descriptions:generate.');
    process.exit(1);
  }
  console.log(`Индекс медиа-описаний синхронизирован: ${records.length} ID.`);
} else {
  fs.writeFileSync(outputPath, body, 'utf8');
  console.log(`Generated ${path.relative(root, outputPath)}`);
}
