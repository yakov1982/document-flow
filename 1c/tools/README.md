# `1c/tools/` — утилиты (опционально)

Здесь лежат небольшие helper-скрипты для работы с Конфигуратором в batch-режиме.

## Скрипты

### `dump-config.sh`
Выгружает **конфигурацию ИБ** в файлы (текстовые исходники) в каталог `1c/src/` (или в указанный).

Пример для файловой ИБ:

```bash
export V8_DESIGNER="/opt/1cv8/x86_64/8.3.xx.xxxx/1cv8"
./1c/tools/dump-config.sh --out ./1c/src /F "/path/to/ib"
```

Пример для серверной ИБ:

```bash
export V8_DESIGNER="/opt/1cv8/x86_64/8.3.xx.xxxx/1cv8"
./1c/tools/dump-config.sh --out ./1c/src /S "server\\base" /N "user" /P "pass"
```

### `load-config.sh`
Загружает конфигурацию **из файлов** в ИБ.

```bash
export V8_DESIGNER="/opt/1cv8/x86_64/8.3.xx.xxxx/1cv8"
./1c/tools/load-config.sh --src ./1c/src /F "/path/to/ib"
```

> Примечание: после загрузки часто требуется обновить конфигурацию БД (`/UpdateDBCfg`). Это зависит от процесса и прав. При необходимости просто добавьте ключи в конец команды (скрипт пробрасывает аргументы как есть).

