# shop_msa
Shop Microservices Architecture. Pet progect &lt;3 



source srv_auth/.venv/bin/activate
uvicorn srv_auth.src.main:app --port 8001 --reload

source srv_catalog/.venv/bin/activate
uvicorn srv_catalog.src.main:app --port 8002 --reload

source srv_order/.venv/bin/activate
uvicorn srv_order.src.main:app --port 8003 --reload

source srv_payment/.venv/bin/activate
uvicorn srv_payment.src.main:app --port 8004 --reload



написать сохранение кэша в корзине,
написать ручки для корзины.
сделать обработку заказов.


1. фронт проверят на правильность баланса
2. если все гуд дергается эндпоинт.
3. сервис в эндпоинте проверят правда ли у такого юзера есть такой заказ.
4. если есть бросает запрос на оплату в другой сервис через брокер.
5. сервис оплаты проверят балик и если все гуд пробрасывает изменение статуса на оплачен, соответсвенно после успешной оплаты.
6. сервис обрабатывает изменение статуса и пробрасывает уведомление что такой заказ оплачен.
1.1 заказ имеет 2 статуса, оплаты и выполнения.


1. при регистрации в оплату пробрасывается кэш юзера, минимальный
через брокера.
uuid_user (FK → auth user)
balance: Decimal = 0
это сделал


а типо мы создаем заказ, кидаем через брокер сообщение что надо проверить такой то остаток, он проверяет - если гуд, то списывает остаток с продуктов и прокидывает в заказы что такой заказ валиден и мы чистим корзину юзера от заказанных товаров, елси остаток не валиден то отменяем заказ и не чистим корзину

Итоговый flow
1. POST /order/create
   └─ Заказ создаётся (статус: pending)
   └─ Публикуем: catalog_order.reserve_stock { order_id, items }

2. Catalog service
   └─ Атомарно списывает stock
   └─ Публикует: catalog_order.stock_reserved / stock_insufficient

3. Order service (consumer)
   └─ stock_reserved → статус: confirmed, чистим корзину
   └─ stock_insufficient → статус: cancelled, корзина на месте
   └─ Публикует в notification exchange: { user_id, order_id, result }

4. Notification service
   └─ Получает результат
   └─ Отправляет юзеру: "Заказ #123 подтверждён" или "Товар X закончился, заказ отменён"
Юзеру всё равно что там pending — он просто ждёт уведомления. Просто и понятно.


перенести Rabbit в общий core_app и вынести все подключения в него


docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 -e RABBITMQ_DEFAULT_USER=guest -e RABBITMQ_DEFAULT_PASS=guest rabbitmq:3-management


docker run --name my-postgres -e POSTGRES_PASSWORD=admin -p 5432:5432 -d postgres:16-alpine

poetry add fastapi uvicorn sqlalchemy pydantic pydantic_settings asyncpg pyjwt aio-pika

source srv_auth/.venv/bin/activate
