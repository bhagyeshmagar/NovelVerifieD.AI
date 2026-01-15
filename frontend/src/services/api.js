const API_BASE = '/api';

export const api = {
    // Stats
    getStats: async () => {
        const res = await fetch(`${API_BASE}/stats`);
        if (!res.ok) {
            // Return empty stats on error
            return { total: 0, supported: 0, contradicted: 0, accuracy: null, avg_confidence: 0 };
        }
        return res.json();
    },

    // Results
    getResults: async () => {
        const res = await fetch(`${API_BASE}/results`);
        if (!res.ok) {
            // Return empty results on error
            return { total: 0, results: [] };
        }
        return res.json();
    },

    getVerdict: async (id) => {
        const res = await fetch(`${API_BASE}/verdict/${id}`);
        return res.json();
    },

    getDossier: async (id) => {
        const res = await fetch(`${API_BASE}/dossier/${id}`);
        return res.json();
    },

    getEvidence: async (id) => {
        const res = await fetch(`${API_BASE}/evidence/${id}`);
        return res.json();
    },

    // Pipeline
    startPipeline: async (clean = true) => {
        const res = await fetch(`${API_BASE}/pipeline/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clean }),
        });
        return res.json();
    },

    stopPipeline: async () => {
        const res = await fetch(`${API_BASE}/pipeline/cancel`, { method: 'POST' });
        return res.json();
    },

    getPipelineStatus: async () => {
        const res = await fetch(`${API_BASE}/pipeline/status`);
        return res.json();
    },

    resetPipeline: async () => {
        const res = await fetch(`${API_BASE}/pipeline/reset`, { method: 'POST' });
        return res.json();
    }
};
