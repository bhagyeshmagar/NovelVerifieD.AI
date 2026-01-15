import React from 'react';

const GlassCard = ({ children, className = "", hoverEffect = false, onClick, style }) => (
    <div
        onClick={onClick}
        style={style}
        className={`
      relative
      bg-white/10 
      backdrop-blur-md 
      border border-white/20 
      shadow-xl 
      rounded-2xl 
      text-white
      ${hoverEffect ? 'transition-transform duration-300 hover:-translate-y-1 hover:bg-white/15' : ''}
      ${onClick ? 'cursor-pointer' : ''}
      ${className}
    `}
    >
        {/* Subtle gradient overlay for depth */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none rounded-2xl" />
        <div className="relative z-10 h-full flex flex-col">
            {children}
        </div>
    </div>
);

export default GlassCard;
