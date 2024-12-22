class InvalidAPIUsage(Exception):
    """Custom exception for API errors."""

    def __init__(self, message, code=400, error=None):
        super().__init__()
        self.message = message
        self.code = code
        self.error = (
            str(error) if error else None
        )  # Convert error to string, handle None
        print("InvalidAPIUsage", self.error)

    def to_dict(self):
        """Convert the exception to a dictionary format."""
        print("InvalidAPIUsage", self.error)
        return {
            "message": self.message,
            "error": self.error,  # Include the error field explicitly
            "code": self.code,
        }
