import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

_p = Path(__file__).resolve().parent.parent / "scripts" / "coverage_audit.py"
_spec = importlib.util.spec_from_file_location("coverage_audit", _p)
ca = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ca)

RC = """
sites:
  - name: Site A
    url: https://a.example.com
  - name: Site B
    url: "https://www.b.example.com/health"
    expectedStatusCodes:
      - 200
notifications:
  - type: email
"""


class TestCoverage(unittest.TestCase):
    def test_monitored_hosts_strip_www_and_path(self):
        self.assertEqual(ca.monitored_hosts(RC), {"a.example.com", "b.example.com"})

    def test_missing_lists_unmonitored_public_homepages(self):
        repos = [
            {"name": "a", "homepageUrl": "https://a.example.com/", "isArchived": False},
            {"name": "trace", "homepageUrl": "https://trace-seven-ashen.vercel.app", "isArchived": False},
            {"name": "nohome", "homepageUrl": "", "isArchived": False},
            {"name": "old", "homepageUrl": "https://old.example.com", "isArchived": True},
            {"name": "gh", "homepageUrl": "https://github.com/x/y", "isArchived": False},
        ]
        self.assertEqual(
            ca.missing(repos, ca.monitored_hosts(RC)),
            [("trace", "trace-seven-ashen.vercel.app")],
        )

    def test_cli_report_and_fail_flag(self):
        with tempfile.TemporaryDirectory() as d:
            rc = Path(d) / "rc.yml"
            rc.write_text(RC)
            rp = Path(d) / "repos.json"
            rp.write_text(json.dumps([{"name": "t", "homepageUrl": "https://t.example.org", "isArchived": False}]))
            self.assertEqual(ca.main(["--config", str(rc), "--repos", str(rp)]), 0)
            self.assertEqual(ca.main(["--config", str(rc), "--repos", str(rp), "--fail-on-missing"]), 1)


if __name__ == "__main__":
    unittest.main()
