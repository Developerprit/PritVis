/**
 * PritVis Example Plugin
 * Demonstrates the plugin API by logging project loads to the console.
 */
window.PritVis.registerPlugin({
    id: 'example.logger',
    name: 'Example Logger',
    version: '0.1.0',

    init() {
        console.log('[Example Plugin] Initialized');
    },

    onProjectLoad(project) {
        console.log(`[Example Plugin] Loaded project: ${project.name} (${project.size} bytes)`);
    }
});
