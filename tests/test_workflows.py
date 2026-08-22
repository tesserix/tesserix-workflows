from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
EXAMPLES = ROOT / "examples" / "vehicle-rental-app"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class VehicleRentalWorkflowContract(unittest.TestCase):
    def test_ci_workflow_keeps_every_mandatory_gate(self) -> None:
        workflow = read(WORKFLOWS / "vehicle-rental-ci.yml")

        for gate in (
            "workflow_call:",
            "cargo fmt --all --check",
            "cargo clippy --workspace --all-targets -- -D warnings",
            "cargo test --workspace --test boundaries",
            "cargo llvm-cov --workspace --all-features",
            "--fail-under-lines 70",
            "scripts/test-db.sh",
            "cargo audit",
            "npm ci",
            "npm run lint",
            "npm test",
            "npm run check-types",
            "npm run build",
            "npm audit --audit-level=high --omit=dev",
            "gitleaks dir . --no-banner --redact",
        ):
            with self.subTest(gate=gate):
                self.assertIn(gate, workflow)

        self.assertNotIn("continue-on-error", workflow)
        self.assertNotIn("Test, without a database", workflow)

    def test_image_workflow_builds_scans_attests_and_signs_each_image(self) -> None:
        workflow = read(WORKFLOWS / "vehicle-rental-images.yml")

        for image in (
            "vehicle-rental-api",
            "vehicle-rental-storefront",
            "vehicle-rental-admin",
            "vehicle-rental-onboarding",
        ):
            with self.subTest(image=image):
                self.assertIn(image, workflow)

        for guarantee in (
            "workflow_call:",
            "push: true",
            "sbom: true",
            "provenance: mode=max",
            "severity: CRITICAL,HIGH",
            "exit-code: 1",
            "cosign sign --yes",
            "steps.build.outputs.digest",
        ):
            with self.subTest(guarantee=guarantee):
                self.assertIn(guarantee, workflow)

    def test_rust_audit_exception_is_central_and_documented(self) -> None:
        workflow = read(WORKFLOWS / "vehicle-rental-ci.yml")
        exception = read(
            ROOT
            / "docs"
            / "security-exceptions"
            / "vehicle-rental-rustsec-2023-0071.md"
        )

        self.assertIn("cargo audit --ignore RUSTSEC-2023-0071", workflow)
        self.assertEqual(workflow.count("--ignore RUSTSEC-2023-0071"), 1)
        self.assertIn("RUSTSEC-2023-0071", exception)
        self.assertIn("2026-11-22", exception)

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

    def test_vehicle_callers_are_thin_and_versioned(self) -> None:
        for name in ("ci.yml", "images.yml"):
            path = EXAMPLES / name
            workflow = read(path)
            meaningful = [
                line
                for line in workflow.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            with self.subTest(path=name):
                self.assertLessEqual(len(meaningful), 30)
                self.assertIn("tesserix/tesserix-workflows/", workflow)
                self.assertIn("@v1.0.0", workflow)
                self.assertNotIn("@main", workflow)

    def test_workflows_default_to_least_privilege(self) -> None:
        ci = read(WORKFLOWS / "vehicle-rental-ci.yml")
        images = read(WORKFLOWS / "vehicle-rental-images.yml")

        self.assertRegex(ci, r"permissions:\s+contents: read")
        self.assertRegex(
            images,
            r"permissions:\s+contents: read\s+packages: write\s+id-token: write",
        )
        self.assertNotIn("secrets: inherit", read(EXAMPLES / "ci.yml"))


if __name__ == "__main__":
    unittest.main()
