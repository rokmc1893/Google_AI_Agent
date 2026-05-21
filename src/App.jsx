import React, { useState } from 'react';
import PortfolioSlide from './components/PortfolioSlide';
import Dashboard from './components/Dashboard';
import { BookOpen, ShieldCheck, ExternalLink } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('portfolio'); // portfolio, dashboard

  return (
    <div className="min-h-screen relative flex flex-col justify-between">
      {/* 배경 은은한 광선 효과 */}
      <div className="bg-glow-effect"></div>
      <div className="bg-glow-effect-2"></div>

      <div>
        {/* 상단 통합 네비게이션 */}
        <header className="nav-bar">
          <div className="logo-container">
            <ShieldCheck className="w-6 h-6 text-emerald-400 stroke-[2.5]" />
            <span>Legal Screening AI</span>
          </div>

          <nav className="nav-links">
            <button 
              onClick={() => setActiveTab('portfolio')}
              className={`nav-tab ${activeTab === 'portfolio' ? 'active' : ''}`}
            >
              <BookOpen className="w-4 h-4" /> 기획안 슬라이드
            </button>
            <button 
              onClick={() => setActiveTab('dashboard')}
              className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            >
              <ShieldCheck className="w-4 h-4" /> 실시간 프로토타입
            </button>
          </nav>

          <div className="flex items-center gap-4 text-xs text-slate-500 font-semibold">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
              Live Sandbox
            </span>
          </div>
        </header>

        {/* 메인 콘텐츠 바디 */}
        <main className="main-layout">
          {activeTab === 'portfolio' ? (
            <PortfolioSlide onStartPrototype={() => setActiveTab('dashboard')} />
          ) : (
            <Dashboard />
          )}
        </main>
      </div>

      {/* 푸터 영역 */}
      <footer className="border-t border-slate-900 bg-[#060a16] py-6 px-10 text-center text-xs text-slate-500 flex flex-col md:flex-row justify-between items-center gap-4">
        <div>
          © 2026 Legal Screening AI. All rights reserved. (Antigravity Multi-Agent Systems)
        </div>
        <div className="flex gap-4">
          <a href="#" className="hover:text-slate-300 flex items-center gap-1 transition-colors">
            기술 백서 <ExternalLink className="w-3 h-3" />
          </a>
          <span className="text-slate-800">|</span>
          <a href="#" className="hover:text-slate-300 flex items-center gap-1 transition-colors">
            LangGraph 설계도 <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </footer>
    </div>
  );
}
