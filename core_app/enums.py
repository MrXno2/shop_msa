from enum import Enum


class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    CREATED = "created"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"