# ADR-0001: Vehicle rental is the first reusable-workflow adopter

Status: accepted

## Context

Vehicle rental currently owns two GitHub Actions workflows totalling roughly
150 lines. CI covers 20 Rust workspace crates, three Next.js applications, a
PostGIS-backed integration suite, and a secret scan. Release builds publish four
images. The latest observed successful runs took 2m05s wall-clock for CI and
2m48s for images, consuming about 2.9 and 3.9 Linux runner-minutes respectively.

The first adoption must keep PR feedback below five minutes at p95 and must not
weaken a gate during migration. GitHub Actions availability is inherited; this
repository promises only that a pinned workflow revision behaves consistently.
The policy contract is versioned separately from product code.

Assets worth protecting are source, package-read credentials, `GITHUB_TOKEN`,
published images, provenance, and the right to merge. Threats include a fork PR,
a compromised third-party action, a malicious dependency, and an accidental
workflow edit. The trust boundaries are the public caller, this public workflow
repository, GitHub's short-lived job token, GHCR, and the external package and
advisory services. Every external action is pinned to a commit, fork PRs receive
no repository secret, and release identity is granted only through the caller's
explicit `packages: write` and `id-token: write` permissions.

## Options considered

1. Keep copied workflows in each product. This preserves a small platform blast
   radius but guarantees policy drift and multiplies every future fix.
2. Build one generic workflow with commands and per-gate switches as inputs.
   This centralises YAML while making the policy optional and exposing an API
   before real callers establish its shape.
3. Move the proven vehicle-rental contract first, leaving only versioned callers
   in the product repository. Extract language workflows when a second adopter
   supplies evidence for the common boundary.

## Decision

Choose option 3. This repository owns two promises:

- `vehicle-rental-ci.yml` validates Rust, web, dependencies, secrets, coverage,
  and pull-request container images.
- `vehicle-rental-images.yml` publishes four immutable image tags, attaches an
  SBOM and provenance, blocks high or critical findings, and signs the digest
  with GitHub OIDC.

The caller exposes no gate toggles. Its only secret is the explicitly mapped,
read-only npm package token. Release callers must grant package and OIDC rights;
the called workflow cannot elevate a weaker caller token.

The workflows are released with immutable semantic-version tags. Product
callers never use `@main`. Third-party actions use full commit SHAs.

## Failure behaviour

- If the schema repository, package registry, advisory database, GHCR, Fulcio,
  or Rekor is unavailable, its gate fails closed. Retrying the same commit is
  safe; builds use immutable commit-derived tags.
- A duplicate image publish resolves to the same content digest. Kargo promotes
  the digest, never a mutable tag.
- A failed scan leaves an unsigned image in GHCR, so signature verification must
  prevent promotion. Cleanup remains a registry-retention concern.
- A workflow defect affects only callers that adopt its version. Fixes produce a
  new immutable patch tag; existing tags are never moved.

## Migration and rollback

1. Merge and release `v1.0.0` here.
2. Replace the two vehicle-rental workflow bodies with the example callers.
3. Observe the real check-run names, then require them on `main` together with
   pull-request approval, conversation resolution, and linear history.
4. Roll back by reverting the caller commit to its previous in-repository
   workflows. Do not move or overwrite `v1.0.0`.

The expected incremental PR cost is about four runner-minutes for four parallel
container verification jobs; wall-clock should stay below five minutes. The
main-branch build avoids this duplicate work and uses the release workflow.

## Consequences

One central change can improve or break every adopted repository, so releases
and staged upgrades become mandatory. The first workflow remains product-shaped
on purpose. Go, Python, and general Rust/Next.js workflows are not implemented
until another existing pipeline supplies a second concrete contract.
