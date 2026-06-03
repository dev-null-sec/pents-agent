from __future__ import annotations

import hashlib
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "cli"
PYTHON = ["uv", "run", "--project", str(CLI), "python", "-X", "utf8", "-m", "pents"]


class PentsCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = ROOT / "projects" / "cli-test"
        if self.project.exists():
            shutil.rmtree(self.project)

    def tearDown(self) -> None:
        if self.project.exists():
            shutil.rmtree(self.project)

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [*PYTHON, *args],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=True,
        )

    def read_project(self, name: str) -> str:
        return (self.project / name).read_text(encoding="utf-8")

    def test_help_runs(self) -> None:
        result = self.run_cli("--help")
        self.assertIn("pents", result.stdout)
        self.assertIn("new", result.stdout)
        self.assertIn("run", result.stdout)
        self.assertIn("static-js", result.stdout)
        self.assertIn("doctor-recon", result.stdout)

    def test_new_copies_project_templates(self) -> None:
        self.run_cli("new", "cli-test", "--target", "https://example.test")
        for name in ("scope.md", "progress.md", "inventory.md", "evidence.md"):
            self.assertTrue((self.project / name).exists(), name)
        self.assertTrue((self.project / "findings").is_dir())
        self.assertIn("https://example.test", self.read_project("scope.md"))

        scope = self.run_cli("scope", "cli-test")
        self.assertIn("测试范围", scope.stdout)
        self.assertIn("https://example.test", scope.stdout)

    def test_inventory_evidence_finding_brief_and_report(self) -> None:
        self.run_cli("new", "cli-test", "--target", "https://example.test")
        self.run_cli("inventory", "cli-test", "--add-url", "https://example.test/login", "--notes", "login page")

        evidence = self.run_cli("evidence", "cli-test", "requests/login.txt", "--type", "request")
        self.assertIn("E-0002", evidence.stdout)

        self.run_cli("finding", "cli-test", "Reflected XSS", "--severity", "High", "--target", "/search")
        self.assertTrue((self.project / "findings" / "F-0001.md").exists())

        # 验证中文模板生成的 finding
        finding = self.read_project("findings/F-0001.md")
        self.assertIn("Reflected XSS", finding)
        self.assertIn("严重程度", finding)

        brief = self.run_cli("brief", "cli-test", "--agent", "api", "--objective", "check authz")
        self.assertIn("代理角色：api", brief.stdout)
        self.assertIn("check authz", brief.stdout)

        self.run_cli("report", "cli-test", "--tester", "codex")
        report = self.read_project("report.md")
        self.assertIn("Reflected XSS", report)
        self.assertIn("漏洞汇总", report)

    def test_evidence_records_js_file_chain_metadata(self) -> None:
        self.run_cli("new", "cli-test", "--target", "https://example.test")
        js_dir = self.project / "js_files"
        js_dir.mkdir()
        js_file = js_dir / "app.js"
        js_content = 'fetch("/api/v1/setup/status");'
        js_file.write_text(js_content, encoding="utf-8")
        digest = hashlib.sha256(js_content.encode("utf-8")).hexdigest()

        result = self.run_cli(
            "evidence",
            "cli-test",
            "js_files/app.js",
            "--type",
            "js",
            "--file",
            "js_files/app.js",
            "--source-url",
            "https://example.test/assets/app.js",
            "--headers",
            "content-type: application/javascript",
            "--finding",
            "F-0001",
        )

        self.assertIn("E-0002", result.stdout)
        self.assertNotIn("WARNING", result.stdout)
        evidence = self.read_project("evidence.md")
        self.assertIn("| E-0002 | js |", evidence)
        self.assertIn("F-0001", evidence)
        self.assertIn("source_url=https://example.test/assets/app.js", evidence)
        self.assertIn("headers=content-type: application/javascript", evidence)
        self.assertIn("file=js_files/app.js", evidence)
        self.assertIn(f"sha256={digest}", evidence)
        self.assertIn("collected_at=", evidence)
        self.assertIn("evidence_type=js", evidence)
        self.assertIn("chain=complete", evidence)

    def test_evidence_warns_when_chain_is_incomplete(self) -> None:
        self.run_cli("new", "cli-test", "--target", "https://example.test")

        result = self.run_cli("evidence", "cli-test", "js_files/app.js", "--type", "js")

        self.assertIn("WARNING: evidence chain incomplete", result.stdout)
        self.assertIn("E-0002", result.stdout)
        evidence = self.read_project("evidence.md")
        self.assertIn("chain=incomplete", evidence)
        self.assertIn("evidence_type=js", evidence)

    def test_run_new_creates_numbered_run_templates(self) -> None:
        self.run_cli("new", "cli-test", "--target", "https://example.test")

        first = self.run_cli("run", "new", "cli-test", "active recon", "--date", "2026-06-03")
        first_run = self.project / "runs" / "R001-2026-06-03-active-recon"
        self.assertIn(str(first_run), first.stdout)
        for name in ("brief.md", "progress.md", "evidence.md", "R001-report-delta.md", "review.md"):
            self.assertTrue((first_run / name).exists(), name)
        self.assertTrue((first_run / "outputs").is_dir())
        self.assertTrue((first_run / "raw").is_dir())
        self.assertIn("R001", (first_run / "progress.md").read_text(encoding="utf-8"))
        self.assertIn("R001", (first_run / "R001-report-delta.md").read_text(encoding="utf-8"))

        self.run_cli("run", "new", "cli-test", "setup verification", "--date", "2026-06-03")
        self.assertTrue((self.project / "runs" / "R002-2026-06-03-setup-verification").is_dir())

        self.run_cli("run", "new", "cli-test", "manual check", "--id", "R009", "--date", "2026-06-04")
        self.assertTrue((self.project / "runs" / "R009-2026-06-04-manual-check" / "R009-report-delta.md").exists())

    def test_static_js_extracts_recon_clues_and_saves_to_run(self) -> None:
        self.run_cli("new", "cli-test", "--target", "https://example.test")
        js_dir = self.project / "js_files"
        js_dir.mkdir()
        (js_dir / "app.js").write_text(
            """
            const client = axios.create({baseURL:"/api/v1"});
            const routes = [{path:"/setup"},{path:"/admin/settings"},{path:"/payment/stripe"}];
            fetch("/api/v1/setup/status");
            fetch("/api/v1/auth/oauth/pending/exchange");
            const params = {provider:"linuxdo", redirect_uri:"/auth/callback", state:"abc", order_id:"O-1"};
            const integrations = "stripe airwallex payment oauth oidc turnstile cloudflare";
            """,
            encoding="utf-8",
        )

        summary = self.run_cli("static-js", "cli-test", "js_files")
        self.assertIn("JS 静态分析摘要", summary.stdout)
        self.assertIn("/api/v1/setup/status", summary.stdout)
        self.assertIn("/setup", summary.stdout)
        self.assertIn("provider", summary.stdout)
        self.assertIn("oauth", summary.stdout)
        self.assertIn("stripe", summary.stdout)
        self.assertIn("turnstile", summary.stdout)

        self.run_cli("run", "new", "cli-test", "static js", "--date", "2026-06-03")
        self.run_cli("static-js", "cli-test", "js_files", "--run", "R001-2026-06-03-static-js", "--save")
        saved = self.project / "runs" / "R001-2026-06-03-static-js" / "outputs" / "static-js-summary.md"
        self.assertTrue(saved.exists())
        self.assertIn("/api/v1/setup/status", saved.read_text(encoding="utf-8"))

    def test_doctor_recon_reports_tools_and_guidance(self) -> None:
        result = self.run_cli("doctor-recon")
        self.assertIn("Recon 工具检查", result.stdout)
        self.assertIn("当前环境", result.stdout)
        self.assertIn("all_proxy", result.stdout)
        self.assertIn("不要把这个本机代理配置套到远端机器", result.stdout)
        for tool in ("subfinder", "dnsx", "httpx", "shuffledns", "subzy", "massdns"):
            self.assertIn(tool, result.stdout)
        for platform_name in ("Windows", "WSL/Linux", "macOS"):
            self.assertIn(platform_name, result.stdout)


if __name__ == "__main__":
    unittest.main()
