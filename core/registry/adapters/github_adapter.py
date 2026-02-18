'''
Copyright 2019-Present The OpenUBA Platform Authors
github repository adapter
'''

import os
import logging
import requests
import json
import base64
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from core.registry.base_adapter import BaseRegistryAdapter

logger = logging.getLogger(__name__)


class GitHubAdapter(BaseRegistryAdapter):
    '''
    adapter for github repositories
    '''

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.api_base = "https://api.github.com"

    def _get_headers(self) -> Dict[str, str]:
        '''
        get request headers with auth if token available
        '''
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def _parse_repo_url(self, repo_url: str) -> tuple:
        '''
        parse github repo url into owner/repo
        '''
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            return path_parts[0], path_parts[1]
        raise ValueError(f"invalid github url: {repo_url}")

    def list_models(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        '''
        search github for openuba models
        uses github search api
        '''
        try:
            url = f"{self.api_base}/search/repositories"
            search_query = "topic:openuba-model"
            if query:
                search_query += f" {query}"
            params = {"q": search_query}
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            models = []
            for repo in data.get("items", []):
                # try to get model.yaml from repo
                try:
                    manifest = self._get_manifest_from_repo(
                        repo["owner"]["login"],
                        repo["name"]
                    )
                    if manifest:
                        models.append(manifest)
                except Exception:
                    pass
            return models
        except Exception as e:
            logger.error(f"error listing models from github: {e}")
            return []

    def _get_manifest_from_repo(
        self,
        owner: str,
        repo: str,
        branch: str = "main"
    ) -> Optional[Dict[str, Any]]:
        '''
        get model.yaml manifest from github repo
        '''
        try:
            url = f"{self.api_base}/repos/{owner}/{repo}/contents/model.yaml"
            params = {"ref": branch}
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 404:
                # try master branch
                params["ref"] = "master"
                response = requests.get(
                    url,
                    params=params,
                    headers=self._get_headers(),
                    timeout=10
                )
            response.raise_for_status()
            data = response.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            import yaml
            manifest = yaml.safe_load(content)
            manifest["source_url"] = f"https://github.com/{owner}/{repo}"
            return self.normalize_manifest(manifest)
        except Exception as e:
            logger.debug(f"no model.yaml in {owner}/{repo}: {e}")
            return None

    def fetch_model(self, model_id: str) -> Dict[str, Any]:
        '''
        fetch model from github repo url or owner/repo
        '''
        if model_id.startswith("http"):
            owner, repo = self._parse_repo_url(model_id)
        else:
            parts = model_id.split("/")
            if len(parts) != 2:
                raise ValueError(f"invalid model_id format: {model_id}")
            owner, repo = parts

        manifest = self._get_manifest_from_repo(owner, repo)
        if not manifest:
            raise ValueError(f"model not found: {model_id}")
        return manifest

    def get_manifest(self, model_id: str) -> Dict[str, Any]:
        return self.fetch_model(model_id)

    def download_model(self, model_id: str, destination: str) -> str:
        '''
        clone or download model from github
        '''
        import subprocess
        import shutil
        try:
            if model_id.startswith("http"):
                repo_url = model_id
            else:
                parts = model_id.split("/")
                if len(parts) != 2:
                    raise ValueError(f"invalid model_id: {model_id}")
                repo_url = f"https://github.com/{parts[0]}/{parts[1]}.git"

            # clone repo to temp directory
            temp_dir = os.path.join(destination, "temp_repo")
            os.makedirs(temp_dir, exist_ok=True)
            subprocess.run(
                ["git", "clone", repo_url, temp_dir],
                check=True,
                capture_output=True
            )
            # move contents to destination
            for item in os.listdir(temp_dir):
                src = os.path.join(temp_dir, item)
                dst = os.path.join(destination, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.move(src, dst)
                else:
                    shutil.move(src, dst)
            shutil.rmtree(temp_dir)
            logger.info(f"downloaded model from {repo_url} to {destination}")
            return destination
        except Exception as e:
            logger.error(f"error downloading model from github: {e}")
            raise

    def get_source_type(self) -> str:
        return "github"

