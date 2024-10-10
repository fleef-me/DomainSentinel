# DomainSentinel

**DomainSentinel** — это Telegram-бот для мониторинга изменений в списке доменов. Бот автоматически отслеживает добавление и удаление доменов, отправляя уведомления подписанным пользователям. Проект разработан для обеспечения актуальной информации о доменах и упрощения управления ими.

## Содержание

- [Особенности](#особенности)
- [Технологии](#технологии)
- [Установка](#установка)
  - [Предварительные требования](#предварительные-требования)
  - [Установка с использованием Docker](#установка-с-использованием-docker)
  - [Установка из исходного кода](#установка-из-исходного-кода)
    - [На Debian/Linux](#на-debianlinux)
    - [На Windows](#на-windows)
- [Конфигурация](#конфигурация)
- [Использование](#использование)
  - [Команды бота](#команды-бота)
- [Логирование](#логирование)
- [Вклад](#вклад)
- [Лицензия](#лицензия)
- [Контакты](#контакты)

## Особенности

- **Автоматический мониторинг доменов:** Бот отслеживает изменения в списке доменов и уведомляет пользователей.
- **Уведомления пользователям:** Отправка уведомлений о добавленных и удалённых доменах.
- **Поддержка нескольких методов установки:** Возможность развертывания как через Docker, так и из исходного кода на различных операционных системах.
- **Рейт-лимитинг:** Ограничение частоты использования команд для предотвращения спама.
- **Кэширование WHOIS-запросов:** Снижение количества повторных запросов и ускорение работы бота.

## Технологии

- **Python 3.8+**
- **Pyrogram** — библиотека для взаимодействия с Telegram API.
- **aiohttp** — асинхронные HTTP-запросы.
- **aiosqlite** — асинхронный интерфейс для SQLite.
- **APScheduler** — планировщик задач.
- **python-whois** — библиотека для получения WHOIS-данных.
- **Tenacity** — библиотека для повторных попыток при ошибках.
- **Docker** — контейнеризация приложения.
- **systemd** — управление сервисами на Linux.

## Установка

### Предварительные требования

- **Операционная система:**
  - [Debian 10+](https://www.debian.org/)
  - [Windows 10+](https://www.microsoft.com/windows)
  - **Docker** (опционально, для установки через Docker)
- **Python 3.8+** (для установки из исходного кода)
- **Git** (опционально, для клонирования репозитория)

### Установка с использованием Docker

Docker упрощает развертывание и управление приложением, обеспечивая изоляцию окружения. Вы можете использовать Docker для локальной установки без необходимости публикации образа в удалённый репозиторий.

#### Шаг 1: Установка Docker

Если Docker ещё не установлен на вашем компьютере, следуйте официальной [инструкции по установке Docker](https://docs.docker.com/get-docker/) для вашей операционной системы.

#### Шаг 2: Создание Dockerfile

Убедитесь, что в корневой директории вашего проекта (`DomainSentinel`) находится файл `Dockerfile` со следующим содержимым:

```dockerfile
# Используем официальный Python-образ
FROM python:3.8-slim

# Установим рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . /app

# Создаём виртуальное окружение
RUN python -m venv venv

# Активируем виртуальное окружение и устанавливаем зависимости
RUN /bin/bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

# Устанавливаем переменные окружения
ENV PATH="/app/venv/bin:$PATH"

# Запускаем бота
CMD ["python", "main.py"]
```

#### Шаг 3: Создание файла `.env`

Создайте файл `.env` в корневой директории проекта и добавьте необходимые переменные:

```dotenv
API_ID=ваш_api_id
API_HASH=ваш_api_hash
BOT_TOKEN=ваш_бот_токен
CHECK_INTERVAL=60
SOURCE_URL=https://community.antifilter.download/list/domains.lst
WHOIS_TIMEOUT=10
DATABASE_PATH=domains.db
USERS_FILE=users.json
ADMIN_USER_IDS=[6153626642, 1234567890]
```

**Примечание:** Замените значения на свои собственные.

#### Шаг 4: Сборка Docker-образа

Перейдите в директорию проекта и выполните сборку образа:

```bash
docker build -t domainsentinel:latest .
```

#### Шаг 5: Запуск Контейнера

Запустите контейнер:

```bash
docker run -d --name domainsentinel \
  --env-file .env \
  domainsentinel:latest
```

**Объяснение Команд:**

- `-d` — запуск контейнера в фоновом режиме (detached).
- `--name domainsentinel` — имя контейнера.
- `--env-file .env` — передача переменных окружения из файла `.env`.

#### Шаг 6: Управление Контейнером

- **Проверка статуса контейнера:**

  ```bash
  docker ps -a
  ```

- **Просмотр логов контейнера:**

  ```bash
  docker logs -f domainsentinel
  ```

- **Перезапуск контейнера:**

  ```bash
  docker restart domainsentinel
  ```

- **Остановка контейнера:**

  ```bash
  docker stop domainsentinel
  ```

#### Дополнительно: Использование Docker Compose (Опционально)

Если вы предпочитаете использовать Docker Compose для управления сервисами, вы можете создать файл `docker-compose.yml`:

```yaml
version: '3.8'

services:
  domainsentinel:
    build: .
    container_name: domainsentinel
    env_file:
      - .env
    restart: always
```

Запустите сервис:

```bash
docker-compose up -d
```

**Объяснение:**

- `restart: always` — автоматически перезапускает контейнер в случае сбоев или перезагрузки системы.

### Установка из исходного кода

Если вы предпочитаете установить приложение напрямую на вашу систему без использования Docker, следуйте следующим инструкциям.

#### На Debian/Linux

##### Шаг 1: Подготовка окружения

1. **Установка необходимых пакетов:**

   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv git
   ```

2. **Клонирование репозитория:**

   ```bash
   git clone https://github.com/fleef-me/DomainSentinel.git
   cd DomainSentinel
   ```

##### Шаг 2: Создание и активация виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
```

##### Шаг 3: Установка зависимостей

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

##### Шаг 4: Настройка systemd

1. **Создание сервисного файла:**

   ```bash
   sudo nano /etc/systemd/system/domainsentinel.service
   ```

2. **Добавление конфигурации:**

   ```ini
   [Unit]
   Description=DomainSentinel Telegram Bot
   After=network.target

   [Service]
   User=fleef
   Group=fleef
   WorkingDirectory=/home/fleef/code/DomainSentinel
   Environment="PATH=/home/fleef/code/DomainSentinel/venv/bin"
   ExecStart=/home/fleef/code/DomainSentinel/venv/bin/python main.py

   # Перезапуск при сбое
   Restart=always
   RestartSec=5

   # Логирование
   StandardOutput=syslog
   StandardError=syslog
   SyslogIdentifier=domainsentinel

   [Install]
   WantedBy=multi-user.target
   ```

   **Примечание:** Убедитесь, что пути и пользователь (`fleef`) соответствуют вашей системе.

3. **Сохранение и выход:**

   Нажмите `CTRL + O` для сохранения и `CTRL + X` для выхода из редактора.

4. **Перезагрузка systemd и запуск сервиса:**

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start domainsentinel.service
   sudo systemctl enable domainsentinel.service
   ```

5. **Проверка статуса сервиса:**

   ```bash
   sudo systemctl status domainsentinel.service
   ```

6. **Просмотр логов:**

   ```bash
   sudo journalctl -u domainsentinel.service -f
   ```

#### На Windows

Для установки на Windows рекомендуется использовать Docker, так как нативная поддержка systemd отсутствует. Однако, если вы хотите установить из исходного кода, следуйте этим шагам:

##### Шаг 1: Установка Python

1. **Скачайте Python 3.8+** с [официального сайта](https://www.python.org/downloads/windows/).
2. **Установите Python**, убедившись, что выбрали опцию "Add Python to PATH".

##### Шаг 2: Установка Git (опционально)

1. **Скачайте Git** с [официального сайта](https://git-scm.com/download/win).
2. **Установите Git** следуя инструкциям установщика.

##### Шаг 3: Клонирование репозитория

Откройте **PowerShell** или **Командную строку** и выполните:

```powershell
git clone https://github.com/fleef-me/DomainSentinel.git
cd DomainSentinel
```

##### Шаг 4: Создание и активация виртуального окружения

```powershell
python -m venv venv
.\venv\Scripts\activate
```

##### Шаг 5: Установка зависимостей

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

##### Шаг 6: Запуск бота

```powershell
python main.py
```

**Примечание:** Для автоматического запуска бота при старте системы рекомендуется использовать Планировщик заданий Windows или сторонние инструменты, такие как [NSSM (Non-Sucking Service Manager)](https://nssm.cc/).

---

## Конфигурация

Файл `.env` содержит все необходимые переменные конфигурации. Убедитесь, что вы правильно настроили его перед запуском приложения.

### Пример `.env`:

```dotenv
API_ID=ваш_api_id
API_HASH=ваш_api_hash
BOT_TOKEN=ваш_бот_токен
CHECK_INTERVAL=60
SOURCE_URL=https://community.antifilter.download/list/domains.lst
WHOIS_TIMEOUT=10
DATABASE_PATH=domains.db
USERS_FILE=users.json
ADMIN_USER_IDS=[6153626642, 1234567890]
```

**Описание переменных:**

- `API_ID` и `API_HASH`: Получите из [Telegram API](https://my.telegram.org/auth).
- `BOT_TOKEN`: Токен вашего бота, полученный от [BotFather](https://t.me/botfather).
- `CHECK_INTERVAL`: Интервал проверки изменений в минутах.
- `SOURCE_URL`: URL источника списка доменов. Если используется локальный файл, настройте `LOCAL_SOURCE` и `SOURCE_PATH` в `config.py`.
- `WHOIS_TIMEOUT`: Таймаут для WHOIS-запросов в секундах.
- `DATABASE_PATH`: Путь к базе данных SQLite.
- `USERS_FILE`: Файл для хранения списка пользователей.
- `ADMIN_USER_IDS`: Список `user_id` администраторов.

---

## Использование

После установки и настройки вы можете управлять ботом через Telegram, используя следующие команды.

### Команды бота

- **/start** — Подписаться на уведомления о изменениях в доменах.
- **/stop** — Отписаться от уведомлений.
- **/status** — Проверить количество подписанных пользователей.
- **/check** — Запустить ручную проверку изменений (доступно администраторам).
- **/check_test** — Инициировать тестовую проверку системы оповещений (доступно администраторам).
- **/add_domain <домен>** — Добавить домен в список (доступно администраторам).
- **/remove_domain <домен>** — Удалить домен из списка (доступно администраторам).

#### Пример использования команд

**Добавление домена:**

```plaintext
/add_domain example-test.com
```

**Удаление домена:**

```plaintext
/remove_domain example-test.com
```

**Запуск тестовой проверки:**

```plaintext
/check_test
```

---

## Логирование

Все логи приложения сохраняются в системный журнал и могут быть просмотрены с помощью соответствующих инструментов.

### Просмотр логов на Linux

```bash
sudo journalctl -u domainsentinel.service -f
```

### Просмотр логов Docker

```bash
docker logs -f domainsentinel
```

---

## Вклад

Мы приветствуем вклады в проект! Если вы хотите помочь, следуйте следующим шагам:

1. **Форкните репозиторий.**
2. **Создайте новую ветку:**

   ```bash
   git checkout -b feature/your-feature
   ```

3. **Внесите изменения и закоммитьте их:**

   ```bash
   git commit -m "Добавлена новая фича"
   ```

4. **Запушьте ветку:**

   ```bash
   git push origin feature/your-feature
   ```

5. **Создайте Pull Request.**

---

## Лицензия

Этот проект лицензирован под лицензией [MIT](LICENSE).

---

## Контакты

Если у вас есть вопросы или предложения, свяжитесь с нами:

- **Email:** your.email@example.com
- **Telegram:** [@yourtelegramhandle](https://t.me/yourtelegramhandle)

---

## Дополнительные Разделы (по желанию)

### Скриншоты

Добавьте скриншоты работы бота, чтобы пользователи могли увидеть, как он выглядит и функционирует.

### Часто Задаваемые Вопросы (FAQ)

Добавьте раздел с часто задаваемыми вопросами и ответами, чтобы помочь пользователям быстрее разобраться с ботом.

---

## Пример Использования Docker Compose (Опционально)

Если вы предпочитаете использовать Docker Compose для управления сервисами, вы можете создать файл `docker-compose.yml`:

```yaml
version: '3.8'

services:
  domainsentinel:
    build: .
    container_name: domainsentinel
    env_file:
      - .env
    restart: always
```

Запустите сервис:

```bash
docker-compose up -d
```
