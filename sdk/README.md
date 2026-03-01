<p align="center">
  <img src="https://raw.githubusercontent.com/GACWR/OpenUBA/master/images/logo.png" alt="OpenUBA" width="400">
</p>

<p align="center">
  <a href="https://pypi.org/project/openuba/"><img src="https://img.shields.io/pypi/v/openuba" alt="PyPI"></a>
  <a href="https://pypi.org/project/openuba/"><img src="https://img.shields.io/pypi/pyversions/openuba" alt="Python"></a>
  <a href="https://github.com/GACWR/OpenUBA/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0-blue" alt="License"></a>
</p>

# OpenUBA

The official CLI and Python SDK for [OpenUBA](https://openuba.org) — an open-source User Behavior Analytics platform.

## Installation

```bash
pip install openuba
```

## CLI Usage

```bash
# Install a model from the registry
openuba install model_sklearn

# List available models
openuba list

# Run a model
openuba run model_sklearn --data path/to/data.csv

# Show version
openuba version
```

## Python SDK Usage

```python
import openuba

# Configure the client (or set OPENUBA_API_URL env var)
openuba.configure(api_url="http://localhost:8000")

# List available models
models = openuba.list_models()
for model in models:
    print(model["name"], model["version"])

# Install a model
openuba.install("model_sklearn")

# Run a model
results = openuba.run("model_sklearn", data="path/to/data.csv")
print(results)
```

## Configuration

The SDK can be configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENUBA_API_URL` | OpenUBA API server URL | `http://localhost:8000` |
| `OPENUBA_TOKEN` | Authentication token | None |

Or programmatically:

```python
import openuba
openuba.configure(api_url="http://your-server:8000", token="your-token")
```

## License

GNU General Public License v3.0 — see [LICENSE](https://github.com/GACWR/OpenUBA/blob/master/LICENSE).
