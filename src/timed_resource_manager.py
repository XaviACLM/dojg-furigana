import threading
from datetime import datetime, timedelta
import time


class TimedResourceManager:
    """
    Abstract base class for managing a resource that should be stopped
    after a period of inactivity.
    """

    def __init__(self, timeout=60):
        self.timeout = timeout
        self.last_request_time = None
        self.is_resource_running = False
        self._lock = threading.Lock()
        self._monitor_thread = None

    def _start_monitor_thread(self):
        def monitor():
            while True:
                if not self.is_resource_running:
                    # got killed externally, time to leave
                    return
                with self._lock:
                    time_until_timeout = timedelta(seconds=self.timeout) - (
                        datetime.now() - self.last_request_time
                    )

                    if time_until_timeout <= timedelta():
                        self._stop_resource_managed()
                        return

                sleep_time = max(0.1, time_until_timeout.total_seconds())
                time.sleep(sleep_time)

        self._monitor_thread = threading.Thread(target=monitor, daemon=True)
        self._monitor_thread.start()

    def handle_request(self, *args, **kwargs):
        """
        Handles a request. Starts the resource if necessary, and resets the timeout.
        """
        with self._lock:
            if not self.is_resource_running:
                self._start_resource_managed()
                self.last_request_time = datetime.now()
                self._start_monitor_thread()
            else:
                # Update the last request time to extend the timeout
                self.last_request_time = datetime.now()
        return self._process_request(*args, **kwargs)

    def shutdown(self):
        with self._lock:
            if self.is_resource_running:
                self._stop_resource_managed()
            # it's a daemon, no need to wait for it to en
            # if self._monitor_thread: self._monitor_thread.join()

    def __del__(self):
        self.shutdown()

    # Resource lifecycle methods
    def _start_resource_managed(self):
        self.is_resource_running = True
        self._start_resource()

    def _start_resource(self):
        raise NotImplementedError()

    def _stop_resource_managed(self):
        self.is_resource_running = False
        self._stop_resource()

    def _stop_resource(self):
        raise NotImplementedError()

    def _process_request(self, *args, **kwargs):
        raise NotImplementedError()
