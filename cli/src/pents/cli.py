from __future__ import annotations

import argparse
import hashlib
import platform
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from . import __version__

PROJECT_FILES = ("scope.md", "progress.md", "inventory.md", "evidence.md")
RUN_TEMPLATE_TARGETS = (
    ("brief.md", "brief.md"),
    ("run-progress.md", "progress.md"),
    ("evidence.md", "evidence.md"),
    ("run-report-delta.md", "{run_id}-report-delta.md"),
    ("run-review.md", "review.md"),
)
TEMPLATE_NAMES = {
    "scope": "scope.md",
    "progress": "progress.md",
    "inventory": "inventory.md",
    "evidence": "evidence.md",
    "finding": "finding.md",
    "report": "report.md",
    "review": "review.md",
    "brief": "brief.md",
}
RECON_TOOLS = (
    {
        "name": "subfinder",
        "purpose": "被动子域名收集",
        "impact": "被动来源覆盖会变少，子域名初始清单质量下降。",
        "install": "go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
    },
    {
        "name": "dnsx",
        "purpose": "DNS 解析验证、记录查询和主动 DNS 枚举辅助",
        "impact": "无法批量验证子域名解析结果，也难以做 wildcard 去噪。",
        "install": "go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest",
    },
    {
        "name": "httpx",
        "purpose": "HTTP 存活探测、标题、状态码和技术栈识别",
        "impact": "无法批量确认 Web/API 入口存活和基础指纹。",
        "install": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
    },
    {
        "name": "shuffledns",
        "purpose": "主动 DNS 子域名字典枚举和 wildcard 处理",
        "impact": "无法用默认子域名字典做受控批量 DNS 枚举。",
        "install": "go install -v github.com/projectdiscovery/shuffledns/cmd/shuffledns@latest",
    },
    {
        "name": "subzy",
        "purpose": "子域名接管风险提示",
        "impact": "无法自动提示疑似接管风险，需要人工检查 CNAME 和第三方服务状态。",
        "install": "go install -v github.com/PentestPad/subzy@latest",
    },
)
STATIC_JS_PARAM_HINTS = (
    "provider",
    "code",
    "state",
    "redirect_uri",
    "token",
    "email",
    "password",
    "amount",
    "currency",
    "price",
    "order_id",
    "subscription",
    "model",
    "channel",
    "api_key",
    "admin_user",
    "db_config",
    "redis_config",
    "smtp",
)
STATIC_JS_OAUTH_HINTS = ("oauth", "oidc", "sso", "callback", "redirect_uri", "state", "provider")
STATIC_JS_PAYMENT_HINTS = ("stripe", "airwallex", "payment", "checkout", "order", "subscription", "qrcode")


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def workspace_root() -> Path:
    return Path.cwd()


def template_dir(root: Path) -> Path:
    return root / "templates"


def projects_dir(root: Path) -> Path:
    return root / "projects"


