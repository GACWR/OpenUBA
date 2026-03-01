"""OpenUBA SDK — install, run, and manage user behavior analytics models."""

from openuba.client import OpenUBAClient

__version__ = "0.0.1"

# Module-level client singleton
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenUBAClient()
    return _client


def configure(api_url=None, token=None, registry_url=None, model_dir=None):
    """Configure the OpenUBA SDK client."""
    global _client
    _client = OpenUBAClient(
        api_url=api_url,
        token=token,
        registry_url=registry_url,
        model_dir=model_dir,
    )


def install(model_name, version=None, source=None):
    """Install a model from the openuba-model-hub registry."""
    return _get_client().install_model(model_name, version=version, source=source)


def uninstall(model_name):
    """Remove a locally installed model."""
    return _get_client().uninstall_model(model_name)


def run(model_name, data=None, parameters=None):
    """Run an installed model locally."""
    return _get_client().run_model(model_name, data=data, parameters=parameters)


def list_models(source=None):
    """List models available in the openuba-model-hub registry."""
    return _get_client().list_models(source=source)


def list_installed():
    """List locally installed models."""
    return _get_client().list_installed()


def get_model(model_name):
    """Get details for a specific model."""
    return _get_client().get_model(model_name)


__all__ = [
    "OpenUBAClient",
    "configure",
    "install",
    "uninstall",
    "run",
    "list_models",
    "list_installed",
    "get_model",
]
