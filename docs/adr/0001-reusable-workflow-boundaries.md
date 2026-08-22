# ADR-0001: Reusable workflows are capability contracts

Status: accepted

## Context and targets

Tesserix expects up to **20 product repositories** in 12 months and 50 in 36
months. The CI workload is bursty rather than request-driven: plan for ten pull
request runs per hour, up to four image builds per run, and checkouts below
500 MB. Pull-request feedback must remain below **five minutes** at p95 for the
current Rust/Next.js adopter; single-language repositories should finish faster.
GitHub Actions availability and latency are inherited dependencies.

Policy copied into every repository drifts. A single product-shaped workflow,
however, merely moves that coupling into a repository with a larger blast
radius. The contract must centralize stable language and supply-chain stages
while leaving product policy at the caller.

Assets worth protecting are source, read-only package credentials, GitHub job
tokens, published images, attestations, and merge rights. Threats include fork
pull requests, compromised dependencies or actions, malicious workflow inputs,
and accidental policy weakening. Trust boundaries are the product caller, this
public repository, GitHub-hosted runners, GHCR, and external advisory services.

## Options considered

1. Keep complete workflows in every repository. This minimizes central blast
   radius but guarantees drift and repeats every security fix.
2. Expose one generic workflow that accepts arbitrary build and test commands.
   This centralizes YAML but turns unvalidated shell strings into a public API.
3. Publish fixed capability workflows for Go, Python, Rust, Next.js, secrets,
   container verification, and container release, plus a thin orchestrator.

## Decision

Choose option 3. Each language workflow owns a complete, opinionated quality
contract. `ci.yml` composes enabled capabilities and always runs secret scanning;
its final `CI gate` depends on every selected capability so branch protection has
one stable required-check name.

Inputs express intent: toolchain versions, working directories, coverage floors,
an immutable database image, a validated bootstrap path, and an image matrix.
There are no arbitrary command inputs. Product-owned audit exceptions use the
language tool's native configuration and stay beside their justification.

All external actions are pinned to full commit SHAs. Default permissions are
read-only. Release alone requests package write and OIDC rights, publishes once,
scans the resulting digest, attaches SBOM and provenance, and signs that digest.
The caller cannot grant a called workflow more privilege than the caller holds.

Versions are immutable semantic tags. Breaking the input or gate contract
requires a new major release; callers never reference `main`.

## Failure behaviour

- A formatter, compiler, test, coverage floor, audit, secret scan, image scan,
  smoke test, or selected capability failure makes `CI gate` fail closed.
- Registry, advisory, package, schema, Fulcio, or Rekor unavailability fails the
  affected gate. Retrying the same commit is safe.
- A disabled language job is skipped and accepted; an enabled failed or cancelled
  job is rejected by the aggregate gate.
- A failed release scan leaves an unsigned digest. Deployment policy must require
  a valid signature, so that digest cannot be promoted.
- A workflow defect affects only callers that adopt its immutable release tag.

## Migration

1. Replace the product-shaped v1 files on `main` with the capability workflows.
2. Validate the v2 candidate through contract tests, Actionlint, and a real
   multi-language product using the candidate commit SHA.
3. Merge and publish the immutable `v2.0.0` tag.
4. Change the product caller from the candidate SHA to `v2.0.0`, observe final
   check names, and require `CI gate` plus the independent security service.

## Rollback

Revert only the product caller to its previous immutable workflow tag or
in-repository workflow. Never move or overwrite a released tag. Container
rollback remains digest-based and is independent of the CI workflow version.

## Consequences and cost

One central patch can improve every opted-in repository, so protected releases
and staged caller upgrades are mandatory. A product runs only its selected
language jobs; secret scanning adds one small runner, and container matrices add
one runner per image. The current four-image adopter should remain near four
runner-minutes and below the five-minute p95 wall-clock target. Go and Python
contracts have static and syntax coverage until their first real adopters provide
measured baselines; those callers must validate before the shared defaults change.
