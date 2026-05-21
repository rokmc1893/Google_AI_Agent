import React, { useState } from 'react';
import { 
  BookOpen, 
  Layers, 
  ShieldCheck, 
  TrendingUp, 
  ChevronLeft, 
  ChevronRight, 
  Play, 
  Cpu, 
  CheckCircle,
  FileText
} from 'lucide-react';

const SLIDES = [
  {
    id: 1,
    title: "1차 법무 스크리닝 AI 어시스턴트",
    subtitle: "프로젝트 기획 개요 및 목표",
    icon: <BookOpen className="w-8 h-8 text-emerald-400" />,
    content: (
      <div className="space-y-6">
        <p className="text-lg leading-relaxed text-slate-300">
          본 시스템은 법률 지식이 부족한 현업 실무자가 법무팀에 정식 검토를 요청하기 전, 또는 법무팀이 대량의 계약서를 신속히 검토해야 할 때 업무 부하를 대폭 줄여주는 <strong className="text-emerald-400 font-semibold">‘1차 스크리닝 AI 협업 비서’</strong>입니다.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800">
            <h4 className="text-emerald-400 font-semibold mb-2 flex items-center gap-2">
              <CheckCircle className="w-4 h-4" /> 실무 효율성 극대화
            </h4>
            <p className="text-sm text-slate-400">
              불필요한 대기 시간을 즉각적으로 해소하고, 비즈니스 의사 결정의 병목 현상을 방지합니다.
            </p>
          </div>
          <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800">
            <h4 className="text-emerald-400 font-semibold mb-2 flex items-center gap-2">
              <CheckCircle className="w-4 h-4" /> 계약 안정성 확보
            </h4>
            <p className="text-sm text-slate-400">
              독소 조항 및 불공정 거래 요소를 사전에 선제 필터링하여 잠재적인 법적 분쟁 리스크를 차단합니다.
            </p>
          </div>
        </div>
        <div className="mt-4 bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-xl text-center">
          <span className="text-emerald-300 font-semibold text-sm">💡 변호사를 완전히 대체하는 것이 아닌, 전문 인력과 실무자의 긴밀한 협업을 이끌어내는 도구입니다.</span>
        </div>
      </div>
    )
  },
  {
    id: 2,
    title: "기존 기술 현황 및 필요성",
    subtitle: "구조적 비대칭과 불공정 계약의 리스크",
    icon: <FileText className="w-8 h-8 text-rose-400" />,
    content: (
      <div className="space-y-6">
        <div className="border-l-4 border-rose-500 pl-4 py-1">
          <h4 className="text-rose-400 font-semibold text-base mb-1">독소 조항의 정보 비대칭 문제</h4>
          <p className="text-sm text-slate-300">
            대기업과 하청업체(중소기업) 간의 용역·공급 계약 시, 경험 부족과 정보 격차로 인해 한쪽에게만 일방적으로 불리한 조항을 인지하지 못한 채 도장을 찍어 막대한 금전 손실과 소송으로 이어지는 문제가 빈번합니다.
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="bg-rose-950/20 p-4 rounded-lg border border-rose-900/30">
            <span className="text-xs font-bold text-rose-400 block mb-1">지식재산권 일방 귀속</span>
            <p className="text-xs text-slate-400">을이 독자 개발한 특허나 기술 자산을 원사업자에게 무상 또는 영구 귀속시키는 독점 조항.</p>
          </div>
          <div className="bg-rose-950/20 p-4 rounded-lg border border-rose-900/30">
            <span className="text-xs font-bold text-rose-400 block mb-1">과도한 지체상금</span>
            <p className="text-xs text-slate-400">납품이 하루 늦어질 때마다 총액의 0.3% 등 상법 표준(0.05%~0.15%)을 초과하는 살인적인 위약 비율 설정.</p>
          </div>
          <div className="bg-rose-950/20 p-4 rounded-lg border border-rose-900/30">
            <span className="text-xs font-bold text-rose-400 block mb-1">무제한 손해배상</span>
            <p className="text-xs text-slate-400">귀책사유 경중과 관계없이 발생한 모든 간접 손해까지 배상하게 하여 한도 규정을 누락하는 행위.</p>
          </div>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 text-sm">
          <h4 className="font-semibold text-slate-200 mb-1">🚀 개선방안</h4>
          <p className="text-slate-400">계약서 업로드 즉시 AI가 독소 조항 후보군을 추출하고 최신 법령/가이드라인과 자동 대조하여, 1차 실시간 자가 스크리닝이 가능하도록 구현합니다.</p>
        </div>
      </div>
    )
  },
  {
    id: 3,
    title: "기술 아키텍처 및 거버넌스",
    subtitle: "LangGraph 기반 멀티 에이전트 오케스트레이션",
    icon: <Cpu className="w-8 h-8 text-blue-400" />,
    content: (
      <div className="space-y-6">
        <p className="text-sm text-slate-300">
          단순한 단발성 프롬프트 질의가 아닌, **LangGraph**를 도입하여 단계별 상태(`State`) 전이와 피드백 루프를 완벽히 통제하는 견고한 아키텍처를 설계했습니다.
        </p>
        
        {/* 아키텍처 다이어그램 시각화 */}
        <div className="bg-slate-950/80 p-5 rounded-xl border border-slate-800 flex flex-col justify-center space-y-4">
          <div className="flex justify-between items-center text-center text-xs font-semibold">
            <div className="bg-slate-800 px-3 py-2 rounded border border-slate-700 w-24">계약서 입력</div>
            <div className="text-slate-500">→</div>
            <div className="bg-emerald-950/40 text-emerald-400 px-3 py-2 rounded border border-emerald-900/60 w-28">마스킹 가드레일<br/>(개인정보 보호)</div>
            <div className="text-slate-500">→</div>
            <div className="bg-slate-800 px-3 py-2 rounded border border-slate-700 w-28">독소 조항 스크리닝<br/>(LLM 분석)</div>
          </div>
          
          <div className="flex justify-center text-slate-500 text-sm">↓ (이슈 발견 시 분기)</div>
          
          <div className="flex justify-between items-center text-center text-xs font-semibold">
            <div className="bg-blue-950/40 text-blue-400 px-3 py-2 rounded border border-blue-900/60 w-32">하이브리드 RAG<br/>(법령 / 사내지침 매핑)</div>
            <div className="text-slate-500">→</div>
            <div className="bg-amber-950/40 text-amber-400 px-3 py-2 rounded border border-amber-900/60 w-32">소스 가드레일 노드<br/>(할루시네이션 방지)</div>
            <div className="text-slate-500">→</div>
            <div className="bg-slate-800 px-3 py-2 rounded border border-slate-700 w-28">보고서 &<br/>메일 초안 생성</div>
          </div>
          
          <div className="flex justify-center text-slate-500 text-sm">↓</div>
          
          <div className="flex justify-center">
            <div className="bg-emerald-950/60 text-emerald-300 px-4 py-2 rounded-lg border border-emerald-500/30 text-xs font-bold text-center">
              최종 산출물 복원 (De-masking) 및 시각화 출력
            </div>
          </div>
        </div>

        <div className="text-xs text-slate-400 grid grid-cols-2 gap-4">
          <div>
            <strong className="text-slate-200">🔒 핵심 거버넌스 1</strong>: 외부 LLM API로 민감 데이터가 유출되지 않도록 전처리와 후처리 과정에서 **로컬 마스킹 엔진**이 가로채서 제어합니다.
          </div>
          <div>
            <strong className="text-slate-200">🛡️ 핵심 거버넌스 2</strong>: RAG에서 실제 검색된 레퍼런스 데이터셋 이외의 창작된 출처 인용은 **소스 가드레일**에서 걸러냅니다.
          </div>
        </div>
      </div>
    )
  },
  {
    id: 4,
    title: "추진 전략 및 리스크 극복",
    subtitle: "생성 AI 도입 장벽의 완벽한 해소",
    icon: <ShieldCheck className="w-8 h-8 text-emerald-400" />,
    content: (
      <div className="space-y-5">
        <div className="space-y-3">
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
            <h4 className="text-sm font-semibold text-emerald-400 mb-1">1. 기밀 데이터 유출 방지 (마스킹)</h4>
            <p className="text-xs text-slate-400">
              정규표현식 및 로컬 NER 패턴을 결합하여 기업명, 사업자번호, 개인정보 등을 `[COMPANY_A]`, `[ID_NO_1]` 등으로 암호화한 뒤 분석을 수행하고 로컬에서 복원하여 외부 유출 리스크를 근본적으로 차단합니다.
            </p>
          </div>
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
            <h4 className="text-sm font-semibold text-emerald-400 mb-1">2. 할루시네이션 제어 (하이브리드 RAG)</h4>
            <p className="text-xs text-slate-400">
              국가 법률(하도급법 등) 및 사내 규정 지침에 대해 키워드 검색(BM25)과 맥락 검색(유사도)을 혼합하여 관련 소스를 가져오고, 생성된 내용과 대조하는 엄격한 소스 검증 프로세스를 가드레일로 구축했습니다.
            </p>
          </div>
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
            <h4 className="text-sm font-semibold text-emerald-400 mb-1">3. 실시간 DB 자동화 파이프라인</h4>
            <p className="text-xs text-slate-400">
              법률 개정 및 사내 가이드라인 변동 시 독립적인 동기화 모듈이 감지하여 실시간으로 임베딩 DB를 업데이트하는 파이프라인을 두어 최신성을 상시 보장합니다.
            </p>
          </div>
        </div>
      </div>
    )
  },
  {
    id: 5,
    title: "정성적 & 정량적 기대효과",
    subtitle: "상생 협력 생태계 구축 및 비용 혁신",
    icon: <TrendingUp className="w-8 h-8 text-emerald-400" />,
    content: (
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800">
            <h4 className="text-sm font-bold text-slate-200 mb-3 text-center">🎯 정성적 효과</h4>
            <ul className="text-xs text-slate-400 space-y-2 list-disc list-inside">
              <li>비전문가인 실무자도 안심하고 안전하게 협상을 진행할 수 있는 환경 조성</li>
              <li>공정하고 투명한 계약 검토를 통해 원·하청 기업 간의 상생적 신뢰 모델 확립</li>
              <li>기업 전반의 리스크 관리 및 법률 준수(Compliance) 역량 내재화</li>
            </ul>
          </div>
          <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800">
            <h4 className="text-sm font-bold text-slate-200 mb-3 text-center">📊 정량적 목표치 및 효과</h4>
            <ul className="text-xs text-slate-400 space-y-2 list-disc list-inside">
              <li>검토 대기 시간 대폭 단축: <strong>수일 {"→"} 10분 이내</strong> (90% 이상 속도 개선)</li>
              <li>독소 조항 탐지 정확도: <strong>85% 이상</strong> 목표 달성</li>
              <li>할루시네이션 방지 법령 매핑률: <strong>100%</strong> 보장</li>
              <li>경미하고 반복적인 검토의 법무 비용 및 로펌 외주 비용 획기적 절감</li>
            </ul>
          </div>
        </div>
        
        <div className="bg-gradient-to-r from-emerald-950/40 to-blue-950/40 p-4 rounded-xl border border-emerald-500/20 text-center">
          <h4 className="text-sm font-semibold text-slate-200 mb-1">💼 기업 인트라넷 표준 모듈로 활용 가능</h4>
          <p className="text-xs text-slate-400">사내 인트라넷에 API 및 플러그인 형태로 연동하여 구매팀, 영업팀, 관리팀의 실무 계약 검토 표준 모듈로 탑재할 수 있습니다.</p>
        </div>
      </div>
    )
  }
];

