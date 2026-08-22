# Vehicle rental exception: RUSTSEC-2023-0071

- Owner: Tesserix platform
- Review by: 2026-11-22
- Affected dependency: `rsa 0.9.10`
- Status: no fixed upstream release is available

`rsa` is a development-only dependency of `vr-auth`. Tests generate an
ephemeral key to exercise JWT verification and a mock JWKS server; the crate is
not linked into the production API. The timing side channel therefore has no
attacker-controlled production private key to observe.

The shared workflow ignores only `RUSTSEC-2023-0071`; every other RustSec
advisory remains fatal. Remove the exception when a fixed `rsa` release is
available or before any production use of the crate.
