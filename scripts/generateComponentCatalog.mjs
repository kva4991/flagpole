import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const projectRoot = process.cwd();
const catalogPath = path.join(projectRoot, 'catalog', 'components.json');
const imageDirectory = path.join(projectRoot, 'catalog', 'images');
const htmlPath = path.join(projectRoot, 'catalog', 'catalog.html');

function htmlEscape(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function validate(source) {
  const failures = [];
  const ids = new Set();

  if (source.schemaVersion !== 1) failures.push('schemaVersion должен быть равен 1');
  if (!Array.isArray(source.components) || source.components.length === 0) {
    failures.push('components должен быть непустым массивом');
    return failures;
  }

  for (const [index, item] of source.components.entries()) {
    const place = `components[${index}]`;
    if (!/^cmp-\d{3}$/.test(item.id ?? '')) failures.push(`${place}.id должен иметь вид cmp-001`);
    if (ids.has(item.id)) failures.push(`${place}.id повторяется: ${item.id}`);
    ids.add(item.id);
    if (!item.name?.trim()) failures.push(`${place}.name обязателен`);
    if (!Array.isArray(item.aliases) || item.aliases.length === 0) failures.push(`${place}.aliases должен быть непустым массивом`);
    if (!item.purpose?.trim()) failures.push(`${place}.purpose обязателен`);
    if (!item.image?.trim() || path.basename(item.image) !== item.image) {
      failures.push(`${place}.image должен быть именем локального файла`);
    } else if (!fs.existsSync(path.join(imageDirectory, item.image))) {
      failures.push(`${place}.image не найден: catalog/images/${item.image}`);
    }
    if (item.additionalImages !== undefined) {
      if (!Array.isArray(item.additionalImages) || item.additionalImages.length === 0) {
        failures.push(`${place}.additionalImages должен быть непустым массивом`);
      }
      for (const [imageIndex, image] of (item.additionalImages ?? []).entries()) {
        if (!image.file?.trim() || path.basename(image.file) !== image.file || !image.label?.trim()) {
          failures.push(`${place}.additionalImages[${imageIndex}] требует безопасное имя file и label`);
        } else if (!fs.existsSync(path.join(imageDirectory, image.file))) {
          failures.push(`${place}.additionalImages[${imageIndex}].file не найден: catalog/images/${image.file}`);
        }
      }
    }
    if (!['confirmed', 'listing', 'reference', 'placeholder'].includes(item.imageStatus)) {
      failures.push(`${place}.imageStatus должен быть confirmed, listing, reference или placeholder`);
    }
    if (!Array.isArray(item.links)) failures.push(`${place}.links должен быть массивом`);
    for (const [linkIndex, link] of (item.links ?? []).entries()) {
      if (!link.label?.trim()) failures.push(`${place}.links[${linkIndex}].label обязателен`);
      try {
        const url = new URL(link.url);
        if (url.protocol !== 'https:') failures.push(`${place}.links[${linkIndex}].url должен использовать HTTPS`);
      } catch {
        failures.push(`${place}.links[${linkIndex}].url некорректен`);
      }
    }
    if (item.specifications !== undefined) {
      if (!Array.isArray(item.specifications) || item.specifications.length === 0) {
        failures.push(`${place}.specifications должен быть непустым массивом`);
      }
      for (const [specIndex, specification] of (item.specifications ?? []).entries()) {
        if (!specification.label?.trim() || !specification.value?.trim()) {
          failures.push(`${place}.specifications[${specIndex}] требует label и value`);
        }
      }
    }
    if (item.imageStatus === 'placeholder' && !item.missing?.trim()) {
      failures.push(`${place}.missing должен объяснять, какие данные нужны`);
    }
  }
  return failures;
}

function renderLinks(links) {
  if (links.length === 0) return '<span class="empty">Ссылка пока не подтверждена</span>';
  return `<ul class="links">${links.map(link => `<li><a href="${htmlEscape(link.url)}" target="_blank" rel="noopener noreferrer">${htmlEscape(link.label)}</a></li>`).join('')}</ul>`;
}

function renderSpecifications(specifications = []) {
  if (specifications.length === 0) return '';
  return `<dl class="specifications">${specifications.map(specification => `<div><dt>${htmlEscape(specification.label)}</dt><dd>${htmlEscape(specification.value)}</dd></div>`).join('')}</dl>`;
}

function renderImageBadge(imageStatus) {
  if (imageStatus === 'confirmed') return '<span class="badge ok">фото экземпляра</span>';
  if (imageStatus === 'listing') return '<span class="badge info">фото продавца</span>';
  if (imageStatus === 'reference') return '<span class="badge info">справочное изображение</span>';
  return '<span class="badge warning">нужно фото</span>';
}

function renderImages(item) {
  const images = [
    { file: item.image, label: item.name },
    ...(item.additionalImages ?? []),
  ];
  return `<div class="gallery">${images.map(image => `<figure><img class="thumb" src="images/${htmlEscape(image.file)}" alt="${htmlEscape(image.label)}" loading="lazy"><figcaption>${htmlEscape(image.label)}</figcaption></figure>`).join('')}</div>${renderImageBadge(item.imageStatus)}`;
}

const source = JSON.parse(fs.readFileSync(catalogPath, 'utf8'));
const failures = validate(source);
if (failures.length > 0) {
  console.error(`Ошибки catalog/components.json:\n- ${failures.join('\n- ')}`);
  process.exit(1);
}

const incompleteCount = source.components.filter(item => item.imageStatus === 'placeholder' || item.missing).length;
const rows = source.components.map(item => {
  const incomplete = item.imageStatus === 'placeholder' || item.missing;
  const searchText = [item.id, item.name, ...item.aliases, item.purpose, ...(item.specifications ?? []).flatMap(specification => [specification.label, specification.value]), item.missing ?? ''].join(' ').toLowerCase();
  return `
    <tr data-incomplete="${incomplete}" data-search="${htmlEscape(searchText)}">
      <td class="id-cell"><code>${htmlEscape(item.id)}</code><button class="copy-id" type="button" data-id="${htmlEscape(item.id)}" title="Скопировать ID">копировать</button></td>
      <td class="image-cell">${renderImages(item)}</td>
      <td><strong>${htmlEscape(item.name)}</strong><ul class="aliases">${item.aliases.map(alias => `<li>${htmlEscape(alias)}</li>`).join('')}</ul></td>
      <td><p>${htmlEscape(item.purpose)}</p>${renderSpecifications(item.specifications)}${item.missing ? `<aside class="needed"><strong>Нужно уточнить:</strong> ${htmlEscape(item.missing)}</aside>` : ''}</td>
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
:root { color-scheme: light dark; --bg:#edf1f3; --panel:#fff; --ink:#172126; --muted:#607078; --line:#d3dde1; --accent:#067a78; --accent-soft:#d8f0ed; --warn:#9b4d00; --warn-bg:#fff0d9; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif; }
header { padding:clamp(24px,5vw,56px); color:#fff; background:linear-gradient(125deg,#15373d,#087d78); }
header h1 { margin:0 0 8px; font-size:clamp(28px,5vw,48px); line-height:1.1; }
header p { max-width:850px; margin:0; color:#daf4f1; }
main { max-width:1500px; margin:auto; padding:24px; }
.summary { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin-top:-48px; margin-bottom:20px; }
.metric { padding:16px 18px; border:1px solid var(--line); border-radius:14px; background:var(--panel); box-shadow:0 8px 30px #102d3320; }
.metric strong { display:block; font-size:28px; color:var(--accent); }
.controls { display:flex; flex-wrap:wrap; align-items:end; gap:12px; padding:16px; border:1px solid var(--line); border-radius:14px; background:var(--panel); }
.search { flex:1 1 360px; }
label span { display:block; margin-bottom:5px; font-weight:650; }
input[type="search"] { width:100%; padding:11px 13px; border:1px solid var(--line); border-radius:9px; background:var(--panel); color:var(--ink); font:inherit; }
.toggle { display:flex; align-items:center; gap:8px; padding:10px 4px; }
.toggle span { margin:0; }
.result-count { color:var(--muted); padding:10px 2px; }
.table-wrap { overflow:auto; margin-top:16px; border:1px solid var(--line); border-radius:14px; background:var(--panel); }
table { width:100%; min-width:1080px; border-collapse:collapse; }
th,td { padding:14px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { position:sticky; top:0; z-index:1; background:#e4eeef; color:#27464c; font-size:13px; text-transform:uppercase; letter-spacing:.035em; }
tbody tr:last-child td { border-bottom:0; }
tbody tr:hover { background:#f3faf9; }
.id-cell code { display:block; font-weight:700; color:var(--accent); }
.copy-id { margin-top:8px; padding:3px 7px; border:1px solid var(--line); border-radius:6px; background:transparent; color:var(--muted); cursor:pointer; }
.gallery { display:grid; gap:8px; }
.gallery figure { margin:0; }
.gallery figcaption { margin-top:3px; max-width:180px; color:var(--muted); font-size:11px; }
.thumb { width:180px; height:140px; object-fit:contain; display:block; border:1px solid var(--line); border-radius:9px; background:#fff; }
.badge { display:inline-block; margin-top:8px; padding:3px 8px; border-radius:999px; font-size:12px; font-weight:700; }
.warning { color:var(--warn); background:var(--warn-bg); }
.ok { color:#126534; background:#dff4e7; }
.info { color:#075985; background:#e0f2fe; }
.aliases,.links { margin:8px 0 0; padding-left:18px; }
.specifications { display:grid; gap:6px; margin:12px 0 0; }
.specifications div { display:grid; grid-template-columns:minmax(95px,auto) 1fr; gap:8px; padding-top:6px; border-top:1px solid var(--line); }
.specifications dt { font-weight:700; color:var(--muted); }
.specifications dd { margin:0; }
.needed { margin-top:10px; padding:10px; border-left:4px solid #db7b16; background:var(--warn-bg); color:#633500; }
.empty { color:var(--muted); font-style:italic; }
.no-results { display:none; padding:30px; text-align:center; color:var(--muted); }
footer { max-width:1500px; margin:auto; padding:0 24px 30px; color:var(--muted); }
@media (prefers-color-scheme:dark) { :root { --bg:#0d171a; --panel:#152227; --ink:#edf6f5; --muted:#a5b5ba; --line:#34464c; --accent:#5ed5cd; --accent-soft:#193a39; --warn:#ffbd78; --warn-bg:#3b2b1b; } th{background:#20343a;color:#c9e7e5} tbody tr:hover{background:#193136}.needed{color:#ffd6a6}.thumb{background:#f8f8f8} a{color:#70c9ff} }
@media (max-width:700px) { main{padding:16px}.summary{margin-top:-32px}.copy-id{display:none} }
</style>
</head>
<body>
<header>
  <h1>Каталог компонентов Crucian</h1>
  <p>Рабочая ведомость известных деталей. Пометка различает фото продавца, фото реального экземпляра и временный эскиз. Чтобы дополнить карточку, пришлите её ID, фотографии, надписи на детали и ссылку продавца.</p>
</header>
<main>
  <section class="summary" aria-label="Сводка">
    <div class="metric"><strong>${source.components.length}</strong>позиций в каталоге</div>
    <div class="metric"><strong>${incompleteCount}</strong>требуют уточнения</div>
    <div class="metric"><strong>${source.components.reduce((total, item) => total + item.links.length, 0)}</strong>справочных ссылок</div>
  </section>
  <section class="controls" aria-label="Фильтры">
    <label class="search"><span>Поиск по ID, названию и назначению</span><input id="search" type="search" placeholder="например: cmp-003, ESP32, токосъёмник"></label>
    <label class="toggle"><input id="incompleteOnly" type="checkbox"><span>Только позиции, которые нужно уточнить</span></label>
    <output id="resultCount" class="result-count"></output>
  </section>
  <div class="table-wrap">
    <table id="catalogTable">
      <thead><tr><th>ID</th><th>Картинка</th><th>Возможные названия компонента</th><th>Зачем он нужен</th><th>Описание или покупка</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    <p id="noResults" class="no-results">По заданному фильтру ничего не найдено.</p>
  </div>
</main>
<footer>Источник данных: <code>catalog/components.json</code>. Страница автономна и не загружает скрипты, шрифты или изображения из интернета.</footer>
<script>
const input = document.getElementById('search');
const incompleteOnly = document.getElementById('incompleteOnly');
const table = document.getElementById('catalogTable');
const resultCount = document.getElementById('resultCount');
const noResults = document.getElementById('noResults');
function applyFilters() {
  const query = input.value.trim().toLowerCase();
  let visible = 0;
  for (const row of table.tBodies[0].rows) {
    const matchesText = row.dataset.search.includes(query);
    const matchesState = !incompleteOnly.checked || row.dataset.incomplete === 'true';
    row.hidden = !(matchesText && matchesState);
    if (!row.hidden) visible += 1;
  }
  resultCount.value = 'Показано: ' + visible;
  noResults.style.display = visible === 0 ? 'block' : 'none';
}
input.addEventListener('input', applyFilters);
incompleteOnly.addEventListener('change', applyFilters);
for (const button of document.querySelectorAll('.copy-id')) {
  button.addEventListener('click', async () => {
    await navigator.clipboard.writeText(button.dataset.id);
    const previous = button.textContent;
    button.textContent = 'скопировано';
    setTimeout(() => { button.textContent = previous; }, 1200);
  });
}
applyFilters();
</script>
</body>
</html>`;

if (process.argv.includes('--check')) {
  const current = fs.existsSync(htmlPath) ? fs.readFileSync(htmlPath, 'utf8') : '';
  if (current !== html) {
    console.error('catalog/catalog.html не соответствует catalog/components.json. Запустите npm run catalog:generate.');
    process.exitCode = 1;
  } else {
    console.log('Каталог компонентов синхронизирован.');
  }
} else {
  fs.writeFileSync(htmlPath, html, 'utf8');
  console.log(`Generated ${htmlPath}`);
}
