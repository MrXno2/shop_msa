from sqlalchemy.ext.asyncio import AsyncSession
from srv_payment.src.db.models.history_wallet import HistoryWalletORM


class HistoryWalletRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def add_history_wallet(self, data_orm: HistoryWalletORM) -> None:
        self.db.add(data_orm)