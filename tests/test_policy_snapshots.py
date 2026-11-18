"""Offline snapshot validation. Synthetic data is never qualification evidence."""
from pathlib import Path
import os
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1] / "policy-snapshots"


class PolicySnapshotTests(unittest.TestCase):
    def run_snapshot(self, name: str, script: str) -> None:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        subprocess.run([sys.executable, "-c", script], cwd=ROOT / name, env=env, check=True)

    def test_governance_profiles(self):
        code = '''
from tools.software_assurance.validate import main
from tools.software_assurance.policy import validate_rollout_candidate
assert main() == 0
for profile in ("balanced", "release"):
    candidate = {"name":"djconnect-music-dj/djconnect", "execution_profile":profile,
      "policy_version":"1.0.0", "timeout_minutes":10, "permissions":{"contents":"read"},
      "concurrency_group":"software-assurance-governance", "action_pinning":"full_length_commit_sha"}
    assert validate_rollout_candidate(candidate) == []
'''
        for name in ("governance-3d7d", "governance-631f"):
            with self.subTest(snapshot=name):
                self.run_snapshot(name, code)

    def test_core_diagnostic_is_manual_and_read_only(self):
        text = (ROOT.parent / ".github/workflows/core-evidence-readonly.yml").read_text()
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("github.actor_id == '19624891'", text)
        self.assertIn("target.id !== 1258575431", text)
        self.assertIn("Core main changed during readback", text)
        self.assertIn("ha-cobertura-coverage", text)
        self.assertIn("ref: ${{ github.sha }}", text)
        self.assertNotIn(": write", text)
        self.assertNotIn("gh release", text)
        self.assertNotIn("createCommitStatus", text)
        self.assertNotIn("upload-artifact", text)

    def test_diagnostic_caller_is_read_only_and_uses_exact_workflow(self):
        text = (ROOT.parent / ".github/workflows/evidence-readonly-diagnostic.yml").read_text()
        self.assertIn("workflow_run:", text)
        self.assertIn("Policy snapshot validation", text)
        self.assertIn("./.github/workflows/policy-evidence-readonly-self.yml", text)
        self.assertIn("policy_source_ref: ${{ github.event.workflow_run.head_sha }}", text)
        self.assertNotIn(": write", text)
        self.assertNotIn("gh release", text)

    def test_self_contained_governance_and_diagnostic_keep_identity_guards(self):
        workflows = ROOT.parent / ".github/workflows"
        policy = (workflows / "policy-snapshot-validation.yml").read_text()
        self.assertEqual(policy.count("./.github/workflows/policy-governance-self.yml"), 2)
        governance = (workflows / "policy-governance-self.yml").read_text()
        self.assertIn("repo.id !== 1461539726", governance)
        self.assertIn("ref: ${{ steps.policy-revision.outputs.sha }}", governance)
        self.assertIn("policySha = base.sha", governance)
        self.assertIn("current.data.commit?.sha !== policySha", governance)
        self.assertIn("validate_rollout_candidate", governance)
        self.assertIn("validate_action_runtimes", governance)
        diagnostic = (workflows / "policy-evidence-readonly-self.yml").read_text()
        self.assertIn("EXPECTED_POLICY_REF: ${{ github.event.workflow_run.head_sha }}", diagnostic)
        self.assertIn("test \"$POLICY_REF\" = \"$EXPECTED_POLICY_REF\"", diagnostic)
        self.assertIn("test \"$POLICY_REF\" = \"$WORKFLOW_REVISION\"", diagnostic)
        self.assertNotIn(": write", diagnostic)
        self.assertNotIn("gh release", diagnostic)

    def test_parentless_commit_is_not_qualified(self):
        code = '''
from tools.trusted_delivery.post_merge_reconciliation import reconcile
request={"repository":"example/djconnect", "main_sha":"a"*40, "main_parents":[],
 "originating_pr":None, "pre_merge":None, "post_merge":None}
result=reconcile(request)
assert result["decision"] == "POST_MERGE_RELEASE_EVIDENCE_NOT_QUALIFIED"
assert "parent" in " ".join(result["findings"]).lower()
'''
        for name in ("evidence-ebbb", "evidence-4877"):
            with self.subTest(snapshot=name):
                self.run_snapshot(name, code)

    def test_evidence_source_identity_and_legacy(self):
        code = '''
import copy, hashlib, json
from tools.trusted_delivery.evidence_preservation import build_record, validate_record
sha="a"*40; policy="b"*40
source={"repository":"example/djconnect", "repository_role":"active_source", "main_sha":sha,
 "decision":"POST_MERGE_RELEASE_EVIDENCE_QUALIFIED", "evidence_digest":"c"*64,
 "pre_merge":{k:"PASS" for k in ("verification","software_assurance","trusted_delivery","workflow_integrity","required_checks")},
 "post_merge":{"sha":sha,"ci":"PASS","tests":"PASS","lint":"PASS","static_analysis":"PASS",
 "build_validation":"PASS","governance":"PASS","coverage":"PASS","coverage_report_sha":sha,
 "coverage_artifact_sha":"d"*64,"workflow_run_ids":["123"]}}
record=build_record(source,policy_source_revision=policy,timestamp="2026-07-27T00:00:00Z",workflow_run_id="456")
assert validate_record(record)==[]
expected={"repository":"djconnect-music-dj/.github","repository_id":1461539726,"revision":policy,
 "snapshot":SNAPSHOT,"original_repository_id":1258575431,"original_revision":ORIGINAL}
record["policy_source_identity"]=copy.deepcopy(expected)
def digest(r): return hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!="integrity"},sort_keys=True,separators=(",",":")).encode()).hexdigest()
record["integrity"]["digest"]=digest(record)
assert validate_record(record,expected_policy_source=expected)==[]
assert validate_record(record)
for key in expected:
    bad=copy.deepcopy(record);bad["policy_source_identity"][key]="wrong";bad["integrity"]["digest"]=digest(bad)
    assert validate_record(bad,expected_policy_source=expected),key
for bad_expected in ({},dict(expected,repository_id=True),dict(expected,snapshot="unknown"),dict(expected,revision="bad")):
    bad=copy.deepcopy(record);bad["policy_source_identity"]=bad_expected;bad["source_revision"]=bad_expected.get("revision");bad["integrity"]["digest"]=digest(bad)
    assert validate_record(bad,expected_policy_source=bad_expected)
'''
        snapshots = {
            "evidence-ebbb": "ebbb35f038a7a3c7d46c12660968bcd50eb67580",
            "evidence-4877": "4877403ba6fc69881439e70d3048da13ecb5576b",
        }
        for name, original in snapshots.items():
            with self.subTest(snapshot=name):
                self.run_snapshot(name, f"SNAPSHOT={name!r}\nORIGINAL={original!r}\n" + code)


if __name__ == "__main__":
    unittest.main()
