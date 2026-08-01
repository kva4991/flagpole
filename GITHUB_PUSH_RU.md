# Как самостоятельно опубликовать проект в GitHub

## 1. Распакуйте архив

Распакуйте каталог `crucian-flagpole-finial` в удобное место.

## 2. Проверьте публичное содержимое

Перед публикацией обратите внимание:

- в проекте нет паролей от реальных аккаунтов и токенов;
- в прошивке присутствует демонстрационный PIN по умолчанию — его нужно сменить перед эксплуатацией;
- лицензия пока не выбрана;
- крупные STL/GLB хранятся как обычные бинарные файлы.

## 3. Создайте репозиторий

```powershell
git init
git add .
git commit -m "Initial cumulative project import v0.6.0"
git branch -M main
git remote add origin https://github.com/USER/REPOSITORY.git
git push -u origin main
```

## 4. Git LFS

Самый большой файл проекта меньше ограничения GitHub в 100 МБ. Поэтому Git LFS не является обязательным.

При частых изменениях STL и GLB можно позже подключить Git LFS:

```powershell
git lfs install
git lfs track "*.stl" "*.glb" "*.blend"
git add .gitattributes
git commit -m "Track 3D assets with Git LFS"
```

Не подключайте LFS автоматически, если не хотите устанавливать его на всех компьютерах.
