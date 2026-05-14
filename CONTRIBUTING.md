# Contributing to OpenUBA

Thank you for your interest in contributing to OpenUBA! This document provides guidelines and information for contributors.

## Developer Certificate of Origin (DCO)

All contributions to OpenUBA must be signed off under the [Developer Certificate of Origin (DCO)](https://developercertificate.org/). By signing off, you certify that you wrote the contribution or otherwise have the right to submit it under the project's license.

Sign off your commits by adding `Signed-off-by` to your commit message:

```
git commit -s -m "Your commit message"
```

Or manually add to your commit message:

```
Signed-off-by: Your Name <your.email@example.com>
```

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/OpenUBA.git
   cd OpenUBA
   ```
3. **Set up development environment:**
   ```bash
   make dev-hybrid   # Backend local + infra in Kind cluster
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Kind (Kubernetes in Docker)
- Node.js 18+ (for frontend)
- Make

### Backend

```bash
pip install -r requirements.txt
python -m uvicorn core.api:app --reload --port 8000
```

### Frontend

```bash
cd interface
npm install
npm run dev
```

### Running Tests

```bash
make test          # All tests
make test-backend  # Backend only
make test-models   # Model pipeline tests
```

## What to Contribute

### Good First Issues

Look for issues labeled `good first issue` in the GitHub issue tracker.

### Areas of Interest

- **New ML models** for the Model Library
- **Data source integrations** (new loaders beyond ES and Spark)
- **Documentation** improvements
- **Test coverage** expansion
- **Frontend UX** improvements
- **Kubernetes operator** development
- **CNCF integration** (Falco, OpenTelemetry, Prometheus)

## Pull Request Process

1. Ensure your code follows the project's coding style
2. Update documentation if your changes affect user-facing behavior
3. Add tests for new functionality
4. Ensure all tests pass (`make test`)
5. Sign off all commits (DCO)
6. Submit a pull request against the `master` branch
7. Describe your changes clearly in the PR description
8. Link to any related issues

## Code Review

- All PRs require at least one maintainer review
- CI must pass before merging
- Maintainers may request changes or improvements

## Reporting Bugs

- Use GitHub Issues to report bugs
- Include: steps to reproduce, expected behavior, actual behavior, environment details
- Check existing issues before creating a new one

## Requesting Features

- Open a GitHub Issue with the `enhancement` label
- Describe the use case and expected behavior
- Be open to discussion about implementation approach

## Code of Conduct

All participants in the OpenUBA community are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

By contributing to OpenUBA, you agree that your contributions will be licensed under the project's license.
