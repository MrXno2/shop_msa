# shop_msa
Shop Microservices Architecture. Pet progect &lt;3 

uvicorn srv_auth.src.main:app --port 8001 --reload

docker run --name my-postgres -e POSTGRES_PASSWORD=admin -p 5432:5432 -d postgres:16-alpine

poetry add fastapi uvicorn sqlalchemy pydantic pydantic_settings asyncpg pyjwt

source .venv/bin/activate