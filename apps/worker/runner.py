import time
import threading

from .tasks import run_one_step


class ChatWorker:
    def __init__(self, interval=2):
        self.interval = interval
        self._running = False
        self._thread = None
        self._last_role = None

    def start(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[Worker] Chat worker started")

    def stop(self):
        self._running = False
        print("[Worker] Chat worker stopped")

    def _loop(self):
        while self._running:
            try:
                self._last_role = run_one_step(self._last_role)
            except Exception as e:
                print(f"[Worker Error] {e}")

            time.sleep(self.interval)