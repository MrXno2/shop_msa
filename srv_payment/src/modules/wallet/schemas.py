from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class DepositWalletSchema(BaseModel):
    uuid_user: UUID
    dep_price: Decimal
