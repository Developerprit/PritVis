# PritVis

> **PritVis 是一个能把任何代码或任何东西变成可视化的框架工具。**

[English README](./README.md)

PritVis 是一个本地可视化框架。把任意 HTML + Python 项目打包成 `.zip`，放进 `vp/` 文件夹，PritVis 会自动解析、扫描可疑代码模式，并在左侧项目启动器中展示。点击项目即可在内置查看器中加载运行。`plugin/` 目录下的 JS 插件可以进一步扩展外壳能力。

## 特性

- **本地 HTTP 服务**，监听端口 `5026`
- **项目启动器** — 左侧边栏列出 `vp/` 内所有 `.zip`
- **安全扫描** — 首次加载前对 Python、JavaScript、HTML 做静态分析
- **浅色 / 深色主题** — 终端绿风格，等宽字体
- **JS 插件系统** — 自动加载 `plugin/*.js`，通过 `window.PritVis.registerPlugin()` 注册
- **零构建步骤** — 纯 Python 标准库 + 原生 HTML/CSS/JS

## 快速开始

```bash
# 1. 克隆或下载项目
cd PritVis

# 2. 启动服务
python server.py

# 3. 浏览器打开 http://localhost:5026
```

把你的可视化项目以 `.zip` 形式放进 `vp/`。每个 zip 至少包含一个 `index.html`。

## 项目格式

PritVis 项目采用松散结构：

```
my-viz.zip
├── index.html      # 必填 — 入口页面
├── main.py         # 可选 — Python 逻辑 / 元数据
└── assets/
    └── style.css
```

PritVis 会解压 zip，找到 `index.html`，并通过 `/project/{name}/` 提供服务。

## 安全扫描

项目首次加载前，PritVis 会扫描代码中的：

- 危险调用：`eval`、`exec`、`os.system`、`subprocess.*`、`socket.*`、原生 `innerHTML` 等
- 可疑导入：`os`、`sys`、`subprocess`、`requests`、`urllib`
- 路径遍历：`../`、`/etc/`、`C:\Windows` 等
- JS 中的网络 / 存储 API

扫描结果缓存在 `data/config.json` 中。标记为 **dangerous** 的项目需要用户显式信任才能加载。

## 插件 API

在 `plugin/` 中创建文件：

```javascript
window.PritVis.registerPlugin({
    id: 'my.plugin',
    name: 'My Plugin',
    init() { console.log('Plugin ready'); },
    onProjectLoad(project) { console.log('Loaded', project.name); }
});
```

支持的生命周期钩子：

- `init()` — 插件加载时调用一次
- `onProjectLoad(project)` — 每次项目加载到查看器时调用

## HTTP API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/projects` | GET | 列出 `vp/` 下所有项目 |
| `/api/scan/{name}` | POST | 扫描指定项目的可疑模式 |
| `/api/trust/{name}` | POST | 信任项目并允许加载 |
| `/api/plugins` | GET | 列出 `plugin/` 下所有插件 |
| `/api/config` | GET/POST | 读取或更新配置 |
| `/project/{name}/` | GET | 加载项目的 `index.html` |
| `/project/{name}/{path}` | GET | 服务项目内的静态文件 |

## 技术栈

- Python 3.13+（`http.server`、`zipfile`、`json`）
- 原生 HTML5 / CSS3 / JavaScript
- 无外部依赖

## 许可证

Available License — 详见 [https://license.kscm.top/available.md](https://license.kscm.top/available.md)。

## 路线图

- [ ] Retinbox 云函数桥接
- [ ] 插件 UI 注入 API
- [ ] 浏览器拖拽导入项目
- [ ] 导出项目清单
