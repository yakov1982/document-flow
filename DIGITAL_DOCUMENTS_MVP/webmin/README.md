# Webmin module для DIGITAL DOCUMENTS MVP

Модуль Webmin для управления настройками системы документооборота через веб-интерфейс.

## Установка

1. Скопируйте каталог `lexima-dms` в директорию модулей Webmin:

```bash
sudo cp -r lexima-dms /usr/share/webmin/
```

2. Установите права:

```bash
sudo chown -R root:root /usr/share/webmin/lexima-dms
sudo chmod 755 /usr/share/webmin/lexima-dms
sudo chmod 755 /usr/share/webmin/lexima-dms/*.cgi
```

3. Перезагрузите Webmin или обновите страницу — модуль появится в меню.

## Настройка

1. Откройте **Webmin** → **Document Management System** (или **Система документооборота**).
2. Укажите **Путь к backend** — каталог с `manage.py` и `lexima_dms` (например, `/opt/documents-mvp/backend`).
3. Заполните настройки JWT и LDAP/AD DS.
4. Нажмите **Сохранить**.

Настройки записываются в файл `.env` в каталоге backend. После изменений перезапустите сервис приложения (uvicorn).

## Управляемые параметры

- **JWT**: секрет, алгоритм, время жизни токена
- **Data directory**: каталог данных
- **LDAP/AD DS**: включение, URL, Base DN, учётная запись сервиса, фильтр поиска, роль по умолчанию

## Требования

- Webmin 1.x или совместимый
- Perl 5.10+
