from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
EXAMPLES = ROOT / "examples"
REUSABLE_WORKFLOWS = {
    "ci.yml",
    "container-ci.yml",
    "container-release.yml",
    "go-ci.yml",
    "nextjs-ci.yml",
    "python-ci.yml",
    "rust-ci.yml",
    "secret-scan.yml",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ReusableWorkflowContract(unittest.TestCase):
    def assert_workflow_contains(self, name: str, *guarantees: str) -> None:
        workflow = read(WORKFLOWS / name)
        for guarantee in guarantees:
            with self.subTest(workflow=name, guarantee=guarantee):
                self.assertIn(guarantee, workflow)

    def test_repository_exposes_only_global_reusable_workflow_names(self) -> None:
        actual = {
            path.name
            for path in WORKFLOWS.glob("*.yml")
            if path.name != "validate.yml"
        }
        self.assertEqual(REUSABLE_WORKFLOWS, actual)

    def test_every_reusable_workflow_fails_closed(self) -> None:
        for name in REUSABLE_WORKFLOWS:
            workflow = read(WORKFLOWS / name)
            with self.subTest(workflow=name):
                self.assertIn("workflow_call:", workflow)
                self.assertNotIn("continue-on-error", workflow)
                self.assertNotIn("secrets: inherit", workflow)
                self.assertNotRegex(workflow, r"\b(?:build|lint|test|run)_command:")

    def test_go_workflow_enforces_the_complete_language_gate(self) -> None:
        self.assert_workflow_contains(
            "go-ci.yml",
            "actions/setup-go@",
            "gofmt -l .",
            "go mod verify",
            "go vet ./...",
            "go build ./...",
            "go test -race",
            "govulncheck ./...",
            "coverage_min_lines",
        )

    def test_python_workflow_enforces_the_complete_language_gate(self) -> None:
        self.assert_workflow_contains(
            "python-ci.yml",
            "actions/setup-python@",
            "astral-sh/setup-uv@",
            "uv sync --locked --all-extras --dev",
            "ruff format --check",
            "ruff check",
            "mypy --strict",
            "pytest --cov",
            "--cov-fail-under",
            "pip-audit",
            "uv build",
        )

    def test_rust_workflow_enforces_quality_and_optional_database_coverage(
        self,
    ) -> None:
        self.assert_workflow_contains(
            "rust-ci.yml",
            "cargo fmt --all --check",
            "cargo clippy --workspace --all-targets -- -D warnings",
            "cargo build --workspace --all-features",
            "cargo test --workspace --all-features",
            "cargo audit",
            "cargo llvm-cov --workspace --all-features",
            "database_enabled",
            "database_image",
            "database_setup_script",
            "--include-ignored",
            "coverage_min_lines",
        )
        self.assertNotIn("RUSTSEC-", read(WORKFLOWS / "rust-ci.yml"))

    def test_nextjs_workflow_enforces_the_complete_framework_gate(self) -> None:
        self.assert_workflow_contains(
            "nextjs-ci.yml",
            "actions/setup-node@",
            "npm ci",
            "legacy_peer_dependencies:",
            "npm ci --legacy-peer-deps",
            "npm run format:check",
            "npm run lint",
            "npm test",
            "npm run check-types",
            "audit_workspaces:",
            "NPM_AUDIT_WORKSPACES",
            "--workspace=$workspace",
            "npm audit --audit-level=high --omit=dev",
            "npm run build",
        )

    def test_container_workflows_build_smoke_scan_and_release_by_digest(self) -> None:
        self.assert_workflow_contains(
            "container-ci.yml",
            "fromJSON(inputs.images)",
            "docker/build-push-action@",
            "Smoke test image",
            "aquasecurity/trivy-action@",
            "severity: CRITICAL,HIGH",
            "exit-code: 1",
            "target: ${{ matrix.target }}",
            "dev.tesserix.source.root=${{ matrix.source_root }}",
            "trivyignores: ${{ matrix.trivy_ignore_file }}",
            "PACKAGE_READ_TOKEN=${{ secrets.package_read_token }}",
            "APPLICATION_BUILD_SECRET=${{ secrets.application_build_secret }}",
            "REUSABLE_BUILD_SECRET_FP",
            "REUSABLE_PUBLIC_BUILD_ARG_8=${{ secrets.public_build_arg_8 }}",
        )
        self.assert_workflow_contains(
            "container-release.yml",
            "fromJSON(inputs.images)",
            "push: true",
            "sbom: true",
            "provenance: mode=max",
            "Smoke test published image",
            "steps.build.outputs.digest",
            "cosign sign --yes",
            "target: ${{ matrix.target }}",
            "dev.tesserix.source.root=${{ matrix.source_root }}",
            "trivyignores: ${{ matrix.trivy_ignore_file }}",
            "PACKAGE_READ_TOKEN=${{ secrets.package_read_token }}",
            "APPLICATION_BUILD_SECRET=${{ secrets.application_build_secret }}",
            "REUSABLE_BUILD_SECRET_FP",
            "REUSABLE_PUBLIC_BUILD_ARG_8=${{ secrets.public_build_arg_8 }}",
        )

    def test_secret_scan_is_a_single_reusable_gate(self) -> None:
        self.assert_workflow_contains(
            "secret-scan.yml",
            "fetch-depth: 0",
            "sha256sum -c -",
            "gitleaks dir . --no-banner --redact",
        )

    def test_orchestrator_composes_capabilities_and_has_one_stable_gate(self) -> None:
        self.assert_workflow_contains(
            "ci.yml",
            "./.github/workflows/go-ci.yml",
            "./.github/workflows/python-ci.yml",
            "./.github/workflows/rust-ci.yml",
            "./.github/workflows/nextjs-ci.yml",
            "./.github/workflows/container-ci.yml",
            "./.github/workflows/secret-scan.yml",
            "name: CI gate",
            "needs.*.result",
            "nextjs_legacy_peer_dependencies:",
            "nextjs_audit_workspaces:",
            "container_registry_token:",
            "container_application_build_secret:",
            "container_public_build_arg_8:",
        )

    def test_external_actions_are_pinned_to_full_commit_shas(self) -> None:
        for path in WORKFLOWS.glob("*.yml"):
            for line in read(path).splitlines():
                match = re.search(r"\buses:\s+([^\s#]+)", line)
                if not match:
                    continue
                reference = match.group(1)
                if reference.startswith("./") or reference.startswith("docker://"):
                    continue
                with self.subTest(path=path.name, reference=reference):
                    self.assertRegex(reference, r"^[^@]+@[0-9a-f]{40}$")

    def test_permissions_are_least_privilege(self) -> None:
        for name in REUSABLE_WORKFLOWS - {"container-release.yml"}:
            with self.subTest(workflow=name):
                self.assertRegex(
                    read(WORKFLOWS / name), r"permissions:\s+contents: read"
                )
        self.assertRegex(
            read(WORKFLOWS / "container-release.yml"),
            r"permissions:\s+contents: read\s+packages: write\s+id-token: write",
        )

    def test_examples_are_thin_and_pin_the_v2_release(self) -> None:
        callers = list(EXAMPLES.rglob("*.yml"))
        self.assertGreaterEqual(len(callers), 2)
        for path in callers:
            workflow = read(path)
            meaningful = [
                line
                for line in workflow.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertLessEqual(len(meaningful), 45)
                self.assertIn("tesserix/tesserix-workflows/", workflow)
                self.assertIn("@v2.1.0", workflow)
                self.assertNotIn("@main", workflow)

    def test_architecture_decision_records_migration_and_rollback(self) -> None:
        decision = read(ROOT / "docs" / "adr" / "0001-reusable-workflow-boundaries.md")
        for guarantee in (
            "20 product repositories",
            "p95",
            "five minutes",
            "Failure behaviour",
            "Migration",
            "Rollback",
            "v2.0.0",
        ):
            with self.subTest(guarantee=guarantee):
                self.assertIn(guarantee, decision)


if __name__ == "__main__":
    unittest.main()
