from srv_payment.src.services.rabbit_payment_order import RabbitPaymentAuthService, RabbitPaymentOrderService
from core_app.rabbit import RabbitMain
from srv_payment.src.db.session import db_session, get_db


async def register_consumers_payment_order(
    rabbit: RabbitMain,
):
    order_serv = RabbitPaymentOrderService()

    rabbit.consumer(
        queue="payment_order.payment",
        routing_key="payment_order.payment",
        handler=order_serv.payment_order,
    )


async def register_consumers_payment_auth(
    rabbit: RabbitMain,
):
    auth_serv = RabbitPaymentAuthService()

    rabbit.consumer(
        queue="payment_auth.created",
        routing_key="payment_auth.created",
        handler=auth_serv.create_user
    )