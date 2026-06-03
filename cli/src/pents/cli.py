from __future__ import annotations

import argparse
import hashlib
import json
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
        "kind": "go",
    },
    {
        "name": "puredns",
        "purpose": "主动 DNS 主引擎：配合 massdns 做完整字典枚举和 wildcard 去噪",
        "impact": "无法使用推荐的 puredns + massdns 主链路执行完整主动 DNS 枚举。",
        "install": "go install -v github.com/d3mondev/puredns/v2@latest",
        "kind": "go",
    },
    {
        "name": "massdns",
        "purpose": "高性能 DNS 解析引擎：puredns 和 shuffledns 的核心依赖",
        "impact": "puredns/shuffledns 即使已安装，也无法稳定执行高性能主动 DNS 枚举。",
        "install": "https://github.com/blechschmidt/massdns",
        "kind": "manual",
    },
    {
        "name": "dnsx",
        "purpose": "DNS 复核工具：resolver 健康检查、A/AAAA/CNAME 复核、小列表解析和 fallback",
        "impact": "无法快速复核子域名解析结果，也缺少轻量 DNS 检查 fallback。",
        "install": "go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest",
        "kind": "go",
    },
    {
        "name": "httpx",
        "purpose": "HTTP 存活探测、标题、状态码和技术栈识别",
        "impact": "无法批量确认 Web/API 入口存活和基础指纹。",
        "install": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
        "kind": "go",
    },
    {
        "name": "shuffledns",
        "purpose": "主动 DNS 兼容替代：配合 massdns 做 ProjectDiscovery 风格字典枚举",
        "impact": "无法使用 shuffledns + massdns 作为主动 DNS 枚举替代链路。",
        "install": "go install -v github.com/projectdiscovery/shuffledns/cmd/shuffledns@latest",
        "kind": "go",
    },
    {
        "name": "subzy",
        "purpose": "子域名接管风险提示",
        "impact": "无法自动提示疑似接管风险，需要人工检查 CNAME 和第三方服务状态。",
        "install": "go install -v github.com/PentestPad/subzy@latest",
        "kind": "go",
    },
)
DEFAULT_DNS_RESOLVERS = ("1.1.1.1", "1.0.0.1", "8.8.8.8", "8.8.4.4", "223.5.5.5", "119.29.29.29")
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
SKILL_ALIASES = {
    "subdomain-enumeration": "subdomain dns cdn origin source wildcard recon 信息收集 子域名 泛解析 源站",
    "javascript-analysis": "javascript js bundle endpoint route api static 静态分析 前端 端点 路由",
    "api-discovery": "api swagger openapi graphql endpoint rest 发现 接口 端点",
    "xss-reflected": "xss reflected stored dom cross site script 跨站 反射",
    "sqli-sqlmap": "sqli sqlmap sql injection 注入 数据库",
    "ssrf": "ssrf server side request forgery metadata cloud 内网",
    "idor": "idor object reference authz authorization 越权 对象",
    "bola": "bola object authorization authz idor api 对象级 授权 越权",
    "bfla": "bfla function authorization authz api 功能级 授权 越权",
    "mass-assignment": "mass assignment api role isadmin 批量赋值 权限字段",
    "jwt-none-attack": "jwt none token signature api 签名",
    "rate-limit-bypass": "rate limit bypass api brute force 速率 限流",
}


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


def local_tool_bin_dir(root: Path) -> Path:
    return root / "tools" / "third-party" / "bin"


def find_local_tool(root: Path, name: str) -> Path | None:
    bin_dir = local_tool_bin_dir(root)
    suffixes = ("", ".exe", ".cmd", ".bat") if platform.system() == "Windows" else ("", ".exe")
    for suffix in suffixes:
        candidate = bin_dir / f"{name}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def find_recon_tool(root: Path, name: str) -> tuple[str, str]:
    local_path = find_local_tool(root, name)
    if local_path:
        return str(local_path), "tools/third-party/bin"
    path = shutil.which(name)
    if path:
        return path, "PATH"
    return "", ""


def install_guidance(tool: dict[str, str]) -> list[str]:
    command = tool["install"]
    if tool.get("kind") == "manual":
        return [
            f"Windows：从官方 release 下载，或从 `tools/third-party/vendor/{tool['name']}/` 构建，把可执行文件放入 `tools/third-party/bin/`。",
            f"WSL/Linux：从官方源码构建或下载 release，把可执行文件放入 `tools/third-party/bin/` 或加入 PATH。",
            f"macOS：从官方源码构建或下载 release，把可执行文件放入 `tools/third-party/bin/` 或加入 PATH。",
            f"来源参考：{command}",
        ]
    return [
        f"Windows：优先安装到项目 `tools/third-party/bin/`：先设置 `$env:GOBIN=(Resolve-Path '.\\tools\\third-party\\bin').Path`，再运行 `{command}`。",
        f"WSL/Linux：安装 Go 后把 GOBIN 指向项目 `tools/third-party/bin/`，再运行 `{command}`；PATH 只作为 fallback。",
        f"macOS：可用 Go 安装到项目 `tools/third-party/bin/`；ProjectDiscovery 工具也可参考官方 Homebrew 方式，但项目本地目录优先。",
    ]


