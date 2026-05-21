import React, { useState, useEffect, useRef } from 'react';
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
  Copy,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Edit3
} from 'lucide-react';

// 샘플 계약서 데이터 (제8조 지식재산권, 제12조 비밀유지 의무로 수정하여 기획안과 완벽 매치)
const SAMPLE_CONTRACTS = {
  subcontract: `소프트웨어 개발 용역 계약서

제1조 (계약 목적)
본 계약은 발주처 주식회사 대성전자 (이하 "갑")와 수급처 (주)마이크로소프트웨어 (이하 "을") 간의 인공지능 기반 사내 시스템 개발 업무를 위탁함에 있어 상호 권리와 의무를 규정함을 목적으로 한다.

제3조 (계약 금액 및 지급)
총 계약 금액은 일금 오천만원정(₩50,000,000원, 부가세 별도)으로 한다. 을은 결과물을 2026년 08월 30일까지 납품 완료하여야 하며, 갑은 검수 완료 후 90일 이내에 현금으로 잔금을 지급한다.

제8조 (지식재산권의 귀속)
본 용역 계약의 수행 결과로 개발된 소프트웨어, 소스코드, 관련 특허 및 저작권을 포함한 일체의 지식재산권은 본 계약의 체결과 동시에 갑에게 전적으로 영구 귀속된다. 을은 이에 대해 저작인격권 등 어떠한 권리도 주장할 수 없으며, 저작자로서의 상업적 이용 및 권리 주장 또한 영구히 배제된다.

제10조 (지체상금 및 위약금)
을이 납기를 준수하지 못할 경우, 지체 1일당 총 계약금액의 1,000분의 3(0.3%)에 해당하는 지체상금을 갑에게 즉시 납부해야 한다. 어떠한 천재지변이나 불가항력적 사유도 지체상금 면책의 조건이 될 수 없다.

제12조 (비밀유지 의무 및 기간)
을은 본 계약의 수행 과정에서 지득한 갑의 모든 기술 정보 및 사업 비밀에 대하여 계약 기간 중은 물론 계약 종료 후에도 영구히 비밀로 유지하여야 하며, 어떠한 경우에도 제3자에게 누설해서는 안 된다. 본 비밀유지 의무는 기한의 정함이 없이 영속하며, 갑은 본 의무에 구속되지 않고 정보를 활용할 수 있다.`,

  clean: `표준 소프트웨어 개발 용역 계약서

제1조 (계약 목적)
본 계약은 발주처 주식회사 대성전자 (이하 "갑")와 수급처 (주)마이크로소프트웨어 (이하 "을") 간의 인공지능 기반 사내 시스템 개발 업무를 위탁함에 있어 상호 권리와 의무를 규정함을 목적으로 한다.

제3조 (계약 금액 및 지급)
총 계약 금액은 일금 오천만원정(₩50,000,000원, 부가세 별도)으로 한다. 을은 결과물을 2026년 08월 30일까지 납품 완료하여야 하며, 갑은 검수 완료 후 60일 이내에 하도급 대금을 지급한다.

제8조 (지식재산권의 귀속)
본 계약에 따라 을이 창작한 결과물의 지식재산권은 갑과 을이 공동으로 소유하는 것을 원칙으로 하며, 세부적인 활용 범위 및 지분 비율은 양사의 기여도에 따라 성실히 협의하여 결정한다.

제10조 (지체상금)
을이 납기를 준수하지 못할 경우, 지체 1일당 총 계약금액의 10,000분의 5(0.05%)에 해당하는 지체상금을 지급하되, 불가항력적 사유에 의한 경우에는 예외로 하며 총액의 10%를 초과할 수 없다.

제12조 (비밀유지 의무 및 기간)
양사는 본 계약과 관련하여 상대방으로부터 제공받은 모든 기밀 정보를 비밀로 유지하며, 본 비밀유지 의무는 계약의 종료 또는 해지 후 3년간 존속한다.`
};

const NODES = [
  { id: 1, label: "[Parser] 비정형 계약서 조·항·호 구조적 파싱 및 전처리" },
  { id: 2, label: "[Masker] 로컬 보안 모듈 - PII 및 기업 민감 정보 암호화(마스킹)" },
  { id: 3, label: "[Screener] 마스킹 텍스트 기반 독소 조항 1차 스크리닝(LLM)" },
  { id: 4, label: "[RAG Retriever] 하이브리드 검색 기반 법령 및 사내 DB 매핑" },
  { id: 5, label: "[Guardrail] 소스 가드레일 - 가짜 인용 정보 검증 (할루시네이션 방지)" },
  { id: 6, label: "[Generator] 스크리닝 위험 분석 리포트 & 메일 초안 자동 빌드" },
  { id: 7, label: "[De-masker] 최종 보고서 내 식별자 정보 원본 데이터 역치환 복원" },
];

