import logging
import threading

_request_id_local = threading.local()


def get_current_request_id():
    return getattr(_request_id_local, 'request_id', '-')


class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_current_request_id()
        return True
