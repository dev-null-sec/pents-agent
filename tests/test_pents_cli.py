from __future__ import annotations

import hashlib
import json
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
        self.assertIn("merge", result.stdout)
        self.assertIn("review-agent-output", result.stdout)
        self.assertIn("suggest-skills", result.stdout)
        self.assertIn("doctor-recon", result.stdout)
        self.assertIn("active-dns", result.stdout)

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
        self.assertIn("输入缺口", brief.stdout)

        self.run_cli("report", "cli-test", "--tester", "codex")
        report = self.read_project("report.md")
        self.assertIn("Reflected XSS", report)
        self.assertIn("漏洞汇总", report)

    def test_brief_builds_task_card_from_short_request(self) -> None:
        self.run_cli("new", "cli-test", "--target", "*.devnu11.cn")

        result = self.run_cli(
            "brief",
            "cli-test",
            "--agent",
            "recon",
            "--task-id",
            "T-0042",
            "--request",
            "对 *.devnu11.cn 做主动 DNS，别碰 HTTP",
            "--objective",
            "生成主动 DNS 枚举计划并回填证据",
            "--in-scope",
            "*.devnu11.cn DNS 子域名枚举",
            "--out-of-scope",
            "HTTP 探测",
            "--forbid",
            "端口扫描",
            "--stop",
            "canary 未命中时停止",
            "--target",
            "*.devnu11.cn|主动 DNS|使用 subdomains-main.txt",
            "--input-gap",
            "canary 子域名",
            "--reference",
            "skill|skills/recon/subdomain-enumeration/SKILL.md|主动 DNS checklist",
            "--acceptance",
            "包含 canary、NXDOMAIN、resolver 自检",
            "--writeback",
            "runs/R002/outputs/active-dns-plan.md",
            "--completion",
            "执行后按 ai-board complete/archive",
            "--save",
        )

        self.assertIn("Created brief", result.stdout)
        saved = self.project / "briefs" / "t-0042-recon.md"
        self.assertTrue(saved.exists())
        text = saved.read_text(encoding="utf-8")
        self.assertIn("用户短指令：对 *.devnu11.cn 做主动 DNS，别碰 HTTP", text)
        self.assertIn("*.devnu11.cn DNS 子域名枚举", text)
        self.assertIn("HTTP 探测", text)
        self.assertIn("端口扫描", text)
        self.assertIn("| *.devnu11.cn | 主动 DNS | 使用 subdomains-main.txt |", text)
        self.assertIn("canary 子域名", text)
        self.assertIn("包含 canary、NXDOMAIN、resolver 自检", text)
        self.assertIn("runs/R002/outputs/active-dns-plan.md", text)
        self.assertIn("执行后按 ai-board complete/archive", text)

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

    def test_report_summarizes_findings_evidence_and_gaps(self) -> None:
        self.run_cli("new", "cli-test", "--target", "https://example.test")
        self.run_cli(
            "finding",
            "cli-test",
            "Confirmed SSRF",
            "--id",
            "F-0001",
            "--severity",
            "High",
            "--status",
            "confirmed",
            "--target",
            "/admin/callback",
        )
        self.run_cli(
            "finding",
            "cli-test",
            "Candidate IDOR",
            "--id",
            "F-0002",
            "--severity",
            "Medium",
            "--status",
            "candidate",
            "--target",
            "/api/v1/users/1",
        )
        self.run_cli(
            "evidence",
            "cli-test",
            "requests/ssrf.txt",
            "--type",
            "request",
            "--finding",
            "F-0001",
            "--source-url",
            "https://example.test/admin/callback",
            "--sha256",
            "abc123",
        )
        finding = self.project / "findings" / "F-0001.md"
        finding.write_text(
            finding.read_text(encoding="utf-8").replace(
                "1. \n2. \n3. ",
                "1. 打开 `/admin/callback`\n2. 发送回调请求\n3. 观察服务端响应",
            ),
            encoding="utf-8",
        )

        self.run_cli("report", "cli-test", "--tester", "codex")
        report = self.read_project("report.md")

        self.assertIn("| F-0001 | Confirmed SSRF | High | confirmed | `E-0002` |", report)
        self.assertIn("| F-0002 | Candidate IDOR | Medium | candidate | 缺失 |", report)
        self.assertIn("## 严重程度统计", report)
        self.assertIn("| High | 1 |", report)
        self.assertIn("| Medium | 1 |", report)
        self.assertIn("## 证据与缺口", report)
        self.assertIn("| F-0002 | candidate | 缺失 | 缺少证据；缺少复现步骤 |", report)

    def test_merge_and_review_agent_output(self) -> None:
        self.run_cli("new", "cli-test", "--target", "https://example.test")
        self.run_cli("finding", "cli-test", "Existing IDOR", "--id", "F-0001", "--severity", "Medium")
        output = self.project / "agent-output.json"
        output.write_text(
            json.dumps(
                {
                    "agent_role": "api-agent",
                    "tested_targets": [
                        {
                            "url": "https://example.test/api/v1/users/1",
                            "method": "GET",
                            "surface": "API",
                            "result": "checked authz",
                            "evidence_refs": ["E-0002"],
                        }
                    ],
                    "potential_findings": [
                        {
                            "title": "Existing IDOR",
                            "reason": "same object authorization issue",
                            "evidence_refs": [],
                        }
                    ],
                    "confirmed_findings": [
                        {
                            "title": "Unauthenticated setup",
                            "severity": "High",
                            "evidence_refs": ["E-0003"],
                        }
                    ],
                    "blocked_or_skipped": [
                        {
                            "target": "/admin",
                            "reason": "missing admin account",
                            "reason_type": "等待账号",
                            "status": "blocker",
                        }
                    ],
                    "scope_risk": [{"target": "https://evil.test", "reason": "outside scope"}],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        merge = self.run_cli("merge", "cli-test", "agent-output.json")
        self.assertIn("Merged agent output", merge.stdout)
        inventory = self.read_project("inventory.md")
        self.assertIn("https://example.test/api/v1/users/1", inventory)
        progress = self.read_project("progress.md")
        self.assertIn("merge agent output", progress)
        self.assertIn("Existing IDOR", progress)
        self.assertIn("Unauthenticated setup", progress)
        self.assertIn("missing admin account", progress)

        review = self.run_cli("review-agent-output", "cli-test", "agent-output.json")
        self.assertIn("越界风险", review.stdout)
        self.assertIn("outside scope", review.stdout)
        self.assertIn("证据不足", review.stdout)
        self.assertIn("Existing IDOR", review.stdout)
        self.assertIn("重复项", review.stdout)
        self.assertIn("候选 Finding", review.stdout)

    def test_suggest_skills_recommends_web_api_and_recon(self) -> None:
        recon = self.run_cli("suggest-skills", "子域名", "dns", "recon", "--limit", "3")
        self.assertIn("subdomain-enumeration", recon.stdout)
        self.assertIn("skills/recon/subdomain-enumeration/SKILL.md", recon.stdout)
        self.assertIn("| subdomain-enumeration | recon |", recon.stdout)

        web = self.run_cli("suggest-skills", "xss", "反射", "--limit", "3")
        self.assertIn("xss-reflected", web.stdout)
        self.assertIn("skills/web/xss-reflected/SKILL.md", web.stdout)
        self.assertIn("| xss-reflected | web |", web.stdout)

        api = self.run_cli("suggest-skills", "bola", "object", "authorization", "api", "--limit", "3")
        self.assertIn("bola", api.stdout)
        self.assertIn("skills/api/bola/SKILL.md", api.stdout)
        self.assertIn("| bola | api |", api.stdout)

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
        self.assertIn("tools/third-party/bin", result.stdout)
        self.assertIn("massdns direct", result.stdout)
        self.assertIn("active-dns-core", result.stdout)
        self.assertIn("optional-wrapper", result.stdout)
        self.assertIn("optional-diagnostic", result.stdout)
        for tool in ("subfinder", "puredns", "massdns", "dnsx", "httpx", "shuffledns", "subzy"):
            self.assertIn(tool, result.stdout)
        for platform_name in ("Windows", "WSL/Linux", "macOS"):
            self.assertIn(platform_name, result.stdout)

    def test_active_dns_generates_precheck_plan_and_saves_to_run(self) -> None:
        self.run_cli("new", "cli-test", "--target", "*.devnu11.cn")
        self.run_cli("run", "new", "cli-test", "active dns", "--date", "2026-06-03")

        result = self.run_cli(
            "active-dns",
            "*.devnu11.cn",
            "--project",
            "cli-test",
            "--run",
            "R001-2026-06-03-active-dns",
            "--dict",
            "dicts/curated/subdomains-main.txt",
            "--resolvers",
            "1.1.1.1,8.8.8.8",
            "--canary",
            "ai",
            "--nonce",
            "nx-test",
            "--save",
        )

        self.assertIn("主动 DNS 执行计划", result.stdout)
        self.assertIn("devnu11.cn", result.stdout)
        self.assertIn("ai.devnu11.cn", result.stdout)
        self.assertIn("nx-test.devnu11.cn", result.stdout)
        self.assertIn("massdns direct", result.stdout)
        self.assertIn("active-dns-massdns.ps1", result.stdout)
        self.assertIn("powershell", result.stdout)
        self.assertIn("resolver 自检", result.stdout)
        self.assertIn("证据登记", result.stdout)

        run = self.project / "runs" / "R001-2026-06-03-active-dns"
        plan = run / "outputs" / "active-dns-plan.md"
        resolvers = run / "outputs" / "active-dns-resolvers.txt"
        canary = run / "outputs" / "active-dns-canary-targets.txt"
        nxdomain = run / "outputs" / "active-dns-nxdomain-targets.txt"
        summary = run / "outputs" / "active-dns-summary.md"
        for path in (plan, resolvers, canary, nxdomain, summary):
            self.assertTrue(path.exists(), path)
        plan_text = plan.read_text(encoding="utf-8")
        self.assertIn("active-dns-massdns.ps1", plan_text)
        self.assertIn("-HashmapSize 10000", plan_text)
        self.assertIn("-RecordTypes @('A')", plan_text)
        self.assertNotIn("puredns bruteforce", plan_text)
        self.assertIn("1.1.1.1", resolvers.read_text(encoding="utf-8"))
        self.assertEqual("ai.devnu11.cn\n", canary.read_text(encoding="utf-8"))
        self.assertEqual("nx-test.devnu11.cn\n", nxdomain.read_text(encoding="utf-8"))

    def test_active_dns_can_add_record_types_and_nodata_check(self) -> None:
        self.run_cli("new", "cli-test", "--target", "*.devnu11.cn")
        self.run_cli("run", "new", "cli-test", "active dns", "--date", "2026-06-03")

        result = self.run_cli(
            "active-dns",
            "*.devnu11.cn",
            "--project",
            "cli-test",
            "--run",
            "R001-2026-06-03-active-dns",
            "--dict",
            "dicts/curated/subdomains-main.txt",
            "--resolvers",
            "1.1.1.1,8.8.8.8",
            "--canary",
            "ai",
            "--nonce",
            "nx-test",
            "--record-types",
            "A,AAAA,CNAME",
            "--nodata-check",
            "--save",
        )

        self.assertIn("查询记录类型：`A,AAAA,CNAME`", result.stdout)
        self.assertIn("NODATA 复核：开启", result.stdout)
        self.assertIn("-RecordTypes @('A', 'AAAA', 'CNAME')", result.stdout)
        self.assertIn("可选 dnsx NOERROR/NODATA 复核", result.stdout)
        self.assertIn("active-dns-nodata-dnsx.jsonl", result.stdout)
        self.assertIn("possible_nodata_or_non_address_diff", result.stdout)
        self.assertNotIn("puredns bruteforce", result.stdout)

        plan = self.project / "runs" / "R001-2026-06-03-active-dns" / "outputs" / "active-dns-plan.md"
        plan_text = plan.read_text(encoding="utf-8")
        self.assertIn("dnsx NOERROR/NODATA 复核", plan_text)
        self.assertIn("NODATA 复核证据登记", plan_text)


if __name__ == "__main__":
    unittest.main()
