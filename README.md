# Kit Runner

Универсальный запускатор инструментов с автоматическим построением пайплайнов из описания цели на естественном языке.

## Возможности

- **Пайплайны из нескольких инструментов** — опишите цель словами, и система сама построит последовательность шагов (yt-dlp → whisper → ffmpeg и т.д.)
- **LLM-планирование** — LiteLLM подбирает инструменты и параметры; при недоступности LLM работает rule-based фоллбэк
- **Resumable jobs** — прерванную задачу можно продолжить с места остановки
- **Автоматическая установка зависимостей** — команда `install` ставит недостающие инструменты через winget / pip / pipx
- **Прокси-поддержка** — SOCKS5 / HTTP прокси для сетевых инструментов (включается/отключается по желанию)
- **Debug-архивы** — сбор логов и артефактов упавшей задачи одной командой

---

## Быстрый старт

### 1. Установка зависимостей

```bash
# Python-зависимости
pip install pyyaml litellm

# Системные инструменты (нужны для пайплайнов)
# macOS
brew install yt-dlp ffmpeg openai-whisper

# Linux (Debian/Ubuntu)
sudo apt install yt-dlp ffmpeg
pip install openai-whisper

# Windows (через winget)
winget install yt-dlp.yt-dlp Gyan.FFmpeg
pip install openai-whisper
```

### 2. Конфигурация

Отредактируйте `config.yaml`:

```yaml
llm:
  provider: openai
  model: qwen3-max
  api_base: "http://192.168.1.2:3264/v1"   # ваш LLM-эндпоинт
  api_key: "dummy"                          # или задайте через OPENAI_API_KEY
```

Если LLM недоступен — система автоматически использует rule-based фоллбэк.

---

## Запуск

### CLI: Kit Runner

```bash
# Запуск по цели (goal)
python -m runner.main --goal "Скачать аудио с YouTube" \
    --input "url=https://www.youtube.com/watch?v=VIDEO_ID"

# Пошаговое выполнение с подтверждением
python -m runner.main --goal "Транскрибировать видео" \
    --input "url=https://www.youtube.com/watch?v=VIDEO_ID" \
    --step-by-step

# Список доступных инструментов
python -m runner.main --tools

# Список последних задач
python -m runner.main --list

# Возобновление прерванной задачи
python -m runner.main --resume <job_id>

# Debug упавшей задачи
python -m runner.main --debug-job <job_id>
```

#### Основные флаги

| Флаг | Описание |
|------|----------|
| `--goal`, `-g` | Цель на естественном языке |
| `--input`, `-i` | Входной параметр `key=value` (можно несколько) |
| `--step-by-step`, `-s` | Подтверждение каждого шага |
| `--resume`, `-r` | ID задачи для возобновления |
| `--list`, `-l` | Показать последние задачи |
| `--tools`, `-t` | Показать доступные инструменты |
| `--debug-job`, `-d` | Собрать debug-архив по ID задачи |
| `--config`, `-c` | Путь к config.yaml (по умолчанию `./config.yaml`) |
| `--proxy` | Включить прокси с URL (например, `socks5://127.0.0.1:10808`) |
| `--no-proxy` | Отключить прокси для этого запуска |
| `--proxy-status` | Показать статус прокси и выйти |

---

## Доступные инструменты

| Инструмент | Режимы | Описание |
|------------|--------|----------|
| **yt-dlp** | `download`, `audio_only`, `subtitles`, `probe`, `playlist` | Скачивание видео/аудио, субтитров |
| **whisper** | `transcribe` | Транскрибация аудио в текст |
| **ffmpeg** | `convert`, `extract_audio` | Конвертация и обработка медиа |

Манифесты находятся в папке `manifests/` и описывают команды, входы/выходы и правила валидации для каждого режима.

---

## yt-dlp: скачивание видео и аудио

### Базовое использование

```bash
# Скачать видео (лучшее качество, формат выбирается автоматически)
python -m runner.main --goal "Скачать видео с YouTube" \
    --input "url=https://youtu.be/VIDEO_ID" --no-proxy

# Скачать аудио (конвертация в MP3)
python -m runner.main --goal "Скачать аудио с YouTube" \
    --input "url=https://youtu.be/VIDEO_ID" --no-proxy
```

### Выбор формата

Формат указывается через параметр `format`. Если не указан — yt-dlp выбирает лучшее качество автоматически.

