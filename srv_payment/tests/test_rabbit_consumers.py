from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from srv_payment.src.db.models.history_wallet import HistoryWalletORM
from srv_payment.src.db.models.wallet import WalletORM
from srv_payment.src.rabbit.services import RabbitPaymentAuthService, RabbitPaymentOrderService


def _make_message(data: dict) -> MagicMock:
    import json
    message = MagicMock()
    message.body = json.dumps(data, default=str).encode()
    return message


async def _seed_wallet(db: AsyncSession, user_uuid=None, balance="0.00", number=None):
    if user_uuid is None:
        user_uuid = uuid4()
    if number is None:
        number = f"+79{uuid4().hex[:8]}"
    wallet = WalletORM(uuid_user=user_uuid, number=number, balance=balance)
    db.add(wallet)
    await db.flush()
    return wallet


class FakeSessionFactory:
    def __init__(self, db):
        self._db = db

    def __call__(self):
        return self._CM(self._db)

    class _CM:
        def __init__(self, db):
            self._db = db

        async def __aenter__(self):
            return self._db

        async def __aexit__(self, *args):
            pass


class TestCreateUser:
    @pytest.mark.asyncio
    async def test_creates_wallet(self, db_session: AsyncSession):
        user_uuid = uuid4()
        data = {"uuid_user": str(user_uuid), "number": "+79991234567"}
        message = _make_message(data)

        service = RabbitPaymentAuthService()

        with patch("srv_payment.src.rabbit.services.db_session", FakeSessionFactory(db_session)):
            await service.create_user(message)

        result = await db_session.execute(
            select(WalletORM).where(WalletORM.uuid_user == user_uuid)
        )
        wallet = result.scalar_one()
        assert wallet is not None
        assert wallet.number == "+79991234567"
        assert wallet.balance == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_invalid_message(self, db_session: AsyncSession):
        message = _make_message({"invalid": "data"})

        service = RabbitPaymentAuthService()

        with patch("srv_payment.src.rabbit.services.db_session", FakeSessionFactory(db_session)):
            with pytest.raises(Exception):
                await service.create_user(message)