def split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def normalize_domain(value: str) -> str:
    domain = value.strip().lower().rstrip(".")
    if domain.startswith("*."):
        domain = domain[2:]
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*\.[a-z0-9-]+", domain):
        raise SystemExit(f"Invalid domain: {value}")
    return domain


def active_dns_target(value: str, domain: str) -> str:
    target = value.strip().lower().rstrip(".")
    if not target:
        return ""
    if target == domain or target.endswith(f".{domain}"):
        return target
    return f"{target}.{domain}"


def default_active_dns_dict(root: Path) -> Path:
    return root / "dicts" / "curated" / "subdomains-main.txt"


def path_text(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def count_lines(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for count, _ in enumerate(handle, 1):
            pass
    return count


def active_dns_engine_label(engine: str) -> str:
    labels = {
        "puredns": "puredns + massdns",
        "shuffledns": "shuffledns + massdns",
        "dnsx": "dnsx -l fallback",
    }
    return labels.get(engine, engine)


def select_active_dns_engine(root: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    if find_recon_tool(root, "puredns")[0] and find_recon_tool(root, "massdns")[0]:
        return "puredns"
    if find_recon_tool(root, "shuffledns")[0] and find_recon_tool(root, "massdns")[0]:
        return "shuffledns"
    if find_recon_tool(root, "dnsx")[0]:
        return "dnsx"
    return "puredns"


def active_dns_required_tools(engine: str) -> list[str]:
    tools = ["dnsx"]
    if engine == "puredns":
        tools.extend(["puredns", "massdns"])
    elif engine == "shuffledns":
        tools.extend(["shuffledns", "massdns"])
    else:
        tools.append("dnsx")
    return sorted(set(tools), key=tools.index)


def active_dns_paths(root: Path, args: argparse.Namespace) -> tuple[Path, Path, Path | None]:
    project = ensure_project(root, args.project) if args.project else None
    if project and args.run:
        run_path = project / "runs" / args.run
        if not run_path.exists():
            raise SystemExit(f"Run does not exist: {run_path}")
        return run_path / "outputs", run_path / "raw", project
    if project:
        return project / "outputs", project / "raw", project
    return Path("outputs"), Path("raw"), None


def active_dns_enum_commands(
    engine: str,
    domain: str,
    dict_path: Path,
    resolvers_file: Path,
    raw_dir: Path,
    root: Path,
    resolvers_csv: str,
    retry: str,
    timeout: str,
    threads: str,
) -> list[str]:
    dict_arg = shell_quote(path_text(root, dict_path))
    resolvers_arg = shell_quote(path_text(root, resolvers_file))
    raw_prefix = path_text(root, raw_dir)
    hits = shell_quote(f"{raw_prefix}/active-dns-hits.txt")
    if engine == "puredns":
        return [
            f"puredns bruteforce {dict_arg} {shell_quote(domain)} -r {resolvers_arg} -w {hits}",
        ]
    if engine == "shuffledns":
        return [
            f"shuffledns -d {shell_quote(domain)} -w {dict_arg} -r {resolvers_arg} -o {hits}",
        ]
    candidates = shell_quote(f"{raw_prefix}/active-dns-candidates.txt")
    jsonl = shell_quote(f"{raw_prefix}/active-dns-dnsx.jsonl")
    return [
        f"awk '{{print $0\".{domain}\"}}' {dict_arg} > {candidates}",
        (
            f"dnsx -silent -l {candidates} -r {shell_quote(resolvers_csv)} "
            f"-a -aaaa -cname -json -o {jsonl} -retry {retry} -timeout {timeout} -t {threads}"
        ),
        f"# 从 {jsonl} 提取命中 host，保存为 {hits}，再进入复核步骤。",
    ]


def build_active_dns_plan(args: argparse.Namespace) -> tuple[str, list[tuple[Path, str]]]:
    root = workspace_root()
    domain = normalize_domain(args.domain)
    dict_path = Path(args.dict) if args.dict else default_active_dns_dict(root)
    if not dict_path.is_absolute():
        dict_path = root / dict_path
    if not dict_path.exists():
        raise SystemExit(f"Dictionary does not exist: {dict_path}")

    resolvers = split_csv(args.resolvers) or list(DEFAULT_DNS_RESOLVERS)
    resolvers_csv = ",".join(resolvers)
    canary_targets = [active_dns_target(item, domain) for item in args.canary]
    canary_targets = [item for item in canary_targets if item]
    nonce = args.nonce or f"nx-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    nx_targets = [active_dns_target(nonce, domain)]
    engine = select_active_dns_engine(root, args.engine)
    output_dir, raw_dir, project = active_dns_paths(root, args)
    resolvers_file = output_dir / "active-dns-resolvers.txt"
    canary_file = output_dir / "active-dns-canary-targets.txt"
    nx_file = output_dir / "active-dns-nxdomain-targets.txt"
    plan_file = output_dir / "active-dns-plan.md"
    summary_file = output_dir / "active-dns-summary.md"
    hits_file = raw_dir / "active-dns-hits.txt"
    verify_file = raw_dir / "active-dns-verify.jsonl"
    canary_raw = raw_dir / "active-dns-canary.jsonl"
    nx_raw = raw_dir / "active-dns-nxdomain.jsonl"

    tool_rows = ["| 工具 | 状态 | 来源 | 说明 |", "| --- | --- | --- | --- |"]
    for name in ("puredns", "massdns", "shuffledns", "dnsx"):
        path, source = find_recon_tool(root, name)
        status = "OK" if path else "MISSING"
        note = "当前引擎需要" if name in active_dns_required_tools(engine) else "备用/参考"
        tool_rows.append(f"| {name} | {status} | {source or '-'} | {note} |")

    commands: list[tuple[str, str]] = []
    dnsx_common = f"-r {shell_quote(resolvers_csv)} -a -aaaa -cname -json -retry {args.retry} -timeout {args.timeout}"
    if canary_targets:
        commands.append(
            (
                "canary 子域校验",
                f"dnsx -silent -l {shell_quote(path_text(root, canary_file))} {dnsx_common} -o {shell_quote(path_text(root, canary_raw))}",
            )
        )
    resolver_source = canary_file if canary_targets else nx_file
    for resolver in resolvers:
        safe_resolver = re.sub(r"[^a-zA-Z0-9]+", "-", resolver).strip("-")
        resolver_raw = raw_dir / f"resolver-health-{safe_resolver}.jsonl"
        commands.append(
            (
                f"resolver 自检：{resolver}",
                (
                    f"dnsx -silent -l {shell_quote(path_text(root, resolver_source))} -r {shell_quote(resolver)} "
                    f"-a -json -retry {args.retry} -timeout {args.timeout} -o {shell_quote(path_text(root, resolver_raw))}"
                ),
            )
        )
    commands.append(
        (
            "随机 NXDOMAIN 泛解析检查",
            f"dnsx -silent -l {shell_quote(path_text(root, nx_file))} {dnsx_common} -o {shell_quote(path_text(root, nx_raw))}",
        )
    )
    for index, command in enumerate(
        active_dns_enum_commands(
            engine,
            domain,
            dict_path,
            resolvers_file,
            raw_dir,
            root,
            resolvers_csv,
            args.retry,
            args.timeout,
            args.threads,
        ),
        1,
    ):
        commands.append((f"完整字典枚举 {index}", command))
    commands.append(
        (
            "A/AAAA/CNAME 复核",
            (
                f"dnsx -silent -l {shell_quote(path_text(root, hits_file))} {dnsx_common} "
                f"-o {shell_quote(path_text(root, verify_file))}"
            ),
        )
    )
    if project:
        commands.append(
            (
                "证据登记",
                (
                    f"uv run --project cli pents evidence {shell_quote(project.name)} {shell_quote(path_text(root, verify_file))} "
                    f"--type active-dns --target {shell_quote(domain)} --file {shell_quote(path_text(root, verify_file))} "
                    "--notes 'active-dns; chain=complete after manual result review'"
                ),
            )
        )

    command_lines = []
    for title, command in commands:
        command_lines.extend([f"### {title}", "", "```bash", command, "```", ""])

    canary_text = ", ".join(canary_targets) if canary_targets else "未提供；正式执行前必须补充至少 1 个已知存在子域，例如 ai.<domain>"
    lines = [
        "# 主动 DNS 执行计划",
        "",
        "## 输入",
        "",
        f"- 根域：`{domain}`",
        f"- 字典：`{path_text(root, dict_path)}`（{count_lines(dict_path)} 行）",
        f"- Resolver：`{resolvers_csv}`",
        f"- Canary：{canary_text}",
        f"- 随机 NXDOMAIN：`{nx_targets[0]}`",
        f"- 选择引擎：`{active_dns_engine_label(engine)}`",
        "",
        "## 工具链",
        "",
        "- 推荐顺序：`puredns + massdns` -> `shuffledns + massdns` -> `dnsx -l fallback`。",
        "- `dnsx` 只作为 canary、resolver 自检、A/AAAA/CNAME 复核和小规模 fallback。",
        "- `dnsx -wd` 禁止作为常规枚举参数，避免 R001 暴露的 0 命中误判。",
        "",
        *tool_rows,
        "",
        "## 停止条件",
        "",
        "- Canary 子域无命中：停止完整字典枚举，先排查 resolver、字典拼接和工具参数。",
        "- 随机 NXDOMAIN 有 A/AAAA/CNAME 命中：停止并按泛解析/wildcard 场景处理。",
        "- 单个 resolver 超时或 0 响应：剔除该 resolver 后再进入完整枚举。",
        "- `puredns/massdns` 缺失时不要假装已走主链路；只能标注为替代链路或 fallback。",
        "",
        "## 输出文件",
        "",
        f"- 计划：`{path_text(root, plan_file)}`",
        f"- 摘要：`{path_text(root, summary_file)}`",
        f"- 命中列表：`{path_text(root, hits_file)}`",
        f"- 复核 JSONL：`{path_text(root, verify_file)}`",
        "",
        "## 执行命令",
        "",
        *command_lines,
        "## 报告摘要模板",
        "",
        "- 主链路是否使用：待执行后填写。",
        "- Canary 结果：待执行后填写。",
        "- NXDOMAIN/wildcard 结果：待执行后填写。",
        "- Resolver 剔除情况：待执行后填写。",
        "- 命中数量和新增资产：待执行后填写。",
        "- 证据编号：待执行后填写。",
    ]
    text = "\n".join(lines).rstrip() + "\n"
    writes = [
        (resolvers_file, "\n".join(resolvers) + "\n"),
        (canary_file, "\n".join(canary_targets) + ("\n" if canary_targets else "")),
        (nx_file, "\n".join(nx_targets) + "\n"),
        (plan_file, text),
        (summary_file, "\n".join(lines[-12:]).rstrip() + "\n"),
    ]
    return text, writes


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


def append_section_table_row(content: str, section: str, row: str) -> str:
    index = content.find(section)
    if index < 0:
        return content.rstrip() + "\n\n" + row.rstrip() + "\n"
    match = re.search(r"^\| .* \|$", content[index:], re.MULTILINE)
    if not match:
        return content.rstrip() + "\n\n" + row.rstrip() + "\n"
    table_start = index + match.start()
    table_end = content.find("\n\n", table_start)
    if table_end < 0:
        table_end = len(content)
    return content[:table_end].rstrip("\n") + "\n" + row.rstrip("\n") + content[table_end:]


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
    write_text(path, append_section_table_row(read_text(path), "## 证据列表", line))
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
        "status": args.status,
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


def brief_items(values: list[str], fallback: str = "待补充") -> str:
    items = [value.strip() for value in values if value.strip()]
    return "\n".join(f"- {value}" for value in items) if items else f"- {fallback}"


def brief_table_rows(values: list[str], columns: int) -> str:
    rows: list[str] = []
    for value in values:
        parts = [part.strip() for part in value.split("|")]
        parts = (parts + [""] * columns)[:columns]
        rows.append("| " + " | ".join(table_cell(part) for part in parts) + " |")
    if rows:
        return "\n".join(rows)
    return "| 待补充 |  |  |"


def cmd_brief(args: argparse.Namespace) -> int:
    root = workspace_root()
    project = ensure_project(root, args.project)
    values = {
        "project_name": args.project,
        "agent_role": args.agent,
        "created_at": now_text(),
        "task_id": args.task_id or "",
        "request_summary": args.request or "",
        "objective": args.objective or "",
        "in_scope_items": brief_items(args.in_scope),
        "out_of_scope_items": brief_items(args.out_of_scope, "未声明"),
        "forbidden_items": brief_items(args.forbid, "未声明；执行前必须确认"),
        "stop_items": brief_items(args.stop, "响应异常、疑似越界、证据不足或触发风控时停止"),
        "target_rows": brief_table_rows(args.target, 3),
        "input_gap_items": brief_items(args.input_gap, "无；若执行中发现缺口必须补记"),
        "reference_rows": brief_table_rows(args.reference, 3),
        "acceptance_items": brief_items(args.acceptance, "输出结构化结果并说明证据/阻塞"),
        "writeback_items": brief_items(args.writeback, "inventory.md、evidence.md、progress.md、review.md"),
        "completion_items": brief_items(args.completion, "回填记录、说明遗留问题，并按 ai-board 完成/归档任务"),
    }
    content = fill_template(read_text(template_dir(root) / "brief.md"), values)
    if args.save:
        filename = f"{slugify(args.task_id)}-{slugify(args.agent)}.md" if args.task_id else f"{slugify(args.agent)}.md"
        target = project / "briefs" / filename
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


def extract_json_payload(text: str) -> str:
    json_fence = re.search(r"```json\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    if json_fence:
        return json_fence.group(1).strip()
    any_fence = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if any_fence:
        return any_fence.group(1).strip()
    return text.strip()


def load_agent_output(root: Path, project: Path, value: str) -> dict[str, object]:
    path = resolve_project_input(root, project, value)
    if not path.exists() or not path.is_file():
        raise SystemExit(f"Agent output not found: {path}")
    try:
        data = json.loads(extract_json_payload(read_text(path)))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Agent output must be JSON or fenced JSON: {path}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Agent output must be a JSON object")
    return data


def list_value(data: dict[str, object], key: str) -> list[object]:
    value = data.get(key, [])
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def text_value(item: object, *keys: str) -> str:
    if isinstance(item, dict):
        for key in keys:
            value = item.get(key)
            if value not in (None, ""):
                return str(value)
        return ""
    return str(item) if item not in (None, "") else ""


def evidence_values(item: object) -> list[str]:
    if not isinstance(item, dict):
        return []
    value = item.get("evidence_refs", [])
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return [str(value)] if value else []


def bullet_lines(values: list[str]) -> list[str]:
    items = [f"- {value}" for value in values if value]
    return items or ["- 无"]


def finding_title_value(item: object) -> str:
    return text_value(item, "title", "name", "finding")


def agent_role(data: dict[str, object]) -> str:
    return text_value(data.get("agent") or data.get("agent_role") or "agent", "agent")


def output_targets(data: dict[str, object]) -> list[object]:
    return [*list_value(data, "tested_targets"), *list_value(data, "discovered_targets")]


def existing_finding_titles(project: Path) -> set[str]:
    titles: set[str] = set()
    for finding in (project / "findings").glob("*.md"):
        title = heading_title(read_text(finding), "# 漏洞记录：")
        if title:
            titles.add(title.lower())
    return titles


def cmd_merge(args: argparse.Namespace) -> int:
    root = workspace_root()
    project = ensure_project(root, args.project)
    data = load_agent_output(root, project, args.output)
    agent = agent_role(data)
    merged_targets = 0
    merged_tests = 0
    merged_blocked = 0
    merged_findings = 0

    inventory_path = project / "inventory.md"
    inventory = read_text(inventory_path)
    for target in output_targets(data):
        url = text_value(target, "url", "target", "endpoint")
        if not url or url in inventory:
            continue
        method = text_value(target, "method") or "GET"
        auth = text_value(target, "auth", "requires_auth") or "unknown"
        notes = text_value(target, "notes", "reason") or f"merged_from={args.output}; agent={agent}"
        row = f"|  | {table_cell(url)} | {table_cell(method)} | {table_cell(auth)} | {table_cell(notes)} |\n"
        inventory = append_section_table_row(inventory, "## URL 列表", row)
        merged_targets += 1
    write_text(inventory_path, inventory)

    progress_path = project / "progress.md"
    progress = read_text(progress_path)
    now = now_text()
    timeline_result = (
        f"targets={len(output_targets(data))}; potential={len(list_value(data, 'potential_findings'))}; "
        f"confirmed={len(list_value(data, 'confirmed_findings'))}; blocked={len(list_value(data, 'blocked_or_skipped'))}"
    )
    progress = append_section_table_row(
        progress,
        "## 时间线",
        f"| {table_cell(now)} | {table_cell(agent)} | merge agent output | {table_cell(timeline_result)} |\n",
    )

    for target in list_value(data, "tested_targets"):
        url = text_value(target, "url", "target", "endpoint")
        if not url:
            continue
        surface = text_value(target, "surface", "test_surface") or "agent-output"
        method = text_value(target, "method") or "子代理测试"
        result = text_value(target, "result", "status", "notes") or "已合并"
        refs = ", ".join(evidence_values(target))
        progress = append_section_table_row(
            progress,
            "## 已执行测试",
            f"| {table_cell(url)} | {table_cell(surface)} | {table_cell(method)} | {table_cell(result)} | {table_cell(refs)} |\n",
        )
        merged_tests += 1

    for blocked in list_value(data, "blocked_or_skipped"):
        target = text_value(blocked, "target", "url", "endpoint")
        reason = text_value(blocked, "reason", "notes")
        reason_type = text_value(blocked, "reason_type") or "其他"
        status = text_value(blocked, "status") or "skipped"
        progress = append_section_table_row(
            progress,
            "## 跳过 / 阻塞项",
            (
                f"| {table_cell(target)} | agent-output | {table_cell(status)} | {table_cell(reason_type)} | "
                f"{table_cell(reason)} | {table_cell(agent)} | 需主代理确认 |  |  |\n"
            ),
        )
        merged_blocked += 1

    for status, key in (("candidate", "potential_findings"), ("confirmed-by-agent", "confirmed_findings")):
        for finding in list_value(data, key):
            title = finding_title_value(finding)
            if not title:
                continue
            refs = ", ".join(evidence_values(finding))
            progress = append_section_table_row(
                progress,
                "## 候选漏洞",
                f"|  | {table_cell(title)} | {status} | {table_cell(refs)} |\n",
            )
            merged_findings += 1
    write_text(progress_path, progress)

    print(
        f"Merged agent output: targets={merged_targets}, tests={merged_tests}, "
        f"blocked={merged_blocked}, findings={merged_findings}"
    )
    return 0


def cmd_review_agent_output(args: argparse.Namespace) -> int:
    root = workspace_root()
    project = ensure_project(root, args.project)
    data = load_agent_output(root, project, args.output)
    existing_titles = existing_finding_titles(project)
    all_findings = [*list_value(data, "potential_findings"), *list_value(data, "confirmed_findings")]

    scope_risks = [text_value(item, "reason", "target", "url", "notes") for item in list_value(data, "scope_risk")]
    insufficient = [
        finding_title_value(item)
        for item in all_findings
        if finding_title_value(item) and not evidence_values(item)
    ]
    seen: set[str] = set()
    duplicates: list[str] = []
    for item in all_findings:
        title = finding_title_value(item)
        if not title:
            continue
        key = title.lower()
        if key in seen or key in existing_titles:
            duplicates.append(title)
        seen.add(key)
    candidates = [finding_title_value(item) for item in list_value(data, "potential_findings") if finding_title_value(item)]

    lines = [
        "# 子代理输出审查",
        "",
        "## 越界风险",
        "",
        *bullet_lines(scope_risks),
        "",
        "## 证据不足",
        "",
        *bullet_lines(insufficient),
        "",
        "## 重复项",
        "",
        *bullet_lines(duplicates),
        "",
        "## 候选 Finding",
        "",
        *bullet_lines(candidates),
    ]
    print("\n".join(lines))
    return 0


def skill_catalog(root: Path) -> list[dict[str, str]]:
    readme = root / "skills" / "README.md"
    if not readme.exists():
        raise SystemExit(f"Skills README not found: {readme}")
    catalog: list[dict[str, str]] = []
    for line in read_text(readme).splitlines():
        match = re.match(r"\| \[([^\]]+)\]\(([^)]+)\) \| ([^|]+) \|", line.strip())
        if not match:
            continue
        name = match.group(1).strip()
        path = match.group(2).strip().replace("\\", "/")
        summary = match.group(3).strip()
        role = path.split("/", 1)[0] if "/" in path else "general"
        catalog.append(
            {
                "name": name,
                "path": f"skills/{path}",
                "summary": summary,
                "role": role,
                "aliases": SKILL_ALIASES.get(name, ""),
            }
        )
    return catalog


def query_terms(query: str) -> list[str]:
    return [term for term in re.split(r"[\s,;/|]+", query.lower()) if term]


def skill_score(skill: dict[str, str], query: str) -> int:
    lowered_query = query.lower()
    terms = query_terms(lowered_query)
    haystack = " ".join(
        [
            skill["name"],
            skill["path"],
            skill["summary"],
            skill["role"],
            skill["aliases"],
        ]
    ).lower()
    score = 0
    if lowered_query and lowered_query in haystack:
        score += 3
    for term in terms:
        if term in haystack:
            score += 2 if term in skill["name"].lower() else 1
    return score


def cmd_suggest_skills(args: argparse.Namespace) -> int:
    root = workspace_root()
    query = " ".join(args.query).strip()
    catalog = skill_catalog(root)
    scored = []
    for skill in catalog:
        if args.role and skill["role"] != args.role:
            continue
        score = skill_score(skill, query)
        if score > 0:
            scored.append((score, skill))
    scored.sort(key=lambda item: (-item[0], item[1]["role"], item[1]["name"]))
    selected = [skill for _, skill in scored[: args.limit]]

    print("# Skill 推荐")
    print()
    print(f"- 查询：{query}")
    print()
    print("| Skill | 建议 agent role | Skill 路径 | 适用场景摘要 |")
    print("| --- | --- | --- | --- |")
    if not selected:
        print("| 无 |  |  | 未匹配到正式 skill |")
        return 0
    for skill in selected:
        print(
            f"| {table_cell(skill['name'])} | {table_cell(skill['role'])} | "
            f"{table_cell(skill['path'])} | {table_cell(skill['summary'])} |"
        )
    return 0


def heading_title(text: str, prefix: str) -> str:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.replace(prefix, "", 1).strip()
    return ""


def markdown_section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    next_match = re.search(r"^## .*$", text[match.end() :], re.MULTILINE)
    end = match.end() + next_match.start() if next_match else len(text)
    return text[match.end() : end].strip()


def split_table_row(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def table_rows(section: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = split_table_row(stripped)
        if not cells or all(set(cell) <= {"-", " "} for cell in cells):
            continue
        rows.append(cells)
    return rows


def evidence_index(project: Path) -> dict[str, dict[str, str]]:
    path = project / "evidence.md"
    if not path.exists():
        return {}
    rows = table_rows(read_text(path))
    evidence: dict[str, dict[str, str]] = {}
    for cells in rows:
        if len(cells) < 6 or not re.fullmatch(r"E-\d{4}", cells[0]):
            continue
        evidence[cells[0]] = {
            "type": cells[1],
            "target": cells[2],
            "finding": cells[3],
            "ref": cells[4],
            "notes": cells[5],
        }
    return evidence


def finding_has_repro_steps(text: str) -> bool:
    section = markdown_section(text, "复现步骤")
    for line in section.splitlines():
        stripped = line.strip()
        if not re.match(r"^\d+\.\s*", stripped):
            continue
        if re.sub(r"^\d+\.\s*", "", stripped).strip():
            return True
    return False


def evidence_ids_for_finding(finding_id: str, text: str, evidence: dict[str, dict[str, str]]) -> list[str]:
    ids = set(re.findall(r"\bE-\d{4}\b", markdown_section(text, "证据")))
    for evidence_id, item in evidence.items():
        if item.get("finding") == finding_id:
            ids.add(evidence_id)
    return sorted(ids)


def evidence_refs(ids: list[str]) -> str:
    return ", ".join(f"`{evidence_id}`" for evidence_id in ids) if ids else "缺失"


def finding_gap_notes(ids: list[str], text: str, evidence: dict[str, dict[str, str]]) -> list[str]:
    gaps: list[str] = []
    if not ids:
        gaps.append("缺少证据")
    if not finding_has_repro_steps(text):
        gaps.append("缺少复现步骤")
    if any("chain=incomplete" in evidence.get(evidence_id, {}).get("notes", "") for evidence_id in ids):
        gaps.append("证据链不完整")
    return gaps


def severity_stat_rows(severities: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    for severity in severities:
        key = severity or "未标注"
        counts[key] = counts.get(key, 0) + 1
    order = ["Critical", "High", "Medium", "Low", "Info", "Informational", "未标注"]
    keys = [key for key in order if key in counts]
    keys.extend(sorted(key for key in counts if key not in keys))
    rows = ["| 严重程度 | 数量 |", "| --- | --- |"]
    rows.extend(f"| {table_cell(key)} | {counts[key]} |" for key in keys)
    return rows


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
        evidence = evidence_index(project)
        summary_rows = ["| 编号 | 标题 | 严重程度 | 状态 | 证据 |", "| --- | --- | --- | --- | --- |"]
        gap_rows = ["| 编号 | 状态 | 证据引用 | 缺口提示 |", "| --- | --- | --- | --- |"]
        severities: list[str] = []
        for finding in findings:
            text = read_text(finding)
            title = heading_title(text, "# 漏洞记录：") or finding.stem
            finding_id = field_value(text, "编号") or finding.stem
            severity = field_value(text, "严重程度")
            status = field_value(text, "状态")
            severities.append(severity)
            ids = evidence_ids_for_finding(finding_id, text, evidence)
            summary_rows.append(
                f"| {table_cell(finding_id)} | {table_cell(title)} | {table_cell(severity)} | "
                f"{table_cell(status)} | {table_cell(evidence_refs(ids))} |"
            )
            gaps = finding_gap_notes(ids, text, evidence)
            if gaps:
                gap_rows.append(
                    f"| {table_cell(finding_id)} | {table_cell(status)} | {table_cell(evidence_refs(ids))} | "
                    f"{table_cell('；'.join(gaps))} |"
                )
        if len(gap_rows) == 2:
            gap_rows.append("| 无 |  |  | 无 |")
        content = replace_section_table(content, "## 漏洞汇总", summary_rows)
        content = replace_section_table(content, "## 严重程度统计", severity_stat_rows(severities))
        content = replace_section_table(content, "## 证据与缺口", gap_rows)
    target = project / "report.md"
    write_text(target, content)
    print(f"Created report: {target}")
    return 0


def cmd_doctor_recon(args: argparse.Namespace) -> int:
    missing: list[str] = []
    root = workspace_root()
    local_bin = local_tool_bin_dir(root)
    print("Recon 工具检查")
    print(f"当前环境：{platform_label()}")
    print(f"项目第三方工具目录：{local_bin}")
    print("查找顺序：tools/third-party/bin -> 系统 PATH。PATH 只作为 fallback，不是推荐安装位置。")
    print("主动 DNS 默认主链路：puredns + massdns；兼容替代：shuffledns + massdns；dnsx 用于复核和小规模 fallback。")
    print("本机下载提示：涉及国外网络的拉取/下载，可在本机 PowerShell 临时设置 `$env:all_proxy='http://127.0.0.1:7890'`；不要把这个本机代理配置套到远端机器。")
    print("安装建议按环境区分：Windows/WSL/Linux/macOS 都优先写入项目第三方工具目录；全局 PATH 仅兜底。")
    print()

    for tool in RECON_TOOLS:
        path, source = find_recon_tool(root, tool["name"])
        status = "OK" if path else "MISSING"
        if not path:
            missing.append(tool["name"])
        print(f"[{status}] {tool['name']}")
        print(f"用途：{tool['purpose']}")
        if path:
            print(f"路径：{path}")
            print(f"来源：{source}")
            if source == "PATH":
                print("提示：这是全局 PATH fallback；推荐迁移或重装到 `tools/third-party/bin/`。")
            if tool["name"] == "httpx":
                print("提示：请确认这是 ProjectDiscovery httpx，不是 Python httpx 同名命令。")
        else:
            print(f"影响：{tool['impact']}")
            print("安装建议：")
            for line in install_guidance(tool):
                print(f"- {line}")
        print()

    if missing:
        print("结论：recon 工具链不完整。Claude 执行时必须在 progress/review 中写明缺失工具、受影响步骤和替代方案。")
        return 2 if args.strict else 0

    print("结论：核心 recon 工具已找到。仍需确认授权窗口、DNS 并发/速率、resolver 和字典规模后再执行主动扫描。")
    return 0


def cmd_active_dns(args: argparse.Namespace) -> int:
    plan, writes = build_active_dns_plan(args)
    print(plan)
    if args.save:
        root = workspace_root()
        _, raw_dir, _ = active_dns_paths(root, args)
        raw_dir.mkdir(parents=True, exist_ok=True)
        for path, content in writes:
            write_text(path, content)
        saved = [str(path) for path, _ in writes]
        print("Saved active DNS plan files:")
        for path in saved:
            print(f"- {path}")
    else:
        print("提示：当前仅打印计划；添加 `--save --project <name> --run <run-dir>` 可写入 run outputs/raw。")
    return 0


def field_value(text: str, field: str) -> str:
    # Match both fullwidth ：(U+FF1A) and ASCII : after field name
    match = re.search(rf"^- {re.escape(field)}[：:]\s*(.*)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def replace_section_table(content: str, section: str, rows: list[str]) -> str:
    index = content.find(section)
    if index < 0:
        return content
    match = re.search(r"^\| .* \|$", content[index:], re.MULTILINE)
    if not match:
        return content
    table_start = index + match.start()
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
    finding_parser.add_argument("--status", default="待确认")
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
    brief_parser.add_argument("--request", default="", help="original short user request")
    brief_parser.add_argument("--objective", default="")
    brief_parser.add_argument("--in-scope", action="append", default=[], help="authorized scope item")
    brief_parser.add_argument("--out-of-scope", action="append", default=[], help="explicitly excluded scope item")
    brief_parser.add_argument("--forbid", action="append", default=[], help="forbidden action")
    brief_parser.add_argument("--stop", action="append", default=[], help="stop condition")
    brief_parser.add_argument("--target", action="append", default=[], help="target row: target|surface|notes")
    brief_parser.add_argument("--input-gap", action="append", default=[], help="missing input that must be confirmed")
    brief_parser.add_argument("--reference", action="append", default=[], help="reference row: type|path|notes")
    brief_parser.add_argument("--acceptance", action="append", default=[], help="acceptance criterion")
    brief_parser.add_argument("--writeback", action="append", default=[], help="file or record to update")
    brief_parser.add_argument("--completion", action="append", default=[], help="completion/archive requirement")
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

    merge_parser = subparsers.add_parser("merge", help="merge structured sub-agent output into project records")
    merge_parser.add_argument("project")
    merge_parser.add_argument("output", help="JSON file or Markdown file with fenced JSON")
    merge_parser.set_defaults(func=cmd_merge)

    review_agent_parser = subparsers.add_parser("review-agent-output", help="review structured sub-agent output")
    review_agent_parser.add_argument("project")
    review_agent_parser.add_argument("output", help="JSON file or Markdown file with fenced JSON")
    review_agent_parser.set_defaults(func=cmd_review_agent_output)

    suggest_parser = subparsers.add_parser("suggest-skills", help="recommend formal skills for a test surface")
    suggest_parser.add_argument("query", nargs="+")
    suggest_parser.add_argument("--role", choices=("recon", "web", "api"), default="")
    suggest_parser.add_argument("--limit", type=int, default=5)
    suggest_parser.set_defaults(func=cmd_suggest_skills)

    report_parser = subparsers.add_parser("report", help="generate report draft")
    report_parser.add_argument("project")
    report_parser.add_argument("--target", default="")
    report_parser.add_argument("--tester", default="")
    report_parser.add_argument("--summary", default="")
    report_parser.set_defaults(func=cmd_report)

    doctor_recon_parser = subparsers.add_parser("doctor-recon", help="check recon tool availability and install guidance")
    doctor_recon_parser.add_argument("--strict", action="store_true", help="return non-zero when core recon tools are missing")
    doctor_recon_parser.set_defaults(func=cmd_doctor_recon)

    active_dns_parser = subparsers.add_parser("active-dns", help="prepare active DNS precheck and execution plan")
    active_dns_parser.add_argument("domain", help="root domain or wildcard scope such as *.example.com")
    active_dns_parser.add_argument("--dict", default="", help="subdomain dictionary path")
    active_dns_parser.add_argument("--resolvers", default=",".join(DEFAULT_DNS_RESOLVERS), help="comma-separated resolvers")
    active_dns_parser.add_argument("--canary", action="append", default=[], help="known existing subdomain label or FQDN")
    active_dns_parser.add_argument("--nonce", default="", help="custom NXDOMAIN label for wildcard check")
    active_dns_parser.add_argument("--engine", choices=("auto", "puredns", "shuffledns", "dnsx"), default="auto")
    active_dns_parser.add_argument("--threads", default="1000", help="dnsx fallback thread count")
    active_dns_parser.add_argument("--retry", default="1")
    active_dns_parser.add_argument("--timeout", default="2")
    active_dns_parser.add_argument("--project", default="", help="project name for evidence command and saved outputs")
    active_dns_parser.add_argument("--run", default="", help="run directory name such as R002-2026-06-03-active-dns")
    active_dns_parser.add_argument("--save", action="store_true", help="save plan and helper input files")
    active_dns_parser.set_defaults(func=cmd_active_dns)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
