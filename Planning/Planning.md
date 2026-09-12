# PritVis 项目规划

> PritVis is a framework tool that can turn any code or anything into a visualization.

## 1. 项目定位

PritVis 是一个本地可视化框架。用户把任意 HTML + Python 项目打包成 `.zip`，放进 `vp/` 目录；PritVis 自动解析、安全扫描，并在左侧集合栏展示。点击即可在右侧主区域加载运行该可视化项目。同时支持 `plugin/` 目录下的 JS 插件自动扩展。

## 2. 已确认技术细节

| 问题 | 用户选择 |
|------|---------|
| 运行形态 | 本地 HTTP 服务，Python 后端监听 **5026** 端口 |
| zip 项目结构 | 松散约定式：必须包含 `index.html`；Python 文件自动探测第一个 `.py` |
| 安全检测 | 本地静态规则扫描（危险 import、敏感系统调用、可疑关键字、路径遍历） |
| 插件机制 | 自动加载 `plugin/*.js`，按 `window.PritVis.registerPlugin` 注册 |

## 3. 技术栈

- **后端**：Python 3.13.12（managed），标准库 `http.server` + `zipfile` + `json`
- **前端**：原生 HTML5 / CSS3 / JavaScript，不使用任何外部构建工具
- **UI 设计**：Impeccable 前端设计技能，深色/浅色双主题
- **安全扫描**：纯本地正则/关键字规则，不依赖第三方 API
- **数据持久化**：JSON 配置文件 `data/config.json`，记录已扫描结果与主题设置
- **部署目标**：本地运行；代码同时保持向 Retinbox 云函数迁移的可能性

## 4. 目录结构

```
E:\PC\PritVis\
├── server.py              # Python HTTP 服务入口，端口 5026
├── index.html             # 主界面
├── static/
│   ├── css/
│   │   └── pritvis.css    # 主题与布局样式
│   └── js/
│       ├── pritvis.js     # 核心交互逻辑
│       └── api.js         # 与后端通信封装
├── plugin/
│   └── example-plugin.js  # 示例插件
├── vp/
│   └── demo.zip           # 示例可视化项目
├── data/
│   └── config.json        # 本地配置与扫描缓存
├── README.md              # 英文 README
├── README-zh.md           # 中文 README
├── PritVis.html           # 商业风格公开落地页
└── Planning/
    └── Planning.md        # 本文档
```

## 5. 核心功能模块

### 5.1 HTTP API（后端）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/projects` | GET | 扫描 `vp/` 下所有 `.zip`，返回项目列表（名称、大小、安全状态） |
| `/api/project/{name}` | GET | 解压指定 zip 到临时目录，返回入口 `index.html` 内容或文件树 |
| `/api/project/{name}/file/{path}` | GET | 代理 zip 内静态资源（CSS/JS/图片等） |
| `/api/scan/{name}` | POST | 对指定 zip 执行本地静态安全扫描 |
| `/api/plugins` | GET | 扫描 `plugin/` 下所有 `.js`，返回插件列表 |
| `/api/config` | GET/POST | 读取/保存用户配置（主题、已确认安全项目等） |

### 5.2 安全扫描规则

扫描 zip 解压后的所有 `.py` 文件：

- 危险内置函数：`exec`, `eval`, `compile`, `__import__`, `os.system`, `subprocess.call`, `subprocess.run`, `subprocess.Popen`
- 敏感模块：`os`, `sys`, `subprocess`, `socket`, `requests`, `urllib`
- 文件系统越界：`..`, `/etc/`, `C:\Windows`, `~`, `regedit`
- 网络/加密可疑行为：`socket.socket`, `requests.get`, `urllib.request`
- 结果分级：`safe` / `warning` / `dangerous`

> 第一次打开项目时弹出扫描结果；用户可勾选「信任此项目」后加载。

### 5.3 前端界面

- 顶部：标题、主题切换、插件入口、刷新按钮
- 左侧集合栏：`vp/` 下所有可视化项目列表，带状态图标
- 右侧主区域：iframe 加载当前选中项目的 `index.html`
- 底部状态栏：当前项目名、安全状态、端口信息

### 5.4 JS 插件系统

- 自动加载 `plugin/*.js`
- 全局对象：`window.PritVis`
- 注册 API：`window.PritVis.registerPlugin({ id, name, init() {}, onProjectLoad(project) {} })`
- 插件可向侧边栏追加按钮、在主区域上方添加工具条、监听项目加载事件

## 6. 设计约束

- 颜色禁用蓝紫/AI 配色，采用终端绿 + 等宽字体风格
- 浅色/深色双主题
- 不依赖外部 npm/前端框架，保证本地双击即可运行
- 不使用 base64 编码传输资源（遵循 AGENTS.md）
- 代码保持中英文关键注释

## 7. 交付物清单

- [ ] `server.py`（可运行）
- [ ] `index.html` + `static/css/pritvis.css` + `static/js/pritvis.js` + `static/js/api.js`
- [ ] `plugin/example-plugin.js`
- [ ] `vp/demo.zip`
- [ ] `data/config.json`
- [ ] `README.md` / `README-zh.md`
- [ ] `PritVis.html` 商业落地页
- [ ] GitHub 推送（若仓库存在）

## 8. 下一步行动

1. 创建目录结构
2. 实现 Python 后端与 API
3. 用 Impeccable 技能实现前端
4. 接入插件系统
5. 打包示例项目
6. 验证运行
7. 编写 README 与落地页
8. 推送 GitHub
