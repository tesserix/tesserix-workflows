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

Assets worth protecting are source, package, Expo, Sentry, and App Store Connect
credentials, GitHub job tokens, unpublished IPAs, published images, attestations,
and merge rights. Threats include fork pull requests, compromised dependencies
or actions, malicious workflow inputs, and accidental policy weakening. Trust
boundaries are the product caller, this public repository, GitHub-hosted runners,
Expo/EAS, Apple, GHCR, and external advisory services.

## Options considered

1. Keep complete workflows in every repository. This minimizes central blast
   radius but guarantees drift and repeats every security fix.
2. Expose one generic workflow that accepts arbitrary build and test commands.
   This centralizes YAML but turns unvalidated shell strings into a public API.
3. Publish fixed capability workflows for Go, Python, Rust, Next.js, Expo,
   secrets, container verification, and release, plus a thin orchestrator.

## Decision

Choose option 3. Each language workflow owns a complete, opinionated quality
contract. `ci.yml` composes enabled capabilities and always runs secret scanning;
its final `CI gate` depends on every selected capability so branch protection has
one stable required-check name.

Inputs express intent: toolchain versions, working directories, coverage floors,
an immutable database image, a validated bootstrap path, and an image matrix.
There are no arbitrary command inputs. Product-owned audit exceptions use the
language tool's native configuration and stay beside their justification.

The additive `v2.1.0` container contract supports monorepo image targets,
source-root labels, product-owned Trivy ignore files, optional private registry
and package credentials, one protected BuildKit application secret, and eight
explicit public build values. Secret values stay on BuildKit secret mounts;
only values already intended for the published client or image configuration
may use the public build-argument interface.

Expo mobile quality is a fixed capability: locked npm or pnpm installation,
typed-route generation, typecheck, standard package scripts, dependency audit,
and a pinned Expo Doctor. Cloud EAS builds and local iOS releases are separate
contracts because they have different cost, runner, artifact, and failure
domains. The cloud contract can queue and optionally link submission on EAS.
The local iOS contract pins macOS, Xcode, Node, EAS CLI, and actions; accepts the
App Store Connect key triple only as all-or-none; requires a product to opt into
the Sentry production guard; and submits the exact local IPA by path without
publishing it as a public Actions artifact.

All external actions are pinned to full commit SHAs. Default permissions are
read-only. Release alone requests package write and OIDC rights, publishes once,
scans the resulting digest, attaches SBOM and provenance, and signs that digest.
The caller cannot grant a called workflow more privilege than the caller holds.

Versions are immutable semantic tags. Breaking the input or gate contract
requires a new major release; callers never reference `main`.

## Failure behaviour

- A formatter, compiler, test, coverage floor, audit, secret scan, image scan,
  smoke test, or selected capability failure makes `CI gate` fail closed.
- Expo authentication, signing, source-map, local build, or exact-artifact
  submission failure stops the mobile release; no stale cloud build is selected.
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
3. The initial migration published immutable `v2.0.0`; additive contracts are
   staged the same way and receive the next unused semantic release.
4. Change product callers from the candidate SHA to that immutable tag, observe
   final check names, and require `CI gate` plus independent security services.

## Rollback

Revert only the product caller to its previous immutable workflow tag or
in-repository workflow. Never move or overwrite a released tag. Container
rollback remains digest-based and is independent of the CI workflow version.
An iOS rollback re-runs the caller at its previous immutable workflow tag and
build profile; store rollback remains product-owned because submission cannot
remove a binary already accepted by App Store Connect.

## Consequences and cost

One central patch can improve every opted-in repository, so protected releases
and staged caller upgrades are mandatory. A product runs only its selected
language jobs; secret scanning adds one small runner, and container matrices add
one runner per image. The current four-image adopter should remain near four
runner-minutes and below the five-minute p95 wall-clock target. Go and Python
contracts have static and syntax coverage until their first real adopters provide
measured baselines; those callers must validate before the shared defaults change.
Cloud EAS builds consume the product's EAS quota. Local iOS releases consume a
GitHub-hosted macOS runner for up to 90 minutes; callers therefore keep their
release triggers manual or tag-scoped and prevent concurrent submissions.
