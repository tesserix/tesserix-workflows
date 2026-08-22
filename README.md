# Tesserix workflows

Versioned reusable GitHub Actions workflows for Tesserix products. Product
repositories keep only a thin event-and-permissions caller; policy and tooling
live here.

## First adopter: vehicle rental

| Workflow | Promise |
| --- | --- |
| `vehicle-rental-ci.yml` | Rust and Next.js format, lint, build, tests, coverage, dependency and secret scanning, plus PR image builds and vulnerability scans |
| `vehicle-rental-images.yml` | Four GHCR images built once, scanned, given an SBOM and provenance, then keylessly signed by digest |

Copy the callers from [`examples/vehicle-rental-app`](examples/vehicle-rental-app)
into the product's `.github/workflows` directory. Callers use an immutable
release such as `v1.0.0`; never use `main`.

The current design and migration/rollback contract are recorded in
[`ADR-0001`](docs/adr/0001-vehicle-rental-first-adopter.md).

## Validation

```bash
python3 -m unittest discover -s tests -v
actionlint
```

The repository CI runs the same contract tests and Actionlint validation.
Versioned reusable GitHub Actions workflows for Tesserix products
