/**
 * PritVis API client
 * Wraps backend HTTP endpoints for projects, plugins, config and scanning.
 */
const API = {
    async getProjects() {
        const res = await fetch('/api/projects');
        return res.json();
    },

    async getPlugins() {
        const res = await fetch('/api/plugins');
        return res.json();
    },

    async getConfig() {
        const res = await fetch('/api/config');
        return res.json();
    },

    async saveConfig(config) {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        return res.json();
    },

    async scanProject(name) {
        const res = await fetch(`/api/scan/${encodeURIComponent(name)}`, {
            method: 'POST'
        });
        return res.json();
    },

    async trustProject(name) {
        const res = await fetch(`/api/trust/${encodeURIComponent(name)}`, {
            method: 'POST'
        });
        return res.json();
    }
};
