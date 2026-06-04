# Contributing to AI Toolkit

Thank you for your interest in contributing. This document covers everything you need to get set up, make a change, and get it merged.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Branch Naming](#branch-naming)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Testing](#testing)

---

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating you agree to abide by its terms.

---

## Getting Started

1. **Fork** the repository and clone your fork.
2. **Create a branch** from `main` following the naming convention below.
3. **Make your changes**, ensuring all hooks and tests pass.
4. **Open a PR** against `main` using the PR template.

---

## Development Setup

This repo uses [uv](https://docs.astral.sh/uv/) for Python dependency management and [pre-commit](https://pre-commit.com/) for automated checks.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install pre-commit hooks (run this once after cloning)
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

### Verify Your Setup

```bash
uv run pre-commit run --all-files
```

All hooks should pass before you start making changes.

---

## Branch Naming

Branches must follow this pattern:

```
<type>/<short-description>
```

| Type | When to use |
|------|-------------|
| `feat/` | New feature or project |
| `fix/` | Bug fix |
| `docs/` | Documentation only |
| `refactor/` | Code refactoring, no behavior change |
| `test/` | Adding or updating tests |
| `chore/` | Tooling, dependencies, CI changes |
| `perf/` | Performance improvements |

**Examples:**
```
feat/langchain-rag-pipeline
fix/openai-retry-logic
docs/setup-guide
chore/update-pre-commit-hooks
```

---

## Commit Messages

This repo follows [Conventional Commits](https://www.conventionalcommits.org/).

**Format:**
```
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `perf`, `revert`

**Rules:**
- Summary line: max 72 characters, lowercase, no period at end
- Use imperative mood: "add feature" not "added feature"
- Reference issues in footer: `Closes #123`

**Examples:**
```
feat(rag): add hybrid search with BM25 and dense retrieval

fix(api): handle rate limit errors with exponential backoff

docs: update setup instructions for uv

chore(ci): pin megalinter to v8
```

---

## Pull Request Process

1. **Title** must follow the same Conventional Commits format as commit messages (enforced by CI).
2. **Fill out** the PR template completely — incomplete PRs will be asked for more detail.
3. **Keep PRs focused** — one logical change per PR. Split unrelated changes.
4. **All CI checks must pass** before a PR can be merged.
5. **Self-review** your diff before requesting review.

### PR Checklist

- [ ] Pre-commit hooks pass locally (`uv run pre-commit run --all-files`)
- [ ] Tests pass for any changed project
- [ ] Documentation updated if behavior changed
- [ ] No secrets or credentials in the diff
- [ ] PR title follows Conventional Commits format

---

## Code Style

### Python

- **Formatter & linter:** [Ruff](https://docs.astral.sh/ruff/) — configured in `pyproject.toml`
- **Line length:** 88 characters
- **Target:** Python 3.11+
- Run: `uv run ruff check --fix . && uv run ruff format .`

### Shell

- **Linter:** [ShellCheck](https://www.shellcheck.net/)
- Scripts must pass `shellcheck` with no warnings

### Go

- **Linter:** [golangci-lint](https://golangci-lint.run/)
- Format with `gofmt`, vet with `go vet`

### Java

- **Formatter:** [google-java-format](https://github.com/google/google-java-format)
- **Style:** Google Java Style Guide

### General

- No trailing whitespace
- Files end with a newline
- Use `.editorconfig` settings (auto-applied by most editors)

---

## Testing

Each project in the monorepo manages its own tests. See the `README.md` inside each project directory for how to run tests.

**General rule:** if you add or change behavior, add a test.

---

## Questions?

Open a [Discussion](https://github.com/ankitsingh7392/ai-toolkit/discussions) or file an [Issue](https://github.com/ankitsingh7392/ai-toolkit/issues) with the `question` label.
