
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Any

class Autoencoder(nn.Module):
    def __init__(self, input_dim):
        super(Autoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim)
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

class Model:
    def __init__(self):
        self.model = None
        self.input_dim = 10 # default fallback
        
    def train(self, ctx) -> Dict[str, Any]:
        """
        Train the PyTorch Autoencoder
        """
        ctx.logger.info("Starting PyTorch Autoencoder training...")
        
        # Data Prep
        if ctx.df is None or ctx.df.empty:
            ctx.logger.warning("No data, generating dummy")
            X = np.random.randn(100, 10).astype(np.float32)
        else:
            X = ctx.df.select_dtypes(include=[np.number]).values.astype(np.float32)
            
        self.input_dim = X.shape[1]
        self.model = Autoencoder(self.input_dim)
        
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.01)
        
        # Training Loop
        epochs = 50
        dataset = torch.tensor(X)
        self.model.train()
        
        loss_val = 0.0
        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = self.model(dataset)
            loss = criterion(outputs, dataset)
            loss.backward()
            optimizer.step()
            loss_val = loss.item()
            
        ctx.logger.info(f"Training completed. Final Loss: {loss_val}")
        
        # Save state (in memory for this instance, usually would save to disk)
        # torch.save(self.model.state_dict(), "model.pth")
        
        return {
            "status": "success",
            "model_type": "PyTorch Autoencoder",
            "final_loss": float(loss_val),
            "input_dim": self.input_dim
        }

    def infer(self, ctx) -> pd.DataFrame:
        """
        Inference: Compute reconstruction error as anomaly score
        """
        ctx.logger.info("Starting PyTorch inference...")
        
        if ctx.df is None or ctx.df.empty:
            X = np.random.randn(20, self.input_dim).astype(np.float32)
            ids = [f"user_{i}" for i in range(20)]
        else:
            X = ctx.df.select_dtypes(include=[np.number]).values.astype(np.float32)
            # Handle dimension mismatch if infer data differs from train default
            if X.shape[1] != self.input_dim:
                 # Resize or pad for demo
                 ctx.logger.warning(f"Dim mismatch: expected {self.input_dim}, got {X.shape[1]}. Truncating/Padding.")
                 if X.shape[1] > self.input_dim:
                     X = X[:, :self.input_dim]
                 else:
                     padding = np.zeros((X.shape[0], self.input_dim - X.shape[1]), dtype=np.float32)
                     X = np.hstack((X, padding))
            
            if "entity_id" in ctx.df.columns:
                ids = ctx.df["entity_id"].values
            else:
                ids = [f"entity_{i}" for i in range(len(X))]

        # Instantiate if not trained
        if self.model is None:
            self.model = Autoencoder(self.input_dim)
            self.model.eval() # Using random weights effectively
        else:
            self.model.eval()

        with torch.no_grad():
            inputs = torch.tensor(X)
            outputs = self.model(inputs)
            mse = torch.mean((inputs - outputs) ** 2, dim=1).numpy()

        results = []
        for i, score in enumerate(mse):
            # Higher reconstruction error = higher anomaly risk
            # Normalize reasonably for demo 0.0 - 2.0 -> 0 - 100
            risk = min(100.0, float(score) * 50)
            
            results.append({
                "entity_id": str(ids[i]),
                "risk_score": float(risk),
                "anomaly_type": "reconstruction_error" if risk > 50 else "normal",
                "details": {"mse": float(score)}
            })
            
        return pd.DataFrame(results)
    
    def execute(self, data=None):
         # shim for v1
        class MockCtx:
            def __init__(self, d): self.df = d if d else pd.DataFrame(); self.logger = type('obj', (object,), {'info': print, 'warning': print})
        return self.infer(MockCtx(pd.DataFrame(data) if data else None)).to_dict('records')
