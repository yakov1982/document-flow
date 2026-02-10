# Проект под 1С:Предприятие 8.3 (шаблон)

Этот каталог — заготовка для разработки на **1С:Предприятие 8.3** в рамках данного репозитория и пример интеграции с backend из `DIGITAL_DOCUMENTS_MVP/backend` (FastAPI).

## Что внутри

- `bsl/LeximaDmsHttpClient.bsl` — пример HTTP‑клиента на BSL:
  - получение JWT токена через `POST /auth/token`
  - вызов `GET /auth/me`, `GET /documents`, `GET /tasks/my`
  - примеры `POST /documents/{id}/approve|reject` (передача `comment` как form-data)
- `.gitignore` — типовые исключения для 1С/EDT/локальных ИБ.

## Как использовать BSL‑клиент

1) Запустите backend (см. `DIGITAL_DOCUMENTS_MVP/README.md`) на `http://localhost:8080`.

2) Создайте пользователя:

```bash
cd DIGITAL_DOCUMENTS_MVP/backend
python manage.py create-user --username admin --password admin --role admin
```

3) В 1С добавьте **общий модуль** (например, `LeximaDmsHttpClient`) и вставьте туда содержимое файла `bsl/LeximaDmsHttpClient.bsl`.

Рекомендации:
- свойства модуля: **Сервер** = Да, **Вызов сервера** = Разрешен, **Экспорт** = Да.

4) Пример вызова (например, из обработчика команды/тестовой процедуры):

```bsl
Процедура Пример_СписокДокументов() Экспорт
	
	Клиент = LeximaDmsHttpClient.Создать("localhost", 8080, Ложь);
	Токен = Клиент.ПолучитьТокен("admin", "admin");
	
	Документы = Клиент.СписокДокументов(Токен, "", "");
	Сообщить("Документов: " + Документы.Количество());
	
КонецПроцедуры
```

## Примечания по интеграции

- Авторизация — OAuth2 password flow: `POST /auth/token` (x-www-form-urlencoded), ответ содержит поле `access_token`.
- Для запросов используйте заголовок `Authorization: Bearer <token>`.
- Если backend развернут по HTTPS или за reverse-proxy, передайте соответствующие параметры в конструктор клиента.

