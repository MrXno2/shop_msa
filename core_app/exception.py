class AppException(Exception):
    """Base class customs error ."""
    pass


class UserNotFound(AppException):
    """User not found ."""
    pass


class UserPhoneAlreadyExists(AppException):
    """User Phone Already Exists ."""
    pass


class UserEmailAlreadyExists(AppException):
    """User Email Already Exists ."""
    pass 


class InvalidPassword(AppException):
    """Invalid Password ."""
    pass


class NotAdminError(AppException):
    """Not Admin Error ."""
    pass


class ProductNotFound(AppException):
    """Product Not Found ."""
    pass


class InsufficientFundsError(AppException):
    """InsufficientFundsError ."""
    pass