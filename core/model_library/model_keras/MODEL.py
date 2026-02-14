
import pandas as pd
import numpy as np
from tensorflow import keras
from tensorflow.keras import layers
from typing import Dict, Any

class Model:
    def __init__(self):
        self.model = None
        self.input_dim = 10 

    def _build_model(self, input_dim):
        """
        Build a Keras LSTM-based Autoencoder (treating params as sequence for demo)
        """
        # Reshaping input to (features, 1) for LSTM
        model = keras.Sequential([
            layers.Input(shape=(input_dim, 1)),
            layers.LSTM(16, activation='relu', return_sequences=False),
            layers.RepeatVector(input_dim),
            layers.LSTM(16, activation='relu', return_sequences=True),
            layers.TimeDistributed(layers.Dense(1))
        ])
        model.compile(optimizer='adam', loss='mae')
        return model

    def train(self, ctx) -> Dict[str, Any]:
        """
        Train Keras model
        """
        ctx.logger.info("Starting Keras LSTM training...")
        
        if ctx.df is None or ctx.df.empty:
            ctx.logger.warning("No data, generating dummy")
            X = np.random.randn(100, 10).astype(np.float32)
        else:
            X = ctx.df.select_dtypes(include=[np.number]).values.astype(np.float32)
            
        self.input_dim = X.shape[1]
        
        # Reshape for LSTM: [samples, time_steps, features] -> treating features as time steps here for structural demo
        X_reshaped = X.reshape((X.shape[0], X.shape[1], 1))
        
        self.model = self._build_model(self.input_dim)
        
        history = self.model.fit(X_reshaped, X_reshaped, epochs=5, batch_size=32, verbose=0)
        final_loss = history.history['loss'][-1]
        
        ctx.logger.info(f"Training completed. Final MAE: {final_loss}")
        
        return {
            "status": "success",
            "model_type": "Keras LSTM Autoencoder",
            "final_loss": float(final_loss)
        }

    def infer(self, ctx) -> pd.DataFrame:
        """
        Inference
        """
        ctx.logger.info("Starting Keras inference...")
        
        if ctx.df is None or ctx.df.empty:
            X = np.random.randn(20, self.input_dim).astype(np.float32)
            ids = [f"user_{i}" for i in range(20)]
        else:
            X = ctx.df.select_dtypes(include=[np.number]).values.astype(np.float32)
            if X.shape[1] != self.input_dim:
                 # simple truncation/padding
                 if X.shape[1] > self.input_dim:
                     X = X[:, :self.input_dim]
                 else:
                     padding = np.zeros((X.shape[0], self.input_dim - X.shape[1]), dtype=np.float32)
                     X = np.hstack((X, padding))
            
            if "entity_id" in ctx.df.columns:
                ids = ctx.df["entity_id"].values
            else:
                ids = [f"entity_{i}" for i in range(len(X))]
                
        if self.model is None:
             self.model = self._build_model(self.input_dim)

        X_reshaped = X.reshape((X.shape[0], X.shape[1], 1))
        reconstructions = self.model.predict(X_reshaped, verbose=0)
        reconstructions = reconstructions.reshape((X.shape[0], X.shape[1]))
        
        mae = np.mean(np.abs(X - reconstructions), axis=1)
        
        results = []
        for i, score in enumerate(mae):
            risk = min(100.0, float(score) * 100)
            results.append({
                "entity_id": str(ids[i]),
                "risk_score": float(risk),
                "anomaly_type": "seq_outlier" if risk > 50 else "normal",
                "details": {"mae": float(score)}
            })
            
        return pd.DataFrame(results)

    def execute(self, data=None):
         # shim for v1
        class MockCtx:
            def __init__(self, d): self.df = d if d else pd.DataFrame(); self.logger = type('obj', (object,), {'info': print, 'warning': print})
        return self.infer(MockCtx(pd.DataFrame(data) if data else None)).to_dict('records')
