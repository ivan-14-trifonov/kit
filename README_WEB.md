# Kit Runner Web Server

Веб-интерфейс для управления задачами Kit Runner.

## Быстрый запуск

```bash
# Запуск сервера (по умолчанию на http://localhost:7700)
python web_server.py

# Запуск на другом порту
python web_server.py --port 8080

# Запуск с отладкой
python web_server.py --debug

# Запуск с указанием конфига
python web_server.py --config config.yaml
```

## Возможности

- **Запуск задач** - создание новых задач через веб-интерфейс
- **Мониторинг** - просмотр списка всех задач и их статуса
- **Детали задач** - просмотр шагов, ошибок, выходных файлов
- **Возобновление** - перезапуск paused/failed задач
- **Инструменты** - просмотр доступных инструментов и их режимов

## API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Веб-интерфейс |
| POST | `/api/run` | Запуск новой задачи |
| GET | `/api/jobs` | Список задач |
| GET | `/api/jobs/<id>` | Детали задачи |
| POST | `/api/jobs/<id>/resume` | Возобновить задачу |
| GET | `/api/tools` | Список инструментов |
| GET | `/api/files/<path>` | Скачать файл |
| GET | `/api/status` | Статус сервера |

## Примеры API

### Запуск задачи
```bash
curl -X POST http://localhost:7700/api/run \
  -H "Content-Type: application/json" \
  -d '{"goal": "Скачать видео", "input_data": {"url": "https://..."}}'
```

### Получить список задач
```bash
curl http://localhost:7700/api/jobs
```

### Получить детали задачи
```bash
curl http://localhost:7700/api/jobs/<job_id>
```
