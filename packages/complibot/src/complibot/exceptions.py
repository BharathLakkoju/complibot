class AppError(Exception):
    def __init__(self, message: str, code: str = "internal", status: int = 500) -> None:
        self.message = message
        self.code = code
        self.status = status
        super().__init__(message)


class NotFound(AppError):
    def __init__(self, message: str = "Not found") -> None:
        super().__init__(message, code="not_found", status=404)


class Forbidden(AppError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, code="forbidden", status=403)


class Conflict(AppError):
    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(message, code="conflict", status=409)


class BadRequest(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="bad_request", status=400)
