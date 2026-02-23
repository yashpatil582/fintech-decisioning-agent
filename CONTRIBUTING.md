# Contributing

## Workflow

1. Fork the repo and clone locally
2. Create a branch: `git checkout -b feat/your-feature`
3. Install dev dependencies: `pip install -r requirements-dev.txt`
4. Make your changes and add tests
5. Run the test suite: `pytest tests/ --cov=app`
6. Push your branch and open a Pull Request

## Code Style

- Follow PEP 8
- Use type hints on all function signatures
- Keep functions focused — one responsibility each
- All new features need a corresponding test

## PR Guidelines

- Keep PRs small and focused
- Reference any related issues in the PR description
- Ensure CI passes before requesting review