def project_path(root: Path, name: str) -> Path:
    return projects_dir(root) / name


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def table_cell(value: str) -> str:
    return value.replace("\r", " ").replace("\n", " ").replace("|", "\\|").strip()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fill_template(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return re.sub(r"\{\{[^}]+\}\}", "", text)


def ensure_project(root: Path, name: str) -> Path:
    path = project_path(root, name)
    if not path.exists():
        raise SystemExit(f"Project not found: {path}")
    return path


def slugify(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "-", text.strip().lower()).strip("-")
    return value or "run"


def normalize_run_id(value: str) -> str:
    match = re.fullmatch(r"[Rr]?(\d{1,3})", value.strip())
    if not match:
        raise SystemExit("Run id must look like R001 or 1")
    return f"R{int(match.group(1)):03d}"


def next_run_id(project: Path) -> str:
    max_number = 0
    runs_dir = project / "runs"
    if runs_dir.exists():
        for path in runs_dir.iterdir():
            if not path.is_dir():
                continue
            match = re.match(r"R(\d{3})-", path.name)
            if match:
                max_number = max(max_number, int(match.group(1)))
    return f"R{max_number + 1:03d}"


def resolve_project_input(root: Path, project: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    project_relative = project / path
    if project_relative.exists():
        return project_relative
    return root / path


def js_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() == ".js" else []
    if path.is_dir():
        return sorted(p for p in path.rglob("*.js") if p.is_file())
    return []


def add_limited(values: set[str], value: str) -> None:
    clean = value.strip().strip("'\"`")
    if clean:
        values.add(clean)


def analyze_static_js(path: Path) -> dict[str, set[str] | list[Path]]:
    files = js_files(path)
    routes: set[str] = set()
    apis: set[str] = set()
    params: set[str] = set()
    oauth: set[str] = set()
    payments: set[str] = set()
    configs: set[str] = set()
    path_pattern = re.compile(r"""["'`](/(?!/)[A-Za-z0-9][A-Za-z0-9_./:@?=&%+-]*)["'`]""")
    url_pattern = re.compile(r"""https?://[A-Za-z0-9_.:/?=&%#,+-]+""")
    param_pattern = re.compile(r"""["'`]([A-Za-z_][A-Za-z0-9_-]{1,40})["'`]\s*:""")

    for file in files:
        text = file.read_text(encoding="utf-8", errors="ignore")
        lowered = text.lower()
        for match in path_pattern.finditer(text):
            value = match.group(1)
            if re.search(r"\.(js|css|png|jpg|jpeg|gif|svg|map|woff2?)($|\?)", value):
                continue
            add_limited(routes, value)
            if re.search(r"(^/api/|/api/|^/v\d+/|/graphql|/setup|/admin)", value):
                add_limited(apis, value)
        for match in url_pattern.finditer(text):
            value = match.group(0)
            if "/api/" in value or "oauth" in value.lower() or "payment" in value.lower():
                add_limited(apis, value)
        for match in param_pattern.finditer(text):
            name = match.group(1)
            if name.lower() in STATIC_JS_PARAM_HINTS:
                add_limited(params, name)
        for hint in STATIC_JS_PARAM_HINTS:
            if hint.lower() in lowered:
                add_limited(params, hint)
        for hint in STATIC_JS_OAUTH_HINTS:
            if hint in lowered:
                add_limited(oauth, hint)
        for hint in STATIC_JS_PAYMENT_HINTS:
            if hint in lowered:
                add_limited(payments, hint)
        for hint in ("baseurl", "base_url", "apibase", "vite_", "turnstile", "captcha", "cloudflare"):
            if hint in lowered:
                add_limited(configs, hint)

    return {
        "files": files,
        "routes": routes,
        "apis": apis,
        "params": params,
        "oauth": oauth,
        "payments": payments,
        "configs": configs,
    }


def markdown_list(values: set[str], max_items: int) -> list[str]:
    items = sorted(values)[:max_items]
    return [f"- `{item}`" for item in items] or ["- 无"]


def build_static_js_summary(project_name: str, input_path: Path, result: dict[str, set[str] | list[Path]], max_items: int) -> str:
    files = result["files"]
    routes = result["routes"]
    apis = result["apis"]
    params = result["params"]
    oauth = result["oauth"]
    payments = result["payments"]
    configs = result["configs"]
    assert isinstance(files, list)
    assert isinstance(routes, set)
    assert isinstance(apis, set)
    assert isinstance(params, set)
    assert isinstance(oauth, set)
    assert isinstance(payments, set)
    assert isinstance(configs, set)
    lines = [
        "# JS 静态分析摘要",
        "",
        "## 元数据",
        "",
        f"- 项目：{project_name}",
        f"- 输入：{input_path}",
        f"- JS 文件数量：{len(files)}",
        f"- 路由数量：{len(routes)}",
        f"- API 端点数量：{len(apis)}",
        f"- 参数线索数量：{len(params)}",
        "",
        "## Inventory 摘要",
        "",
        "### 路由",
        "",
        *markdown_list(routes, max_items),
        "",
        "### API 端点",
        "",
        *markdown_list(apis, max_items),
        "",
        "### 参数名线索",
        "",
        *markdown_list(params, max_items),
        "",
        "### OAuth / OIDC 线索",
        "",
        *markdown_list(oauth, max_items),
        "",
        "### 支付线索",
        "",
        *markdown_list(payments, max_items),
        "",
        "### 配置 / CDN / WAF 线索",
        "",
        *markdown_list(configs, max_items),
        "",
        "## Evidence 摘要",
        "",
        "| 类型 | 内容 |",
        "| --- | --- |",
        f"| js-files | {len(files)} 个本地 JS 文件 |",
        f"| routes | {len(routes)} 条路由线索 |",
        f"| api-endpoints | {len(apis)} 条 API 端点线索 |",
        f"| params | {len(params)} 个参数名线索 |",
        "",
        "## 后续建议",
        "",
        "- 将 API 端点和参数线索合并到 inventory。",
        "- 将本摘要文件登记到 evidence。",
        "- 对 setup、admin、OAuth、支付相关端点保持待确认状态，未获授权前不主动请求。",
    ]
    return "\n".join(lines).strip() + "\n"


def platform_label() -> str:
    system = platform.system()
    if system == "Linux":
        version_path = Path("/proc/version")
        version = version_path.read_text(encoding="utf-8", errors="ignore").lower() if version_path.exists() else ""
        return "WSL/Linux" if "microsoft" in version or "wsl" in version else "Linux"
    if system == "Darwin":
        return "macOS"
    return system or "unknown"


def install_guidance(tool: dict[str, str]) -> list[str]:
    command = tool["install"]
    return [
        f"Windows：优先在 WSL 中安装；也可下载 release 二进制加入 PATH。Go 安装：{command}",
        f"WSL/Linux：安装 Go 后运行 `{command}`，并确认 `$HOME/go/bin` 在 PATH。",
        f"macOS：可用 Go 安装 `{command}`；ProjectDiscovery 工具也可参考官方 Homebrew 安装方式。",
    ]


def next_numbered_id(existing: list[str], prefix: str) -> str:
    max_number = 0
    pattern = re.compile(rf"\b{re.escape(prefix)}-(\d{{4}})\b")
    for text in existing:
        for match in pattern.finditer(text):
            max_number = max(max_number, int(match.group(1)))
    return f"{prefix}-{max_number + 1:04d}"


def copy_project_template(root: Path, project: Path, template_name: str, values: dict[str, str]) -> None:
    source = template_dir(root) / template_name
    target = project / template_name
    content = fill_template(read_text(source), values)
    write_text(target, content)


def copy_named_template(root: Path, template_name: str, target: Path, values: dict[str, str]) -> None:
    content = fill_template(read_text(template_dir(root) / template_name), values)
    write_text(target, content)


def cmd_new(args: argparse.Namespace) -> int:
    root = workspace_root()
    project = project_path(root, args.name)
    if project.exists() and not args.force:
        raise SystemExit(f"Project already exists: {project}")

    values = {
        "project_name": args.name,
        "target": args.target or args.name,
        "owner": args.owner or "",
        "created_at": now_text(),
        "updated_at": now_text(),
        "phase": "scope",
        "authorization_source": "",
        "authorized_by": "",
        "start_at": "",
        "end_at": "",
        "emergency_contact": "",
        "max_request_rate": "",
        "data_handling_notes": "",
    }

    project.mkdir(parents=True, exist_ok=True)
    (project / "findings").mkdir(exist_ok=True)
    (project / "briefs").mkdir(exist_ok=True)
    for template_name in PROJECT_FILES:
        copy_project_template(root, project, template_name, values)
    print(f"Created project: {project}")
    return 0


def cmd_scope(args: argparse.Namespace) -> int:
    root = workspace_root()
    project = ensure_project(root, args.project)
    print(read_text(project / "scope.md").strip())
    return 0


def cmd_inventory(args: argparse.Namespace) -> int:
    root = workspace_root()
    project = ensure_project(root, args.project)
    path = project / "inventory.md"
    if args.add_url:
        line = f"|  | {args.add_url} | {args.method} | {args.auth} | {args.notes or ''} |\n"
        with path.open("a", encoding="utf-8") as file:
            file.write("\n" + line)
        print(f"Added inventory URL: {args.add_url}")
        return 0
    print(read_text(path).strip())
    return 0


def cmd_evidence(args: argparse.Namespace) -> int:
    root = workspace_root()
    project = ensure_project(root, args.project)
    path = project / "evidence.md"
    evidence_id = next_numbered_id([read_text(path)], "E")
    evidence_file = ""
    sha256 = args.sha256.strip()
    if args.file:
        file_path = resolve_project_input(root, project, args.file)
        if not file_path.exists() or not file_path.is_file():
            raise SystemExit(f"Evidence file not found: {file_path}")
        evidence_file = args.file
        if not sha256:
            sha256 = file_sha256(file_path)

    metadata = [
        f"collected_at={args.collected_at or now_text()}",
        f"evidence_type={args.type}",
    ]
    if args.source_url:
        metadata.append(f"source_url={args.source_url}")
    if args.headers:
        metadata.append(f"headers={args.headers}")
    if evidence_file:
        metadata.append(f"file={evidence_file}")
    if sha256:
        metadata.append(f"sha256={sha256}")

    missing = []
    if not args.source_url:
        missing.append("source URL")
    if not sha256:
        missing.append("file hash")
    metadata.append("chain=incomplete" if missing else "chain=complete")
    notes = "; ".join(part for part in (args.notes, *metadata) if part)
    line = (
        f"| {table_cell(evidence_id)} | {table_cell(args.type)} | {table_cell(args.target or '')} | "
        f"{table_cell(args.finding or '')} | {table_cell(args.ref)} | {table_cell(notes)} |\n"
    )
    with path.open("a", encoding="utf-8") as file:
        file.write("\n" + line)
    if missing:
        print(f"WARNING: evidence chain incomplete: missing {', '.join(missing)}")
    print(evidence_id)
    return 0


def cmd_finding(args: argparse.Namespace) -> int:
    root = workspace_root()
    project = ensure_project(root, args.project)
    findings_dir = project / "findings"
    existing = [path.name for path in findings_dir.glob("*.md")]
    finding_id = args.id or next_numbered_id(existing, "F")
    values = {
        "finding_id": finding_id,
        "project_name": args.project,
        "title": args.title,
        "severity": args.severity,
        "cvss": args.cvss or "",
        "affected_target": args.target or "",
        "discovered_at": now_text(),
        "confirmed_by": args.confirmed_by or "",
        "summary": args.summary or "",
        "impact": args.impact or "",
        "remediation": args.remediation or "",
    }
    template = read_text(template_dir(root) / "finding.md")
    target = findings_dir / f"{finding_id}.md"
    write_text(target, fill_template(template, values))
    print(f"Created finding: {target}")
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    root = workspace_root()
    project = ensure_project(root, args.project)
    values = {
        "project_name": args.project,
        "agent_role": args.agent,
        "created_at": now_text(),
        "task_id": args.task_id or "",
        "objective": args.objective or "",
    }
    content = fill_template(read_text(template_dir(root) / "brief.md"), values)
    if args.save:
        target = project / "briefs" / f"{args.agent}.md"
        write_text(target, content)
        print(f"Created brief: {target}")
    else:
        print(content.strip())
    return 0


def cmd_run_new(args: argparse.Namespace) -> int:
    root = workspace_root()
    project = ensure_project(root, args.project)
    run_id = normalize_run_id(args.id) if args.id else next_run_id(project)
    run_name = f"{run_id}-{args.date}-{slugify(args.purpose)}"
    run_path = project / "runs" / run_name
    if run_path.exists() and not args.force:
        raise SystemExit(f"Run already exists: {run_path}")

    values = {
        "project_name": args.project,
        "run_id": run_id,
        "run_name": run_name,
        "phase": args.phase or "planned",
        "executor": args.executor or "",
        "updated_at": now_text(),
        "agent_role": args.agent or "recon",
        "created_at": now_text(),
        "task_id": run_id,
        "objective": args.objective or args.purpose,
    }

    run_path.mkdir(parents=True, exist_ok=True)
    (run_path / "outputs").mkdir(exist_ok=True)
    (run_path / "raw").mkdir(exist_ok=True)
    for template_name, target_name in RUN_TEMPLATE_TARGETS:
        target = run_path / target_name.format(run_id=run_id)
        copy_named_template(root, template_name, target, values)

    print(f"Created run: {run_path}")
    return 0


def cmd_static_js(args: argparse.Namespace) -> int:
    root = workspace_root()
    project = ensure_project(root, args.project)
    input_path = resolve_project_input(root, project, args.js_path)
    if not input_path.exists():
        raise SystemExit(f"JS path not found: {input_path}")
    result = analyze_static_js(input_path)
    files = result["files"]
    assert isinstance(files, list)
    if not files:
        raise SystemExit(f"No .js files found: {input_path}")
    summary = build_static_js_summary(args.project, input_path, result, args.max_items)

    if args.save:
        if args.run:
            output_dir = project / "runs" / args.run / "outputs"
            if not output_dir.exists():
                raise SystemExit(f"Run outputs directory not found: {output_dir}")
        else:
            output_dir = project / "outputs"
            output_dir.mkdir(exist_ok=True)
        target = output_dir / "static-js-summary.md"
        write_text(target, summary)
        print(f"Created static JS summary: {target}")
        return 0

    print(summary.strip())
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    root = workspace_root()
    project = ensure_project(root, args.project)
    values = {
        "project_name": args.project,
        "target": args.target or args.project,
        "report_date": now_text(),
        "tester": args.tester or "",
        "executive_summary": args.summary or "",
    }
    content = fill_template(read_text(template_dir(root) / "report.md"), values)
    findings = sorted((project / "findings").glob("*.md"))
    if findings:
        rows = ["| 编号 | 标题 | 严重程度 | 状态 |", "| --- | --- | --- | --- |"]
        for finding in findings:
            text = read_text(finding)
            title = text.splitlines()[0].replace("# 漏洞记录：", "").strip() if text.splitlines() else finding.stem
            severity = field_value(text, "严重程度")
            status = field_value(text, "状态")
            rows.append(f"| {finding.stem} | {title} | {severity} | {status} |")
        content = replace_section_table(content, "## 漏洞汇总", rows)
    target = project / "report.md"
    write_text(target, content)
    print(f"Created report: {target}")
    return 0


def cmd_doctor_recon(args: argparse.Namespace) -> int:
    missing: list[str] = []
    print("Recon 工具检查")
    print(f"当前环境：{platform_label()}")
    print("本机下载提示：涉及国外网络的拉取/下载，可在本机 PowerShell 临时设置 `$env:all_proxy='http://127.0.0.1:7890'`；不要把这个本机代理配置套到远端机器。")
    print("安装建议按环境区分：Windows 优先 WSL 或 release 二进制；WSL/Linux 优先 Go 安装；macOS 可用 Go 或官方 Homebrew 方式。")
    print()

    for tool in RECON_TOOLS:
        path = shutil.which(tool["name"])
        status = "OK" if path else "MISSING"
        if not path:
            missing.append(tool["name"])
        print(f"[{status}] {tool['name']}")
        print(f"用途：{tool['purpose']}")
        if path:
            print(f"路径：{path}")
            if tool["name"] == "httpx":
                print("提示：请确认这是 ProjectDiscovery httpx，不是 Python httpx 同名命令。")
        else:
            print(f"影响：{tool['impact']}")
            print("安装建议：")
            for line in install_guidance(tool):
                print(f"- {line}")
        print()

    massdns_path = shutil.which("massdns")
    print(f"[{'OK' if massdns_path else 'MISSING'}] massdns（shuffledns 依赖）")
    if massdns_path:
        print(f"路径：{massdns_path}")
    else:
        print("影响：shuffledns 即使已安装，也可能无法执行主动 DNS 枚举；请按 shuffledns 文档补齐 massdns。")
    print()

    if missing:
        print("结论：recon 工具链不完整。Claude 执行时必须在 progress/review 中写明缺失工具、受影响步骤和替代方案。")
        return 2 if args.strict else 0

    print("结论：核心 recon 工具已在 PATH 中找到。仍需确认授权窗口、DNS 并发/速率、resolver 和字典规模后再执行主动扫描。")
    return 0


def field_value(text: str, field: str) -> str:
    # Match both fullwidth ：(U+FF1A) and ASCII : after field name
    match = re.search(rf"^- {re.escape(field)}[：:]\s*(.*)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def replace_section_table(content: str, section: str, rows: list[str]) -> str:
    index = content.find(section)
    if index < 0:
        return content
    # Match Chinese (| 编号 |) or English (| ID |) table headers
    table_start = content.find("| 编号 |", index)
    if table_start < 0:
        table_start = content.find("| ID |", index)
    if table_start < 0:
        return content
    table_end = content.find("\n\n", table_start)
    if table_end < 0:
        table_end = len(content)
    return content[:table_start] + "\n".join(rows) + content[table_end:]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pents", description="Claude Code 渗透测试工作台辅助 CLI")
    parser.add_argument("--version", action="version", version=f"pents {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_parser = subparsers.add_parser("new", help="create a pentest project from templates")
    new_parser.add_argument("name")
    new_parser.add_argument("--target", default="")
    new_parser.add_argument("--owner", default="")
    new_parser.add_argument("--force", action="store_true")
    new_parser.set_defaults(func=cmd_new)

    scope_parser = subparsers.add_parser("scope", help="print project scope")
    scope_parser.add_argument("project")
    scope_parser.set_defaults(func=cmd_scope)

    inventory_parser = subparsers.add_parser("inventory", help="show or append inventory")
    inventory_parser.add_argument("project")
    inventory_parser.add_argument("--add-url", default="")
    inventory_parser.add_argument("--method", default="GET")
    inventory_parser.add_argument("--auth", default="unknown")
    inventory_parser.add_argument("--notes", default="")
    inventory_parser.set_defaults(func=cmd_inventory)

    evidence_parser = subparsers.add_parser("evidence", help="add evidence and return an evidence ID")
    evidence_parser.add_argument("project")
    evidence_parser.add_argument("ref")
    evidence_parser.add_argument("--type", default="note")
    evidence_parser.add_argument("--target", default="")
    evidence_parser.add_argument("--finding", default="")
    evidence_parser.add_argument("--notes", default="")
    evidence_parser.add_argument("--source-url", default="")
    evidence_parser.add_argument("--headers", default="")
    evidence_parser.add_argument("--file", default="")
    evidence_parser.add_argument("--sha256", "--hash", dest="sha256", default="")
    evidence_parser.add_argument("--collected-at", default="")
    evidence_parser.set_defaults(func=cmd_evidence)

    finding_parser = subparsers.add_parser("finding", help="create a finding from template")
    finding_parser.add_argument("project")
    finding_parser.add_argument("title")
    finding_parser.add_argument("--id", default="")
    finding_parser.add_argument("--severity", default="Medium")
    finding_parser.add_argument("--cvss", default="")
    finding_parser.add_argument("--target", default="")
    finding_parser.add_argument("--confirmed-by", default="")
    finding_parser.add_argument("--summary", default="")
    finding_parser.add_argument("--impact", default="")
    finding_parser.add_argument("--remediation", default="")
    finding_parser.set_defaults(func=cmd_finding)

    brief_parser = subparsers.add_parser("brief", help="print or save a sub-agent brief")
    brief_parser.add_argument("project")
    brief_parser.add_argument("--agent", required=True)
    brief_parser.add_argument("--task-id", default="")
    brief_parser.add_argument("--objective", default="")
    brief_parser.add_argument("--save", action="store_true")
    brief_parser.set_defaults(func=cmd_brief)

    run_parser = subparsers.add_parser("run", help="manage per-run retest directories")
    run_subparsers = run_parser.add_subparsers(dest="run_command", required=True)
    run_new_parser = run_subparsers.add_parser("new", help="create a numbered project run")
    run_new_parser.add_argument("project")
    run_new_parser.add_argument("purpose")
    run_new_parser.add_argument("--id", default="", help="explicit run id such as R001 or 1")
    run_new_parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    run_new_parser.add_argument("--phase", default="planned")
    run_new_parser.add_argument("--executor", default="")
    run_new_parser.add_argument("--agent", default="recon")
    run_new_parser.add_argument("--objective", default="")
    run_new_parser.add_argument("--force", action="store_true")
    run_new_parser.set_defaults(func=cmd_run_new)

    static_js_parser = subparsers.add_parser("static-js", help="analyze downloaded JS files and summarize recon clues")
    static_js_parser.add_argument("project")
    static_js_parser.add_argument("js_path")
    static_js_parser.add_argument("--run", default="", help="run directory name such as R001-2026-06-03-active-recon")
    static_js_parser.add_argument("--save", action="store_true", help="save summary to project or run outputs")
    static_js_parser.add_argument("--max-items", type=int, default=30)
    static_js_parser.set_defaults(func=cmd_static_js)

    report_parser = subparsers.add_parser("report", help="generate report draft")
    report_parser.add_argument("project")
    report_parser.add_argument("--target", default="")
    report_parser.add_argument("--tester", default="")
    report_parser.add_argument("--summary", default="")
    report_parser.set_defaults(func=cmd_report)

    doctor_recon_parser = subparsers.add_parser("doctor-recon", help="check recon tool availability and install guidance")
    doctor_recon_parser.add_argument("--strict", action="store_true", help="return non-zero when core recon tools are missing")
    doctor_recon_parser.set_defaults(func=cmd_doctor_recon)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
