from fastapi import APIRouter


router = APIRouter(prefix="/order")


@router.post("/create")
async def create_order() -> None:
    ...


@router.patch("/update_status")
async def update_status_order() -> None:
    ...