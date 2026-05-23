import { useState } from 'react';
import { Dashboard } from './views/Dashboard';
import { Scale, ShieldCheck } from 'lucide-react';

function App() {
  const [dashboardKey, setDashboardKey] = useState(0);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between selection:bg-navy-800/10 selection:text-navy-800">
      <header id="main-app-header" className="sticky top-0 z-50 bg-white/75 backdrop-blur-md border-b border-slate-200/80 px-6 py-3.5 transition-all duration-300">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <button
            type="button"
            id="brand-logo"
            onClick={() => setDashboardKey((k) => k + 1)}
            className="flex items-center gap-2.5 select-none group cursor-pointer text-left"
            aria-label="업로드 화면으로 돌아가기"
          >
            <div className="w-9 h-9 rounded-xl bg-navy-800 flex items-center justify-center text-white transition-all duration-300 group-hover:scale-[1.03] shadow-sm group-hover:shadow-navy-800/15">
              <Scale className="w-4.5 h-4.5" />
            </div>
            <div>
              <span className="font-semibold text-slate-900 tracking-tight text-base group-hover:text-navy-800 transition-colors">
                Deepgle <span className="font-medium text-slate-600">Legal</span>
              </span>
              <span className="block text-xs tracking-wide text-slate-500 font-medium -mt-0.5">
                계약 분석 시스템
              </span>
            </div>
          </button>
        </div>
      </header>

      <main id="main-app-content" className="flex-grow px-6 py-10">
        <Dashboard key={dashboardKey} />
      </main>

      <footer id="main-app-footer" className="bg-white border-t border-slate-200 py-6 px-6 text-center text-xs text-slate-600">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-navy-800" />
            <span>&copy; {new Date().getFullYear()} Deepgle Legal. All rights reserved.</span>
          </div>
          <div className="flex items-center">
            <span className="text-slate-500">법무 검토 보조용 AI 계약 분석 시스템</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
