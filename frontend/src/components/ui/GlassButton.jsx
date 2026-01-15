import React from 'react';

const GlassButton = ({ children, onClick, variant = 'primary', className = "", disabled = false }) => {
    const variants = {
        primary: "bg-blue-600/80 hover:bg-blue-500/90 border-blue-400/30 text-white shadow-[0_0_15px_rgba(37,99,235,0.3)]",
        danger: "bg-red-500/80 hover:bg-red-400/90 border-red-400/30 text-white shadow-[0_0_15px_rgba(239,68,68,0.3)]",
        ghost: "bg-white/5 hover:bg-white/10 border-white/10 text-blue-100",
        success: "bg-emerald-500/80 hover:bg-emerald-400/90 border-emerald-400/30 text-white shadow-[0_0_15px_rgba(16,185,129,0.3)]"
    };

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={`
        px-4 py-2 rounded-xl font-medium 
        backdrop-blur-sm border shadow-lg 
        transition-all duration-200 active:scale-95
        disabled:opacity-50 disabled:cursor-not-allowed
        flex items-center justify-center gap-2
        ${variants[variant]}
        ${className}
      `}
        >
            {children}
        </button>
    );
};

export default GlassButton;
