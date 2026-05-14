"""
test-sklearn-compat — sklearn model registered via OpenUBA SDK.
Loads pre-trained model from model.pkl and exposes the v2 interface.
"""

import os
import pickle
import pandas as pd
import numpy as np
from typing import Dict, Any


class Model:
    def __init__(self):
        model_dir = os.path.dirname(os.path.abspath(__file__))
        pkl_path = os.path.join(model_dir, "model.pkl")
        if os.path.exists(pkl_path):
            with open(pkl_path, "rb") as f:
                self.model = pickle.load(f)
            self.is_trained = True
        else:
            self.model = None
            self.is_trained = False

    def _ensure_model(self, params=None):
        """Create a default model if none was loaded from pickle."""
        if self.model is not None:
            return
        from sklearn.ensemble import IsolationForest
        hp = params or {}
        self.model = IsolationForest(
            n_estimators=int(hp.get("n_estimators", 200)),
            contamination=float(hp.get("contamination", 0.05)),
            random_state=42,
        )

    def train(self, ctx) -> Dict[str, Any]:
        """Train the model on data from context."""
        ctx.logger.info("Starting training...")
        if ctx.df is None or (hasattr(ctx.df, "empty") and ctx.df.empty):
            raise ValueError("No training data provided.")

        X = ctx.df.select_dtypes(include=[np.number]).values
        if X.shape[0] == 0 or X.shape[1] == 0:
            raise ValueError(f"No numeric columns in data (shape={ctx.df.shape})")

        self._ensure_model(getattr(ctx, "params", None))
        self.model.fit(X)
        self.is_trained = True
        ctx.logger.info(f"Training completed on {X.shape[0]} samples, {X.shape[1]} features.")
        return {
            "status": "success",
            "model_type": type(self.model).__name__,
            "n_samples": len(X),
            "n_features": X.shape[1],
        }

    def infer(self, ctx) -> pd.DataFrame:
        """Run inference and return anomaly results."""
        ctx.logger.info("Starting inference...")
        if ctx.df is None or (hasattr(ctx.df, "empty") and ctx.df.empty):
            raise ValueError("No inference data provided.")

        X = ctx.df.select_dtypes(include=[np.number]).values
        if X.shape[0] == 0 or X.shape[1] == 0:
            raise ValueError(f"No numeric columns in data (shape={ctx.df.shape})")

        if "entity_id" in ctx.df.columns:
            ids = ctx.df["entity_id"].values
        elif "user_id" in ctx.df.columns:
            ids = ctx.df["user_id"].values
        else:
            ids = [f"entity_{i}" for i in range(len(X))]

        self._ensure_model(getattr(ctx, "params", None))

        # re-fit if model expects different feature count than data
        needs_fit = not hasattr(self.model, "estimators_")
        if not needs_fit and hasattr(self.model, "n_features_in_"):
            if self.model.n_features_in_ != X.shape[1]:
                ctx.logger.info(
                    f"Feature count mismatch (model: {self.model.n_features_in_}, "
                    f"data: {X.shape[1]}), re-fitting on inference data..."
                )
                needs_fit = True
        if needs_fit:
            ctx.logger.info("Fitting model on inference data...")
            self.model.fit(X)

        predictions = self.model.predict(X)
        scores = self.model.decision_function(X)

        results = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            risk = min(100.0, abs(score) * 100 + 50) if pred == -1 else max(0.0, (1 - score) * 20)
            results.append({
                "entity_id": str(ids[i]),
                "risk_score": float(risk),
                "anomaly_type": "statistical_outlier" if pred == -1 else "normal",
                "details": {"raw_score": float(score)},
            })

        return pd.DataFrame(results)
