
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Dict, Any

class Model:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.is_trained = False

    def train(self, ctx) -> Dict[str, Any]:
        """
        Train the isolation forest model
        """
        ctx.logger.info("Starting Sklearn Isolation Forest training...")
        
        # Load data from context
        if ctx.df is None or (hasattr(ctx.df, 'empty') and ctx.df.empty):
            raise ValueError("No training data provided. Specify a data source (elasticsearch, spark, or local_csv).")

        X = ctx.df.select_dtypes(include=[np.number]).values
        if X.shape[0] == 0 or X.shape[1] == 0:
            raise ValueError(f"Training data has no numeric columns (shape={ctx.df.shape}, numeric_shape={X.shape})")
            
        self.model.fit(X)
        self.is_trained = True
        
        ctx.logger.info("Training completed.")
        return {
            "status": "success",
            "model_type": "IsolationForest",
            "n_samples": len(X),
            "n_features": X.shape[1]
        }

    def infer(self, ctx) -> pd.DataFrame:
        """
        Inference using the trained model
        """
        ctx.logger.info("Starting inference...")
        
        if not self.is_trained:
            ctx.logger.warning("Model not explicitly trained, fitting on inference data for demo")
        
        if ctx.df is None or (hasattr(ctx.df, 'empty') and ctx.df.empty):
            raise ValueError("No inference data provided. Specify a data source (elasticsearch, spark, or local_csv).")

        X = ctx.df.select_dtypes(include=[np.number]).values
        if X.shape[0] == 0 or X.shape[1] == 0:
            raise ValueError(f"Inference data has no numeric columns (shape={ctx.df.shape}, numeric_shape={X.shape})")

        # Try to find an ID column
        if "entity_id" in ctx.df.columns:
            ids = ctx.df["entity_id"].values
        elif "user_id" in ctx.df.columns:
            ids = ctx.df["user_id"].values
        else:
            ids = [f"entity_{i}" for i in range(len(X))]

        # Fit if needed (for demo purposes if weights loading isn't fully implemented in runner)
        if not hasattr(self.model, "estimators_"):
            ctx.logger.info(f"fitting IsolationForest on {X.shape[0]} samples, {X.shape[1]} features...")
            self.model.fit(X)

        ctx.logger.info(f"running predictions on {X.shape[0]} samples...")
        predictions = self.model.predict(X)
        ctx.logger.info(f"computing anomaly scores...")
        scores = self.model.decision_function(X)

        ctx.logger.info(f"building risk scores for {len(predictions)} results...")
        # -1 is anomaly, 1 is normal in IsolationForest
        # We want risk score 0-100.
        # decision_function: lower is more anomalous.

        results = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            # convert score to risk (simple heuristic)
            risk = 0.0
            if pred == -1:
                risk = min(100.0, abs(score) * 100 + 50)
            else:
                risk = max(0.0, (1 - score) * 20)
                
            results.append({
                "entity_id": str(ids[i]),
                "risk_score": float(risk),
                "anomaly_type": "statistical_outlier" if pred == -1 else "normal",
                "details": {"raw_score": float(score)}
            })
            
        return pd.DataFrame(results)

    def execute(self, data=None):
        # shim for v1 interface
        class MockCtx:
            def __init__(self, d): self.df = d if d else pd.DataFrame(); self.logger = type('obj', (object,), {'info': print, 'warning': print})
        return self.infer(MockCtx(pd.DataFrame(data) if data else None)).to_dict('records')
