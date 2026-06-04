# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main` | Yes |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub Issues.**

If you discover a security vulnerability, please report it by emailing **ankitsingh7392@gmail.com** with:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix (optional)

You will receive a response within **48 hours** acknowledging receipt. We aim to patch confirmed vulnerabilities within **7 days** and will credit reporters in the release notes (unless you prefer to remain anonymous).

## Secret Scanning

This repository has automated secret scanning enabled:

- **GitHub Secret Scanning** — scans all pushes for known credential patterns
- **Gitleaks** — runs on every PR and push via CI, and as a pre-commit hook locally
- **detect-secrets** — additional pre-commit layer for sensitive patterns

If you accidentally commit a secret, **rotate the credential immediately** — even if you delete the commit, it may have been cached or cloned.

## Security Best Practices for Contributors

- Never commit API keys, tokens, passwords, or private keys
- Use environment variables or a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault)
- Keep dependencies up to date — Dependabot is enabled on this repo
- Follow the [CONTRIBUTING.md](CONTRIBUTING.md) checklist before opening a PR
