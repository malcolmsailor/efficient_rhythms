import contextlib
import threading
import time

from . import er_make
from .er_globals import DEBUG


def timer(timeout, duration):
    wait = 0.1
    for _ in range(int(duration // wait)):
        if timeout.is_set():
            return
        time.sleep(wait)
    timeout.set()


def stop_timer(timeout, timeout_thread):
    timeout.set()
    timeout_thread.join()


@contextlib.contextmanager
def timeout(er):
    if er.timeout is None:
        # do nothing
        try:
            yield None
        finally:
            pass
    else:
        timeout_event = threading.Event()
        er.add_timeout_event(timeout_event)
        timeout_thread = threading.Thread(
            target=timer, args=[timeout_event, er.timeout]
        )
        timeout_thread.start()
        try:
            yield None
        finally:
            stop_timer(timeout_event, timeout_thread)


# after https://stackoverflow.com/a/65447493/10155119 and
# https://stackoverflow.com/a/31614591/10155119
class ThreadWithResult(threading.Thread):
    def __init__(
        self,
        group=None,
        target=None,
        name=None,
        args=(),
        kwargs=None,
        *,
        daemon=None
    ):
        def function():
            try:
                self.result = target(*args, **kwargs)
            except Exception as exc:
                self.exc = exc

        if kwargs is None:
            kwargs = {}
        self.exc = None
        super().__init__(group=group, target=function, name=name, daemon=daemon)


def make_super_pattern(er, debug=DEBUG):
    if debug:
        # The threading seems to work havoc with pdb, so we just skip it if
        # we are debugging.
        return er_make.make_super_pattern(er)
    with timeout(er):
        main_thread = ThreadWithResult(
            target=er_make.make_super_pattern, args=[er]
        )
        main_thread.start()
        main_thread.join()
    if main_thread.exc is not None:
        raise main_thread.exc
    return main_thread.result
