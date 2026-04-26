import threading
from .tasks import start_worker


class ChatWorker:

    def __init__(self):
        self._thread = None
        self._running = False

    def start(self):
        if self._running:
            return

        self._running = True

        self._thread = threading.Thread(
            target=start_worker,
            daemon=True
        )
        self._thread.start()

        print("[Worker] Multi-room worker started")

    def stop(self):
        self._running = False
        print("[Worker] stopped")