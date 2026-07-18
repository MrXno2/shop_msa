# shop_msa
Shop Microservices Architecture. Pet progect &lt;3 



source srv_auth/.venv/bin/activate
uvicorn srv_auth.src.main:app --port 8001 --reload

source srv_catalog/.venv/bin/activate
uvicorn srv_catalog.src.main:app --port 8002 --reload


написать сохранение кэша в корзине,
написать ручки для корзины.
сделать обработку заказов.


docker run --name my-postgres -e POSTGRES_PASSWORD=admin -p 5432:5432 -d postgres:16-alpine

poetry add fastapi uvicorn sqlalchemy pydantic pydantic_settings asyncpg pyjwt

source srv_auth/.venv/bin/activate
