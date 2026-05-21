import { useState } from 'react';
import { DesignSystem } from './views/DesignSystem';
import { Dashboard } from './views/Dashboard';
import { Scale, Palette, ShieldCheck, Heart } from 'lucide-react';

function App() {
  const [currentView, setCurrentView] = useState<'dashboard' | 'designSystem'>('dashboard');

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between selection:bg-navy-800/10 selection:text-navy-800">
      {/* Top Premium Sticky Header */}
      <header id="main-app-header" className="sticky top-0 z-50 bg-white/75 backdrop-blur-md border-b border-slate-200/80 px-6 py-3.5 transition-all duration-300">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo Brand Brand Accent */}
          <div id="brand-logo" className="flex items-center gap-2.5 cursor-pointer select-none group" onClick={() => setCurrentView('dashboard')}>
            <div className="w-9 h-9 rounded-xl bg-navy-800 flex items-center justify-center text-white transition-all duration-300 group-hover:scale-[1.03] shadow-sm group-hover:shadow-navy-800/15">
              <Scale className="w-4.5 h-4.5" />
            </div>
            <div>
              <span className="font-extrabold text-slate-900 tracking-tight text-base group-hover:text-navy-800 transition-colors">
                Deepgle <span className="font-medium text-slate-600">Legal</span>
              </span>
              <span className="block text-[8.5px] uppercase tracking-widest text-slate-500 font-bold -mt-0.5 font-mono">
                Screening Assistant
              </span>
            </div>
          </div>

          {/* Navigation Controls */}
          <nav id="navbar-navigation" className="flex items-center gap-1 bg-slate-100/90 p-1 rounded-xl border border-slate-200/60 shadow-inner">
            <button
              id="btn-nav-dashboard"
              onClick={() => setCurrentView('dashboard')}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold tracking-wide transition-all duration-300 flex items-center gap-1.5 cursor-pointer ${
                currentView === 'dashboard'
                  ? 'bg-navy-800 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              스크리닝 대시보드
            </button>
            
            <button
              id="btn-nav-showroom"
              onClick={() => setCurrentView('designSystem')}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold tracking-wide transition-all duration-300 flex items-center gap-1.5 cursor-pointer ${
                currentView === 'designSystem'
                  ? 'bg-navy-800 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              <Palette className="w-3.5 h-3.5" />
              디자인 규격 쇼룸
            </button>
          </nav>

          {/* Telemetry telemetry engine status - visible on desktop */}
          <div className="hidden lg:flex items-center gap-4 text-xs font-sans">
            <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200/50 text-emerald-800 rounded-full font-bold shadow-sm shadow-emerald-50">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0"></span>
              AI 엔진: 최적 (42ms)
            </div>
            <div className="flex items-center gap-1.5 text-slate-500 font-mono border-l border-slate-200 pl-4">
              <span>세션:</span>
              <span className="font-semibold text-slate-800">DG-892A</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main id="main-app-content" className="flex-grow px-6 py-10">
        {currentView === 'dashboard' ? <Dashboard /> : <DesignSystem />}
      </main>

      {/* Footer System */}
      <footer id="main-app-footer" className="bg-white border-t border-slate-200 py-6 px-6 text-center text-xs text-slate-600">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-navy-800" />
            <span>&copy; {new Date().getFullYear()} Deepgle Legal. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-1">
            <span>Designed with</span>
            <Heart className="w-3 h-3 text-rose-500 fill-rose-500" />
            <span>for professionals.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
