"""
Predictor: cualquier objeto con predict(features: dict) -> segundos (float).
Para conectar el modelo real: dejá un .joblib en MODEL_PATH, o escribí otra
clase acá y devolvela desde get_predictor().
"""
import os
from functools import lru_cache

from . import config


class MockPredictor:
    is_mock = True

    def predict(self, features: dict) -> float:
        if features.get("detenido"):
            return 0.0
        return round(120 * (features.get("ratio_congestion") or 1.0), 1)


class JoblibPredictor:
    is_mock = False

    def __init__(self, path: str, columns: list[str]):
        import joblib
        self.model = joblib.load(path)
        self.columns = columns

    def predict(self, features: dict) -> float:
        import pandas as pd
        row = pd.DataFrame([{c: features.get(c) for c in self.columns}])
        return float(self.model.predict(row)[0])


@lru_cache(maxsize=1)
def get_predictor():
    if config.MODEL_PATH and os.path.exists(config.MODEL_PATH):
        return JoblibPredictor(config.MODEL_PATH, config.MODEL_FEATURES)
    return MockPredictor()