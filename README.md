# shop_msa
Shop Microservices Architecture. Pet progect &lt;3 



source srv_auth/.venv/bin/activate
uvicorn srv_auth.src.main:app --port 8001 --reload

source srv_catalog/.venv/bin/activate
uvicorn srv_catalog.src.main:app --port 8002 --reload


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
это сделал осталось в сервисе оплаты прнять uuid из auth


docker run --name my-postgres -e POSTGRES_PASSWORD=admin -p 5432:5432 -d postgres:16-alpine

poetry add fastapi uvicorn sqlalchemy pydantic pydantic_settings asyncpg pyjwt

source srv_auth/.venv/bin/activate
