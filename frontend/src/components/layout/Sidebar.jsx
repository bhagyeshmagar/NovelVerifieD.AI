import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Play,
  FileText,
  BookOpen,
  ChevronRight,
  Menu,
  X
} from 'lucide-react';

const Sidebar = ({ isOpen, onClose }) => {
  const navItems = [
    { icon: <LayoutDashboard size={20} />, label: 'Dashboard', path: '/' },
    { icon: <Play size={20} />, label: 'Pipeline Control', path: '/pipeline' },
    { icon: <FileText size={20} />, label: 'Results', path: '/results' },
    { icon: <BookOpen size={20} />, label: 'Documentation', path: '/docs' },
  ];

  return (
    <aside className={`
      fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out
      bg-black/20 backdrop-blur-xl border-r border-white/10 flex flex-col
      lg:relative lg:translate-x-0
      ${isOpen ? 'translate-x-0' : '-translate-x-full'}
    `}>
      {/* Header */}
      <div className="p-6 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center shadow-lg shadow-blue-500/30">
            <BookOpen size={18} className="text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight">NovelVerified<span className="text-blue-400">.AI</span></h1>
            <p className="text-[10px] text-gray-400 tracking-widest uppercase">NovelVerified.AI Team</p>
          </div>
        </div>
        <button onClick={onClose} className="lg:hidden text-gray-400 hover:text-white">
          <X size={20} />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={() => onClose && onClose()}
            className={({ isActive }) =>
              `w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group
              ${isActive
                ? 'bg-blue-600/20 text-blue-200 border border-blue-500/30 shadow-[0_0_15px_rgba(37,99,235,0.2)]'
                : 'text-gray-400 hover:bg-white/5 hover:text-white'}
              `
            }
          >
            {({ isActive }) => (
              <>
                <span className="relative z-10">{item.icon}</span>
                <span className="font-medium relative z-10">{item.label}</span>
                {isActive && <ChevronRight size={16} className="ml-auto opacity-50" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-white/10 bg-black/20">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 border border-white/20 flex items-center justify-center text-xs font-bold text-white">
            KD
          </div>
          <div>
            <p className="text-sm font-medium text-white">NovelVerified.AI</p>
            <p className="text-xs text-gray-500">Pathway-based</p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
