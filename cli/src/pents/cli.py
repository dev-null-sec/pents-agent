from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import platform
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
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
        "name": "massdns",
        "purpose": "主动 DNS 核心执行器：文件驱动高速解析候选子域名",
        "impact": "无法使用默认 massdns direct 主链路执行完整主动 DNS 枚举。",
        "install": "https://github.com/blechschmidt/massdns",
        "kind": "manual",
        "tier": "active-dns-core",
    },
    {
        "name": "subfinder",
        "purpose": "被动子域名收集",
        "impact": "被动来源覆盖会变少，子域名初始清单质量下降。",
        "install": "go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
        "kind": "go",
        "tier": "optional-passive",
    },
    {
        "name": "puredns",
        "purpose": "可选主动 DNS wrapper：人工诊断或复杂 wildcard 场景参考",
        "impact": "无法使用 puredns wrapper；默认 massdns direct 主链路不受影响。",
        "install": "go install -v github.com/d3mondev/puredns/v2@latest",
        "kind": "go",
        "tier": "optional-wrapper",
    },
    {
        "name": "dnsx",
        "purpose": "可选 DNS 诊断工具：小列表人工复核，不作为默认扫描链路",
        "impact": "无法使用 dnsx 做人工诊断；默认 massdns direct 主链路不受影响。",
        "install": "go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest",
        "kind": "go",
        "tier": "optional-diagnostic",
    },
    {
        "name": "httpx",
        "purpose": "HTTP 存活探测、标题、状态码和技术栈识别",
        "impact": "无法批量确认 Web/API 入口存活和基础指纹。",
        "install": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
        "kind": "go",
        "tier": "post-processing",
    },
    {
        "name": "shuffledns",
        "purpose": "主动 DNS 兼容替代：配合 massdns 做 ProjectDiscovery 风格字典枚举",
        "impact": "无法使用 shuffledns + massdns 作为主动 DNS 枚举替代链路。",
        "install": "go install -v github.com/projectdiscovery/shuffledns/cmd/shuffledns@latest",
        "kind": "go",
        "tier": "optional-fallback",
    },
    {
        "name": "subzy",
        "purpose": "子域名接管风险提示",
        "impact": "无法自动提示疑似接管风险，需要人工检查 CNAME 和第三方服务状态。",
        "install": "go install -v github.com/PentestPad/subzy@latest",
        "kind": "go",
        "tier": "post-processing",
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
VISION_RESULT_DEFAULTS = {
    "can_read_image": False,
    "blocker": "",
    "page_type": "",
    "captcha_or_waf": {
        "present": None,
        "type": "",
        "evidence": "",
    },
    "visible_interactive_elements": [],
    "sensitive_content": {
        "present": None,
        "description": "",
    },
    "confidence": "low",
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


def file_size(path: Path) -> int:
    return path.stat().st_size


def image_mime_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    if guessed and guessed.startswith("image/"):
        return guessed
    suffix = path.suffix.lower()
    if suffix == ".jpg":
        return "image/jpeg"
    if suffix in {".png", ".jpeg", ".webp", ".gif"}:
        return f"image/{suffix.lstrip('.')}"
    raise SystemExit(f"Unsupported image type: {path.suffix or '(no extension)'}")


def image_data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{image_mime_type(path)};base64,{encoded}"


def openai_compatible_endpoint(base_url: str) -> str:
    value = base_url.rstrip("/")
    if value.endswith("/chat/completions"):
        return value
    return value + "/chat/completions"


def deep_copy_json(value: dict[str, object]) -> dict[str, object]:
    return json.loads(json.dumps(value, ensure_ascii=False))


def normalize_vision_result(value: dict[str, object] | None) -> dict[str, object]:
    result = deep_copy_json(VISION_RESULT_DEFAULTS)
    if value:
        if "can_read_image" not in value and "blocker" not in value:
            result["can_read_image"] = True
        if value.get("后台登录页") is True:
            result["page_type"] = "后台登录页"
        if "验证码或验证组件" in value:
            captcha = result.get("captcha_or_waf")
            if isinstance(captcha, dict):
                captcha["present"] = value.get("验证码或验证组件")
                captcha["type"] = "验证码或验证组件" if value.get("验证码或验证组件") else ""
        if "敏感信息" in value:
            sensitive = result.get("sensitive_content")
            if isinstance(sensitive, dict):
                sensitive["present"] = value.get("敏感信息")
        if value.get("可见交互元素") is True:
            result["visible_interactive_elements"] = ["存在可见交互元素"]
        for key, item in value.items():
            if key in {"captcha_or_waf", "sensitive_content"} and isinstance(item, dict):
                nested = result.get(key)
                if isinstance(nested, dict):
                    nested.update(item)
                continue
            result[key] = item
    for key in ("captcha_or_waf", "sensitive_content"):
        if not isinstance(result.get(key), dict):
            result[key] = deep_copy_json(VISION_RESULT_DEFAULTS)[key]
    if not isinstance(result.get("visible_interactive_elements"), list):
        result["visible_interactive_elements"] = [str(result["visible_interactive_elements"])]
    visible_text = " ".join(str(item).lower() for item in result.get("visible_interactive_elements", []))
    captcha = result.get("captcha_or_waf")
    if isinstance(captcha, dict) and captcha.get("present") is None and ("captcha" in visible_text or "验证码" in visible_text):
        captcha["present"] = True
        captcha["type"] = captcha.get("type") or ("captcha" if "captcha" in visible_text else "验证码")
    return result


def vision_system_prompt() -> str:
    return (
        "你是截图视觉复核器。只看用户提供的截图，不访问网络，不推测漏洞。"
        "请只输出 JSON object。推荐字段：can_read_image, blocker, page_type, captcha_or_waf, "
        "visible_interactive_elements, sensitive_content, confidence。"
    )


def vision_user_text(question: str, context: list[str]) -> str:
    lines = [
        "请只根据截图回答这个窄问题。",
        f"问题：{question}",
    ]
    if context:
        lines.append("必要上下文：")
        lines.extend(f"- {item}" for item in context)
    lines.append("不要推测漏洞，不要构造 payload，不要访问网络。")
    return "\n".join(lines)


def build_vision_payload(args: argparse.Namespace, image_url: str) -> dict[str, object]:
    token_param = args.token_param or "max_tokens"
    payload: dict[str, object] = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": vision_system_prompt()},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": vision_user_text(args.question, args.context)},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
        "temperature": 0,
        token_param: args.max_tokens,
    }
    if args.json_mode:
        payload["response_format"] = {"type": "json_object"}
    return payload


