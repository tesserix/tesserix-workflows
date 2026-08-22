# Vehicle rental Rust coverage

The complete workspace measured **52.70% line coverage** on 22 August 2026.
The reusable workflow therefore rejects coverage below 52% from its first
adoption. This is an enforceable baseline, not a claim that 52% is sufficient.

Coverage runs across the whole workspace with every feature and the ignored
Postgres integration tests enabled. Production transport and wiring code stays
in scope; only test files and generated API bindings are excluded.

The ratchet target is **70%**. Raise the blocking threshold as tests land and
never lower it without a time-bounded, reviewed exception that records the
measured baseline and an owner.
