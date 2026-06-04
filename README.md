# AI Toolkit

<p align="center">
  <img src="https://img.shields.io/github/actions/workflow/status/ankitsingh7392/ai-toolkit/ci.yml?branch=main&label=CI&logo=github" alt="CI">
  <img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit" alt="pre-commit">
  <img src="https://img.shields.io/badge/code%20style-ruff-000000?logo=python" alt="Ruff">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/uv-package%20manager-blueviolet" alt="uv">
  <img src="https://img.shields.io/github/license/ankitsingh7392/ai-toolkit" alt="License">
</p>

<p align="center">
  A mono-repo of production-grade AI projects — each isolated, enterprise-ready, and built for real-world use.
</p>

---

## Overview

**AI Toolkit** is a curated collection of standalone AI projects built to production standards. Each project lives in its own directory with its own dependencies, documentation, and tests — but they all share the same quality bar: linted, tested, reviewed, and ready to ship.

## Projects

| Project | Language | Status | Description |
|---------|----------|--------|-------------|
| *(coming soon)* | — | — | First enterprise project |

## Repository Standards

This repo enforces:

- **Conventional Commits** for all commit messages and PR titles
- **Pre-commit hooks** (ruff, shellcheck, golangci-lint, gitleaks) run before every commit
- **CI checks** (MegaLinter) run on every PR — Python, Shell, Go, Java, YAML, Markdown
- **Secret scanning** via Gitleaks on every PR and push
- **Branch protection** — no direct pushes to `main`, PRs required

## Getting Started

### Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
- [pre-commit](https://pre-commit.com/) — Git hook manager
- [Go](https://go.dev/) *(for Go projects)*
- [Java 17+](https://adoptium.net/) *(for Java projects)*

### Setup

```bash
# Clone the repo
git clone https://github.com/ankitsingh7392/ai-toolkit.git
cd ai-toolkit

# Install Python toolchain via uv
uv sync

# Install pre-commit hooks
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

### Running Hooks Manually

```bash
# Run all hooks on all files
uv run pre-commit run --all-files

# Run a specific hook
uv run pre-commit run ruff --all-files
uv run pre-commit run gitleaks --all-files
```

## Project Structure

```
ai-toolkit/
├── .github/
│   ├── workflows/          # CI/CD pipelines
│   ├── ISSUE_TEMPLATE/     # Bug reports & feature requests
│   └── PULL_REQUEST_TEMPLATE.md
├── projects/               # Individual AI projects (each self-contained)
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
└── pyproject.toml          # Root Python tooling config
```

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR. All contributions must pass pre-commit hooks and CI checks.

## Security

To report a vulnerability, see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
