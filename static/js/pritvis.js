/**
 * PritVis frontend core
 * Handles project gallery, security scan UI, iframe loading, theme and plugins.
 */
(function () {
    const state = {
        projects: [],
        plugins: [],
        config: {},
        currentProject: null,
        pendingProject: null
    };

    const els = {
        projectList: document.getElementById('project-list'),
        projectCount: document.getElementById('project-count'),
        viewer: document.getElementById('viewer'),
        emptyStage: document.getElementById('empty-stage'),
        statusProject: document.getElementById('status-project'),
        statusState: document.getElementById('status-state'),
        statusPlugins: document.getElementById('status-plugins'),
        securityModal: document.getElementById('security-modal'),
        scanTitle: document.getElementById('scan-title'),
        scanBody: document.getElementById('scan-body'),
        btnTrustLoad: document.getElementById('btn-trust-load'),
        btnCancelLoad: document.getElementById('btn-cancel-load'),
        pluginsModal: document.getElementById('plugins-modal'),
        pluginList: document.getElementById('plugin-list'),
        themeIcon: document.getElementById('theme-icon')
    };

    /**
     * Public plugin API.
     * Plugins in plugin/*.js can call window.PritVis.registerPlugin({...}).
     */
    window.PritVis = {
        version: '0.1.0',
        plugins: [],

        registerPlugin(plugin) {
            if (!plugin || !plugin.id) {
                console.warn('[PritVis] Plugin rejected: missing id');
                return;
            }
            this.plugins.push(plugin);
            console.log(`[PritVis] Plugin registered: ${plugin.id}`);
            if (typeof plugin.init === 'function') {
                try {
                    plugin.init();
                } catch (err) {
                    console.error(`[PritVis] Plugin init error (${plugin.id}):`, err);
                }
            }
        },

        emit(eventName, data) {
            this.plugins.forEach(p => {
                if (typeof p[eventName] === 'function') {
                    try {
                        p[eventName](data);
                    } catch (err) {
                        console.error(`[PritVis] Plugin event error (${p.id}):`, err);
                    }
                }
            });
        }
    };

    async function init() {
        state.config = await API.getConfig();
        applyTheme(state.config.theme || 'dark');
        bindEvents();
        await Promise.all([loadProjects(), loadPlugins()]);
        setStatus('idle');
    }

    function applyTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        state.config.theme = theme;
        if (els.themeIcon) {
            els.themeIcon.textContent = theme === 'dark' ? '◐' : '◑';
        }
    }

    async function toggleTheme() {
        const next = state.config.theme === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        await API.saveConfig(state.config);
    }

    async function loadProjects() {
        state.projects = await API.getProjects();
        renderProjects();
    }

    function renderProjects() {
        els.projectCount.textContent = state.projects.length;

        if (state.projects.length === 0) {
            els.projectList.innerHTML = `
                <div class="empty-state-mini">
                    <p>No projects in <code>vp/</code></p>
                    <p class="hint">Drop a .zip and refresh.</p>
                </div>`;
            return;
        }

        els.projectList.innerHTML = state.projects.map(p => `
            <div class="project-item ${state.currentProject === p.name ? 'active' : ''}" data-name="${escapeHtml(p.name)}">
                <div class="project-icon">✦</div>
                <div class="project-info">
                    <span class="project-name">${escapeHtml(p.name)}</span>
                    <span class="project-meta">${formatBytes(p.size)}</span>
                </div>
                <span class="badge ${p.status}">${p.status}</span>
            </div>
        `).join('');

        els.projectList.querySelectorAll('.project-item').forEach(item => {
            item.addEventListener('click', () => onProjectClick(item.dataset.name));
        });
    }

    async function onProjectClick(name) {
        const project = state.projects.find(p => p.name === name);
        if (!project) return;

        state.pendingProject = project;
        setStatus('loading');
        renderProjects();

        const result = await API.scanProject(name);
        if (result.error) {
            alert(`Scan failed: ${result.error}`);
            setStatus('idle');
            state.pendingProject = null;
            renderProjects();
            return;
        }

        const isTrusted = state.config.trusted && state.config.trusted[name];
        if (result.status === 'safe' || isTrusted) {
            await loadProject(project);
        } else {
            showSecurityModal(result);
        }
    }

    function showSecurityModal(result) {
        els.scanTitle.textContent = `Security Scan: ${result.name}`;
        const dangerousCount = result.findings.dangerous.length;
        const warningCount = result.findings.warning.length;
        const total = result.total_files.py + result.total_files.js + result.total_files.html;

        let html = `
            <div class="scan-summary">
                <span class="badge ${result.status}">${result.status}</span>
                <span class="scan-counts">
                    ${total} file${total === 1 ? '' : 's'} scanned
                    · ${dangerousCount} dangerous · ${warningCount} warning
                </span>
            </div>`;

        if (dangerousCount > 0) {
            html += renderFindingGroup('dangerous', result.findings.dangerous);
        }
        if (warningCount > 0) {
            html += renderFindingGroup('warning', result.findings.warning);
        }
        if (dangerousCount === 0 && warningCount === 0) {
            html += `<p class="scan-status">No suspicious patterns found.</p>`;
        }

        els.scanBody.innerHTML = html;
        els.securityModal.classList.remove('hidden');
    }

    function renderFindingGroup(category, items) {
        if (items.length === 0) return '';
        const display = items.slice(0, 50);
        return `
            <div class="finding-group">
                <h4>${category} (${items.length})</h4>
                <ul class="finding-list ${category}">
                    ${display.map(f => `
                        <li>
                            <span class="finding-file">${escapeHtml(f.file)}</span>
                            <span class="finding-line">line ${f.line}</span>
                            <code class="finding-code">${escapeHtml(f.content)}</code>
                        </li>
                    `).join('')}
                </ul>
            </div>`;
    }

    async function loadProject(project) {
        state.currentProject = project.name;
        state.pendingProject = null;
        els.viewer.src = `/project/${encodeURIComponent(project.name)}/`;
        els.viewer.classList.add('active');
        els.emptyStage.classList.add('hidden');
        renderProjects();
        setStatus('active');
        els.statusProject.textContent = project.name;
        window.PritVis.emit('onProjectLoad', project);
    }

    function setStatus(name) {
        els.statusState.className = `state ${name}`;
        els.statusState.textContent = name;
    }

    function bindEvents() {
        document.getElementById('btn-refresh').addEventListener('click', loadProjects);
        document.getElementById('btn-theme').addEventListener('click', toggleTheme);
        document.getElementById('btn-plugins').addEventListener('click', showPluginsModal);

        document.querySelectorAll('.modal-close, .modal-close-btn').forEach(btn => {
            btn.addEventListener('click', closeModals);
        });

        els.btnCancelLoad.addEventListener('click', () => {
            state.pendingProject = null;
            closeModals();
            setStatus('idle');
            renderProjects();
        });

        els.btnTrustLoad.addEventListener('click', async () => {
            if (!state.pendingProject) return;
            await API.trustProject(state.pendingProject.name);
            state.config = await API.getConfig();
            closeModals();
            await loadProject(state.pendingProject);
        });

        // Close modal on backdrop click
        document.querySelectorAll('.modal-backdrop').forEach(bg => {
            bg.addEventListener('click', closeModals);
        });
    }

    function closeModals() {
        els.securityModal.classList.add('hidden');
        els.pluginsModal.classList.add('hidden');
    }

    async function loadPlugins() {
        state.plugins = await API.getPlugins();
        els.statusPlugins.textContent = `${state.plugins.length} plugin${state.plugins.length === 1 ? '' : 's'}`;

        for (const plugin of state.plugins) {
            try {
                await loadPluginScript(plugin.filename);
            } catch (err) {
                console.error(`[PritVis] Failed to load plugin ${plugin.filename}:`, err);
            }
        }
    }

    function loadPluginScript(filename) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = `/plugin/${encodeURIComponent(filename)}`;
            script.onload = () => resolve();
            script.onerror = () => reject(new Error(`Could not load ${filename}`));
            document.body.appendChild(script);
        });
    }

    function showPluginsModal() {
        if (state.plugins.length === 0) {
            els.pluginList.innerHTML = '<li style="color:var(--text-muted)">No plugins in plugin/</li>';
        } else {
            els.pluginList.innerHTML = state.plugins.map(p => `
                <li>
                    <span class="plugin-name">${escapeHtml(p.name)}</span>
                    <span class="plugin-file">${escapeHtml(p.filename)}</span>
                </li>
            `).join('');
        }
        els.pluginsModal.classList.remove('hidden');
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatBytes(bytes) {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    init();
})();