export default function Dashboard() {
  const [inputText, setInputText] = useState('');
  const [selectedSample, setSelectedSample] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [step, setStep] = useState(0); // 0: 대기, 1~7: 에이전트 단계
  const [progress, setProgress] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const [activeResultTab, setActiveResultTab] = useState('report'); // report, email, masking
  const [copySuccess, setCopySuccess] = useState('');
  const [showToast, setShowToast] = useState(false);
  
  // 신규 드롭존 및 인터랙션 상태
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isDirectInput, setIsDirectInput] = useState(false);
  const [selectedIssueId, setSelectedIssueId] = useState('ISSUE_IP');
  const fileInputRef = useRef(null);

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
    setUploadedFile({
      name: key === 'subcontract' ? '소프트웨어_개발_용역_계약서_초안.docx' : '표준_소프트웨어_개발_용역_계약서_합의본.docx',
      size: key === 'subcontract' ? '28.4' : '24.1'
    });
    setIsDirectInput(false);
    setShowResults(false);
    setStep(0);
  };

  const triggerFileSelect = () => {
    fileInputRef.current.click();
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      processUploadedFile(files[0]);
    }
  };

  const handleFileSelect = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      processUploadedFile(files[0]);
    }
  };

  const processUploadedFile = (file) => {
    const ext = file.name.split('.').pop().toLowerCase();
    if (['pdf', 'docx', 'txt'].includes(ext)) {
      setUploadedFile({
        name: file.name,
        size: (file.size / 1024).toFixed(1)
      });
      setSelectedSample('');
      setIsDirectInput(false);

      if (ext === 'txt') {
        const reader = new FileReader();
        reader.onload = (event) => {
          setInputText(event.target.result);
        };
        reader.readAsText(file);
      } else {
        // PDF, DOCX는 데모 시뮬레이션용 파일명에 따라 매핑 분기
        const isCleanKeyword = file.name.includes("표준") || 
                               file.name.includes("합의본") || 
                               file.name.includes("clean") || 
                               file.name.includes("safe");
        if (isCleanKeyword) {
          setInputText(SAMPLE_CONTRACTS.clean);
        } else {
          setInputText(SAMPLE_CONTRACTS.subcontract);
        }
      }
      setShowResults(false);
    } else {
      alert("법무 검토에 적합한 문서 확장자만 안정적으로 수용합니다. (PDF, Word, Text 파일만 지원)");
    }
  };

  const handleCopy = (text, type) => {
    navigator.clipboard.writeText(text);
    setCopySuccess(type);
    setShowToast(true);
    setTimeout(() => {
      setCopySuccess('');
      setShowToast(false);
    }, 2000);
  };

  // 실시간 시뮬레이션 타이머 연동 (3초 고속 로딩 스캔)
  const startScreening = () => {
    if (!inputText.trim()) {
      alert("계약서 파일을 업로드하거나 샘플 계약서를 선택해 주세요.");
      return;
    }

    setIsRunning(true);
    setShowResults(false);
    setProgress(0);
    setStep(1);

    const duration = 3000; // 3초 하이테크 로딩 시나리오
    const intervalTime = 30; // 30ms 간격 업데이트
    const increment = 100 / (duration / intervalTime);

    let currentProgress = 0;
    const timer = setInterval(() => {
      currentProgress += increment;
      if (currentProgress >= 100) {
        currentProgress = 100;
        clearInterval(timer);
        
        setStep(8);
        setIsRunning(false);
        setShowResults(true);
        generateSimulationData();
      } else {
        setProgress(Math.round(currentProgress));
        // 진행률에 따라 실시간으로 LangGraph 노드를 스텝 업 (1 ~ 7단계)
        const currentStep = Math.min(7, Math.floor(currentProgress / 14.2) + 1);
        setStep(currentStep);
      }
    }, intervalTime);
  };

  // Python 백엔드 로직에 기반한 시뮬레이션 결과 생성
  const generateSimulationData = () => {
    const isSubcontract = inputText.includes("영구 귀속") || inputText.includes("0.3%") || selectedSample === 'subcontract';
    
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
            title: "제8조 지식재산권 귀속 독소 조항",
            risk: "DANGER",
            clause: "제8조 (지식재산권의 귀속)\n...일체의 지식재산권은 본 계약의 체결과 동시에 갑에게 전적으로 영구 귀속된다. 을은 이에 대해 저작인격권 등 어떠한 권리도 주장할 수 없으며...",
            lawBasis: "사내 가이드라인 IP 귀속 제3조 및 불공정거래 심사지침",
            lawDetail: "용역 결과물에 대한 지식재산권을 기여도 안분이나 상응 대가 없이 원사업자(갑)에게 일방적·영구 무상 독점 귀속시키는 조항은 법적 분쟁 소지가 매우 높으며 사내 표준 규정에 위배됩니다.",
            suggestion: "결과물에 대한 지식재산권은 양사 공동 소유로 수정하거나, 발주처 독점 귀속 시 을의 고유 특허 권리에 대한 면책 및 합당한 사용료 지불 조항을 협의해야 합니다."
          },
          {
            id: "ISSUE_CONFIDENTIALITY",
            title: "제12조 비밀유지 의무 일방 부과 및 무기한 설정",
            risk: "WARNING",
            clause: "제12조 (비밀유지 의무 및 기간)\n...계약 종료 후에도 영구히 비밀로 유지하여야 하며... 본 비밀유지 의무는 기한의 정함이 없이 영속하며, 갑은 본 의무에 구속되지 않고...",
            lawBasis: "하도급거래 표준계약서 안 및 사내 정보보호 정책 제5조",
            lawDetail: "비밀유지 의무 기간을 기한 없이 '영구'로 설정하고, 을에게만 일방적인 패널티를 지우는 구조는 불공정 계약 조건에 해당합니다. 표준 존속 기한 설정이 권장됩니다.",
            suggestion: "비밀유지 의무를 상호 대등한 쌍무 조항으로 수정하고, 유효 기한을 '계약 종료 또는 해지 후 3년'으로 제한하는 명시적 수정이 필요합니다."
          },
          {
            id: "ISSUE_LIABILITY",
            title: "과도한 지체상금 및 불가항력 조항 배제",
            risk: "DANGER",
            clause: "제10조 (지체상금 및 위약금)\n...지체 1일당 총 계약금액의 1,000분의 3(0.3%)에 해당하는 지체상금... 어떠한 천재지변이나 불가항력적 사유도 지체상금 면책의 조건이 될 수 없다.",
            lawBasis: "상법 표준 지체요율 가이드 및 하도급법 제13조",
            lawDetail: "1일당 0.3% 지체상금율은 통상적인 소프트웨어 개발 표준 요율(0.05%~0.1%)의 약 3배에서 6배에 해당합니다. 천재지변 면책 불가 조항 또한 계약 당사자의 정당한 권리를 배제합니다.",
            suggestion: "지체상금 요율을 기재부 및 업계 표준인 0.05%~0.1% 수준으로 인하하고, 천재지변 등 불가항력적인 지연은 면책한다는 예외 규정과 총액 10%의 상한선을 추가해야 합니다."
          }
        ],
        finalReport: `[1차 법무 스크리닝 AI 위험 분석 보고서]

본 보고서는 LangGraph 멀티 에이전트 파이프라인에 의해 1차 자동 스크리닝된 결과이며, 공식적인 법적 효력을 갖지 않으므로 최종 계약 전 사내 법무팀과의 교차 검토를 추천합니다.

1. 검토 요약
  - 업로드된 계약서에서 총 3건의 리스크 요인이 검출되었습니다.
  - DANGER (중대 위험): 2건
  - WARNING (주의 요구): 1건

2. 상세 위험 분석 결과
  
  ■ [DANGER] 제8조 지식재산권 귀속 독소 조항
    - 관련 조항: 제8조 (지식재산권의 귀속)
    - 위험 요소: 을의 고유 산출물 권리까지 갑에게 대가 없이 일방적 영구 독점 귀속시킴.
    - 매핑 근거: 사내 가이드라인 IP 귀속 제3조 (기여도 안분 및 공동 소유 표준)
    - 수정 가이드: "성과물의 지식재산권은 양사 공동 소유로 하며, 활용 범위는 협의하여 결정한다"로 수정 요망.

  ■ [DANGER] 과도한 지체상금 및 불가항력 조항 배제
    - 관련 조항: 제10조 (지체상금 및 위약금)
    - 위험 요소: 표준 지체상금율(0.05%)을 초과하는 1일당 0.3% 부과 및 불가항력 면책 차단.
    - 매핑 근거: 하도급법 제13조 및 상법 표준안
    - 수정 가이드: 지체상금율을 0.05%로 하향 조정 및 상한선(최대 10%) 추가.

  ■ [WARNING] 제12조 비밀유지 의무 일방 부과 및 무기한 설정
    - 관련 조항: 제12조 (비밀유지 의무 및 기간)
    - 위험 요소: 무제한 비밀유지 기간 설정 및 발주처 면책 독소 조항.
    - 매핑 근거: 사내 표준 규정 책임제한 제5조 & 민법 제398조
    - 수정 가이드: 비밀유지 의무를 상호 쌍무화하고 보존 기간을 계약 종료 후 3년으로 제한.`,
        
        emailDraft: `받는사람: 주식회사 대성전자 계약담당자 귀하
보낸사람: (주)마이크로소프트웨어 법무/계약 실무 담당자

제목: [수정 요청] 소프트웨어 개발 용역 계약서 조항 수정 제안의 건

안녕하십니까, 주식회사 대성전자 담당자님.
보내주신 '소프트웨어 개발 용역 계약서' 초안에 대해 감사드리며, 당사 내부의 안정적인 업무 수행 및 상호 신뢰를 바탕으로 한 공정한 계약 관계 구축을 위해 아래와 같이 일부 조항에 대한 정중한 수정 검토를 제안드립니다.

[주요 수정 제안 사항]

1. 제8조 (지식재산권의 귀속) 관련
  - 현행: 소프트웨어 및 일체의 지식재산권이 갑에게 전적으로 영구 귀속됨.
  - 제안: 양사의 공동 개발 성격 및 기술 파트너십 유지를 위해, 결과물의 지식재산권은 기여도에 따라 양사 공동 소유로 하거나, 별도의 활용 협약을 맺는 방향으로 수정을 희망합니다.

2. 제10조 (지체상금 및 위약금) 관련
  - 현행: 납기 지연 시 불가항력 포함 1일당 0.3% 부과.
  - 제안: 관계 법령과 일반 상거래 관행에 부합하도록 지체상금율을 일당 0.05%로 하향 조정하고, 불가항력적 사유 시 지연이 면책되는 조항 보완 및 총 지체상금의 한도(상한 10%) 규정을 추가해주시기 바랍니다.

3. 제12조 (비밀유지 의무 및 기간) 관련
  - 현행: 을에게만 일방적인 비밀유지 의무 부과 및 기한 없는 영속 설정.
  - 제안: 상호 기밀 유지를 원칙으로 한 쌍무 의무로 개정하고, 비밀 보증 존속 기간을 계약 종료 후 3년으로 한정해 주실 것을 제안합니다.

보내드리는 제안 사항에 대해 긍정적인 검토를 부탁드리며, 조율 가능한 미팅 일정이나 의견 회신해 주시면 감사하겠습니다.

감사합니다.
(주)마이크로소프트웨어 드림`
      });
      setSelectedIssueId('ISSUE_IP');
    } else {
      setSimState({
        maskedText: masked,
        issues: [],
        finalReport: `[1차 법무 스크리닝 AI 위험 분석 보고서]

1. 검토 요약
  - 업로드된 표준 소프트웨어 개발 용역 계약서 검토 결과, 독소 조항이나 불공정 요소가 검출되지 않았습니다.
  - 모든 조항(지식재산권 공동소유, 표준 지체상금율 0.05%, 책임 제한 한도 상호 100%)이 사내 가이드라인 및 하도급법 요건을 충족합니다.
  - 즉시 날인 및 체결을 진행하셔도 안전합니다.`,
        emailDraft: `받는사람: 주식회사 대성전자 계약담당자 귀하
보낸사람: (주)마이크로소프트웨어 법무/계약 실무 담당자

제목: [검토 완료] 소프트웨어 개발 용역 계약서 날인 진행의 건

안녕하십니까, 담당자님.
검토 요청해주신 계약서를 내부 AI 법무 스크리닝을 통해 1차 검증한 결과, 모든 조항이 공정거래 표준 규정 및 사내 리스크 기준을 완벽하게 만족함을 확인하였습니다.

별도의 조항 수정 요구 없이 정식 서명 날인 절차를 진행하고자 하오니, 날인 가능한 시간과 장소를 알려주시면 감사하겠습니다.

감사합니다.
(주)마이크로소프트웨어 드림`
      });
    }
  };

  // 계약서 텍스트 중 독소 조항을 실시간으로 감지하여 하이라이트하는 렌더링 함수
  const renderHighlightedContract = (text, selectedId, onSelect) => {
    if (!text) return <p className="text-slate-500 text-sm">계약서 내용이 비어있습니다.</p>;
    
    // 안전 계약서(이슈 없음)의 경우 조항 하이라이트 렌더링을 완전히 생략
    if (simState.issues.length === 0) {
      return text.split('\n').map((line, idx) => (
        <p key={idx} className="mb-2.5 text-slate-400 font-mono text-xs">{line}</p>
      ));
    }

    const lines = text.split('\n');
    return lines.map((line, idx) => {
      let isIntellectualProperty = line.includes("지식재산권") || line.includes("제8조") || line.includes("영구 귀속");
      let isConfidentiality = line.includes("비밀유지") || line.includes("제12조");
      let isLiability = line.includes("지체상금") || line.includes("0.3%") || line.includes("위약금") || line.includes("제10조");

      if (isIntellectualProperty && text.includes("영구 귀속")) {
        const isSelected = selectedId === 'ISSUE_IP';
        return (
          <p key={idx} className="mb-2.5">
            <span 
              onClick={() => onSelect('ISSUE_IP')}
              className={`highlight-danger ${isSelected ? 'highlight-selected' : ''} inline-block w-full`}
              title="클릭하여 변호사 의견 보기"
            >
              {line}
            </span>
          </p>
        );
      } else if (isConfidentiality && text.includes("비밀유지")) {
        const isSelected = selectedId === 'ISSUE_CONFIDENTIALITY';
        return (
          <p key={idx} className="mb-2.5">
            <span 
              onClick={() => onSelect('ISSUE_CONFIDENTIALITY')}
              className={`highlight-warning ${isSelected ? 'highlight-selected' : ''} inline-block w-full`}
              title="클릭하여 변호사 의견 보기"
            >
              {line}
            </span>
          </p>
        );
      } else if (isLiability && (text.includes("0.3%") || text.includes("불가항력"))) {
        const isSelected = selectedId === 'ISSUE_LIABILITY';
        return (
          <p key={idx} className="mb-2.5">
            <span 
              onClick={() => onSelect('ISSUE_LIABILITY')}
              className={`highlight-danger ${isSelected ? 'highlight-selected' : ''} inline-block w-full`}
              title="클릭하여 변호사 의견 보기"
            >
              {line}
            </span>
          </p>
        );
      }
      
      return <p key={idx} className="mb-2.5 text-slate-400 font-mono text-xs">{line}</p>;
    });
  };

  // SVG 도넛 게이지 서클 컴포넌트
  const renderGaugeCircle = (score) => {
    const radius = 50;
    const stroke = 6;
    const normalizedRadius = radius - stroke * 2;
    const circumference = normalizedRadius * 2 * Math.PI;
    const strokeDashoffset = circumference - (score / 100) * circumference;

    return (
      <div className="flex flex-col items-center justify-center p-4 bg-slate-900/40 border border-slate-900/60 rounded-xl w-36 text-center">
        <span className="text-[9px] font-bold text-slate-500 tracking-wider uppercase mb-1">리스크 지수</span>
        <div className="relative flex items-center justify-center w-24 h-24">
          <svg className="w-full h-full transform -rotate-90">
            <circle
              stroke="rgba(255, 255, 255, 0.04)"
              fill="transparent"
              strokeWidth={stroke}
              r={normalizedRadius}
              cx="50%"
              cy="50%"
            />
            <circle
              stroke="url(#silverGradient)"
              fill="transparent"
              strokeWidth={stroke}
              strokeDasharray={circumference + ' ' + circumference}
              style={{ strokeDashoffset, transition: 'stroke-dashoffset 0.8s ease' }}
              r={normalizedRadius}
              cx="50%"
              cy="50%"
            />
            <defs>
              <linearGradient id="silverGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ffffff" />
                <stop offset="100%" stopColor="#475569" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute flex flex-col items-center justify-center leading-none text-slate-200">
            <span className="text-[8px] font-bold text-slate-500 tracking-tight">위험도</span>
            <span className="text-2xl font-black mt-0.5">{score}</span>
            <span className="text-[8px] font-bold text-slate-500 tracking-tight">점</span>
          </div>
        </div>
      </div>
    );
  };

  // 우측 슬라이딩 변호사 의견 카드 렌더링
  const renderRightOpinionCard = () => {
    if (simState.issues.length === 0) {
      return (
        <div className="glass-panel border-slate-800 p-6 flex flex-col justify-center items-center text-center h-[520px] fade-in">
          <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-4">
            <CheckCircle className="w-6 h-6 text-slate-300" />
          </div>
          <h4 className="text-base font-bold text-slate-200">리스크 프리 (안전)</h4>
          <p className="text-xs text-slate-400 max-w-[240px] leading-relaxed mt-2">
            AI 에이전트의 1차 진단 결과, 사내 규정 및 법령을 위반하거나 수급인에게 과도하게 불리한 독소 조항이 발견되지 않았습니다. 즉시 계약 진행이 가능합니다.
          </p>
          <div className="text-[9px] text-slate-500 font-mono mt-6 flex items-center gap-1">
            <Database className="w-3 h-3" /> 규정 DB 교차검증 완료 100%
          </div>
        </div>
      );
    }
    
    const selectedIssue = simState.issues.find(issue => issue.id === selectedIssueId) || simState.issues[0];
    if (!selectedIssue) return null;
    
    return (
      <div 
        key={selectedIssue.id} 
        className="glass-panel border-slate-800 p-6 flex flex-col justify-between h-[520px] fade-in"
      >
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className={`badge ${selectedIssue.risk === 'DANGER' ? 'badge-danger' : 'badge-warning'}`}>
              {selectedIssue.risk === 'DANGER' ? '중대 위험' : '주의 요구'}
            </span>
            <span className="text-[9px] text-slate-500 font-mono">{selectedIssue.id}</span>
          </div>
          
          <h4 className="text-sm font-bold text-slate-200">{selectedIssue.title}</h4>
          
          <div className="space-y-1">
            <span className="text-[9px] font-semibold text-slate-500 tracking-wider uppercase">검출 조항 원문</span>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-900 font-mono text-xs text-rose-300/80 max-h-24 overflow-y-auto whitespace-pre-wrap leading-relaxed">
              {selectedIssue.clause}
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[9px] font-semibold text-slate-500 tracking-wider uppercase">판례 및 규정 근거</span>
            <div className="text-xs text-slate-400 font-semibold flex items-center gap-1.5 mt-0.5">
              <Database className="w-3.5 h-3.5 text-slate-500" /> {selectedIssue.lawBasis}
            </div>
            <p className="text-xs text-slate-400 leading-relaxed mt-1 overflow-y-auto max-h-20">
              {selectedIssue.lawDetail}
            </p>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-900 space-y-1.5">
          <span className="text-[9px] font-semibold text-slate-500 tracking-wider uppercase">변호사 추천 수정 대안</span>
          <div className="bg-emerald-950/10 border border-emerald-900/20 p-3 rounded-lg text-xs text-emerald-300/90 leading-relaxed font-mono">
            💡 {selectedIssue.suggestion}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-8 fade-in">
      {/* 타이틀 헤더 */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-900 pb-6">
        <div>
          <span className="badge badge-primary mb-2 flex items-center gap-1.5 w-fit">
            <Shield className="w-3.5 h-3.5" /> Local Security Active
          </span>
          <h2 className="text-2xl font-extrabold text-slate-100 font-title">
            Deepgle Legal AI 스크리닝
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            계약서 파일을 드롭하여 독소 조항 스크리닝 및 규정 매핑 보고서를 실시간 생성합니다.
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

      {/* 1. 업로드 및 대기 화면 */}
      {!showResults && !isRunning && (
        <div className="space-y-6">
          {/* 드롭존 영역 */}
          {!isDirectInput && (
            <div 
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={triggerFileSelect}
              className={`glass-panel border-dashed border-2 p-12 text-center cursor-pointer transition-all duration-300 flex flex-col items-center justify-center min-h-[300px] ${
                isDragging 
                  ? 'border-white bg-slate-900/80 scale-[1.01]' 
                  : 'border-slate-800 hover:border-slate-700 bg-slate-950/30'
              }`}
            >
              <input 
                type="file" 
                ref={fileInputRef}
                onChange={handleFileSelect}
                className="hidden"
                accept=".pdf,.docx,.txt"
              />
              
              <div className="w-14 h-14 bg-slate-900 rounded-2xl border border-slate-800 flex items-center justify-center mb-4 transition-transform duration-300 hover:scale-105">
                <Upload className="w-6 h-6 text-slate-400" />
              </div>
              <h3 className="text-base font-bold text-slate-200 mb-1.5">검토할 계약서 파일 드래그 앤 드롭</h3>
              <p className="text-xs text-slate-500 max-w-md leading-relaxed">
                마우스로 PDF나 Word(docx), Text(txt) 파일을 끌어다 놓거나 클릭하여 쉽게 파일을 첨부할 수 있습니다.
              </p>
              <span className="text-[10px] text-slate-600 mt-4 font-mono">
                지원 형식: PDF, DOCX, TXT (법무 보안 필터링 적용)
              </span>
            </div>
          )}

          {/* 직접 붙여넣기 텍스트 입력창 (토글형) */}
          {isDirectInput && (
            <div className="glass-panel space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-slate-400" /> 계약서 텍스트 직접 입력
                </h3>
                <span className="text-xs text-slate-500">{inputText.length} 자 입력됨</span>
              </div>
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="여기에 검토가 필요한 계약서 내용을 붙여넣어 주세요."
                className="w-full h-72 bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-xs text-slate-300 focus:outline-none focus:border-slate-500 focus:ring-1 focus:ring-slate-800 transition-all font-mono leading-relaxed resize-none"
              />
            </div>
          )}

          {/* 업로드 완료 상태 표시 카드 */}
          {uploadedFile && (
            <div className="glass-panel border-slate-800 flex justify-between items-center p-4 fade-in">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-slate-300" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-200">{uploadedFile.name}</h4>
                  <p className="text-[10px] text-slate-500">{uploadedFile.size} KB • 대기 중</p>
                </div>
              </div>
              
              <div className="flex gap-2">
                <button 
                  onClick={() => {
                    setUploadedFile(null);
                    setInputText('');
                  }}
                  className="btn btn-secondary py-1.5 px-3 text-xs"
                >
                  초기화
                </button>
                <button 
                  onClick={startScreening}
                  className="btn btn-primary py-1.5 px-4 text-xs flex items-center gap-1.5"
                >
                  분석 시작하기 <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}

          {/* 입력 전환 링크 버튼 */}
          <div className="text-center">
            <button 
              onClick={() => {
                setIsDirectInput(!isDirectInput);
                setUploadedFile(null);
                setInputText('');
              }}
              className="text-xs text-slate-400 hover:text-slate-200 underline font-medium"
            >
              {isDirectInput ? "📄 파일 드롭존 업로드 방식으로 전환" : "✍️ 계약서 본문 직접 붙여넣기"}
            </button>
          </div>
        </div>
      )}

      {/* 2. 하이테크 스캔 로딩 화면 (2가지 버전의 로딩 기능 완벽 통합) */}
      {isRunning && (
        <div className="glass-panel border-slate-800 py-16 flex flex-col items-center justify-center text-center space-y-6 relative overflow-hidden min-h-[450px] fade-in">
          
          {/* 가상 스캔 카드 */}
          <div className="relative w-56 h-32 bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between text-left overflow-hidden shadow-2xl z-10">
            {/* 레이저 스캔 광원 */}
            <div className="laser-scan-line"></div>
            
            <div className="flex justify-between items-start">
              <FileText className="w-8 h-8 text-slate-400" />
              <span className="text-[9px] bg-slate-800 border border-slate-700 text-slate-300 px-1.5 py-0.5 rounded font-mono animate-pulse">
                SCANNING
              </span>
            </div>
            <div>
              <h4 className="text-[10px] font-bold text-slate-300 truncate">
                {uploadedFile ? uploadedFile.name : "계약서_초안_임시본.txt"}
              </h4>
              <p className="text-[8px] text-slate-500 font-mono mt-0.5">
                {uploadedFile ? uploadedFile.size : "12.5"} KB
              </p>
            </div>
          </div>

          {/* 대기 문구 가이드 */}
          <div className="space-y-1.5 z-10">
            <h3 className="text-sm font-bold text-slate-200">AI 에이전트가 계약서를 정밀 분석 중입니다...</h3>
            <p className="text-[10px] text-slate-500">
              예상 소요 시간: 약 3분 (국가법령 및 사내 규정 DB 교차 검증 중)
            </p>
          </div>

          {/* 실시간 프로그레스 바 */}
          <div className="w-80 bg-slate-950 border border-slate-900 h-2.5 rounded-full overflow-hidden relative z-10">
            <div 
              className="bg-white h-full transition-all duration-100 ease-out" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>

          {/* 기술 강점: LangGraph 멀티 에이전트 파이프라인 트래커 동시 시각화 */}
          <div className="border-t border-slate-900 pt-6 w-full max-w-md">
            <span className="text-[9px] font-semibold text-slate-500 tracking-wider uppercase block mb-3 font-mono">
              LANGGRAPH PIPELINE TRACKING
            </span>
            <div className="space-y-2 mt-4 text-xs font-mono max-w-sm mx-auto text-left">
              {NODES.map((node) => {
                const isActive = step === node.id;
                const isCompleted = step > node.id;
                return (
                  <div 
                    key={node.id} 
                    className={`flex items-center gap-2 p-1.5 rounded transition-all duration-300 ${
                      isActive ? 'text-slate-100 font-bold scale-[1.01] bg-slate-900/50 border border-slate-800' :
                      isCompleted ? 'text-slate-500' : 'text-slate-700'
                    }`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${
                      isActive ? 'bg-white animate-pulse' :
                      isCompleted ? 'bg-slate-600' : 'bg-slate-800'
                    }`}></span>
                    <span className="truncate">{node.label}</span>
                    {isActive && (
                      <span className="text-[8px] bg-slate-800 border border-slate-750 text-slate-300 px-1 rounded animate-pulse ml-auto">
                        ACTIVE
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* 3. 분석 결과 대시보드 화면 */}
      {showResults && (
        <div className="space-y-6 fade-in">
          {/* 상단 통합 탭 네비게이션 */}
          <div className="flex border-b border-slate-900 pb-3 gap-6">
            <button 
              onClick={() => setActiveResultTab('report')}
              className={`pb-2 text-xs font-bold border-b-2 transition-all ${
                activeResultTab === 'report' ? 'border-white text-white' : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              📊 리스크 종합 분석
            </button>
            <button 
              onClick={() => setActiveResultTab('email')}
              className={`pb-2 text-xs font-bold border-b-2 transition-all ${
                activeResultTab === 'email' ? 'border-white text-white' : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              ✉️ 수정 요청 메일 에디터
            </button>
            <button 
              onClick={() => setActiveResultTab('masking')}
              className={`pb-2 text-xs font-bold border-b-2 transition-all ${
                activeResultTab === 'masking' ? 'border-white text-white' : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              🔒 데이터 마스킹 비교
            </button>
          </div>

          {/* 탭 1: 리스크 종합 분석 (게이지, 하이라이터 본문, 변호사 의견서 2분할 레이아웃) */}
          {activeResultTab === 'report' && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              
              {/* 좌측 영역 (8/12) */}
              <div className="lg:col-span-8 space-y-6">
                {/* 게이지 + 검출 요약 헤더 */}
                <div className="glass-panel border-slate-800 p-5 flex flex-col sm:flex-row items-center gap-6">
                  {renderGaugeCircle(simState.issues.length > 0 ? 85 : 12)}
                  <div className="space-y-2 text-center sm:text-left flex-1">
                    <span className="badge badge-primary">AI 진단 요약</span>
                    <h3 className="text-base font-bold text-slate-200">
                      {simState.issues.length > 0 
                        ? "위험 - 검토 및 계약 조율 강력 권고" 
                        : "안전 - 표준 하도급 조건 부합"}
                    </h3>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      {simState.issues.length > 0
                        ? `대법원 판례 및 사내 내부 규정 위반 조항이 총 ${simState.issues.length}건 발견되었습니다. 지식재산권 일방 귀속 조항과 과도한 배상 요율을 수정 조율할 필요가 있습니다.`
                        : "사내 표준 거래 가이드라인에 부합하며, 지식재산권 공동소유 및 표준 지체상금율 조건이 모두 만족됩니다."}
                    </p>
                    {simState.issues.length > 0 && (
                      <div className="flex flex-wrap gap-2 pt-1.5">
                        {simState.issues.map((issue) => (
                          <span 
                            key={issue.id}
                            onClick={() => setSelectedIssueId(issue.id)}
                            className={`text-[9px] px-2 py-0.5 rounded border font-mono font-bold cursor-pointer transition-all duration-200 ${
                              selectedIssueId === issue.id 
                                ? 'bg-white text-slate-900 border-white' 
                                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
                            }`}
                          >
                            {issue.title.split(" ")[0]} ({issue.risk})
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* 계약서 본문 검토 (원문 텍스트 내 리스크 실시간 하이라이트) */}
                <div className="glass-panel border-slate-800 space-y-4">
                  <div className="flex justify-between items-center border-b border-slate-900 pb-3">
                    <h4 className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-slate-400" /> 계약서 원문 검토
                    </h4>
                    <span className="text-[10px] text-slate-500">
                      {simState.issues.length > 0 
                        ? "💡 하이라이트 부분을 누르면 법무 에이전트 의견서가 변경됩니다" 
                        : "✅ 모든 문구가 안전 규정을 만족합니다"}
                    </span>
                  </div>
                  
                  <div className="bg-slate-950/60 border border-slate-900 rounded-xl p-6 h-[400px] overflow-y-auto leading-relaxed select-text">
                    {renderHighlightedContract(inputText, selectedIssueId, setSelectedIssueId)}
                  </div>
                </div>
              </div>

              {/* 우측 영역 (4/12) : 슬라이딩 변호사 정밀 의견서 카드 */}
              <div className="lg:col-span-4">
                <div className="sticky top-24">
                  {renderRightOpinionCard()}
                </div>
              </div>
            </div>
          )}

          {/* 탭 2: 비즈니스 메일 초안 에디터 (은백색 네온 글로우 & 토스트 알림 연동) */}
          {activeResultTab === 'email' && (
            <div className="glass-panel border-slate-800 space-y-6 fade-in max-w-4xl mx-auto">
              <div className="flex justify-between items-center border-b border-slate-900 pb-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                    <Mail className="w-4 h-4 text-slate-400" /> 수정 제안용 비즈니스 메일 초안 에디터
                  </h3>
                  <p className="text-[10px] text-slate-500 mt-1">
                    AI가 분석한 위반 조항의 타당한 대안이 녹아있는 발송용 이메일 템플릿입니다. 직접 수정 가능합니다.
                  </p>
                </div>
                <button 
                  onClick={() => handleCopy(simState.emailDraft, 'email')}
                  className="btn btn-primary py-1.5 px-4 text-xs flex items-center gap-1.5"
                >
                  <Copy className="w-3.5 h-3.5" /> 메일 초안 복사하기
                </button>
              </div>

              {/* 은백색 네온 글로우가 탑재된 텍스트박스 에디터 */}
              <div className="relative">
                <textarea
                  value={simState.emailDraft}
                  onChange={(e) => setSimState({ ...simState, emailDraft: e.target.value })}
                  className="w-full h-[400px] bg-slate-950/90 border border-slate-800 rounded-xl p-6 text-xs text-slate-300 font-mono leading-relaxed resize-none transition-all duration-300 neon-glow-silver"
                  placeholder="작성된 이메일 내용이 들어옵니다."
                />
                <div className="absolute bottom-4 right-4 flex items-center gap-1 text-[9px] text-slate-600 pointer-events-none">
                  <Edit2 className="w-3 h-3" /> 실시간 수정 활성화됨
                </div>
              </div>
            </div>
          )}

          {/* 탭 3: 데이터 마스킹 비교 (개인 정보 유출 원천 차단 시뮬레이터) */}
          {activeResultTab === 'masking' && (
            <div className="glass-panel border-slate-800 space-y-6 fade-in max-w-5xl mx-auto">
              <div className="border-b border-slate-900 pb-4">
                <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-slate-400" /> 보안 거버넌스 1: 외부 유출 방지 로컬 PII 마스킹
                </h3>
                <p className="text-[10px] text-slate-500 mt-1">
                  외부 LLM API 호출 전, 로컬 마스킹 엔진이 기업 민감 비밀 및 개인 정보를 식별 토큰으로 실시간 암호화합니다. 최종 결과 출력 시에만 복원됩니다.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-mono text-xs">
                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-slate-500 tracking-wider uppercase block">Original Contract (원본 문서)</span>
                  <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-900 h-80 overflow-y-auto leading-relaxed text-slate-300">
                    {inputText}
                  </div>
                </div>
                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-slate-500 tracking-wider uppercase block flex items-center gap-1.5 text-slate-300">
                    Masked Send-Payload (API 전송용 마스킹 문서)
                  </span>
                  <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-900 h-80 overflow-y-auto leading-relaxed text-slate-400">
                    {simState.maskedText}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 하단 제어 바 */}
          <div className="flex justify-end gap-2 border-t border-slate-900 pt-6">
            <button 
              onClick={() => {
                setUploadedFile(null);
                setInputText('');
                setShowResults(false);
                setStep(0);
                setSelectedSample('');
                setIsDirectInput(false);
              }}
              className="btn btn-secondary text-xs"
            >
              처음으로 돌아가기
            </button>
            <button 
              onClick={() => handleCopy(activeResultTab === 'report' ? simState.finalReport : simState.emailDraft, 'all')}
              className="btn btn-primary text-xs"
            >
              전체 검토 결과 복사
            </button>
          </div>
        </div>
      )}

      {/* 부드러운 복사 토스트 알림 팝업 */}
      <div className={`toast-popup ${showToast ? 'show' : ''}`}>
        ✉️ 클립보드에 초안 텍스트가 즉시 복사되었습니다.
      </div>
    </div>
  );
}
