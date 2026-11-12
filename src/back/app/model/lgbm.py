import joblib
import numpy as np
import pandas as pd
from app.model.base import ETAModel


class LGBMETAModel(ETAModel):
    def __init__(self, path):
        self._model = joblib.load(path)

    def predict(self, X: pd.DataFrame) -> float:
        pred = self._model.predict(X)
        return float(np.clip(pred, 0, None)[0])