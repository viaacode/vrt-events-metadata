class InvalidEventException(Exception):
    def __init__(self, message, **kwargs):
        self.message = message
        self.kwargs = kwargs