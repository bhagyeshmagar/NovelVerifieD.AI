import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import { Menu } from 'lucide-react';

const Layout = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/': return 'Dashboard';
      case '/pipeline': return 'Pipeline Control';
      case '/results': return 'Results';
      case '/docs': return 'Documentation';
      default: return 'NovelVerified.AI';
    }
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-white font-sans selection:bg-blue-500/30 selection:text-white overflow-x-hidden relative">
      {/* Dynamic Background Elements */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-purple-600/20 rounded-full blur-[120px] animate-blob" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-600/20 rounded-full blur-[120px] animate-blob animation-delay-2000" />
        <div className="absolute top-[20%] right-[20%] w-[30%] h-[30%] bg-emerald-600/10 rounded-full blur-[100px] animate-blob animation-delay-4000" />
      </div>

      <div className="relative z-10 flex h-screen">
        <Sidebar isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)} />

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col overflow-hidden w-full">
          {/* Header */}
          <header className="h-16 border-b border-white/10 bg-black/10 backdrop-blur-sm flex items-center justify-between px-6 lg:px-8">
            <button
              className="lg:hidden p-2 text-gray-400 hover:text-white"
              onClick={() => setIsMobileMenuOpen(true)}
            >
              <Menu />
            </button>

            <h2 className="text-lg font-semibold text-gray-200 lg:hidden">{getPageTitle()}</h2>

            <div className="flex items-center gap-4 ml-auto">
              {/* Status indicator can be added here globally if needed */}
            </div>
          </header>

          <div className="flex-1 overflow-y-auto p-6 lg:p-8 custom-scrollbar relative">
            <Outlet />
          </div>
        </main>

        {/* Mobile Overlay */}
        {isMobileMenuOpen && (
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
            onClick={() => setIsMobileMenuOpen(false)}
          />
        )}
      </div>
    </div>
  );
};

export default Layout;