class TestPaymentOrderSuccess:
    @pytest.mark.asyncio
    async def test_debits_wallet_and_creates_history(self, db_session: AsyncSession):
        user_uuid = uuid4()
        await _seed_wallet(db_session, user_uuid, balance="500.00")

        data = {
            "uuid_user": str(user_uuid),
            "id_order": 1,
            "total_price": "200.00",
        }
        message = _make_message(data)

        service = RabbitPaymentOrderService()

        mock_payment_order = MagicMock()
        mock_payment_order.publish = AsyncMock()
        mock_notif = MagicMock()
        mock_notif.publish = AsyncMock()

        with (
            patch("srv_payment.src.rabbit.services.db_session", FakeSessionFactory(db_session)),
            patch("srv_payment.src.rabbit.services.rabbit_payment_order", mock_payment_order),
            patch("srv_payment.src.rabbit.services.rabbit_all_notification", mock_notif),
        ):
            await service.payment_order(message)

        result = await db_session.execute(
            select(WalletORM).where(WalletORM.uuid_user == user_uuid)
        )
        wallet = result.scalar_one()
        assert wallet.balance == Decimal("300.00")

        result = await db_session.execute(
            select(HistoryWalletORM).where(HistoryWalletORM.uuid_user == user_uuid)
        )
        history = result.scalar_one()
        assert history.transaction_type == "payment"
        assert history.amount == Decimal("200.00")

    @pytest.mark.asyncio
    async def test_publishes_response(self, db_session: AsyncSession):
        user_uuid = uuid4()
        await _seed_wallet(db_session, user_uuid, balance="500.00")

        data = {
            "uuid_user": str(user_uuid),
            "id_order": 42,
            "total_price": "100.00",
        }
        message = _make_message(data)

        service = RabbitPaymentOrderService()

        mock_payment_order = MagicMock()
        mock_payment_order.publish = AsyncMock()
        mock_notif = MagicMock()
        mock_notif.publish = AsyncMock()

        with (
            patch("srv_payment.src.rabbit.services.db_session", FakeSessionFactory(db_session)),
            patch("srv_payment.src.rabbit.services.rabbit_payment_order", mock_payment_order),
            patch("srv_payment.src.rabbit.services.rabbit_all_notification", mock_notif),
        ):
            await service.payment_order(message)

        mock_payment_order.publish.assert_awaited_once()
        call_args = mock_payment_order.publish.call_args
        assert call_args.args[0] == "payment_order.update_status_payment"
        payload = call_args.args[1]
        assert payload["payment_success"] is True
        assert payload["id_order"] == 42

        mock_notif.publish.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_insufficient_funds(self, db_session: AsyncSession):
        user_uuid = uuid4()
        await _seed_wallet(db_session, user_uuid, balance="50.00")

        data = {
            "uuid_user": str(user_uuid),
            "id_order": 5,
            "total_price": "200.00",
        }
        message = _make_message(data)

        service = RabbitPaymentOrderService()

        mock_payment_order = MagicMock()
        mock_payment_order.publish = AsyncMock()
        mock_notif = MagicMock()
        mock_notif.publish = AsyncMock()

        with (
            patch("srv_payment.src.rabbit.services.db_session", FakeSessionFactory(db_session)),
            patch("srv_payment.src.rabbit.services.rabbit_payment_order", mock_payment_order),
            patch("srv_payment.src.rabbit.services.rabbit_all_notification", mock_notif),
        ):
            await service.payment_order(message)

        result = await db_session.execute(
            select(WalletORM).where(WalletORM.uuid_user == user_uuid)
        )
        wallet = result.scalar_one()
        assert wallet.balance == Decimal("50.00")

        result = await db_session.execute(
            select(HistoryWalletORM).where(HistoryWalletORM.uuid_user == user_uuid)
        )
        assert result.scalar_one_or_none() is None

        mock_payment_order.publish.assert_awaited_once()
        call_args = mock_payment_order.publish.call_args
        payload = call_args.args[1]
        assert payload["payment_success"] is False

    @pytest.mark.asyncio
    async def test_insufficient_funds_publishes_notification(self, db_session: AsyncSession):
        user_uuid = uuid4()
        await _seed_wallet(db_session, user_uuid, balance="10.00")

        data = {
            "uuid_user": str(user_uuid),
            "id_order": 3,
            "total_price": "100.00",
        }
        message = _make_message(data)

        service = RabbitPaymentOrderService()

        mock_payment_order = MagicMock()
        mock_payment_order.publish = AsyncMock()
        mock_notif = MagicMock()
        mock_notif.publish = AsyncMock()

        with (
            patch("srv_payment.src.rabbit.services.db_session", FakeSessionFactory(db_session)),
            patch("srv_payment.src.rabbit.services.rabbit_payment_order", mock_payment_order),
            patch("srv_payment.src.rabbit.services.rabbit_all_notification", mock_notif),
        ):
            await service.payment_order(message)

        mock_notif.publish.assert_awaited_once()
        call_args = mock_notif.publish.call_args
        payload = call_args.args[1]
        assert "недостаточно средств" in payload["message_notification"]

    @pytest.mark.asyncio
    async def test_exact_balance_debit(self, db_session: AsyncSession):
        user_uuid = uuid4()
        await _seed_wallet(db_session, user_uuid, balance="100.00")

        data = {
            "uuid_user": str(user_uuid),
            "id_order": 10,
            "total_price": "100.00",
        }
        message = _make_message(data)

        service = RabbitPaymentOrderService()

        mock_payment_order = MagicMock()
        mock_payment_order.publish = AsyncMock()
        mock_notif = MagicMock()
        mock_notif.publish = AsyncMock()

        with (
            patch("srv_payment.src.rabbit.services.db_session", FakeSessionFactory(db_session)),
            patch("srv_payment.src.rabbit.services.rabbit_payment_order", mock_payment_order),
            patch("srv_payment.src.rabbit.services.rabbit_all_notification", mock_notif),
        ):
            await service.payment_order(message)

        result = await db_session.execute(
            select(WalletORM).where(WalletORM.uuid_user == user_uuid)
        )
        wallet = result.scalar_one()
        assert wallet.balance == Decimal("0.00")
