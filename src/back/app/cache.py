import json
import threading
import time
from pathlib import Path


class TTLCache:
    def __init__(self, ttl_seconds: float):
        self.ttl = ttl_seconds
        self._data = {}
        self._lock = threading.Lock()

    def get_or_set(self, key, producir):
        with self._lock:
            hit = self._data.get(key)
            if hit and time.monotonic() - hit[0] < self.ttl:
                return hit[1]
        valor = producir()
        with self._lock:
            self._data[key] = (time.monotonic(), valor)
        return valor


class ContadorUso:
    """Cuenta consultas y las guarda en disco para que sobrevivan a los reinicios."""

    def __init__(self, path, limite: int):
        self.path = Path(path)
        self.limite = limite
        self._lock = threading.Lock()
        self.usadas = self._leer()

    def _leer(self) -> int:
        try:
            return int(json.loads(self.path.read_text())["usadas"])
        except (FileNotFoundError, ValueError, KeyError):
            return 0

    def reservar(self) -> bool:
        with self._lock:
            if self.usadas >= self.limite:
                return False
            self.usadas += 1
            self.path.write_text(json.dumps({"usadas": self.usadas}))
            return True