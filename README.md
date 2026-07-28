# Shop MSA

Микросервисная архитектура интернет-магазина. Pet-проект, демонстрирующий полный цикл работы e-commerce backend'а с асинхронным взаимодействием сервисов через RabbitMQ.

## Быстрый старт

```bash
git clone https://github.com/MrXno2/shop_msa.git
cd shop_msa
cp .env.example .env
docker compose up -d
```

После запуска доступны:

| Сервис | URL |
|---|---|
| Frontend | http://localhost |
| Auth | http://localhost:8001/docs |
| Catalog | http://localhost:8002/docs |
| Order | http://localhost:8003/docs |
| Payment | http://localhost:8004/docs |
| Notification | http://localhost:8005/docs |
| RabbitMQ Management | http://localhost:15672 (guest/guest) |

Для входа в админ-панель: `/admin/login` на фронтенде (логин default: `admin`, пароль default: `qwerty`).

## Архитектура

```
                          ┌──────────────┐
                          │   Frontend   │
                          │  React/Vite  │
                          │  port: 80    │
                          └──────┬───────┘
                                 │ nginx
                          ┌──────▼───────┐
                          │    Nginx     │
                          │ API Gateway  │
                          └──────┬───────┘
                                 │ /api/*
        ┌────────────┬───────────┼───────────┬────────────┐
        ▼            ▼           ▼           ▼            ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │srv_auth │ │srv_cata-│ │srv_order│ │srv_pay- │ │srv_noti-│
   │  :8001  │ │  log    │ │  :8003  │ │  ment   │ │ fication│
   │         │ │  :8002  │ │         │ │  :8004  │ │  :8005  │
   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
        │           │           │           │           │
        │           │           │           │           │
        │           │           │           │           │
        │           │           │           │           │
        │           │           │           │           │
        │           │           │           │           │
        ▼           ▼           ▼           ▼           ▼
   ┌─────────────────────────────────────────────────────────┐
   │                    PostgreSQL 16                        │
   │  shop_auth | shop_catalog | shop_order | shop_payment   │
   │                    shop_notification                    │
   └─────────────────────────────────────────────────────────┘
```

## Сервисы

### srv_auth — Аутентификация
- Регистрация и авторизация пользователей
- JWT-токены в HTTP-only cookies (`access_token` для пользователей, `admin_access_token` для админов)
- Хеширование паролей bcrypt
- При регистрации отправляет событие в RabbitMQ для создания кошелька

### srv_catalog — Каталог товаров
- CRUD категорий и товаров
- Фильтрация, пагинация, сортировка товаров
- Списание остатков при подтверждении заказа (атомарное через `UPDATE ... WHERE stock >= count`)
- Синхронизация кэша товаров в srv_order через RabbitMQ

### srv_order — Заказы и корзина
- Управление корзиной пользователя
- Создание заказов со статусами (PENDING → CREATED → PROCESSING → SHIPPED → DELIVERED)
- Кэш товаров из каталога для отображения корзины
- Обработка результатов списания остатков и обновления статусов оплаты

### srv_payment — Платежи и кошельки
- Кошельки пользователей с балансом
- Депозит средств (только через админку)
- Дебет кошелька при оплате заказа
- История транзакций

### srv_notification — Уведомления
- Хранение уведомлений для пользователей
- Счётчик непрочитанных
- Пометка как прочитанные

## Взаимодействие через RabbitMQ

Все межсервисное взаимодействие полностью асинхронное и построено на RabbitMQ с Direct exchange. Сервисы не звонят друг другу напрямую — только через обмен сообщениями.

### Exchange: `payment_auth`
```
srv_auth ──(payment_auth.created)──▶ srv_payment
```
При регистрации пользователя `srv_auth` публикует событие. `srv_payment` создаёт кошелёк с балансом 0.

### Exchange: `catalog_order`
```
srv_order ──(catalog_order.deduct_from_stock)──▶ srv_catalog
srv_catalog ──(catalog_order.handle_stock_deduction_result)──▶ srv_order
srv_catalog ──(catalog_order.created)──▶ srv_order
srv_catalog ──(catalog_order.delete)──▶ srv_order
srv_catalog ──(catalog_order.update)──▶ srv_order
```
- При создании заказа `srv_order` запрашивает списание остатков у `srv_catalog`
- `srv_catalog` проверяет наличие и цены, списывает остатки, возвращает результат
- `srv_order` обновляет статус заказа (CREATED или CANCELLED)
- При CRUD товаров в каталоге `srv_catalog` синхронизирует кэш товаров в `srv_order`

