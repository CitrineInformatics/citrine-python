class Response:
    """Model for REST calls that return only responses (e.g. DELETE)."""

    def __init__(self, message: str, status: str):
        self.message = message
        self.status = status

    def __repr__(self):
        return 'Response({!r}, {!r})'.format(self.message, self.status)

    def __str__(self):
        return '<Response {!r}>'.format(self.message)
