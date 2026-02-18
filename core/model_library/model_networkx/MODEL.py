
import pandas as pd
import networkx as nx
from typing import Dict, Any

class Model:
    def __init__(self):
        self.graph = None
        
    def train(self, ctx) -> Dict[str, Any]:
        """
        Build graph from data (Training = Graph Construction)
        """
        ctx.logger.info("Starting NetworkX Graph construction...")
        
        G = nx.Graph()
        
        if isinstance(ctx.df, dict):
            # SourceGroup multi-table support: pick first available source for now
            if not ctx.df:
                ctx.logger.warning("Received empty dictionary input")
                ctx.df = None
            else:
                first_key = next(iter(ctx.df))
                ctx.logger.info(f"Received dictionary input. Using source: {first_key}")
                ctx.df = ctx.df[first_key]

        if ctx.df is None or ctx.df.empty:
            ctx.logger.warning("No data, generating dummy graph")
            # Generate random edges between 20 nodes
            import random
            nodes = [f"user_{i}" for i in range(20)]
            for _ in range(50):
                u, v = random.sample(nodes, 2)
                G.add_edge(u, v)
        else:

            # Use parameters if available
            source_col = "source"
            target_col = "target"
            
            # Check for hyperparameters (safely access if attribute or dict)
            params = {}
            if hasattr(ctx, 'hyperparameters'):
                params = ctx.hyperparameters or {}
            elif isinstance(ctx, dict) and 'hyperparameters' in ctx:
                params = ctx['hyperparameters'] or {}
                
            if params.get('source_column'):
                source_col = params['source_column']
            if params.get('target_column'):
                target_col = params['target_column']
                
            ctx.logger.info(f"Using columns - Source: {source_col}, Target: {target_col}")

            cols = ctx.df.columns
            # Validate columns exist
            if source_col not in cols or target_col not in cols:
                ctx.logger.warning(f"Specified columns ({source_col}, {target_col}) not found in data: {cols}. Falling back to position.")
                if len(cols) >= 2:
                    source_col = cols[0]
                    target_col = cols[1]
                else:
                    ctx.logger.warning("Not enough columns for graph, using dummy")
                    G.add_node("dummy_node")
                    self.graph = G
                    return {
                        "status": "warning",
                        "message": "Not enough columns",
                        "nodes": 1,
                        "edges": 0
                    }

            edges = list(zip(ctx.df[source_col], ctx.df[target_col]))
            G.add_edges_from(edges)
        
        self.graph = G
        ctx.logger.info(f"Graph constructed. Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
        
        return {
            "status": "success",
            "model_type": "NetworkX PageRank",
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges()
        }

    def infer(self, ctx) -> pd.DataFrame:
        """
        Inference: Calculate PageRank centrality
        """
        ctx.logger.info("Starting NetworkX inference...")
        
        if self.graph is None:
             self.train(ctx)
             
        # Calculate PageRank
        try:
            pagerank = nx.pagerank(self.graph)
        except Exception as e:
            ctx.logger.warning(f"PageRank failed: {e}, returning empty")
            return pd.DataFrame()

        # Users want anomalies. Let's say high Pagerank = "Key Player" (Anomaly type)
        # Or low pagerank = "Isolate".
        
        results = []
        for node, score in pagerank.items():
            # Normalize score for risk 0-100? PageRank sums to 1.
            # Multiply by N to normalize relative to uniform?
            N = self.graph.number_of_nodes()
            relative_score = score * N 
            
            # Simple heuristic: heavily central nodes are "risky" or "important"
            risk = min(100.0, relative_score * 20)
            
            results.append({
                "entity_id": str(node),
                "risk_score": float(risk),
                "anomaly_type": "high_centrality" if risk > 50 else "normal",
                "details": {"pagerank": float(score)}
            })
            
        return pd.DataFrame(results)

    def execute(self, data=None):
         # shim for v1
        class MockCtx:
            def __init__(self, d): self.df = d if d else pd.DataFrame(); self.logger = type('obj', (object,), {'info': print, 'warning': print})
        return self.infer(MockCtx(pd.DataFrame(data) if data else None)).to_dict('records')
