# Tesserix workflows

Versioned, product-neutral GitHub Actions workflows for Tesserix repositories.
Product repositories own triggers and product policy; this repository owns the
repeatable implementation of quality, security, and image-supply-chain gates.

| Workflow | Contract |
| --- | --- |
| `ci.yml` | Composes enabled capabilities and exposes one stable aggregate gate |
| `go-ci.yml` | Format, dependency verification, vet, build, race tests, coverage, and vulnerability audit |
| `python-ci.yml` | Locked uv install, Ruff, strict mypy, pytest coverage, dependency audit, and package build |
| `rust-ci.yml` | Format, Clippy, build, tests, audit, coverage, and optional Postgres integration coverage |
| `nextjs-ci.yml` | Locked npm install, format, lint, tests, typecheck, workspace-scoped audit, and production build |
| `container-ci.yml` | Matrix build, optional HTTP smoke test, and blocking Trivy scan |
| `container-release.yml` | GHCR publish with smoke test, SBOM, provenance, digest scan, and keyless signing |
| `secret-scan.yml` | Full-history Gitleaks scan with a checksum-verified binary |

## Caller contract

Callers pin an immutable semantic release such as `v2.1.0`; they never use
`main`. Inputs describe intent and repository layout, not shell commands:

- enabled language capabilities and their working directories;
- toolchain versions and coverage floors;
- an immutable database image and validated bootstrap-script path when needed;
- a JSON image matrix containing Dockerfiles, optional targets, source roots,
  public build arguments, product-owned Trivy exceptions, and smoke paths;
- an explicitly mapped read-only npm token when private packages are used.

Container callers may also map a private registry token, a package token, one
protected application build secret, and up to eight values that are public by
definition once baked into an image. The protected values are mounted through
BuildKit secrets and never accepted as build arguments. Callers map public
values to the fixed `REUSABLE_PUBLIC_BUILD_ARG_*` interface in their Dockerfile.

Repository-specific coverage baselines, advisory exceptions, schema bootstrap,
and image names remain with the product. Standard package scripts are the
language boundary; the shared workflow does not accept arbitrary commands.

See [`examples/polyglot-app`](examples/polyglot-app) for thin CI and release
callers. The boundary, failure behaviour, migration, and rollback decision is
recorded in [`ADR-0001`](docs/adr/0001-reusable-workflow-boundaries.md).

## Validation

```bash
python3 -m unittest discover -s tests -v
actionlint
```

The repository required check runs the same contract suite and Actionlint.
