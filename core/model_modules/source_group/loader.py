import logging
from typing import Any, Dict, Optional
import os
import pandas as pd

from core.db import get_db_context
from core.db.models import SourceGroup
from core.model_modules.local_pandas.local_pandas import LocalPandasLoader
# Import other loaders as needed e.g. SparkLoader

logger = logging.getLogger(__name__)

class SourceGroupLoader:
    """
    Meta-loader that resolves a SourceGroup configuration and delegates to the appropriate
    physical data loader (e.g. LocalPandas, Spark).
    """

    def load(self, context: Dict[str, Any]) -> Any:
        # 1. Get SourceGroup ID or Slug from context
        # Context might have 'source_group_id' or 'source_group_slug'
        # Or even 'source_group' if passed directly
        
        group_slug = context.get('source_group_slug') or context.get('slug')
        log_name = context.get('log_name') # Optional specific log to fetch
        
        if not group_slug:
            raise ValueError("SourceGroupLoader requires 'source_group_slug' in context")

        # 2. Fetch Config from DB
        config = self._fetch_config(group_slug)
        if not config:
            raise ValueError(f"SourceGroup '{group_slug}' not found or has no config")

        # 3. Select Best Source
        # For now, simplistic selection: find the source matching 'log_name' if provided,
        # or just take the first one.
        # Future: Check 'location_type' vs environment (e.g. if on K8s, prefer HDFS/ES).
        
        if log_name:
            # 3a. Select Specific Source
            selected_source = None
            for src in config:
                if src.get('log_name') == log_name:
                    selected_source = src
                    break
            if not selected_source:
                raise ValueError(f"Log '{log_name}' not found in SourceGroup '{group_slug}'")
            
            logger.info(f"SourceGroup resolving single source: {log_name}")
            return self._load_single_source(selected_source)
        else:
            # 3b. Load All Sources (Multi-Table support)
            logger.info(f"SourceGroup loading all {len(config)} sources for group '{group_slug}'")
            results = {}
            for src in config:
                name = src.get('log_name') or f"source_{config.index(src)}"
                try:
                    results[name] = self._load_single_source(src)
                except Exception as e:
                    logger.warning(f"Failed to load source '{name}': {e}")
                    # Decide if we fail hard or partial? For now, fail hard on critical data usually better
                    raise e
            
            # If only 1 source, we could flatten? 
            # BUT user asked for "several tables". Consistency suggests returning Dict.
            # To preserve strict backward compatibility for single-source models unaware of this change,
            # we might want to flatten if len=1. 
            # However, explicit is better. 'SourceGroup' -> Group of sources.
            return results

    def _load_single_source(self, source_config: Dict[str, Any]) -> Any:
        loader_type = source_config.get('type')
        logger.info(f"Loading source: {source_config.get('log_name')} (type={loader_type})")

        if loader_type == 'csv' and source_config.get('location_type') == 'disk':
            # Delegate to LocalPandasLoader
            loader = LocalPandasLoader()
            return loader.load(source_config)
            
        elif loader_type == 'es':
             # Delegate to ElasticLoader
             # from core.model_modules.es.es_loader import ElasticLoader
             raise NotImplementedError("ElasticSearch delegation not yet implemented in SourceGroupLoader")
             
        else:
             raise ValueError(f"Unsupported physical loader type: {loader_type}")

    def _fetch_config(self, slug: str) -> Optional[List[Dict[str, Any]]]:
        with get_db_context() as db:
            sg = db.query(SourceGroup).filter(SourceGroup.slug == slug).first()
            if sg:
                return sg.config
        return None
