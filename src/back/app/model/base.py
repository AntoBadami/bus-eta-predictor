from abc import ABC, abstractmethod
import pandas as pd


class ETAModel(ABC):
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> float:
        """Recibe el DataFrame de 1 fila con las 23 features y devuelve el ETA en segundos."""