
import pandas as pd
import numpy as np
import tensorflow as tf
from typing import Dict, Any

class Model:
    def __init__(self):
        self.model = None
        self.input_dim = 10 

    def _build_model(self, input_dim):
        """
        Build a simple TF Autoencoder
        """
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(16, activation='relu', input_shape=(input_dim,)),
            tf.keras.layers.Dense(8, activation='relu'),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(input_dim, activation='linear')
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def train(self, ctx) -> Dict[str, Any]:
        """
        Train TensorFlow model
        """
        ctx.logger.info("Starting TensorFlow training...")
        
        if ctx.df is None or ctx.df.empty:
            ctx.logger.warning("No data, generating dummy")
            X = np.random.randn(100, 10).astype(np.float32)
        else:
            X = ctx.df.select_dtypes(include=[np.number]).values.astype(np.float32)
            
        self.input_dim = X.shape[1]
        self.model = self._build_model(self.input_dim)
        
        history = self.model.fit(X, X, epochs=10, batch_size=32, verbose=0)
        final_loss = history.history['loss'][-1]
        
        ctx.logger.info(f"Training completed. Loss: {final_loss}")
        
        # self.model.save("tf_model") # In real app, save to artifacts
        
        return {
            "status": "success",
            "model_type": "TensorFlow Autoencoder",
            "final_loss": float(final_loss)
        }

    def infer(self, ctx) -> pd.DataFrame:
        """
        Inference
        """
        ctx.logger.info("Starting TensorFlow inference...")
        
        if ctx.df is None or ctx.df.empty:
            X = np.random.randn(20, self.input_dim).astype(np.float32)
            ids = [f"user_{i}" for i in range(20)]
        else:
            X = ctx.df.select_dtypes(include=[np.number]).values.astype(np.float32)
             # Handle dimension mismatch
            if X.shape[1] != self.input_dim:
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

        reconstructions = self.model.predict(X, verbose=0)
        mse = np.mean(np.power(X - reconstructions, 2), axis=1)
        
        results = []
        for i, score in enumerate(mse):
            risk = min(100.0, float(score) * 50)
            results.append({
                "entity_id": str(ids[i]),
                "risk_score": float(risk),
                "anomaly_type": "tf_reconstruction_error" if risk > 50 else "normal",
                "details": {"mse": float(score)}
            })
            
        return pd.DataFrame(results)

    def execute(self, data=None):
         # shim for v1
        class MockCtx:
            def __init__(self, d): self.df = d if d else pd.DataFrame(); self.logger = type('obj', (object,), {'info': print, 'warning': print})
        return self.infer(MockCtx(pd.DataFrame(data) if data else None)).to_dict('records')
