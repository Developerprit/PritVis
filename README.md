# PritVis

> **PritVis is a framework tool that can turn any code or anything into a visualization.**

[中文说明](./README-zh.md)

PritVis is a local visualization framework. Drop any HTML + Python project as a `.zip` into the `vp/` folder, and PritVis will parse it, scan it for suspicious code patterns, and present it in a clean project launcher. Click a project to load it instantly in the built-in viewer. JS plugins in `plugin/` can extend the shell even further.

## Features

- **Local HTTP server** running on port `5026`
- **Project launcher** — left sidebar lists every `.zip` inside `vp/`
- **Security scan** — static analysis of Python, JavaScript and HTML files before first load
- **Light / dark themes** — terminal-green aesthetic, monospace typography
- **JS plugin system** — auto-load `plugin/*.js` via `window.PritVis.registerPlugin()`
- **Zero build step** — pure Python standard library + vanilla HTML/CSS/JS

## Quick Start

```bash
# 1. Clone or download the project
cd PritVis

# 2. Start the server
python server.py

# 3. Open http://localhost:5026 in your browser
```

Put your visualization projects into `vp/` as `.zip` files. Each zip should contain at least an `index.html`.

## Project Format

A PritVis project is a zip archive with loose structure:

```
my-viz.zip
├── index.html      # required — entry point
├── main.py         # optional — Python logic / metadata
└── assets/
    └── style.css
```

PritVis extracts the zip, finds `index.html`, and serves the project under `/project/{name}/`.

## Security Scan

Before a project is loaded for the first time, PritVis scans its code for:

- Dangerous calls: `eval`, `exec`, `os.system`, `subprocess.*`, `socket.*`, raw `innerHTML`, etc.
- Suspicious imports: `os`, `sys`, `subprocess`, `requests`, `urllib`
- Path traversal: `../`, `/etc/`, `C:\Windows`, etc.
- Network / storage APIs in JS

Results are cached in `data/config.json`. Projects marked **dangerous** require explicit user trust before loading.

## Plugin API

Create a file in `plugin/`:

```javascript
window.PritVis.registerPlugin({
    id: 'my.plugin',
    name: 'My Plugin',
    init() { console.log('Plugin ready'); },
    onProjectLoad(project) { console.log('Loaded', project.name); }
});
```

Supported lifecycle hooks:

- `init()` — called once when the plugin is loaded
- `onProjectLoad(project)` — called whenever a project is loaded into the viewer

## HTTP API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects` | GET | List all projects in `vp/` |
| `/api/scan/{name}` | POST | Scan a project for suspicious patterns |
| `/api/trust/{name}` | POST | Trust a project and allow loading |
| `/api/plugins` | GET | List all plugins in `plugin/` |
| `/api/config` | GET/POST | Read or update configuration |
| `/project/{name}/` | GET | Load project's `index.html` |
| `/project/{name}/{path}` | GET | Serve static files from project |

## Tech Stack

- Python 3.13+ (`http.server`, `zipfile`, `json`)
- Vanilla HTML5 / CSS3 / JavaScript
- No external dependencies

## License

Available License — see [https://license.kscm.top/available.md](https://license.kscm.top/available.md).

## Roadmap

- [ ] Python cloud-function bridge for Retinbox hosting
- [ ] Plugin UI injection API
- [ ] Project import via browser drag & drop
- [ ] Export project manifest
