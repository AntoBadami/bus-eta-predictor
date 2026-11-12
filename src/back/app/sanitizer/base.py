from typing import Protocol


class Sanitizer(Protocol):
    def sanitize(self, raw: dict) -> dict:
        """
        Recibe y devuelve un dict con:
          vehicle   -> dict del colectivo (MBTA)
          clima     -> dict de Open-Meteo
          trafico   -> dict de tráfico
          timestamp -> datetime en UTC del reporte
        """
        ...


class PassthroughSanitizer:
    """Implementación provisoria: no modifica nada."""

    def sanitize(self, raw: dict) -> dict:
        return raw