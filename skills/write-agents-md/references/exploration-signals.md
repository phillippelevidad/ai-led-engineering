# Exploration signals by project type

Read during Step 2. Extract only facts the agent would guess wrong — never copy config into `AGENTS.md`.

## Software — JavaScript / TypeScript

| Signal | Extract |
| ------ | ------- |
| `package.json` | Package manager, scripts (`dev`, `test`, `build`, `lint`, `typecheck`), engines, workspace layout |
| `pnpm-workspace.yaml`, `lerna.json`, `nx.json`, `turbo.json` | Monorepo boundaries, task runner |
| `tsconfig.json`, `jsconfig.json` | Module system, path aliases, strictness the agent must respect |
| `.eslintrc*`, `eslint.config.*`, `prettier.config.*`, `biome.json` | Only non-obvious lint/format rules not inferable from defaults |
| `vitest.config.*`, `jest.config.*`, `playwright.config.*` | Test runner, e2e vs unit split, unusual test paths |
| `next.config.*`, `vite.config.*`, `webpack.config.*` | Framework-specific constraints |
| `Dockerfile`, `docker-compose.yml` | Runtime side effects, required services |

## Software — Python

| Signal | Extract |
| ------ | ------- |
| `pyproject.toml`, `setup.py`, `requirements*.txt`, `Pipfile` | Package manager, scripts, Python version, optional deps |
| `poetry.lock`, `uv.lock` | Lockfile presence — do not duplicate versions into AGENTS.md |
| `tox.ini`, `noxfile.py`, `Makefile` | Multi-env test/build commands |
| `.python-version`, `.tool-versions` | Pin the agent must not override |
| `pytest.ini`, `conftest.py` location | Test layout, fixtures pattern |
| `ruff.toml`, `.flake8`, `mypy.ini` | Lint/type rules the agent can't infer |

## Software — Rust, Go, Java, .NET, Ruby, PHP

| Ecosystem | Key signals |
| --------- | ----------- |
| Rust | `Cargo.toml`, `rust-toolchain.toml`, workspace members |
| Go | `go.mod`, `Makefile`, `internal/` vs `pkg/` layout |
| Java/Kotlin | `pom.xml`, `build.gradle*`, `settings.gradle*` |
| .NET | `*.csproj`, `*.sln`, `Directory.Build.props` |
| Ruby | `Gemfile`, `Rakefile`, `bin/` scripts |
| PHP | `composer.json`, `phpunit.xml`, `artisan` (Laravel) |

Distill: build command, test command, module/package boundaries, generated dirs to never edit.

## Infra / ops

| Signal | Extract |
| ------ | ------- |
| `terraform/`, `*.tf` | State backend, env separation, modules the agent must not restructure |
| `helm/`, `k8s/`, `charts/` | Deploy targets, namespace conventions |
| `.github/workflows/`, `.gitlab-ci.yml` | Required checks, deploy gates, secrets/env assumptions |
| `ansible/`, `pulumi/`, `cdk.json` | Idempotency rules, env naming |

## Non-software (docs, research, content, design)

| Signal | Extract |
| ------ | ------- |
| README, CONTRIBUTING | Audience, publishing workflow, review gates |
| Parent `AGENTS.md` | Upstream lifecycle, folder roles, tone |
| Style guides, templates | Voice, heading rules, required frontmatter |
| Folder names | Canonical vs scratch (`draft/` vs `published/`, `brainstorming/` vs `research/`) |
| CMS/export config | Build or publish steps if non-obvious |
| CI on markdown | Link check, spell check, lint rules worth stating |

Skip stack/tooling and commands sections when there is no toolchain. See [non-software-example.md](non-software-example.md).

## What to skip everywhere

- Verbatim config dumps
- Version numbers the agent reads from lockfiles
- Standard directory layouts for the detected framework
- Git/PR workflow
- Business domain facts (belong in task prompts)
