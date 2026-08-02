# Как опубликовать кумулятивный архив v0.7.4

Архив содержит полное дерево проекта без `.git`, кэшей и локальных build-каталогов.

## Вариант 1: заменить содержимое локального клона

```powershell
git clone https://github.com/kva4991/flagpole.git
cd flagpole
git checkout main
git pull --ff-only
```

Распакуйте каталог `flagpole-v0.7.4` рядом. Скопируйте его содержимое поверх клона, удалив файлы, которые отсутствуют в архиве, но не удаляйте `.git`.

Проверка:

```powershell
npm.cmd run quality:gate
git status --short
git diff --check
```

Публикация:

```powershell
git checkout -b update/v0.7.4
git add -A
git commit -m "Release cumulative v0.7.4 mechanical update"
git push -u origin update/v0.7.4
```

После push дождитесь GitHub Actions. Зелёный CI не заменяет печать купонов и аппаратные испытания.

## Проверка архива

Сравните SHA-256 ZIP с отдельным файлом `.sha256`. Внутри проекта `CHECKSUMS_SHA256.txt` проверяет каждый публикуемый файл:

```powershell
npm.cmd run checksums:check
```
