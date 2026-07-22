class BaseExceptionApp(Exception):
    """Base class customs error ."""
    pass


class UserNotFound(BaseExceptionApp):
    """User not found ."""
    pass


class UserPhoneAlreadyExists(BaseExceptionApp):
    """User Phone Already Exists ."""
    pass


class UserEmailAlreadyExists(BaseExceptionApp):
    """User Email Already Exists ."""
    pass 


class InvalidPassword(BaseExceptionApp):
    """Invalid Password ."""
    pass


class NotAdminError(BaseExceptionApp):
    """Not Admin Error ."""
    pass


class ProductNotFound(BaseExceptionApp):
    """Product Not Found ."""
    pass


class InsufficientFundsError(BaseExceptionApp):
    """InsufficientFundsError ."""
    pass