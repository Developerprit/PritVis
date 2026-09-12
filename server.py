#!/usr/bin/env python3
"""
PritVis - Visualization Framework Server
Runs on port 5026, parses .zip projects from vp/ and serves them via HTTP.
"""
import json
import os
import re
import shutil
import sys
import time
import urllib.parse
import zipfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
VP_DIR = ROOT / "vp"
PLUGIN_DIR = ROOT / "plugin"
DATA_DIR = ROOT / "data"
CONFIG_FILE = DATA_DIR / "config.json"
TEMP_DIR = ROOT / ".tmp"
PORT = 5026

# Ensure required directories exist
VP_DIR.mkdir(exist_ok=True)
PLUGIN_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Security scan patterns
DANGEROUS_PATTERNS = {
    "dangerous": [
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"\bcompile\s*\(",
        r"\b__import__\s*\(",
        r"os\.system",
        r"subprocess\.(call|run|Popen|check_output)",
        r"socket\.socket",
        r"urllib\.request",
        r"requests\.(get|post|put|delete|request)",
        r"platform\.system",
        r"os\.remove\s*\(",
        r"shutil\.rmtree",
        r"open\s*\(.*['\"]w",
        r"open\s*\(.*['\"]a",
        r"document\.write\s*\(",
        r"\.innerHTML\s*=",
        r"<script[^>]*>[^<]*eval",
        r"new\s+Function\s*\(",
        r"setTimeout\s*\(\s*['\"]",
        r"setInterval\s*\(\s*['\"]",
    ],
    "warning": [
        r"\bimport\s+os\b",
        r"\bimport\s+sys\b",
        r"\bimport\s+subprocess\b",
        r"\bimport\s+socket\b",
        r"\bimport\s+requests\b",
        r"\bimport\s+urllib\b",
        r"\bfrom\s+os\b",
        r"\bfrom\s+sys\b",
        r"\bfrom\s+subprocess\b",
        r"\.\./",
        r"\.\.\\\\",
        r"~/",
        r"C:\\\\Windows",
        r"/etc/",
        r"localStorage\.",
        r"fetch\s*\(",
        r"XMLHttpRequest",
        r"WebSocket",
    ],
}


