from dataclasses import dataclass


@dataclass(frozen=True)
class MessagesNotification:
    NAME_ORDER: str = "Заказ номер:"
    DESC_ORDER_CANCELED: str = "Заказ отменен по неизвестной причине, попробуйте пересоздать заказ позже."
    DESC_ORDER_CREATED: str = "Заказ успешно создан и ожидает оплаты."
    DESC_ORDER_PAYMENT_TRUE: str = "Оплата заказа прошла успешно."
    DESC_ORDER_PAYMENT_FALSE: str = "Не удалось оплатить заказ, недостаточно средств."
    DESC_ORDER_NEW_STATUS: str = "Статус заказа был изменен на:"

messages = MessagesNotification()