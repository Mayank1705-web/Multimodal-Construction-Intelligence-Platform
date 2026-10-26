class AppError(Exception):
    """Raised for any expected failure. Converted to the JSON error envelope."""

    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