```bash
# Скачать в 720p
python -m runner.main --goal "Скачать видео" \
    --input "url=https://youtu.be/VIDEO_ID" \
    --input "format=best[height<=720]" --no-proxy

# Скачать в 1080p
python -m runner.main --goal "Скачать видео" \
    --input "url=https://youtu.be/VIDEO_ID" \
    --input "format=best[height<=1080]" --no-proxy

# Только MP4 форматы
python -m runner.main --goal "Скачать видео" \
    --input "url=https://youtu.be/VIDEO_ID" \
    --input "format=best[ext=mp4]" --no-proxy

# Наименьшее качество (для экономии места)
python -m runner.main --goal "Скачать видео" \
    --input "url=https://youtu.be/VIDEO_ID" \
    --input "format=worst" --no-proxy
```

### Популярные форматы yt-dlp

| Формат | Описание |
|--------|----------|
| `bestvideo+bestaudio/best` | Лучшее качество (по умолчанию) |
| `best[height<=1080]` | Лучшее до 1080p |
| `best[height<=720]` | Лучшее до 720p |
| `best[ext=mp4]` | Лучшее в MP4 |
| `worst` | Наименьшее качество |
| `bestvideo` | Только видео (без аудио) |
| `bestaudio` | Только аудио (лучшее) |

### Выходные файлы

Файлы сохраняются в папке `outputs/` проекта:

```
project/
├── outputs/
│   ├── step-1/
│   │   └── Название_видео.mp4    # или .mp3 для audio_only
│   └── step-2/
│       └── ...
└── ...
```

Расширение файла определяется автоматически в зависимости от формата.

---

## Структура проекта

```
media_bot/
├── config.yaml              # Основная конфигурация
├── Dockerfile               # Docker образ
├── docker-compose.yml       # Docker Compose для разработки
├── .dockerignore            # Исключения для Docker
├── runner/                  # Ядро Kit Runner
│   ├── main.py              # CLI entry point
│   ├── executor.py          # Исполнитель шагов с retry
│   ├── pipeline.py          # LLM-планировщик пайплайнов
│   ├── installer.py         # Автоустановка инструментов
│   ├── job.py               # Модель задач и шагов
│   ├── validator.py         # Валидация результатов
│   ├── proxy.py             # Управление прокси
│   └── debug.py             # Сбор debug-архивов
├── manifests/               # Манифесты инструментов
│   ├── yt-dlp.yaml
│   ├── whisper.yaml
│   ├── ffmpeg.yaml
│   └── winget.yaml
├── youtube_audio.py         # Пользовательские сценарии
├── web_server.py            # Веб-сервер (Flask)
├── storage/                 # Хранилище задач и результатов
└── ui/                      # Веб-интерфейс (в разработке)
```
Пакетный модуль (__init__.py) экспортирует все публичные классы и функции из подмодулей, включая JobCard, StepExecutor, PipelineBuilder, KitRunner, ToolInstaller и DebugCollector.

Модуль job.py содержит модели данных и хранилище. В нём определяются JobCard (задача), StepCard (шаг), перечисления статусов, а также JobStorage — SQLite-хранилище для сохранения job-карточек и выходных данных.

Модуль executor.py отвечает за исполнитель шагов. Он запускает команды через subprocess, поддерживает повторные попытки (retry) с экспоненциальной задержкой, инжектирует прокси, выполняет парсинг stdout/stderr и валидацию выходных данных.

Модуль validator.py реализует валидатор выходных данных. Он проверяет файлы и параметры по схеме манифеста: типы данных, диапазоны значений, перечисления (enum), расширения файлов, а также выполняет probing медиафайлов через ffprobe.

Модуль pipeline_builder.py предоставляет построитель pipeline из естественного языка. Используя LiteLLM, он генерирует последовательность шагов по описанию цели. Поддерживается shortcut-детекция — например, фраза «установи ffmpeg» автоматически преобразуется в готовый шаблон.

Модуль installer.py представляет собой универсальный установщик инструментов. Он пробует методы установки по приоритету: сначала winget, затем pip/pipx, и наконец загрузка с GitHub releases. Содержит конфигурацию известных инструментов, таких как ffmpeg и yt-dlp.

Модуль debug_collector.py занимается сбором диагностической информации. При возникновении сбоя он создаёт ZIP-архив с job-карточкой, логами шагов, манифестами и системной информацией. Все чувствительные данные автоматически санитизируются (очищаются).

Наконец, модуль main.py является точкой входа в приложение. В нём определён класс KitRunner — оркестратор, который инициализирует хранилище, загрузку манифестов, executor и pipeline builder, а затем запускает pipeline на основе указанной цели.

---

