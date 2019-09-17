class Response:
    """
    Model for REST calls that return only responses (e.g. DELETE).

    This assumes nothing other than that the response has an HTTP status code attached to it.
    """

    def __init__(self, status_code: int = None, body: dict = None):
        self.status_code = status_code
        self.body = body

    def _get_status_string(self):
        if self.status_code is not None:
            return str(self.status_code)
        else:
            return "No HTTP status available"

    def _get_body_string(self):
        if self.body is not None:
            return str(self.body)
        else:
            return "No body available"

    def __repr__(self):
        return 'Response({!r}), {!r})'.format(self._get_status_string(), self._get_body_string())

    def __str__(self):
        return '<Response {!r}>'.format(self._get_status_string())
