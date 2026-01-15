import React from 'react';

const Badge = ({ type, text }) => {
    const styles = {
        consistent: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
        contradicted: "bg-rose-500/20 text-rose-300 border-rose-500/30",
        processing: "bg-blue-500/20 text-blue-300 border-blue-500/30",
        pending: "bg-gray-500/20 text-gray-400 border-gray-500/30",
        success: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
        danger: "bg-rose-500/20 text-rose-300 border-rose-500/30"
    };

    const defaultLabels = {
        consistent: "Consistent",
        contradicted: "Contradicted",
        processing: "Analyzing...",
        pending: "Queued",
        success: "Success",
        danger: "Failed"
    };

    // Map 1/0 to consistent/contradicted if numbers are passed
    let safeType = type;
    if (type === 1) safeType = 'consistent';
    if (type === 0) safeType = 'contradicted';

    // Normalize string inputs (e.g. "Supported" -> "consistent")
    if (typeof safeType === 'string') {
        const lower = safeType.toLowerCase();
        if (lower.includes('support')) safeType = 'consistent';
        if (lower.includes('contradict')) safeType = 'contradicted';
    }

    const styleClass = styles[safeType] || styles.pending;
    const label = text || defaultLabels[safeType] || safeType;

    return (
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styleClass}`}>
            {label}
        </span>
    );
};

export default Badge;
