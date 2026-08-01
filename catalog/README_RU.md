# Каталог компонентов и локальная HTML-страница

<!-- §catalog -->

Этот каталог адаптирован под проект Crucian по той же идее, что и инструкция из другого проекта:

- один JSON-файл `catalog/components.json` хранит редактируемые данные;
- генератор `scripts/generateComponentCatalog.mjs` строит автономную HTML-страницу `catalog/catalog.html`;
- отдельный backend не нужен;
- при необходимости страницу можно открывать локально через Python mini-server.

## Структура

```text
project/
├── catalog/
│   ├── components.json
│   ├── catalog.html
│   ├── images/
│   └── README_RU.md
└── scripts/
    └── generateComponentCatalog.mjs
```

## Поля строки каталога

- `id` — внутренний идентификатор позиции;
- `image` — имя локального файла с изображением;
- `aliases` — возможные названия, по которым компонент можно искать;
- `purpose` — пояснение, зачем он нужен;
- `links` — список ссылок на описание или покупку.

## Перегенерация

Из корня проекта:

```powershell
npm.cmd run catalog:generate
npm.cmd run catalog:check
```

Первая команда обновляет HTML, вторая ничего не изменяет и завершается ошибкой,
если опубликованная страница расходится с JSON-источником.

## Открытие без сервера

Можно просто открыть файл:

```powershell
Start-Process .\catalog\catalog.html
```

## Локальный mini-server

Если удобнее открыть страницу по HTTP:

```powershell
py -m http.server 8080 --bind 127.0.0.1
```

После этого открыть:

```text
http://127.0.0.1:8080/catalog/catalog.html
```

`--bind 127.0.0.1` принципиален: страница должна быть доступна только локально.
