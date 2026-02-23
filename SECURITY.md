# Security Policy

## Reporting a Vulnerability

Please report security vulnerabilities via **GitHub Issues** using the private/confidential option, or email the maintainer directly.

Do **not** open a public issue for security vulnerabilities.

## Important Notes

- Never commit `.env` files or real AWS credentials to this repository
- All AWS keys must be stored as GitHub Actions secrets or injected at runtime
- The `.gitignore` excludes `.env` by default — do not override this
- Rotate any credentials immediately if accidentally committed

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |
