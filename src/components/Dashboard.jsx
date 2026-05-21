import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  Shield, 
  Eye, 
  FileText, 
  Play, 
  AlertTriangle, 
  Mail, 
  CheckCircle,
  Database,
  ArrowRight,
  RefreshCw,
  Copy
} from 'lucide-react';

// 샘플 계약서 데이터
const SAMPLE_CONTRACTS = {
  subcontract: `소프트웨어 개발 용역 계약서

제1조 (계약 목적)
본 계약은 발주처 주식회사 대성전자 (이하 "갑")와 수급처 (주)마이크로소프트웨어 (이하 "을") 간의 인공지능 기반 사내 시스템 개발 업무를 위탁함에 있어 상호 권리와 의무를 규정함을 목적으로 한다.

제3조 (계약 금액 및 지급)
총 계약 금액은 일금 오천만원정(₩50,000,000원, 부가세 별도)으로 한다. 을은 결과물을 2026년 08월 30일까지 납품 완료하여야 하며, 갑은 검수 완료 후 90일 이내에 현금으로 잔금을 지급한다.

제5조 (지식재산권의 귀속)
본 용역 계약의 수행 결과로 개발된 소프트웨어, 소스코드, 관련 특허 및 저작권을 포함한 일체의 지식재산권은 본 계약의 체결과 동시에 갑에게 전적으로 영구 귀속된다. 을은 어떠한 권리도 주장할 수 없으며, 저작인격권 또한 행사할 수 없다.

제7조 (지체상금)
을이 납기를 준수하지 못할 경우, 지체 1일당 총 계약금액의 1,000분의 3(0.3%)에 해당하는 지체상금을 갑에게 즉시 납부해야 한다.

제12조 (손해배상 및 책임)
을이 계약 사항을 불이행하여 갑에게 손실을 초래한 경우, 을은 갑에게 발생한 직접적, 간접적 손해 및 특별 손해를 한도 없이 전액 배상할 책임을 진다. 갑의 귀책사유로 인한 경우에는 갑은 책임을 지지 아니한다.`,
  clean: `표준 소프트웨어 개발 용역 계약서

제1조 (계약 목적)
본 계약은 발주처 주식회사 대성전자 (이하 "갑")와 수급처 (주)마이크로소프트웨어 (이하 "을") 간의 인공지능 기반 사내 시스템 개발 업무를 위탁함에 있어 상호 권리와 의무를 규정함을 목적으로 한다.

제3조 (계약 금액 및 지급)
총 계약 금액은 일금 오천만원정(₩50,000,000원, 부가세 별도)으로 한다. 을은 결과물을 2026년 08월 30일까지 납품 완료하여야 하며, 갑은 검수 완료 후 60일 이내에 하도급 대금을 지급한다.

제5조 (지식재산권의 귀속)
본 계약에 따라 을이 창작한 결과물의 지식재산권은 갑과 을이 공동으로 소유하는 것을 원칙으로 하며, 지분율 및 활용 권한은 양사 기여도에 따라 별도로 약정한다.

제7조 (지체상금)
을이 납기를 준수하지 못할 경우, 지체 1일당 총 계약금액의 10,000분의 5(0.05%)에 해당하는 지체상금을 지급하되, 불가항력적 사유에 의한 경우에는 예외로 하며 총액의 10%를 초과할 수 없다.

제12조 (손해배상 및 책임)
계약 위반으로 인한 손해배상은 상대방에게 발생한 통상의 직접 손해에 한하며, 손해배상 총 책임 한도는 총 계약금액을 초과할 수 없다.`
};

export default function Dashboard() {
  const [inputText, setInputText] = useState('');
  const [selectedSample, setSelectedSample] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [step, setStep] = useState(0); // 0: 대기, 1~7: 각 에이전트 단계
  const [showResults, setShowResults] = useState(false);
  const [activeResultTab, setActiveResultTab] = useState('report'); // report, email, masking
  const [copySuccess, setCopySuccess] = useState('');

  // 시뮬레이션 상태값
  const [simState, setSimState] = useState({
    maskedText: '',
    issues: [],
    retrievedDocs: [],
    finalReport: '',
    emailDraft: ''
  });

  const loadSample = (key) => {
    setSelectedSample(key);
    setInputText(SAMPLE_CONTRACTS[key]);
    setShowResults(false);
    setStep(0);
  };

  const handleCopy = (text, type) => {
    navigator.clipboard.writeText(text);
    setCopySuccess(type);
    setTimeout(() => setCopySuccess(''), 2000);
  };

  const startScreening = () => {
    if (!inputText.trim()) {
      alert("계약서 내용을 입력하거나 샘플 계약서를 선택해 주세요.");
      return;
    }

    setIsRunning(true);
    setShowResults(false);
    setStep(1);

    // 백엔드 아키텍처 로직을 단계별 타임아웃으로 프론트엔드에서 시각화하여 시뮬레이션
    const steps = [
      { t: 800, s: 2 }, // 마스킹 노드
      { t: 1800, s: 3 }, // 스크리닝 노드 (독소 조항 탐지)
      { t: 2800, s: 4 }, // RAG 검색 노드
      { t: 3800, s: 5 }, // 소스 가드레일 검증 노드
      { t: 4800, s: 6 }, // 보고서/메일 생성 노드
      { t: 5600, s: 7 }, // 역마스킹(데마스킹) 복원 노드
      { t: 6200, s: 8 }  // 완료
    ];

    steps.forEach((item) => {
      setTimeout(() => {
        setStep(item.s);
        if (item.s === 8) {
          setIsRunning(false);
          setShowResults(true);
          generateSimulationData();
        }
      }, item.t);
    });
  };

  // 백엔드 Python 로직 시뮬레이션 결과 데이터 생성
  const generateSimulationData = () => {
    const isSubcontract = inputText.includes("영구 귀속") || inputText.includes("0.3%") || inputText.includes("한도 없이 전액 배상") || selectedSample === 'subcontract';
    
    let masked = inputText
      .replace(/주식회사 대성전자/g, "[COMPANY_A]")
      .replace(/\(주\)마이크로소프트웨어/g, "[COMPANY_B]")
      .replace(/오천만원정\(₩50,000,000원/g, "[VALUE_1]")
      .replace(/2026년 08월 30일/g, "[DATE_1]");

    if (isSubcontract) {
      setSimState({
        maskedText: masked,
        issues: [
          {
            id: "ISSUE_IP",
            title: "지식재산권 일방적 영구 귀속 독소 조항",
            risk: "HIGH",
            clause: "제5조 (지식재산권의 귀속)\n...지식재산권은 본 계약의 체결과 동시에 갑에게 전적으로 영구 귀속된다...",
            lawBasis: "사내 가이드라인 IP 귀속 제3조",
            lawDetail: "공동 용역 및 연구개발 성과물의 지식재산권은 공동 소유가 원칙이며, 기여도에 따라 귀속을 안분해야 합니다. 일방의 독점을 강제하는 계약은 불공정거래 소지가 높습니다.",
            suggestion: "계약 결과물에 대한 지식재산권은 양사 공동 소유로 하거나, 발주처 귀속 시 그에 상응하는 합당한 대가(기술료 등)가 지급되도록 문구를 수정해야 합니다."
          },
          {
            id: "ISSUE_DELAY",
            title: "과도한 지체상금율 설정",
            risk: "MEDIUM",
            clause: "제7조 (지체상금)\n...지체 1일당 총 계약금액의 1,000분의 3(0.3%)에 해당하는 지체상금...",
            lawBasis: "하도급법 제13조 (대금지급) 및 상법 표준안",
            lawDetail: "표준 소프트웨어 용역 계약의 지체상금율은 통상 1일당 0.05% ~ 0.15% 수준입니다. 0.3%는 표준 대비 약 3배~6배 수준으로 과도합니다.",
            suggestion: "지체상금율을 상법 및 기획재정부 표준 요율인 0.05%~0.1% 수준으로 낮추고, 불가항력적 사유에 의한 납기 지연은 면책하는 단서를 추가해야 합니다."
          },
          {
            id: "ISSUE_LIMIT",
            title: "손해배상 책임 한도 무제한 및 일방 면책",
            risk: "HIGH",
            clause: "제12조 (손해배상 및 책임)\n...간접 손해 및 특별 손해를 한도 없이 전액 배상할 책임을 진다. 갑의 귀책사유로 인한 경우에는 갑은 책임을 지지 아니한다.",
            lawBasis: "사내 표준 규정 책임제한 제5조 및 민법 제398조",
            lawDetail: "계약 위반 배상 책임은 고의 또는 중과실이 없는 한 계약 금액의 100%를 초과하지 않도록 한도를 상호 설정하는 것이 표준입니다. 일방면책 및 간접/특별손해 무한 배상은 매우 위험합니다.",
            suggestion: "손해배상 책임을 '상대방에게 발생한 직접적인 통상 손해'로 제한하고, 총 배상액 한도를 '총 계약금액'으로 캡을 씌우는 조항으로 개정이 강하게 권고됩니다."
          }
        ],
        finalReport: `[1차 법무 스크리닝 AI 위험 분석 보고서]

본 보고서는 LangGraph 멀티 에이전트 파이프라인에 의해 1차 자동 스크리닝된 결과이며, 공식적인 법적 효력을 갖지 않으므로 최종 계약 전 사내 법무팀과의 교차 검토를 추천합니다.

1. 검토 요약
  - 업로드된 계약서에서 총 3건의 리스크 요인이 검출되었습니다.
  - HIGH (치명적 위험): 2건
  - MEDIUM (주의 위험): 1건

2. 상세 위험 분석 결과
  
  ■ [HIGH] 지식재산권 일방적 영구 귀속 독소 조항
    - 관련 조항: 제5조 (지식재산권의 귀속)
    - 위험 요소: 을의 고유 산출물 권리까지 갑에게 대가 없이 일방적 영구 독점 귀속시킴.
    - 매핑 근거: 사내 가이드라인 IP 귀속 제3조 (기여도 안분 및 공동 소유 표준)
    - 수정 가이드: "성과물의 지식재산권은 양사 공동 소유로 하며, 활용 범위는 협의하여 결정한다"로 수정 요망.

  ■ [HIGH] 손해배상 책임 한도 무제한 및 일방 면책
    - 관련 조항: 제12조 (손해배상 및 책임)
    - 위험 요소: 무제한 책임 범위 설정 및 발주처 귀책에 대한 일방적 면책 약정.
    - 매핑 근거: 사내 표준 규정 책임제한 제5조 & 민법 제398조
    - 수정 가이드: 손해배상 범위를 '통상 손해'로 제한하고, 배상 한도를 '총 계약금액'으로 캡 설정 필요.

  ■ [MEDIUM] 과도한 지체상금율 설정
    - 관련 조항: 제7조 (지체상금)
    - 위험 요소: 표준 지체상금율(0.05%~0.15%)을 초과하는 1일당 0.3% 부과.
    - 매핑 근거: 하도급법 제13조 및 상법 표준안
    - 수정 가이드: 지체상금율을 0.05%로 하향 조정 및 상한선(최대 10%) 추가.

--------------------------------------------------
분석 완료 시간: 2026-05-21 (제한 시간 3분 내 신속 검토 완료)`,
        emailDraft: `받는사람: 주식회사 대성전자 계약담당자 귀하
보낸사람: (주)마이크로소프트웨어 법무/계약 실무 담당자

제목: [수정 요청] 소프트웨어 개발 용역 계약서 조항 수정 제안의 건

안녕하십니까, 주식회사 대성전자 담당자님.
보내주신 '소프트웨어 개발 용역 계약서' 초안에 대해 감사드리며, 당사 내부의 안정적인 업무 수행 및 상호 신뢰를 바탕으로 한 공정한 계약 관계 구축을 위해 아래와 같이 일부 조항에 대한 정중한 수정 검토를 제안드립니다.

[주요 수정 제안 사항]

1. 제5조 (지식재산권의 귀속) 관련
  - 현행: 소프트웨어 및 일체의 지식재산권이 갑에게 전적으로 영구 귀속됨.
  - 제안: 양사의 공동 개발 성격 및 기술 파트너십 유지를 위해, 결과물의 지식재산권은 기여도에 따라 양사 공동 소유로 하거나, 별도의 활용 협약을 맺는 방향으로 수정을 희망합니다.

2. 제7조 (지체상금) 관련
  - 현행: 납기 지연 시 일당 총 계약금액의 0.3% 부과.
  - 제안: 통상적인 소프트웨어 용역 표준 비율이자 관계 법령에 부합하는 일당 0.05%~0.1%로 하향 조정하고, 불가항력적 사유 시 지연이 면책되는 조항 보완을 부탁드립니다.

3. 제12조 (손해배상 및 책임) 관련
  - 현행: 간접/특별손해 포함 무제한 배상 및 갑의 일방 면책.
  - 제안: 고의 또는 중과실이 없는 한 배상 책임을 '통상적인 직접 손해'로 한정하고, 총 배상액의 상한선을 '총 계약금액'으로 상호 합의 제한할 것을 제안합니다.

보내드리는 제안 사항에 대해 긍정적인 검토를 부탁드리며, 조율 가능한 미팅 일정이나 의견 회신해 주시면 감사하겠습니다.

감사합니다.
(주)마이크로소프트웨어 드림`
      });
    } else {
      // 위험 요인이 없는 클린 계약서인 경우
      setSimState({
        maskedText: masked,
        issues: [],
        finalReport: `[1차 법무 스크리닝 AI 위험 분석 보고서]

1. 검토 요약
  - 업로드된 표준 소프트웨어 개발 용역 계약서 검토 결과, 독소 조항이나 불공정 요소가 검출되지 않았습니다.
  - 모든 조항(지식재산권 공동소유, 표준 지체상금율 0.05%, 책임 제한 한도 상호 100%)이 사내 가이드라인 및 하도급법 요건을 충족합니다.
  - 즉시 날인 및 체결을 진행하셔도 안전합니다.`,
        emailDraft: `제목: [검토 완료] 소프트웨어 개발 용역 계약서 날인 진행의 건

안녕하십니까, 담당자님.
검토 요청해주신 계약서를 내부 AI 법무 스크리닝을 통해 1차 검증한 결과, 모든 조항이 공정거래 표준 규정 및 사내 리스크 기준을 완벽하게 만족함을 확인하였습니다.

별도의 조항 수정 요구 없이 정식 서명 날인 절차를 진행하고자 하오니, 날인 가능한 시간과 장소를 알려주시면 감사하겠습니다.

감사합니다.`
      });
    }
  };

  return (
    <div className="space-y-8 fade-in">
      {/* 타이틀 헤더 */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-800 pb-6">
        <div>
          <span className="badge badge-primary mb-2 flex items-center gap-1.5 w-fit">
            <Shield className="w-3.5 h-3.5 fill-current" /> Local Security Active
          </span>
          <h2 className="text-2xl font-extrabold text-slate-100 font-title">
            1차 계약서 스크리닝 대시보드
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            계약서 초안을 업로드하여 독소 조항 필터링 및 RAG 매핑 보고서를 실시간으로 생성합니다.
          </p>
        </div>
        
        {/* 샘플 데이터 로더 */}
        <div className="flex gap-2">
          <button 
            onClick={() => loadSample('subcontract')}
            className={`btn text-xs ${selectedSample === 'subcontract' ? 'btn-primary' : 'btn-secondary'}`}
          >
            🔥 불공정 용역 계약서 로드
          </button>
          <button 
            onClick={() => loadSample('clean')}
            className={`btn text-xs ${selectedSample === 'clean' ? 'btn-primary' : 'btn-secondary'}`}
          >
            ✅ 표준(안전) 계약서 로드
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* 왼쪽 패널: 계약서 입력 및 시뮬레이션 상태 */}
        <div className="space-y-6">
          <div className="glass-panel space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-base font-bold text-slate-200 flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-400" /> 계약서 텍스트 입력
              </h3>
              <span className="text-xs text-slate-500">
                {inputText.length} 자 입력됨
              </span>
            </div>
            
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="여기에 검토가 필요한 계약서 초안을 직접 붙여넣거나, 우측 상단의 샘플 계약서 단추를 클릭해 주세요."
              className="w-full h-80 bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-sm text-slate-300 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30 transition-all font-mono leading-relaxed resize-none"
              disabled={isRunning}
            />

            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Shield className="w-3.5 h-3.5 text-emerald-400" />
                외부 전송 전 자동 비식별화(PII 마스킹) 탑재
              </div>
              <button
                onClick={startScreening}
                disabled={isRunning}
                className="btn btn-primary"
              >
                {isRunning ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" /> 에이전트 가동 중...
                  </>
                ) : (
                  <>
                    스크리닝 에이전트 실행 <Play className="w-4 h-4 fill-current" />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* LangGraph 워크플로우 실시간 트래커 */}
          {(isRunning || step > 0) && (
            <div className="glass-panel space-y-4">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <Database className="w-4 h-4 text-emerald-400" /> LangGraph 멀티 에이전트 파이프라인 실시간 동작 상태
              </h3>
              
              <div className="space-y-3 text-xs">
                {/* 1. Parser Node */}
                <div className={`flex justify-between items-center p-2.5 rounded-lg border transition-all duration-300 ${
                  step === 1 ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300' :
                  step > 1 ? 'bg-slate-900/40 border-slate-800 text-slate-500' : 'border-transparent text-slate-600'
                }`}>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                    <span>[Parser] 비정형 계약서 조·항·호 구조적 파싱 및 전처리</span>
                  </div>
                  <span>{step === 1 ? '실행 중' : step > 1 ? '완료' : '대기'}</span>
                </div>

                {/* 2. Masking Node */}
                <div className={`flex justify-between items-center p-2.5 rounded-lg border transition-all duration-300 ${
                  step === 2 ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300' :
                  step > 2 ? 'bg-slate-900/40 border-slate-800 text-slate-500' : 'border-transparent text-slate-600'
                }`}>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                    <span>[Masker] 로컬 보안 모듈 - PII 및 기업 민감 정보 암호화(마스킹)</span>
                  </div>
                  <span>{step === 2 ? '실행 중' : step > 2 ? '완료' : '대기'}</span>
                </div>

                {/* 3. Screener Node */}
                <div className={`flex justify-between items-center p-2.5 rounded-lg border transition-all duration-300 ${
                  step === 3 ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300' :
                  step > 3 ? 'bg-slate-900/40 border-slate-800 text-slate-500' : 'border-transparent text-slate-600'
                }`}>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                    <span>[Screener] 마스킹 텍스트 기반 독소 조항 1차 스크리닝(LLM)</span>
                  </div>
                  <span>{step === 3 ? '실행 중' : step > 3 ? '완료' : '대기'}</span>
                </div>

                {/* 4. RAG Node */}
                <div className={`flex justify-between items-center p-2.5 rounded-lg border transition-all duration-300 ${
                  step === 4 ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300' :
                  step > 4 ? 'bg-slate-900/40 border-slate-800 text-slate-500' : 'border-transparent text-slate-600'
                }`}>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                    <span>[RAG Retriever] 하이브리드 검색 기반 법령 및 사내 DB 매핑</span>
                  </div>
                  <span>{step === 4 ? '실행 중' : step > 4 ? '완료' : '대기'}</span>
                </div>

                {/* 5. Guardrail Node */}
                <div className={`flex justify-between items-center p-2.5 rounded-lg border transition-all duration-300 ${
                  step === 5 ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300' :
                  step > 5 ? 'bg-slate-900/40 border-slate-800 text-slate-500' : 'border-transparent text-slate-600'
                }`}>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                    <span>[Guardrail] 소스 가드레일 - 가짜 인용 정보 검증 (할루시네이션 방지)</span>
                  </div>
                  <span>{step === 5 ? '실행 중' : step > 5 ? '완료' : '대기'}</span>
                </div>

                {/* 6. Generator Node */}
                <div className={`flex justify-between items-center p-2.5 rounded-lg border transition-all duration-300 ${
                  step === 6 ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300' :
                  step > 6 ? 'bg-slate-900/40 border-slate-800 text-slate-500' : 'border-transparent text-slate-600'
                }`}>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                    <span>[Generator] 스크리닝 위험 분석 리포트 & 메일 초안 자동 빌드</span>
                  </div>
                  <span>{step === 6 ? '실행 중' : step > 6 ? '완료' : '대기'}</span>
                </div>

                {/* 7. Demasking Node */}
                <div className={`flex justify-between items-center p-2.5 rounded-lg border transition-all duration-300 ${
                  step === 7 ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300' :
                  step > 7 ? 'bg-slate-900/40 border-slate-800 text-slate-500' : 'border-transparent text-slate-600'
                }`}>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                    <span>[De-masker] 최종 보고서 내 식별자 정보 원본 데이터 역치환 복원</span>
                  </div>
                  <span>{step === 7 ? '실행 중' : step > 7 ? '완료' : '대기'}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 오른쪽 패널: 분석 결과 시각화 */}
        <div className="space-y-6">
          {showResults ? (
            <div className="glass-panel space-y-6 fade-in min-h-[500px] flex flex-col justify-between">
              <div>
                {/* 탭 네비게이션 */}
                <div className="flex border-b border-slate-800 pb-3 mb-5 gap-4">
                  <button 
                    onClick={() => setActiveResultTab('report')}
                    className={`pb-2 text-sm font-semibold border-b-2 transition-all ${
                      activeResultTab === 'report' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    📊 위험 분석 보고서
                  </button>
                  <button 
                    onClick={() => setActiveResultTab('email')}
                    className={`pb-2 text-sm font-semibold border-b-2 transition-all ${
                      activeResultTab === 'email' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    ✉️ 메일 초안
                  </button>
                  <button 
                    onClick={() => setActiveResultTab('masking')}
                    className={`pb-2 text-sm font-semibold border-b-2 transition-all ${
                      activeResultTab === 'masking' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    🔒 데이터 마스킹 비교
                  </button>
                </div>

                {/* 탭 1: 위험 분석 보고서 */}
                {activeResultTab === 'report' && (
                  <div className="space-y-6 fade-in">
                    <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 text-xs leading-relaxed font-mono whitespace-pre-wrap max-h-96 overflow-y-auto">
                      {simState.finalReport}
                    </div>
                    
                    {simState.issues.length > 0 && (
                      <div className="space-y-4">
                        <h4 className="text-sm font-bold text-slate-200">⚠️ 탐지된 독소 조항 세부 내용</h4>
                        {simState.issues.map((issue) => (
                          <div 
                            key={issue.id} 
                            className={`p-4 rounded-xl border ${
                              issue.risk === 'HIGH' ? 'bg-rose-950/15 border-rose-900/30' : 'bg-amber-950/15 border-amber-900/30'
                            }`}
                          >
                            <div className="flex justify-between items-start mb-2">
                              <span className={`badge ${issue.risk === 'HIGH' ? 'badge-danger' : 'badge-warning'}`}>
                                Risk: {issue.risk}
                              </span>
                              <span className="text-xs text-slate-500 font-semibold">{issue.lawBasis}</span>
                            </div>
                            <h5 className="text-sm font-bold text-slate-200 mb-1">{issue.title}</h5>
                            <p className="text-xs text-rose-300 font-mono bg-slate-950/40 p-2 rounded mb-2 border border-slate-900">
                              {issue.clause}
                            </p>
                            <p className="text-xs text-slate-300 mb-3">{issue.lawDetail}</p>
                            <div className="text-xs text-emerald-300 font-semibold bg-emerald-950/20 p-2 rounded border border-emerald-900/30">
                              💡 수정안: {issue.suggestion}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 탭 2: 비즈니스 메일 초안 */}
                {activeResultTab === 'email' && (
                  <div className="space-y-4 fade-in">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-slate-400">상대방 담당자에게 보낼 수정 요청 이메일 가이드 초안입니다.</span>
                      <button 
                        onClick={() => handleCopy(simState.emailDraft, 'email')}
                        className="btn btn-secondary py-1.5 px-3 text-xs flex items-center gap-1.5"
                      >
                        <Copy className="w-3.5 h-3.5" /> 
                        {copySuccess === 'email' ? '복사 완료!' : '복사하기'}
                      </button>
                    </div>
                    <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 text-xs leading-relaxed font-mono whitespace-pre-wrap max-h-96 overflow-y-auto">
                      {simState.emailDraft}
                    </div>
                  </div>
                )}

                {/* 탭 3: 데이터 마스킹 비교 */}
                {activeResultTab === 'masking' && (
                  <div className="space-y-4 fade-in">
                    <p className="text-xs text-slate-400">
                      외부 LLM API 호출 전, 기업 기밀 및 개인 식별 정보를 암호화 토큰으로 완벽 필터링합니다. 분석 결과 출력 시 로컬에서 다시 복원됩니다.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <span className="text-xs font-semibold text-slate-400 block mb-2">Original (원본)</span>
                        <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-800 text-xs font-mono h-80 overflow-y-auto leading-relaxed">
                          {inputText}
                        </div>
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-slate-400 block mb-2 flex items-center gap-1 text-emerald-400">
                          Masked (마스킹 - 외부 전송 상태)
                        </span>
                        <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-800 text-xs font-mono h-80 overflow-y-auto leading-relaxed text-slate-400">
                          {simState.maskedText}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* 하단 다운로드/초기화 기능 */}
              <div className="flex justify-end gap-2 border-t border-slate-800 pt-4 mt-6">
                <button 
                  onClick={() => handleCopy(activeResultTab === 'report' ? simState.finalReport : simState.emailDraft, 'file')}
                  className="btn btn-primary text-xs"
                >
                  {copySuccess === 'file' ? '클립보드 복사 완료!' : '스크리닝 결과 복사'}
                </button>
                <button 
                  onClick={() => {
                    setInputText('');
                    setShowResults(false);
                    setStep(0);
                    setSelectedSample('');
                  }}
                  className="btn btn-secondary text-xs"
                >
                  처음으로 돌아가기
                </button>
              </div>
            </div>
          ) : (
            // 스크리닝 대기 상태 카드
            <div className="glass-panel min-h-[500px] flex flex-col items-center justify-center text-center p-8 space-y-4">
              <div className="w-16 h-16 bg-slate-900 rounded-2xl border border-slate-800 flex items-center justify-center mb-2">
                <Shield className="w-8 h-8 text-slate-600" />
              </div>
              <h3 className="text-lg font-bold text-slate-200">1차 분석 대기 중</h3>
              <p className="text-xs text-slate-500 max-w-sm">
                좌측 입력 필드에 계약서 내용을 기재하거나 샘플 계약서를 선택한 후, <strong className="text-emerald-400">‘스크리닝 에이전트 실행’</strong> 버튼을 눌러주세요.
              </p>
              
              {isRunning && (
                <div className="flex flex-col items-center gap-2 mt-4">
                  <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-xs text-emerald-400 font-semibold font-mono animate-pulse">
                    LangGraph Agent Pipeline Running...
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
