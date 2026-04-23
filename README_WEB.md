# Kit Runner Web Server

Веб-интерфейс для управления задачами Kit Runner.

## Быстрый запуск

```bash
# Запуск сервера (по умолчанию на http://0.0.0.0:7700)
python web_server.py

# Запуск на другом порту
python web_server.py --port 8080

# Запуск на конкретном хосте
python web_server.py --host 127.0.0.1

# Запуск с отладкой
python web_server.py --debug

# Запуск с указанием конфига
python web_server.py --config config.yaml
```

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `PORT` | Порт для сервера | `7700` |

Сервер автоматически читает переменную `PORT` из окружения — это удобно для деплоя на Render, Heroku и других платформах.

### Деплой на Render

#### Вариант A: Python Service (без Docker)

**Build Command:**
```bash
pip install -r requirements.txt
```

**Pre-Deploy Command:**
```bash
apt-get update && apt-get install -y yt-dlp ffmpeg
```

**Start Command:**
```bash
python web_server.py
```

#### Вариант B: Docker Service

Используйте готовый `Dockerfile` в репозитории. В настройках Render выберите **Docker** как среду развертывания.

Render автоматически установит переменную `PORT`, сервер запустится на нужном порту и будет доступен извне.

---

## Системные требования

Для работы пайплайнов необходимы следующие инструменты:

| Инструмент | Назначение | Установка (Linux) |
|------------|------------|-------------------|
| `yt-dlp` | Скачивание видео/аудио | `apt-get install yt-dlp` |
| `ffmpeg` | Обработка медиа | `apt-get install ffmpeg` |
| `openai-whisper` | Транскрибация | `pip install openai-whisper` |

Проверить наличие инструментов:
```bash
yt-dlp --version
ffmpeg -version
whisper --version
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

### Запуск с cookies (для YouTube)
```bash
curl -X POST http://localhost:7700/api/run \
  -F "goal=Скачать видео" \
  -F "input_data={\"url\": \"https://...\"}" \
  -F "cookies_file=@cookies.txt"
```

---

## YouTube Cookies

Для доступа к возрастным видео и обхода ограничений YouTube требуется аутентификация.

### Как экспортировать cookies

**Способ 1: Расширение браузера**
1. Установите расширение "Get cookies.txt" (Chrome/Firefox)
2. Зайдите на YouTube и войдите в аккаунт
3. Нажмите на иконку расширения → "Export cookies"
4. Сохраните файл `cookies.txt`

**Способ 2: Утилита ytdlp-cookies**
```bash
pip install ytdlp-cookies
ytdlp-cookies --browser chrome
```

### Загрузка через веб-интерфейс

1. Откройте вкладку **"Новая задача"**
2. Заполните цель (например, "Скачать видео с YouTube")
3. Укажите URL в JSON параметрах: `{"url": "https://youtube.com/watch?v=..."}`
4. Выберите файл `cookies.txt` в поле **"Cookies файл"**
5. Нажмите **"Запустить задачу"**

### Поддерживаемые браузеры

| Браузер | Параметр |
|---------|----------|
| Chrome | `chrome` |
| Firefox | `firefox` |
| Edge | `edge` |
| Safari | `safari` |

Для локального запуска можно использовать параметр `cookies_from_browser` вместо файла:
```json
{"url": "https://...", "cookies_from_browser": "chrome"}
```

### Получить список задач
```bash
curl http://localhost:7700/api/jobs
```

### Получить детали задачи
```bash
curl http://localhost:7700/api/jobs/<job_id>
```
