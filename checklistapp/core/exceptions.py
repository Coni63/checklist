class CustomExceptionError(Exception):
    custom = True


class RecordNotFoundError(CustomExceptionError):
    pass


class InvalidParameterError(CustomExceptionError):
    pass


class PermissionError(CustomExceptionError):
    pass
