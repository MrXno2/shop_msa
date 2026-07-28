class AppException(Exception):
    """Base class customs error ."""



class UserNotFound(AppException):
    """User not found ."""



class UserPhoneAlreadyExists(AppException):
    """User Phone Already Exists ."""



class UserEmailAlreadyExists(AppException):
    """User Email Already Exists ."""



class InvalidPassword(AppException):
    """Invalid Password ."""



class NotAdminError(AppException):
    """Not Admin Error ."""



class ProductNotFound(AppException):
    """Product Not Found ."""



class InsufficientFundsError(AppException):
    """InsufficientFundsError ."""