def load_config():
    """Load or initialize config file."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"theme": "dark", "scan_results": {}, "trusted": {}}


def save_config(config):
    """Persist config file."""
    CONFIG_FILE.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def list_projects():
    """Return all .zip projects in vp/."""
    projects = []
    if VP_DIR.exists():
        for f in sorted(VP_DIR.iterdir()):
            if f.suffix.lower() == ".zip":
                projects.append(
                    {
                        "name": f.stem,
                        "filename": f.name,
                        "size": f.stat().st_size,
                        "status": get_project_status(f.stem),
                    }
                )
    return projects


def get_project_status(name):
    """Compute display status for a project."""
    config = load_config()
    if config.get("trusted", {}).get(name, False):
        return "trusted"
    result = config.get("scan_results", {}).get(name)
    if result:
        return result.get("status", "unscanned")
    return "unscanned"


def scan_zip(name):
    """Perform static security scan on a .zip project."""
    zf = VP_DIR / f"{name}.zip"
    if not zf.exists():
        return {"error": "Project not found"}

    findings = {"dangerous": [], "warning": []}
    total_files = {"py": 0, "js": 0, "html": 0}

    try:
        with zipfile.ZipFile(zf, "r") as z:
            for info in z.infolist():
                fname = info.filename.lower()
                if not (fname.endswith(".py") or fname.endswith(".js") or fname.endswith(".html")):
                    continue
                if fname.endswith(".py"):
                    total_files["py"] += 1
                elif fname.endswith(".js"):
                    total_files["js"] += 1
                elif fname.endswith(".html"):
                    total_files["html"] += 1

                try:
                    content = z.read(info.filename).decode("utf-8", errors="ignore")
                except Exception:
                    continue

                lines = content.splitlines()
                for category, patterns in DANGEROUS_PATTERNS.items():
                    for pattern in patterns:
                        regex = re.compile(pattern, re.IGNORECASE)
                        for i, line in enumerate(lines, 1):
                            if regex.search(line):
                                findings[category].append(
                                    {
                                        "file": info.filename,
                                        "line": i,
                                        "content": line.strip(),
                                        "pattern": pattern,
                                    }
                                )
    except Exception as e:
        return {"error": str(e)}

    if findings["dangerous"]:
        status = "dangerous"
    elif findings["warning"]:
        status = "warning"
    else:
        status = "safe"

    result = {
        "name": name,
        "status": status,
        "total_files": total_files,
        "findings": findings,
        "scanned_at": int(time.time()),
    }

    config = load_config()
    config.setdefault("scan_results", {})[name] = result
    save_config(config)
    return result


def extract_project(name):
    """Extract project zip to temp directory."""
    target = TEMP_DIR / name
    zf = VP_DIR / f"{name}.zip"
    if not zf.exists():
        return None
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zf, "r") as z:
        z.extractall(target)
    return target


def find_entry(project_dir):
    """Find index.html inside extracted project."""
    for f in project_dir.rglob("index.html"):
        return f
    return None


class Handler(BaseHTTPRequestHandler):
    """Custom HTTP request handler."""

    def log_message(self, fmt, *args):
        # Minimal request logging to stdout
        sys.stdout.write(f"[{self.log_date_time_string()}] {args[0]}\n")

    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type=None):
        p = Path(path)
        if not p.exists() or not p.is_file():
            self.send_error(404)
            return

        if content_type is None:
            ext = p.suffix.lower()
            mapping = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".json": "application/json; charset=utf-8",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".svg": "image/svg+xml",
                ".ico": "image/x-icon",
                ".txt": "text/plain; charset=utf-8",
                ".md": "text/markdown; charset=utf-8",
                ".zip": "application/zip",
            }
            content_type = mapping.get(ext, "application/octet-stream")

        data = p.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return self.rfile.read(length).decode("utf-8")
        return ""

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        # Main UI
        if path in ("/", "/index.html"):
            self._send_file(ROOT / "index.html")
            return

        # Static assets
        if path.startswith("/static/"):
            self._send_file(ROOT / path.lstrip("/"))
            return

        # Plugins served as static files
        if path.startswith("/plugin/"):
            self._send_file(ROOT / path.lstrip("/"))
            return

        # API: list projects
        if path == "/api/projects":
            self._send_json(list_projects())
            return

        # API: list plugins
        if path == "/api/plugins":
            plugins = []
            if PLUGIN_DIR.exists():
                for f in sorted(PLUGIN_DIR.iterdir()):
                    if f.suffix.lower() == ".js":
                        plugins.append({"name": f.stem, "filename": f.name})
            self._send_json(plugins)
            return

        # API: config
        if path == "/api/config":
            self._send_json(load_config())
            return

        # Serve project: /project/{name}/ -> index.html
        if re.match(r"^/project/[^/]+/$", path):
            name = path.split("/")[2]
            project_dir = extract_project(name)
            if not project_dir:
                self.send_error(404)
                return
            entry = find_entry(project_dir)
            if not entry:
                self.send_error(404)
                return
            self._send_file(entry)
            return

        # Serve project files: /project/{name}/path/to/file
        m = re.match(r"^/project/([^/]+)/(.*)$", path)
        if m:
            name, rest = m.group(1), m.group(2)
            project_dir = TEMP_DIR / name
            if not project_dir.exists():
                project_dir = extract_project(name)
            if not project_dir:
                self.send_error(404)
                return

            target = (project_dir / rest).resolve()
            # Prevent directory traversal outside project_dir
            if not str(target).startswith(str(project_dir.resolve())):
                self.send_error(403)
                return

            self._send_file(target)
            return

        self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        # Scan project
        if path.startswith("/api/scan/"):
            name = path[len("/api/scan/") :]
            self._send_json(scan_zip(name))
            return

        # Trust project
        if path.startswith("/api/trust/"):
            name = path[len("/api/trust/") :]
            config = load_config()
            config.setdefault("trusted", {})[name] = True
            save_config(config)
            self._send_json({"name": name, "trusted": True})
            return

        # Update config
        if path == "/api/config":
            body = self._read_body()
            try:
                incoming = json.loads(body)
                config = load_config()
                config.update(incoming)
                save_config(config)
                self._send_json(load_config())
            except Exception as e:
                self._send_json({"error": str(e)}, 400)
            return

        self.send_error(404)


def main():
    save_config(load_config())
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[PritVis] Server running at http://localhost:{PORT}")
    print(f"[PritVis] Put .zip projects into: {VP_DIR}")
    print(f"[PritVis] Put .js plugins into: {PLUGIN_DIR}")
    print("[PritVis] Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[PritVis] Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