### Exchange: `payment_order`
```
srv_order ──(payment_order.payment)──▶ srv_payment
srv_payment ──(payment_order.update_status_payment)──▶ srv_order
```
- `srv_order` отправляет запрос на оплату
- `srv_payment` дебетует кошелёк, записывает историю, возвращает результат
- `srv_order` обновляет статус оплаты заказа

### Exchange: `all_notification`
```
srv_order ──(all_notification.add)──▶ srv_notification
srv_payment ──(all_notification.add)──▶ srv_notification
```
- `srv_payment` отправляет уведомление при успешной/неуспешной оплате
- `srv_order` отправляет уведомление при создании/отмене заказа и смене статуса

## Базы данных

Сейчас все сервисы используют одну PostgreSQL базу с разными схемами. Это упрощает локальную разработку и деплой.

Для продакшена каждый сервис должен иметь свою изолированную БД. Для этого достаточно:
1. Создать отдельные контейнеры PostgreSQL в `docker-compose.yml` (или использовать managed DB)
2. Изменить порты/хосты в `.env` для каждого `POSTGRES_URL_SERV_*`

```env
# Пример: разные хосты для каждого сервиса
POSTGRES_URL_SERV_AUTH="postgresql+asyncpg://user:pass@auth-db:5432/shop_auth"
POSTGRES_URL_SERV_CATALOG="postgresql+asyncpg://user:pass@catalog-db:5432/shop_catalog"
POSTGRES_URL_SERV_ORDER="postgresql+asyncpg://user:pass@order-db:5432/shop_order"
POSTGRES_URL_SERV_PAYMENT="postgresql+asyncpg://user:pass@payment-db:5432/shop_payment"
POSTGRES_URL_SERV_NOTIFICATION="postgresql+asyncpg://user:pass@notification-db:5432/shop_notification"
```

## Стек технологий

### Backend
- Python 3.12+
- FastAPI — async REST API
- SQLAlchemy 2.0 — async ORM
- Pydantic v2 — валидация и сериализация
- Alembic — миграции
- aio-pika — асинхронный RabbitMQ клиент
- PyJWT — JWT-токены
- bcrypt — хеширование паролей

### Frontend
- React 18 + TypeScript
- Vite — сборка
- Tailwind CSS — стили
- React Router v6 — маршрутизация
- Tanstack Query — серверное состояние
- Axios — HTTP-клиент

### Инфраструктура
- Docker Compose — оркестрация
- PostgreSQL 16 — база данных
- RabbitMQ 3 — очередь сообщений
- nginx — API Gateway и раздача фронтенда

## API Endpoints

### Auth (srv_auth)
| Method | Path | Auth | Описание |
|---|---|---|---|
| POST | `/auth/register` | — | Регистрация |
| POST | `/auth/login` | — | Вход пользователя |
| POST | `/auth/login_admin` | — | Вход админа |
| GET | `/auth/me` | user | UUID текущего пользователя |
| GET | `/auth/me_admin` | admin | UUID текущего админа |

### Catalog (srv_catalog)
| Method | Path | Auth | Описание |
|---|---|---|---|
| GET | `/category/all` | — | Список категорий |
| POST | `/category/add` | admin | Создать категорию |
| DELETE | `/category/del/{uuid}` | admin | Удалить категорию |
| GET | `/product/get_list` | — | Список товаров (фильтры, пагинация) |
| GET | `/product/get/{uuid}` | — | Товар по UUID |
| POST | `/product/create` | admin | Создать товар |
| PATCH | `/product/full_update` | admin | Обновить товар |
| DELETE | `/product/delete/{uuid}` | admin | Удалить товар |

### Order (srv_order)
| Method | Path | Auth | Описание |
|---|---|---|---|
| POST | `/cart/add/{uuid}` | user | Добавить в корзину |
| DELETE | `/cart/del/{uuid}` | user | Удалить из корзины |
| GET | `/cart/get_all` | user | Содержимое корзины |
| POST | `/order/create` | user | Создать заказ |
| POST | `/order/pay_order/{id}` | user | Оплатить заказ |
| GET | `/order/list` | admin | Список заказов |
| PATCH | `/order/update_status_order` | admin | Статус заказа |
| PATCH | `/order/update_status_payment` | admin | Статус оплаты |

### Payment (srv_payment)
| Method | Path | Auth | Описание |
|---|---|---|---|
| GET | `/payment/balance` | user | Баланс кошелька |
| POST | `/payment/deposit` | admin | Депозит на кошелёк |

### Notification (srv_notification)
| Method | Path | Auth | Описание |
|---|---|---|---|
| GET | `/notification/count` | user | Непрочитанные уведомления |
| GET | `/notification/all` | user | Список уведомлений |
| PATCH | `/notification/update` | user | Пометить как прочитанные |