def post_json(url: str, payload: dict[str, object], api_key: str, timeout: int) -> tuple[int, str]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read().decode("utf-8", errors="replace")


def openai_message_text(data: dict[str, object]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("missing choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("invalid choice")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("missing message")
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        if parts:
            return "\n".join(parts)
    reasoning_content = message.get("reasoning_content")
    if isinstance(reasoning_content, str) and reasoning_content.strip():
        return reasoning_content
    raise ValueError("missing message content")


def resolve_plain_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def parse_env_value(value: str) -> str:
    item = value.strip()
    if len(item) >= 2 and item[0] == item[-1] and item[0] in {'"', "'"}:
        return item[1:-1]
    return item


def load_env_file(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    for raw_line in read_text(path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue
        os.environ.setdefault(key, parse_env_value(value))
    return True


def load_env_files(root: Path, explicit: str) -> list[str]:
    candidates = [resolve_plain_path(root, explicit)] if explicit else [root / ".env", root / ".env.local"]
    loaded: list[str] = []
    for path in candidates:
        if load_env_file(path):
            loaded.append(str(path))
    return loaded


def vision_record(
    *,
    status: str,
    mode: str,
    provider: str,
    model: str,
    image_path: Path,
    question: str,
    started_at: str,
    elapsed_ms: int,
    result: dict[str, object] | None = None,
    error_type: str = "",
    message: str = "",
    api_base_url: str = "",
    http_status: int | None = None,
    raw_text_preview: str = "",
    env_files_loaded: list[str] | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "status": status,
        "mode": mode,
        "provider": provider,
        "model": model,
        "api_base_url": api_base_url,
        "started_at": started_at,
        "elapsed_ms": elapsed_ms,
        "question": question,
        "image": {
            "path": str(image_path),
            "sha256": file_sha256(image_path),
            "mime_type": image_mime_type(image_path),
            "bytes": file_size(image_path),
        },
        "result": normalize_vision_result(result),
        "error_type": error_type,
        "message": message,
        "env_files_loaded": env_files_loaded or [],
    }
    if http_status is not None:
        record["http_status"] = http_status
    if raw_text_preview:
        record["raw_text_preview"] = raw_text_preview[:800]
    return record


def emit_json_result(record: dict[str, object], out: str) -> None:
    text = json.dumps(record, ensure_ascii=False, indent=2)
    if out:
        target = resolve_plain_path(workspace_root(), out)
        write_text(target, text + "\n")
    print(text)


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


def powershell_array_literal(values: list[str]) -> str:
    return "@(" + ", ".join(shell_quote(value) for value in values) + ")"


def parse_dns_record_types(value: str) -> list[str]:
    allowed = {"A", "AAAA", "CNAME"}
    record_types: list[str] = []
    for part in value.split(","):
        item = part.strip().upper()
        if not item:
            continue
        if item not in allowed:
            raise SystemExit(f"Unsupported DNS record type for active-dns: {item}")
        if item not in record_types:
            record_types.append(item)
    return record_types or ["A"]


def command_tool(root: Path, name: str) -> str:
    local_path = find_local_tool(root, name)
    if local_path:
        return shell_quote(path_text(root, local_path))
    return name


def timed_shell_command(command: str) -> str:
    if command.lstrip().startswith("#"):
        return command
    return "\n".join(
        [
            "START=$(date +%s)",
            command,
            "STATUS=$?",
            "END=$(date +%s)",
            'echo "elapsed: $((END - START))s; exit=$STATUS"',
            "test $STATUS -eq 0",
        ]
    )


def count_lines(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for count, _ in enumerate(handle, 1):
            pass
    return count


def active_dns_engine_label(engine: str) -> str:
    labels = {
        "massdns": "massdns direct",
        "puredns": "puredns + massdns",
        "shuffledns": "shuffledns + massdns",
        "dnsx": "dnsx -l fallback",
    }
    return labels.get(engine, engine)


def select_active_dns_engine(root: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    if find_recon_tool(root, "massdns")[0]:
        return "massdns"
    return "massdns"


def active_dns_required_tools(engine: str) -> list[str]:
    tools: list[str] = []
    if engine == "massdns":
        tools.append("massdns")
    elif engine == "puredns":
        tools.extend(["puredns", "massdns", "dnsx"])
    elif engine == "shuffledns":
        tools.extend(["shuffledns", "massdns", "dnsx"])
    else:
        tools.append("dnsx")
    return sorted(set(tools), key=tools.index)


def active_dns_effective_required_tools(engine: str, nodata_check: bool) -> list[str]:
    tools = active_dns_required_tools(engine)
    if nodata_check and "dnsx" not in tools:
        tools.append("dnsx")
    return tools


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
    rate_limit: str,
) -> list[str]:
    puredns_cmd = command_tool(root, "puredns")
    massdns_cmd = command_tool(root, "massdns")
    shuffledns_cmd = command_tool(root, "shuffledns")
    dnsx_cmd = command_tool(root, "dnsx")
    dict_arg = shell_quote(path_text(root, dict_path))
    resolvers_arg = shell_quote(path_text(root, resolvers_file))
    raw_prefix = path_text(root, raw_dir)
    hits = shell_quote(f"{raw_prefix}/active-dns-hits.txt")
    massdns_out = shell_quote(f"{raw_prefix}/active-dns-massdns.txt")
    if engine == "puredns":
        return [
            (
                f"{puredns_cmd} bruteforce {dict_arg} {shell_quote(domain)} -r {resolvers_arg} "
                f"-b {massdns_cmd} --rate-limit {rate_limit} -w {hits} --write-massdns {massdns_out}"
            ),
        ]
    if engine == "shuffledns":
        return [
            f"{shuffledns_cmd} -d {shell_quote(domain)} -w {dict_arg} -r {resolvers_arg} -o {hits}",
        ]
    candidates = shell_quote(f"{raw_prefix}/active-dns-candidates.txt")
    jsonl = shell_quote(f"{raw_prefix}/active-dns-dnsx.jsonl")
    return [
        f"awk '{{print $0\".{domain}\"}}' {dict_arg} > {candidates}",
        (
            f"{dnsx_cmd} -silent -l {candidates} -r {shell_quote(resolvers_csv)} "
            f"-a -aaaa -cname -json -o {jsonl} -retry {retry} -timeout {timeout} -t {threads}"
        ),
        f"# 从 {jsonl} 提取命中 host，保存为 {hits}，再进入复核步骤。",
    ]


def active_dns_massdns_command(
    domain: str,
    dict_path: Path,
    resolvers_file: Path,
    output_dir: Path,
    raw_dir: Path,
    root: Path,
    canary_targets: list[str],
    nx_target: str,
    hashmap_size: str,
    record_types: list[str],
) -> str:
    script = shell_quote(path_text(root, root / "tools" / "recon" / "active-dns-massdns.ps1"))
    massdns = command_tool(root, "massdns")
    parts = [
        "&",
        script,
        "-Domain",
        shell_quote(domain),
        "-Dictionary",
        shell_quote(path_text(root, dict_path)),
        "-ResolversFile",
        shell_quote(path_text(root, resolvers_file)),
        "-OutputDir",
        shell_quote(path_text(root, output_dir)),
        "-RawDir",
        shell_quote(path_text(root, raw_dir)),
        "-Nonce",
        shell_quote(nx_target),
        "-Massdns",
        massdns,
        "-HashmapSize",
        hashmap_size,
        "-RecordTypes",
        powershell_array_literal(record_types),
    ]
    if canary_targets:
        parts.extend(["-Canary", powershell_array_literal(canary_targets)])
    return " ".join(parts)


def active_dns_nodata_command(
    domain: str,
    raw_dir: Path,
    root: Path,
    resolvers_csv: str,
    verify_retry: str,
    verify_timeout: str,
) -> str:
    dnsx_cmd = command_tool(root, "dnsx")
    candidates = shell_quote(path_text(root, raw_dir / "active-dns-candidates.txt"))
    hits = shell_quote(path_text(root, raw_dir / "active-dns-hits.txt"))
    nodata = shell_quote(path_text(root, raw_dir / "active-dns-nodata-dnsx.jsonl"))
    return "\n".join(
        [
            "$sw = [System.Diagnostics.Stopwatch]::StartNew()",
            (
                f"& {dnsx_cmd} -silent -l {candidates} -r {shell_quote(resolvers_csv)} "
                f"-a -aaaa -cname -json -rcode noerror -retry {verify_retry} "
                f"-timeout {verify_timeout} -o {nodata}"
            ),
            "$status = $LASTEXITCODE",
            "$sw.Stop()",
            f"$massdnsHits = if (Test-Path {hits}) {{ (Get-Content {hits} | Measure-Object -Line).Lines }} else {{ 0 }}",
            f"$dnsxNoerror = if (Test-Path {nodata}) {{ (Get-Content {nodata} | Measure-Object -Line).Lines }} else {{ 0 }}",
            "$possibleNodata = [Math]::Max(0, $dnsxNoerror - $massdnsHits)",
            "$elapsed = [math]::Round($sw.Elapsed.TotalSeconds, 3)",
            (
                f"Write-Host \"nodata-check complete: domain={domain} "
                "elapsed=${elapsed}s; exit=$status; massdns_hits=$massdnsHits; "
                "dnsx_noerror_lines=$dnsxNoerror; possible_nodata_or_non_address_diff=$possibleNodata\""
            ),
            'if ($status -ne 0) { throw "dnsx nodata check failed: exit=$status" }',
        ]
    )


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
    record_types = parse_dns_record_types(args.record_types)
    if args.nodata_check and engine != "massdns":
        raise SystemExit("--nodata-check currently requires massdns direct because it reuses active-dns-candidates.txt")
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
    nodata_file = raw_dir / "active-dns-nodata-dnsx.jsonl"

    tool_rows = ["| 工具 | 状态 | 来源 | 说明 |", "| --- | --- | --- | --- |"]
    required_tools = active_dns_effective_required_tools(engine, args.nodata_check)
    for name in ("massdns", "puredns", "dnsx", "shuffledns"):
        path, source = find_recon_tool(root, name)
        status = "OK" if path else "MISSING"
        note = "当前引擎需要" if name in required_tools else "备用/参考"
        if args.nodata_check and name == "dnsx":
            note = "可选 NODATA 复核需要"
        tool_rows.append(f"| {name} | {status} | {source or '-'} | {note} |")

    commands: list[tuple[str, str, str]] = []
    if engine == "massdns":
        commands.append(
            (
                "massdns direct 文件驱动执行器",
                active_dns_massdns_command(
                    domain,
                    dict_path,
                    resolvers_file,
                    output_dir,
                    raw_dir,
                    root,
                    canary_targets,
                    nx_targets[0],
                    args.hashmap_size,
                    record_types,
                ),
                "powershell",
            )
        )
    else:
        dnsx_cmd = command_tool(root, "dnsx")
        dnsx_common = f"-r {shell_quote(resolvers_csv)} -a -aaaa -cname -json -retry {args.retry} -timeout {args.timeout}"
        verify_dnsx_common = (
            f"-r {shell_quote(resolvers_csv)} -a -aaaa -cname -json "
            f"-retry {args.verify_retry} -timeout {args.verify_timeout}"
        )
        if canary_targets:
            commands.append(
                (
                    "canary 子域校验",
                    f"{dnsx_cmd} -silent -l {shell_quote(path_text(root, canary_file))} {dnsx_common} -o {shell_quote(path_text(root, canary_raw))}",
                    "bash",
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
                        f"{dnsx_cmd} -silent -l {shell_quote(path_text(root, resolver_source))} -r {shell_quote(resolver)} "
                        f"-a -json -retry {args.retry} -timeout {args.timeout} -o {shell_quote(path_text(root, resolver_raw))}"
                    ),
                    "bash",
                )
            )
        commands.append(
            (
                "随机 NXDOMAIN 泛解析检查",
                f"{dnsx_cmd} -silent -l {shell_quote(path_text(root, nx_file))} {dnsx_common} -o {shell_quote(path_text(root, nx_raw))}",
                "bash",
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
                args.rate_limit,
            ),
            1,
        ):
            commands.append((f"完整字典枚举 {index}", command, "bash"))
        commands.append(
            (
                "A/AAAA/CNAME 复核",
                (
                    f"{dnsx_cmd} -silent -l {shell_quote(path_text(root, hits_file))} {verify_dnsx_common} "
                    f"-o {shell_quote(path_text(root, verify_file))}"
                ),
                "bash",
            )
        )
    if args.nodata_check:
        commands.append(
            (
                "可选 dnsx NOERROR/NODATA 复核",
                active_dns_nodata_command(domain, raw_dir, root, resolvers_csv, args.verify_retry, args.verify_timeout),
                "powershell",
            )
        )
    if project:
        evidence_path = hits_file if engine == "massdns" else verify_file
        commands.append(
            (
                "证据登记",
                (
                    f"uv run --project cli pents evidence {shell_quote(project.name)} {shell_quote(path_text(root, evidence_path))} "
                    f"--type active-dns --target {shell_quote(domain)} --file {shell_quote(path_text(root, evidence_path))} "
                    "--notes 'active-dns; chain=complete after manual result review'"
                ),
                "bash",
            )
        )
        if args.nodata_check:
            commands.append(
                (
                    "NODATA 复核证据登记",
                    (
                        f"uv run --project cli pents evidence {shell_quote(project.name)} {shell_quote(path_text(root, nodata_file))} "
                        f"--type active-dns-nodata --target {shell_quote(domain)} --file {shell_quote(path_text(root, nodata_file))} "
                        "--notes 'optional dnsx noerror/nodata review; compare with massdns hits'"
                    ),
                    "bash",
                )
            )

    command_lines = []
    for title, command, language in commands:
        rendered_command = command if language == "powershell" else timed_shell_command(command)
        command_lines.extend([f"### {title}", "", f"```{language}", rendered_command, "```", ""])

    canary_text = ", ".join(canary_targets) if canary_targets else "未提供；正式执行前必须补充至少 1 个已知存在子域，例如 ai.<domain>"
    nodata_text = "开启；对候选 FQDN 追加 dnsx NOERROR/NODATA 复核，可能显著增加耗时" if args.nodata_check else "关闭；默认只输出可解析入口命中"
    lines = [
        "# 主动 DNS 执行计划",
        "",
        "## 输入",
        "",
        f"- 根域：`{domain}`",
        f"- 字典：`{path_text(root, dict_path)}`（{count_lines(dict_path)} 行）",
        f"- Resolver：`{resolvers_csv}`",
        f"- 查询记录类型：`{','.join(record_types)}`",
        f"- massdns hashmap size：`{args.hashmap_size}`",
        f"- 兼容参数：dnsx retry=`{args.retry}`、timeout=`{args.timeout}`；puredns rate limit=`{args.rate_limit}` qps",
        f"- NODATA 复核：{nodata_text}",
        f"- Canary：{canary_text}",
        f"- 随机 NXDOMAIN：`{nx_targets[0]}`",
        f"- 选择引擎：`{active_dns_engine_label(engine)}`",
        "",
        "## 工具链",
        "",
        "- 默认主链路：`massdns direct`，先生成候选文件，再把候选文件作为 massdns 输入。",
        "- 默认只查询 `A` 记录；如需 IPv6/CNAME 入口线索，显式使用 `--record-types A,AAAA,CNAME`。",
        "- 脚本内置流程：canary 校验、resolver 自检、NXDOMAIN/wildcard 检查、候选生成、完整枚举、命中提取。",
        "- `puredns` 只作为可选 wrapper/人工诊断，不再让 Claude Code 默认执行，避免 puredns -> massdns stdin pipe 卡死。",
        "- `dnsx` 只作为可选诊断工具；只有开启 `--nodata-check` 时才追加 NOERROR/NODATA 复核。",
        "- 扫描脚本会记录每步 `elapsed`、退出码、候选数、命中数和 summary。",
        "- Windows/Claude Code 场景默认使用 PowerShell 脚本，不使用 Bash 管道。",
        "",
        *tool_rows,
        "",
        "## 停止条件",
        "",
        "- Canary 子域无命中：停止完整字典枚举，先排查 resolver、字典拼接和工具参数。",
        "- 随机 NXDOMAIN 有命中：停止并按泛解析/wildcard 场景处理。",
        "- 单个 resolver 超时或 0 响应：剔除该 resolver 后再进入完整枚举。",
        "- massdns direct 无输出但进程长时间存在：检查候选文件、resolver 文件和 massdns 输入文件参数，不再改用 puredns pipe。",
        "- `massdns` 缺失时不要假装已走主链路；先补齐项目本地工具。",
        "",
        "## 输出文件",
        "",
        f"- 计划：`{path_text(root, plan_file)}`",
        f"- 摘要：`{path_text(root, summary_file)}`",
        f"- 命中列表：`{path_text(root, hits_file)}`",
        f"- massdns 原始输出：`{path_text(root, raw_dir / 'active-dns-massdns.txt')}`",
        f"- metrics：`{path_text(root, output_dir / 'active-dns-metrics.json')}`",
        f"- summary：`{path_text(root, output_dir / 'active-dns-summary.json')}`",
        f"- 可选 NODATA 复核：`{path_text(root, nodata_file)}`",
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
        "- 记录类型差异：待执行后填写 A/AAAA/CNAME 命中差异。",
        "- dnsx NOERROR/NODATA 复核：未开启或待执行后填写；需对比 `dnsx_noerror_lines` 与 `massdns_hits`。",
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


def cmd_vision_review(args: argparse.Namespace) -> int:
    root = workspace_root()
    image_path = resolve_plain_path(root, args.image)
    if not image_path.exists() or not image_path.is_file():
        raise SystemExit(f"Image file not found: {image_path}")
    image_mime_type(image_path)
    loaded_env_files = load_env_files(root, args.env_file)

    started_at = now_text()
    start = time.monotonic()
    provider = args.provider
    base_url = args.base_url or os.environ.get("PENTS_VISION_BASE_URL", "https://api.openai.com/v1")
    model = args.model or os.environ.get("PENTS_VISION_MODEL", "")
    args.model = model
    args.token_param = args.token_param or os.environ.get("PENTS_VISION_TOKEN_PARAM", "")
    if not args.token_param and "api.xiaomimimo.com" in base_url:
        args.token_param = "max_completion_tokens"

    if args.mock or os.environ.get("PENTS_VISION_MOCK") == "1":
        record = vision_record(
            status="ok",
            mode="mock",
            provider=provider,
            model=model or "mock-vision",
            api_base_url=base_url,
            image_path=image_path,
            question=args.question,
            started_at=started_at,
            elapsed_ms=int((time.monotonic() - start) * 1000),
            result={
                "can_read_image": False,
                "blocker": "mock_mode_no_image_read",
                "page_type": "",
                "confidence": "low",
            },
            message="mock mode: no external API call was made",
            env_files_loaded=loaded_env_files,
        )
        emit_json_result(record, args.out)
        return 0

    api_key = os.environ.get(args.api_key_env, "").strip()
    if not api_key:
        record = vision_record(
            status="error",
            mode="api",
            provider=provider,
            model=model,
            api_base_url=base_url,
            image_path=image_path,
            question=args.question,
            started_at=started_at,
            elapsed_ms=int((time.monotonic() - start) * 1000),
            error_type="missing_api_key",
            message=f"environment variable {args.api_key_env} is not set",
            env_files_loaded=loaded_env_files,
        )
        emit_json_result(record, args.out)
        return 2
    if not model:
        record = vision_record(
            status="error",
            mode="api",
            provider=provider,
            model=model,
            api_base_url=base_url,
            image_path=image_path,
            question=args.question,
            started_at=started_at,
            elapsed_ms=int((time.monotonic() - start) * 1000),
            error_type="missing_model",
            message="set --model or PENTS_VISION_MODEL",
            env_files_loaded=loaded_env_files,
        )
        emit_json_result(record, args.out)
        return 2

    endpoint = openai_compatible_endpoint(base_url)
    payload = build_vision_payload(args, image_data_url(image_path))
    raw_preview = ""
    try:
        http_status, body = post_json(endpoint, payload, api_key, args.timeout)
        raw_preview = body
        response = json.loads(body)
        if not isinstance(response, dict):
            raise ValueError("API response is not a JSON object")
        model_text = openai_message_text(response)
        raw_preview = model_text
        model_result = json.loads(extract_json_payload(model_text))
        if not isinstance(model_result, dict):
            raise ValueError("model output is not a JSON object")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        record = vision_record(
            status="error",
            mode="api",
            provider=provider,
            model=model,
            api_base_url=base_url,
            image_path=image_path,
            question=args.question,
            started_at=started_at,
            elapsed_ms=int((time.monotonic() - start) * 1000),
            error_type="api_http_error",
            message=str(exc),
            http_status=exc.code,
            raw_text_preview=error_body,
            env_files_loaded=loaded_env_files,
        )
        emit_json_result(record, args.out)
        return 2
    except (urllib.error.URLError, TimeoutError) as exc:
        record = vision_record(
            status="error",
            mode="api",
            provider=provider,
            model=model,
            api_base_url=base_url,
            image_path=image_path,
            question=args.question,
            started_at=started_at,
            elapsed_ms=int((time.monotonic() - start) * 1000),
            error_type="api_timeout_or_network_error",
            message=str(exc),
            env_files_loaded=loaded_env_files,
        )
        emit_json_result(record, args.out)
        return 2
    except (json.JSONDecodeError, ValueError) as exc:
        record = vision_record(
            status="error",
            mode="api",
            provider=provider,
            model=model,
            api_base_url=base_url,
            image_path=image_path,
            question=args.question,
            started_at=started_at,
            elapsed_ms=int((time.monotonic() - start) * 1000),
            error_type="invalid_api_or_model_json",
            message=str(exc),
            raw_text_preview=raw_preview,
            env_files_loaded=loaded_env_files,
        )
        emit_json_result(record, args.out)
        return 2

    record = vision_record(
        status="ok",
        mode="api",
        provider=provider,
        model=model,
        api_base_url=base_url,
        image_path=image_path,
        question=args.question,
        started_at=started_at,
        elapsed_ms=int((time.monotonic() - start) * 1000),
        result=model_result,
        http_status=http_status,
        env_files_loaded=loaded_env_files,
    )
    emit_json_result(record, args.out)
    return 0


def first_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        return ""
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_string:
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return ""


def extract_json_payload(text: str) -> str:
    json_fence = re.search(r"```json\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    if json_fence:
        return json_fence.group(1).strip()
    any_fence = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if any_fence:
        return any_fence.group(1).strip()
    return first_json_object(text) or text.strip()


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
    missing_core: list[str] = []
    root = workspace_root()
    local_bin = local_tool_bin_dir(root)
    print("Recon 工具检查")
    print(f"当前环境：{platform_label()}")
    print(f"项目第三方工具目录：{local_bin}")
    print("查找顺序：tools/third-party/bin -> 系统 PATH。PATH 只作为 fallback，不是推荐安装位置。")
    print("主动 DNS 默认主链路：massdns direct 文件输入；puredns/dnsx/shuffledns 仅作为可选诊断或替代。")
    print("本机下载提示：涉及国外网络的拉取/下载，可在本机 PowerShell 临时设置 `$env:all_proxy='http://127.0.0.1:7890'`；不要把这个本机代理配置套到远端机器。")
    print("安装建议按环境区分：Windows/WSL/Linux/macOS 都优先写入项目第三方工具目录；全局 PATH 仅兜底。")
    print()

    for tool in RECON_TOOLS:
        path, source = find_recon_tool(root, tool["name"])
        status = "OK" if path else "MISSING"
        tier = tool.get("tier", "optional")
        if not path:
            missing.append(tool["name"])
            if tier == "active-dns-core":
                missing_core.append(tool["name"])
        print(f"[{status}] {tool['name']}")
        print(f"分级：{tier}")
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

    if missing_core:
        print("结论：主动 DNS 核心工具缺失。Claude Code 不得执行完整主动 DNS 枚举，必须先补齐 massdns direct 主链路。")
        return 2 if args.strict else 0

    if missing:
        print("结论：主动 DNS 核心工具已就绪；缺失项为可选/后处理工具，不应因此阻塞 massdns direct 主链路。")
        return 0

    print("结论：核心 recon 工具已找到。仍需确认授权窗口、resolver 和字典规模后再执行主动扫描。")
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

    vision_parser = subparsers.add_parser("vision-review", help="review a screenshot through a vision API and write JSON")
    vision_parser.add_argument("image", help="local screenshot path")
    vision_parser.add_argument("--question", required=True, help="narrow visual question to answer")
    vision_parser.add_argument("--context", action="append", default=[], help="optional context line, no secrets")
    vision_parser.add_argument("--out", default="", help="write JSON result to this file")
    vision_parser.add_argument("--provider", default="openai-compatible", choices=("openai-compatible",))
    vision_parser.add_argument("--base-url", default="", help="OpenAI-compatible base URL; defaults to PENTS_VISION_BASE_URL or OpenAI")
    vision_parser.add_argument("--model", default="", help="vision model; defaults to PENTS_VISION_MODEL")
    vision_parser.add_argument("--api-key-env", default="PENTS_VISION_API_KEY", help="environment variable that stores the API key")
    vision_parser.add_argument("--env-file", default="", help="load env vars from this file; defaults to .env and .env.local")
    vision_parser.add_argument("--timeout", type=int, default=30)
    vision_parser.add_argument("--max-tokens", type=int, default=1600)
    vision_parser.add_argument(
        "--token-param",
        choices=("max_tokens", "max_completion_tokens"),
        default="",
        help="token limit field name; official MiMo API examples use max_completion_tokens",
    )
    vision_parser.add_argument("--json-mode", action="store_true", help="send response_format=json_object when provider supports it")
    vision_parser.add_argument("--mock", action="store_true", help="validate JSON output shape without calling any external API")
    vision_parser.set_defaults(func=cmd_vision_review)

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
    active_dns_parser.add_argument("--engine", choices=("auto", "massdns", "puredns", "shuffledns", "dnsx"), default="auto")
    active_dns_parser.add_argument("--record-types", default="A", help="comma-separated massdns record types: A,AAAA,CNAME")
    active_dns_parser.add_argument("--threads", default="1000", help="dnsx fallback thread count")
    active_dns_parser.add_argument("--hashmap-size", default="10000", help="massdns direct concurrent lookup hashmap size")
    active_dns_parser.add_argument("--rate-limit", default="10000", help="puredns public resolver rate limit in qps")
    active_dns_parser.add_argument("--retry", default="1")
    active_dns_parser.add_argument("--timeout", default="2")
    active_dns_parser.add_argument("--verify-retry", default="2", help="dnsx retry count for final hit verification")
    active_dns_parser.add_argument("--verify-timeout", default="3", help="dnsx timeout for final hit verification")
    active_dns_parser.add_argument("--nodata-check", action="store_true", help="append optional dnsx NOERROR/NODATA review against generated candidates")
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
