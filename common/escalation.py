import os


def is_root():
    return os.getuid() == 0

class EscalationNecessaryError(RuntimeError):
    def __init__(self, message):
        super().__init__(message)
