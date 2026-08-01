import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const projectRoot = process.cwd();
const catalogPath = path.join(projectRoot, 'catalog', 'components.json');
const htmlPath = path.join(projectRoot, 'catalog', 'catalog.html');

function htmlEscape(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function renderLinks(links) {
  if (!links || links.length === 0) {
    return '<span class="muted">ссылки пока не добавлены</span>';
  }
  return '<ul>' + links.map(link => `<li><a href="${htmlEscape(link.url)}" target="_blank" rel="noreferrer">${htmlEscape(link.label)}</a></li>`).join('') + '</ul>';
}

const source = JSON.parse(fs.readFileSync(catalogPath, 'utf-8'));
const rows = source.components.map(item => {
  return `
    <tr>
      <td>${htmlEscape(item.id)}</td>
      <td><img class="thumb" src="images/${htmlEscape(item.image)}" alt="${htmlEscape(item.name)}"></td>
      <td><strong>${htmlEscape(item.name)}</strong><br><small>${item.aliases.map(htmlEscape).join('<br>')}</small></td>
      <td>${htmlEscape(item.purpose)}</td>
      <td>${renderLinks(item.links)}</td>
    </tr>`;
}).join('');

const html = `<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crucian — каталог компонентов</title>
<style>
:root { color-scheme: light dark; }
body { font-family: Arial, Helvetica, sans-serif; margin: 0; background: #f5f5f5; color: #202020; }
header { padding: 20px 24px; background: #222; color: #fff; }
main { padding: 24px; }
input { width: min(540px, 100%); padding: 10px 12px; font-size: 16px; }
table { width: 100%; border-collapse: collapse; background: #fff; margin-top: 16px; }
th, td { border: 1px solid #ddd; padding: 10px; vertical-align: top; }
th { background: #fafafa; text-align: left; }
.thumb { width: 180px; max-width: 100%; height: auto; display: block; }
.muted { color: #666; }
@media (prefers-color-scheme: dark) {
  body { background: #121212; color: #f0f0f0; }
  table { background: #1a1a1a; }
  th, td { border-color: #444; }
  th { background: #222; }
  a { color: #8cc6ff; }
}
</style>
</head>
<body>
<header>
  <h1>Crucian — каталог компонентов</h1>
  <p>Локальная автономная HTML-страница. JSON — источник истины. Таблицу можно дополнять вручную через <code>catalog/components.json</code> и повторную генерацию.</p>
</header>
<main>
  <label>
    <span>Поиск</span><br>
    <input id="search" type="search" placeholder="например, ESP32, MOSFET, M12, TPU">
  </label>
  <table id="catalogTable">
    <thead>
      <tr>
        <th>ID</th>
        <th>Картинка</th>
        <th>Возможные названия компонента</th>
        <th>Пояснение, зачем нужен</th>
        <th>Ссылки</th>
      </tr>
    </thead>
    <tbody>${rows}</tbody>
  </table>
</main>
<script>
const input = document.getElementById('search');
const table = document.getElementById('catalogTable');
input.addEventListener('input', () => {
  const q = input.value.trim().toLowerCase();
  for (const row of table.tBodies[0].rows) {
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  }
});
</script>
</body>
</html>`;

if (process.argv.includes('--check')) {
  const current = fs.existsSync(htmlPath) ? fs.readFileSync(htmlPath, 'utf-8') : '';
  if (current !== html) {
    console.error('catalog/catalog.html не соответствует catalog/components.json. Запустите npm run catalog:generate.');
    process.exitCode = 1;
  } else {
    console.log('Каталог компонентов синхронизирован.');
  }
} else {
  fs.writeFileSync(htmlPath, html, 'utf-8');
  console.log(`Generated ${htmlPath}`);
}