## Входные данные в Kit Runner

  1. CLI (командная строка) — runner/main.py

   1 # main.py, функция main()
   2 parser.add_argument('--goal', '-g', help='Natural language goal to execute')
   3 parser.add_argument('--input', '-i', action='append', help='Input parameter (key=value)')

  Формат: пары key=value через аргумент --input:

   1 python -m runner.main --goal "Download video and extract audio" \
   2   --input "url=https://youtube.com/watch?v=abc123" \
   3   --input "format=mp3"

  Парсинг (строки → dict):

   1 # main.py, ~строка 340
   2 input_data = {}
   3 if args.input:
   4     for param in args.input:
   5         if '=' in param:
   6             key, value = param.split('=', 1)
   7             input_data[key] = value

  Результат — Dict[str, str], например:

   1 {"url": "https://youtube.com/watch?v=abc123", "format": "mp3"}

  ---

  2. Программный вызов — KitRunner.run_goal()

   1 # main.py, метод run_goal()
   2 def run_goal(
   3     self,
   4     goal: str,
   5     input_data: Dict[str, Any],   # ← входные данные
   6     expected_output: Optional[List[str]] = None,
   7     step_by_step: bool = False,
   8 ) -> JobCard:

  Формат: Dict[str, Any] — любой сериализуемый тип:

   1 runner.run_goal(
   2     goal="Download and transcribe",
   3     input_data={
   4         "url": "https://youtube.com/watch?v=xyz",
   5         "lang": "ru",
   6         "write_subs": True,
   7     }
   8 )

  ---

  3. Как данные проходят через pipeline
```
    1 input_data (Dict[str, Any])
    2     │
    3     ▼
    4 PipelineBuilder.build_pipeline(goal, input_data)  ← LLM читает данные при планировании
    5     │
    6     ▼
    7 JobCard.input_data  ← сохраняется в job
    8     │
    9     ▼
   10 StepCard.input_params  ← каждый шаг получает свои параметры
   11     │
   12     ▼
   13 StepExecutor._build_command()  ← подставляет в шаблон команды
   14     │
   15     ▼
   16 subprocess.Popen(cmd)  ← реальный запуск
```
  ---

  4. Ссылки на входные данные в шагах

  Шаги могут ссылаться на входные данные через $input.<key>:

   1 # pipeline.py, fallback-генерация
   2 {'url': '$input.url'}  ← будет заменено на реальное значение из input_data

  А также на выходы предыдущих шагов через $prev.<key>:

   1 {'audio_file': '$prev.output_file'}  ← цепочка между шагами


---

## Примеры пайплайнов

### Скачать видео с YouTube

```bash
# Лучшее качество (автоматический выбор формата)
python -m runner.main --goal "Скачать видео с YouTube" \
    --input "url=https://youtu.be/VIDEO_ID" --no-proxy

# Конкретный формат (720p)
python -m runner.main --goal "Скачать видео" \
    --input "url=https://youtu.be/VIDEO_ID" \
    --input "format=best[height<=720]" --no-proxy
```

### Скачать аудио с YouTube

```bash
python -m runner.main \
    --goal "Скачать аудио с YouTube" \
    --input "url=https://www.youtube.com/watch?v=dQw4w9WgXcQ" --no-proxy
```

Файл сохраняется в `outputs/step-1/` проекта.

### Транскрибировать видео

```bash
python -m runner.main \
    --goal "Транскрибировать видео на русский" \
    --input "url=https://www.youtube.com/watch?v=VIDEO_ID" \
    --input "language=ru"
```

Система автоматически построит пайплайн: `yt-dlp (download) → whisper (transcribe)`.

---

## Прокси

Прокси используется для обхода географических ограничений (например, для YouTube).

### Настройка в config.yaml

```yaml
proxy:
  enabled: true                          # включить/отключить глобально
  socks5: "socks5://127.0.0.1:10808"    # URL прокси
  auto_detect: true                      # авто-проверка доступности
```

### Управление через CLI

```bash
# Проверить статус прокси
python -m runner.main --proxy-status

# Запустить с конкретным прокси
python -m runner.main --goal "Скачать видео" \
    --input "url=..." \
    --proxy "socks5://127.0.0.1:10808"

# Запустить без прокси (игнорируя настройки в config.yaml)
python -m runner.main --goal "Скачать видео" \
    --input "url=..." \
    --no-proxy
```

### Режимы инжектирования

Прокси может передаваться в инструменты двумя способами:

1. **Через переменные окружения** (`method: env`) — устанавливает `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`
2. **Через параметр командной строки** (`method: param`) — добавляет `--proxy <url>` к команде

Режим настраивается в манифесте инструмента или глобально в `config.yaml`.

---

## Хранение данных

По умолчанию все данные хранятся в `~/.kit/`:

```
~/.kit/
├── jobs.db          # База задач
├── outputs/         # Результаты выполнения
└── logs/            # Debug-архивы
```

Пути можно изменить в `config.yaml` в секции `storage`.
