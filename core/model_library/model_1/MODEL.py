from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ModelContext:
    '''
    Mock context for local execution/testing if not provided by runner
    '''
    def __init__(self, df=None, params: Dict[str, Any] = None):
        self.df = df
        self.params = params or {}
        self.logger = logger

class Model:
    def __init__(self):
        self.model_state = {}

    def train(self, ctx: Any) -> Dict[str, Any]:
        '''
        Train the model
        '''
        ctx.logger.info("model_1 v2 training...")
        # Simulate training logic
        self.model_state["status"] = "trained"
        self.model_state["accuracy"] = 0.95
        
        return {
            "status": "success",
            "metrics": {
                "accuracy": 0.95,
                "loss": 0.05
            },
            "artifacts": ["model.pt"] # Mock artifact list
        }

    def infer(self, ctx: Any, loaded_model: Any = None) -> Any:
        '''
        Run inference
        '''
        import pandas as pd
        ctx.logger.info("model_1 v2 inference...")
        # Simulate inference logic
        results = []
        for i in range(5):
            results.append({
                "user_id": f"user_{i}",
                "risk_score": 0.85 + (i * 0.01),
                "reason": "simulated_anomaly"
            })
        
        return pd.DataFrame(results)