export default function PortfolioSlide({ onStartPrototype }) {
  const [currentIdx, setCurrentIdx] = useState(0);

  const nextSlide = () => {
    if (currentIdx < SLIDES.length - 1) {
      setCurrentIdx(currentIdx + 1);
    }
  };

  const prevSlide = () => {
    if (currentIdx > 0) {
      setCurrentIdx(currentIdx - 1);
    }
  };

  const currentSlide = SLIDES[currentIdx];

  return (
    <div className="max-w-4xl mx-auto py-8">
      {/* 슬라이드 헤더 정보 */}
      <div className="text-center mb-8">
        <span className="badge badge-primary mb-2">예선 심사용 포트폴리오 슬라이드</span>
        <h2 className="text-3xl font-extrabold tracking-tight mt-1 bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
          Project Presentation
        </h2>
        <p className="text-sm text-slate-500 mt-1">프로젝트 기획안 및 기술 아키텍처 상세 설명</p>
      </div>

      {/* 메인 슬라이드 카드 */}
      <div className="glass-panel glass-panel-glow min-h-[480px] flex flex-col justify-between p-8 relative overflow-hidden transition-all duration-500">
        
        {/* 배경 은은한 빛 효과 */}
        <div className="absolute top-0 right-0 w-48 h-48 bg-emerald-500/5 rounded-full filter blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-blue-500/5 rounded-full filter blur-3xl pointer-events-none"></div>

        <div>
          {/* 슬라이드 탑 타이틀 영역 */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
            <div className="flex items-center gap-3">
              {currentSlide.icon}
              <div>
                <span className="text-xs text-emerald-400 font-bold tracking-wider uppercase">{currentSlide.subtitle}</span>
                <h3 className="text-2xl font-bold text-slate-100 mt-0.5">{currentSlide.title}</h3>
              </div>
            </div>
            <div className="text-sm font-semibold text-slate-500">
              {currentSlide.id} / {SLIDES.length}
            </div>
          </div>

          {/* 슬라이드 내용 */}
          <div className="py-2 text-slate-300">
            {currentSlide.content}
          </div>
        </div>

        {/* 하단 내비게이션 컨트롤 */}
        <div className="flex items-center justify-between border-t border-slate-800 pt-6 mt-8">
          <button 
            onClick={prevSlide}
            disabled={currentIdx === 0}
            className="btn btn-secondary text-xs disabled:opacity-40 disabled:pointer-events-none"
          >
            <ChevronLeft className="w-4 h-4" /> 이전
          </button>
          
          <div className="flex gap-2">
            {SLIDES.map((_, idx) => (
              <span 
                key={idx}
                className={`w-2 h-2 rounded-full transition-all duration-300 ${idx === currentIdx ? 'bg-emerald-400 w-5' : 'bg-slate-700'}`}
              ></span>
            ))}
          </div>

          {currentIdx === SLIDES.length - 1 ? (
            <button 
              onClick={onStartPrototype}
              className="btn btn-primary text-xs"
            >
              실제 프로토타입 실행 <Play className="w-3.5 h-3.5 fill-current" />
            </button>
          ) : (
            <button 
              onClick={nextSlide}
              className="btn btn-secondary text-xs"
            >
              다음 <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div className="text-center mt-6 text-xs text-slate-500">
        💡 키보드 방향키 또는 하단 버튼을 활용해 기획안을 슬라이드 형태로 읽으실 수 있습니다.
      </div>
    </div>
  );
}
