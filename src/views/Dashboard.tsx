import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription } from '../components/Card';
import { Badge } from '../components/Badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/Table';
import { Accordion, AccordionItem } from '../components/Accordion';
import { sampleContract, koreanHeadings } from '../mockData/sampleContract';
import { 
  AlertTriangle, 
  FileText, 
  CheckCircle2, 
  Sparkles, 
  Upload, 
  RefreshCw, 
  Search, 
  FileCheck,
  ChevronRight,
  Info,
  Copy,
  Undo,
  Check,
  Activity,
  ShieldAlert
} from 'lucide-react';

interface ContractBlock {
  id: string;
  text: string;
  isRisk: boolean;
  riskId?: string;
  isResolved?: boolean;
  originalText?: string;
}

// Client-side lightweight word-level LCS (Longest Common Subsequence) diff utility
function computeWordDiff(str1: string, str2: string) {
  // Normalize whitespaces but keep structure
  const words1 = str1.split(/(\s+)/).filter(w => w.length > 0);
  const words2 = str2.split(/(\s+)/).filter(w => w.length > 0);
  
  const dp: number[][] = Array(words1.length + 1).fill(0).map(() => Array(words2.length + 1).fill(0));
  
  for (let i = 1; i <= words1.length; i++) {
    for (let j = 1; j <= words2.length; j++) {
      if (words1[i - 1] === words2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }
  
  const diff: { type: 'added' | 'removed' | 'common', text: string }[] = [];
  let i = words1.length, j = words2.length;
  
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && words1[i - 1] === words2[j - 1]) {
      diff.unshift({ type: 'common', text: words1[i - 1] });
      i--;
      j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      diff.unshift({ type: 'added', text: words2[j - 1] });
      j--;
    } else if (i > 0 && (j === 0 || dp[i][j - 1] < dp[i - 1][j])) {
      diff.unshift({ type: 'removed', text: words1[i - 1] });
      i--;
    }
  }
  
  return diff;
}

export const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'viewer'>('overview');
  const [selectedRiskId, setSelectedRiskId] = useState<string>('risk-2'); // default highlight high risk
  const [searchTerm, setSearchTerm] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadStep, setUploadStep] = useState<number>(0);
  const [diffViewMode, setDiffViewMode] = useState<'side-by-side' | 'redline'>('redline');
  const [shineBlockId, setShineBlockId] = useState<string | null>(null);

  // Stateful text blocks for direct interactive redlining
  const [blocks, setBlocks] = useState<ContractBlock[]>([
    { 
      id: 'intro', 
      text: `MUTUAL NON-DISCLOSURE AGREEMENT\n\nThis Mutual Non-Disclosure Agreement (the "Agreement") is entered into by and between Deepgle Design LLC ("Company") and Global Ventures Inc. ("Partner").\n\n1. PURPOSE & CONFIDENTIAL INFORMATION\nThe parties wish to explore a business opportunity of mutual interest (the "Purpose"). In connection with the Purpose, either party may disclose to the other party certain proprietary, sensitive, and confidential information, whether written, oral, or visual, labeled as confidential or which by its nature should be reasonably understood to be confidential.\n\n2. STANDARD OF CARE & PERMITTED USE\nThe Receiving Party shall maintain the Confidential Information in strict confidence and shall use at least the same degree of care, but no less than a reasonable degree of care, to prevent the unauthorized disclosure or use of the Disclosing Party's Confidential Information. The Receiving Party shall use the Confidential Information solely for the Purpose.`,
      isRisk: false 
    },
    { 
      id: 'risk-1', 
      text: `3. UNILATERAL PERPETUAL OBLIGATION\nNotwithstanding any termination of this Agreement, the Receiving Party’s obligations under this Agreement with respect to all Confidential Information disclosed shall continue in perpetuity from the date of disclosure. The Receiving Party agrees that all obligations of confidentiality shall remain binding indefinitely, regardless of whether the information ceases to be a trade secret or falls into the public domain through no fault of the Receiving Party.`, 
      isRisk: true, 
      riskId: 'risk-1',
      isResolved: false,
      originalText: `3. UNILATERAL PERPETUAL OBLIGATION\nNotwithstanding any termination of this Agreement, the Receiving Party’s obligations under this Agreement with respect to all Confidential Information disclosed shall continue in perpetuity from the date of disclosure. The Receiving Party agrees that all obligations of confidentiality shall remain binding indefinitely, regardless of whether the information ceases to be a trade secret or falls into the public domain through no fault of the Receiving Party.`
    },
    { 
      id: 'risk-2', 
      text: `4. INDEMNIFICATION AND UNLIMITED LIABILITY\nThe Receiving Party agrees to indemnify, defend, and hold harmless the Disclosing Party from and against any and all claims, liabilities, losses, damages, costs, or expenses (including reasonable attorneys' fees) arising out of or in connection with any breach of this Agreement by the Receiving Party. The Receiving Party agrees that its liability under this Section 4 shall be completely unlimited and shall not be subject to any caps or limitations of liability agreed upon elsewhere.`, 
      isRisk: true, 
      riskId: 'risk-2',
      isResolved: false,
      originalText: `4. INDEMNIFICATION AND UNLIMITED LIABILITY\nThe Receiving Party agrees to indemnify, defend, and hold harmless the Disclosing Party from and against any and all claims, liabilities, losses, damages, costs, or expenses (including reasonable attorneys' fees) arising out of or in connection with any breach of this Agreement by the Receiving Party. The Receiving Party agrees that its liability under this Section 4 shall be completely unlimited and shall not be subject to any caps or limitations of liability agreed upon elsewhere.`
    },
    { 
      id: 'risk-3', 
      text: `5. INTELLECTUAL PROPERTY OWNERSHIP AND AUTOMATIC ASSIGNMENT\nAll Confidential Information remains the sole property of the Disclosing Party. However, if the Receiving Party suggests any feedback, improvements, or modifications to the Disclosing Party's technology or business during the term of this Agreement, the Receiving Party hereby automatically and irrevocably assigns all right, title, and interest in and to such feedback, including all intellectual property rights therein, to the Disclosing Party without any requirement for further consideration or compensation.`, 
      isRisk: true, 
      riskId: 'risk-3',
      isResolved: false,
      originalText: `5. INTELLECTUAL PROPERTY OWNERSHIP AND AUTOMATIC ASSIGNMENT\nAll Confidential Information remains the sole property of the Disclosing Party. However, if the Receiving Party suggests any feedback, improvements, or modifications to the Disclosing Party's technology or business during the term of this Agreement, the Receiving Party hereby automatically and irrevocably assigns all right, title, and interest in and to such feedback, including all intellectual property rights therein, to the Disclosing Party without any requirement for further consideration or compensation.`
    },
    { 
      id: 'risk-4', 
      text: `6. GOVERNING LAW AND JURISDICTION\nThis Agreement, and all claims or causes of action arising hereunder, shall be governed by, and construed in accordance with, the laws of the State of New York, without regard to its conflict of laws principles. Any legal suit, action, or proceeding arising out of or relating to this Agreement shall be instituted exclusively in the federal courts of the United States or the courts of the State of New York, in each case located in the City of New York, County of New York, and each party irrevocably submits to the exclusive jurisdiction of such courts.`, 
      isRisk: true, 
      riskId: 'risk-4',
      isResolved: false,
      originalText: `6. GOVERNING LAW AND JURISDICTION\nThis Agreement, and all claims or causes of action arising hereunder, shall be governed by, and construed in accordance with, the laws of the State of New York, without regard to its conflict of laws principles. Any legal suit, action, or proceeding arising out of or relating to this Agreement shall be instituted exclusively in the federal courts of the United States or the courts of the State of New York, in each case located in the City of New York, County of New York, and each party irrevocably submits to the exclusive jurisdiction of such courts.`
    },
    { 
      id: 'outro', 
      text: `\nIN WITNESS WHEREOF, the parties hereto have executed this Mutual Non-Disclosure Agreement as of the date first written above.`, 
      isRisk: false 
    }
  ]);

  // Handle mock uploading file with sequential, multi-stage loading timeline
  const handleUpload = () => {
    if (isUploading) return;
    setIsUploading(true);
    setUploadStep(1);
    
    // Animate step 1 to 4 with staggered timers
    setTimeout(() => {
      setUploadStep(2);
      setTimeout(() => {
        setUploadStep(3);
        setTimeout(() => {
          setUploadStep(4);
          setTimeout(() => {
            setUploadStep(5); // finished analysis
            setIsUploading(false);
            setUploadSuccess(true);
            setTimeout(() => {
              setUploadSuccess(false);
              setUploadStep(0);
            }, 3000);
          }, 950);
        }, 800);
      }, 750);
    }, 850);
  };

  // Direct edit: apply AI recommendation to the document block text
  const handleApplyRecommendation = (riskId: string, recommendationText: string) => {
    setBlocks(prev => prev.map(block => {
      if (block.riskId === riskId) {
        // Find clause number from original block text to prefix
        const originalFirstLine = block.originalText?.split('\n')[0] || '';
        const match = originalFirstLine.match(/^(\d+\.\s+)/);
        const prefix = match ? match[1] : '';
        
        return {
          ...block,
          text: prefix + recommendationText,
          isResolved: true
        };
      }
      return block;
    }));

    // Trigger visual shine micro-animation on the document block
    setShineBlockId(riskId);
    setTimeout(() => {
      setShineBlockId(null);
    }, 1000);
  };

  // Direct edit: revert to original clause
  const handleRevertClause = (riskId: string) => {
    setBlocks(prev => prev.map(block => {
      if (block.riskId === riskId) {
        return {
          ...block,
          text: block.originalText || block.text,
          isResolved: false
        };
      }
      return block;
    }));
  };

  // Calculate current risk stats
  const activeRisks = sampleContract.risks.filter(r => {
    const block = blocks.find(b => b.riskId === r.id);
    return block && !block.isResolved;
  });

  const resolvedCount = blocks.filter(b => b.isRisk && b.isResolved).length;
  
  const highRiskCount = activeRisks.filter(r => r.severity === 'high').length;
  const mediumRiskCount = activeRisks.filter(r => r.severity === 'medium').length;
  const lowRiskCount = activeRisks.filter(r => r.severity === 'low').length;

  // Dynamically compute the Safety Score / Risk Index
  // Deduct 25 for each High Risk, 12 for Medium Risk, 5 for Low Risk
  const maxScore = 100;
  const penalty = (highRiskCount * 25) + (mediumRiskCount * 12) + (lowRiskCount * 5);
  const safetyScore = Math.max(0, maxScore - penalty);

  // SVG Radial Gauge Metrics
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (safetyScore / 100) * circumference;

  // Score visual text labels
  const getScoreInfo = (score: number) => {
    if (score >= 90) return { label: '최상 (Excellent)', color: 'text-emerald-600', stroke: '#10b981' };
    if (score >= 70) return { label: '양호 (Good)', color: 'text-sky-600', stroke: '#3b82f6' };
    if (score >= 50) return { label: '주의 (Caution)', color: 'text-amber-600', stroke: '#f59e0b' };
    return { label: '위험 (Warning)', color: 'text-rose-600', stroke: '#ef4444' };
  };

  const scoreInfo = getScoreInfo(safetyScore);

  const selectedRisk = sampleContract.risks.find(r => r.id === selectedRiskId);
  const selectedBlock = blocks.find(b => b.riskId === selectedRiskId);

  // Search filter
  const filteredRisksList = sampleContract.risks.filter(r => {
    const query = searchTerm.toLowerCase();
    return r.clauseName.toLowerCase().includes(query) || 
           r.summary.toLowerCase().includes(query) || 
           r.category.toLowerCase().includes(query);
  });

  // Helper to render word-level inline diff elements
  const renderWordDiff = (original: string, modified: string) => {
    if (!original || !modified) return null;
    
    // Strip clause numbers (like '4. ' or '3. ') from original comparison to match recommendation scope
    const origClean = original.replace(/^(\d+\.\s+)/, '');
    const diffs = computeWordDiff(origClean, modified);
    
    return (
      <div className="p-4 bg-slate-50/70 border border-slate-200/80 rounded-xl text-[13px] font-sans text-slate-800 leading-relaxed max-h-72 overflow-y-auto tracking-normal whitespace-pre-wrap select-text shadow-inner">
        {diffs.map((part, index) => {
          if (part.type === 'added') {
            return (
              <span key={index} className="diff-word-add mx-0.5">
                {part.text}
              </span>
            );
          } else if (part.type === 'removed') {
            return (
              <span key={index} className="diff-word-del mx-0.5">
                {part.text}
              </span>
            );
          }
          return <span key={index} className="opacity-90">{part.text}</span>;
        })}
      </div>
    );
  };

  return (
    <div className="w-full max-w-7xl mx-auto space-y-8 animate-fade-in-up">
      
      {/* Top Banner Dashboard Actions */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <div className="inline-flex items-center gap-1.5 bg-navy-50 text-navy-800 px-3 py-1 rounded-full border border-navy-100 text-xs font-semibold uppercase tracking-wider mb-2">
            <Activity className="w-3.5 h-3.5" />
            AI 법률 스크리닝 플랫폼
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 leading-tight tracking-tight">
            {koreanHeadings.dashboardTitle}
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            NDA 및 상거래 계약서 내 독소 조항과 배상 한도를 실시간 검출하고 최적의 대안 합의안을 작성합니다.
          </p>
        </div>

        {/* View Switcher Controls */}
        <div className="flex items-center gap-1.5 bg-slate-200/50 p-1.5 rounded-xl border border-slate-200/60 self-start shadow-sm">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4.5 py-2 rounded-lg text-xs font-bold tracking-wide transition-all duration-300 cursor-pointer ${
              activeTab === 'overview'
                ? 'bg-white text-navy-800 shadow-sm border border-slate-200/50'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            대시보드 홈 (Overview)
          </button>
          <button
            onClick={() => setActiveTab('viewer')}
            className={`px-4.5 py-2 rounded-lg text-xs font-bold tracking-wide transition-all duration-300 flex items-center gap-2 cursor-pointer ${
              activeTab === 'viewer'
                ? 'bg-white text-navy-800 shadow-sm border border-slate-200/50'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            실시간 문서 스크리닝 (Viewer)
            {activeRisks.length > 0 && (
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
              </span>
            )}
          </button>
        </div>
      </div>

      {/* VIEW 1: OVERVIEW DASHBOARD */}
      {activeTab === 'overview' && (
        <div className="space-y-8 animate-fade-in-up">
          
          {/* Key Metrics Dashboard Grid (Includes Circular Gauge Safety Summary) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            
            {/* dynamic Circular Safety Gauge (Takes 5 Cols on desktop) */}
            <Card variant="dashboard" className="lg:col-span-5 flex flex-col justify-between overflow-hidden relative group radial-glow-navy p-6 select-none">
              <div className="absolute top-0 right-0 w-32 h-32 bg-slate-100/10 rounded-bl-full pointer-events-none"></div>
              
              <CardHeader className="p-0 mb-4">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-navy-600"></span>
                  <CardTitle className="text-base font-bold text-slate-800">계약 안전성 종합 레포트</CardTitle>
                </div>
                <CardDescription className="text-xs">
                  검출된 리스크 가중치(위험도)를 정량 계산한 실시간 보안 신뢰 점수입니다.
                </CardDescription>
              </CardHeader>
              
              <div className="flex items-center gap-6 py-2">
                {/* SVG Circle Progress */}
                <div className="relative flex items-center justify-center shrink-0">
                  <svg className="w-26 h-26 transform -rotate-90">
                    {/* Background track */}
                    <circle
                      cx="52"
                      cy="52"
                      r={radius}
                      stroke="#f1f5f9"
                      strokeWidth="9"
                      fill="transparent"
                    />
                    {/* Animated color scale progress */}
                    <circle
                      cx="52"
                      cy="52"
                      r={radius}
                      stroke={scoreInfo.stroke}
                      strokeWidth="9"
                      fill="transparent"
                      strokeDasharray={circumference}
                      strokeDashoffset={strokeDashoffset}
                      strokeLinecap="round"
                      className="transition-all duration-1000 ease-out donut-segment"
                    />
                  </svg>
                  {/* Inside circle number */}
                  <div className="absolute flex flex-col items-center justify-center">
                    <span className="text-2xl font-extrabold text-slate-900 leading-none">{safetyScore}</span>
                    <span className="text-[10px] text-slate-500 font-bold mt-0.5 uppercase tracking-wide">Score</span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="text-xs text-slate-600 font-medium">안전성 평가 등급</div>
                  <div className={`text-lg font-extrabold ${scoreInfo.color} flex items-center gap-1.5`}>
                    {scoreInfo.label}
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed font-medium">
                    {safetyScore === 100 
                      ? "검출된 계약 리스크가 존재하지 않아 아주 안전합니다." 
                      : `고위험 요인을 포함하여 총 ${activeRisks.length}개의 리스크가 검출되었습니다.`
                    }
                  </p>
                </div>
              </div>
              
              <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs font-semibold">
                <span className="text-slate-600">
                  AI 권고안 반영률: <span className="text-navy-800 font-bold">{resolvedCount} / {sampleContract.risks.length} 건</span>
                </span>
                {safetyScore < 100 && (
                  <button 
                    onClick={() => {
                      // Navigate directly to viewer with high risk selected
                      const firstActive = activeRisks[0] || sampleContract.risks[0];
                      setSelectedRiskId(firstActive.id);
                      setActiveTab('viewer');
                    }}
                    className="text-navy-800 hover:text-navy-900 flex items-center gap-1 transition-colors group/btn cursor-pointer"
                  >
                    즉시 조치하기
                    <ChevronRight className="w-3.5 h-3.5 transition-transform group-hover/btn:translate-x-0.5" />
                  </button>
                )}
              </div>
            </Card>

            {/* Severity Breakdown Stats Cards Container (7 Cols) */}
            <div className="lg:col-span-7 grid sm:grid-cols-3 gap-6 items-stretch">
              
              {/* High Risks Card */}
              <Card variant="dashboard" className="border-l-4 border-rose-500 flex flex-col justify-between p-6 hover:-translate-y-1 shadow-sm transition-all duration-300">
                <CardHeader className="p-0">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-rose-800 uppercase tracking-wide">
                      {koreanHeadings.highRisks}
                    </span>
                    <div className="w-8 h-8 rounded-lg bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-500">
                      <ShieldAlert className="w-4 h-4" />
                    </div>
                  </div>
                  <div className="text-4xl font-extrabold text-rose-600 mt-3 tracking-tight">
                    {highRiskCount} <span className="text-xs text-slate-500 font-semibold">건</span>
                  </div>
                </CardHeader>
                <div className="text-[11px] text-slate-600 font-semibold pt-4 mt-2 border-t border-slate-100">
                  <Badge variant="high" className="px-2 py-0.5 text-[10px]">즉시 삭제 권고</Badge>
                </div>
              </Card>

              {/* Medium Risks Card */}
              <Card variant="dashboard" className="border-l-4 border-amber-500 flex flex-col justify-between p-6 hover:-translate-y-1 shadow-sm transition-all duration-300">
                <CardHeader className="p-0">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-amber-800 uppercase tracking-wide">
                      {koreanHeadings.mediumRisks}
                    </span>
                    <div className="w-8 h-8 rounded-lg bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-500">
                      <AlertTriangle className="w-4 h-4" />
                    </div>
                  </div>
                  <div className="text-4xl font-extrabold text-amber-600 mt-3 tracking-tight">
                    {mediumRiskCount} <span className="text-xs text-slate-500 font-semibold">건</span>
                  </div>
                </CardHeader>
                <div className="text-[11px] text-slate-600 font-semibold pt-4 mt-2 border-t border-slate-100">
                  <Badge variant="medium" className="px-2 py-0.5 text-[10px]">조건 조율 / 완화</Badge>
                </div>
              </Card>

              {/* Low Risks Card */}
              <Card variant="dashboard" className="border-l-4 border-emerald-500 flex flex-col justify-between p-6 hover:-translate-y-1 shadow-sm transition-all duration-300">
                <CardHeader className="p-0">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-emerald-800 uppercase tracking-wide">
                      {koreanHeadings.lowRisks}
                    </span>
                    <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-500">
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                  </div>
                  <div className="text-4xl font-extrabold text-emerald-600 mt-3 tracking-tight">
                    {lowRiskCount} <span className="text-xs text-slate-500 font-semibold">건</span>
                  </div>
                </CardHeader>
                <div className="text-[11px] text-slate-600 font-semibold pt-4 mt-2 border-t border-slate-100">
                  <Badge variant="low" className="px-2 py-0.5 text-[10px]">상대적 권고 / 경미</Badge>
                </div>
              </Card>

            </div>

          </div>

          {/* Interactive Screen & Upload Area */}
          <div className="grid lg:grid-cols-12 gap-8 items-start">
            
            {/* Left side: Upload Card (4 Cols) */}
            <div className="lg:col-span-4 space-y-6">
              <Card variant="dashboard" className="flex flex-col justify-between border-dashed border-2 hover:border-navy-800/40 p-6 min-h-[440px] radial-glow-navy transition-all duration-300 group">
                <div className="space-y-4">
                  <CardHeader className="p-0">
                    <div className="w-10 h-10 rounded-xl bg-navy-800/5 text-navy-800 flex items-center justify-center mb-2 group-hover:scale-105 group-hover:bg-navy-800/10 transition-all duration-300">
                      <Upload className="w-5 h-5" />
                    </div>
                    <CardTitle className="text-lg font-bold text-slate-800">{koreanHeadings.uploadContract}</CardTitle>
                    <CardDescription className="text-xs leading-relaxed">
                      신규 PDF 또는 Word 계약서 문서를 업로드해 AI 법령 체크리스트 및 독소 배상 조항을 실시간 탐지해 보세요.
                    </CardDescription>
                  </CardHeader>
                  
                  {/* Interactive Upload Dropzone or Sequential Process Loading State */}
                  <div 
                    className="border border-slate-200 border-dashed rounded-xl p-5 bg-slate-50/50 text-center flex flex-col items-center justify-center cursor-pointer transition-all duration-300 hover:bg-slate-100/50 focus-within:ring-2 focus-within:ring-navy-800/20"
                    onClick={handleUpload}
                  >
                    {isUploading ? (
                      <div className="flex flex-col items-start w-full gap-3.5 py-2 px-1 select-none animate-slide-in">
                        <div className="flex items-center gap-2 w-full">
                          <RefreshCw className="w-4 h-4 text-navy-800 animate-spin shrink-0" />
                          <span className="text-[11px] font-bold text-slate-700">AI 정밀 스크리닝 동작 중</span>
                        </div>
                        {/* Shimmering Timeline Steps */}
                        <div className="space-y-3 w-full text-left">
                          <div className="flex items-center gap-2">
                            <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold shrink-0 ${
                              uploadStep > 1 ? 'bg-emerald-500 text-white' : 'bg-navy-800 text-white animate-pulse'
                            }`}>
                              {uploadStep > 1 ? <Check className="w-2.5 h-2.5" /> : '1'}
                            </span>
                            <span className={`text-[10px] font-semibold transition-colors duration-300 ${uploadStep === 1 ? 'text-navy-800' : uploadStep > 1 ? 'text-slate-400' : 'text-slate-300'}`}>
                              계약서 구조 파악 및 문서 벡터화
                            </span>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold shrink-0 ${
                              uploadStep > 2 ? 'bg-emerald-500 text-white' : uploadStep === 2 ? 'bg-navy-800 text-white animate-pulse' : 'bg-slate-200 text-slate-500'
                            }`}>
                              {uploadStep > 2 ? <Check className="w-2.5 h-2.5" /> : '2'}
                            </span>
                            <span className={`text-[10px] font-semibold transition-colors duration-300 ${uploadStep === 2 ? 'text-navy-800' : uploadStep > 2 ? 'text-slate-400' : 'text-slate-300'}`}>
                              법률 위반 및 표준 조항 대비 검색
                            </span>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold shrink-0 ${
                              uploadStep > 3 ? 'bg-emerald-500 text-white' : uploadStep === 3 ? 'bg-navy-800 text-white animate-pulse' : 'bg-slate-200 text-slate-500'
                            }`}>
                              {uploadStep > 3 ? <Check className="w-2.5 h-2.5" /> : '3'}
                            </span>
                            <span className={`text-[10px] font-semibold transition-colors duration-300 ${uploadStep === 3 ? 'text-navy-800' : uploadStep > 3 ? 'text-slate-400' : 'text-slate-300'}`}>
                              책임 한도액 및 면책 위험도 분류
                            </span>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold shrink-0 ${
                              uploadStep > 4 ? 'bg-emerald-500 text-white' : uploadStep === 4 ? 'bg-navy-800 text-white animate-pulse' : 'bg-slate-200 text-slate-500'
                            }`}>
                              {uploadStep > 4 ? <Check className="w-2.5 h-2.5" /> : '4'}
                            </span>
                            <span className={`text-[10px] font-semibold transition-colors duration-300 ${uploadStep === 4 ? 'text-navy-800' : 'text-slate-300'}`}>
                              AI 최적 수정 권고 조항 최종 검토
                            </span>
                          </div>
                        </div>
                        {/* Shimmer line bar */}
                        <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden mt-1">
                          <div className="bg-navy-800 h-full transition-all duration-300" style={{ width: `${(uploadStep - 1) * 25}%` }}></div>
                        </div>
                      </div>
                    ) : uploadSuccess ? (
                      <div className="flex flex-col items-center gap-2.5 py-8 animate-scale-in">
                        <div className="w-12 h-12 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-500 animate-pulse-ring">
                          <Check className="w-6 h-6" />
                        </div>
                        <span className="text-xs font-bold text-slate-800">스크리닝 분석이 로드되었습니다!</span>
                        <span className="text-[10px] text-emerald-700 font-semibold bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                          Ready to Audit
                        </span>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center py-6">
                        <FileText className="w-10 h-10 text-slate-400 group-hover:text-navy-800 group-hover:scale-105 transition-all duration-300 mb-3" />
                        <span className="text-xs font-bold text-slate-800">PDF, DOCX 계약서 문서 분석</span>
                        <span className="text-[10px] text-slate-600 mt-1.5">클릭하거나 마우스로 드래그 앤 드롭</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100 mt-4 flex items-center gap-1.5 text-xs text-slate-600 font-medium">
                  <Info className="w-3.5 h-3.5 text-navy-800 shrink-0" />
                  <span>보안 규정: 민감 법률 정보 암호화 보관</span>
                </div>
              </Card>
            </div>

            {/* Right side: Detailed interactive report summary table (8 Cols) */}
            <div className="lg:col-span-8 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="text-slate-900 font-bold text-lg flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-navy-800 animate-pulse-subtle" />
                  실시간 스크리닝 리스크 검출 조항
                </div>
                
                {/* Search Bar Input */}
                <div className="relative max-w-xs w-full">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="조항명, 카테고리, 요약 내용 검색..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full text-xs pl-9 pr-4 py-2 bg-white border border-slate-200/90 rounded-lg focus:outline-none focus:ring-2 focus:ring-navy-800/10 focus:border-navy-800 transition-all duration-300 font-medium placeholder-slate-400 shadow-sm"
                  />
                </div>
              </div>

              {/* Risky Clauses Table */}
              <div className="overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-2/5">검출 조항 (Clause)</TableHead>
                      <TableHead>위험 수준</TableHead>
                      <TableHead>분야 (Category)</TableHead>
                      <TableHead className="text-right">스크리닝 Audit</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredRisksList.map((risk) => {
                      const block = blocks.find(b => b.riskId === risk.id);
                      const isResolved = block?.isResolved;

                      return (
                        <TableRow 
                          key={risk.id} 
                          className={`transition-all duration-300 cursor-pointer ${
                            isResolved 
                              ? 'bg-emerald-50/20 hover:bg-emerald-50/30' 
                              : selectedRiskId === risk.id 
                                ? 'bg-slate-50/90 font-medium' 
                                : 'hover:bg-slate-50/50'
                          }`}
                          onClick={() => {
                            setSelectedRiskId(risk.id);
                            setActiveTab('viewer');
                          }}
                        >
                          <TableCell className="font-semibold text-slate-900 py-3.5">
                            <div className="flex items-center gap-2.5">
                              {isResolved ? (
                                <div className="w-5 h-5 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 shrink-0">
                                  <Check className="w-3.5 h-3.5" />
                                </div>
                              ) : (
                                <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
                                  risk.severity === 'high' ? 'bg-rose-50 border border-rose-100 text-rose-500' :
                                  risk.severity === 'medium' ? 'bg-amber-50 border border-amber-100 text-amber-500' :
                                  'bg-slate-50 border border-slate-200 text-slate-500'
                                }`}>
                                  <AlertTriangle className="w-3 h-3" />
                                </div>
                              )}
                              <span>{risk.clauseName}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            {isResolved ? (
                              <Badge variant="low">조치 완료</Badge>
                            ) : (
                              <Badge variant={risk.severity}>{
                                risk.severity === 'high' ? '고위험' :
                                risk.severity === 'medium' ? '중위험' : '저위험'
                              }</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <span className="text-[11px] text-slate-600 font-semibold bg-slate-100 border border-slate-200/50 px-2.5 py-0.5 rounded-md">
                              {risk.category}
                            </span>
                          </TableCell>
                          <TableCell className="text-right">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedRiskId(risk.id);
                                setActiveTab('viewer');
                              }}
                              className="inline-flex items-center gap-1 text-xs font-bold text-navy-800 hover:text-navy-900 transition-colors group/act cursor-pointer"
                            >
                              {koreanHeadings.viewDetails}
                              <ChevronRight className="w-3.5 h-3.5 transition-transform group-hover/act:translate-x-0.5" />
                            </button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                    {filteredRisksList.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center py-12 text-slate-600 font-medium">
                          검색 요건에 매칭되는 계약 조항 리스크 요인이 검출되지 않았습니다.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 2: HIGH-FIDELITY SCREENING VIEWER */}
      {activeTab === 'viewer' && (
        <div className="grid lg:grid-cols-12 gap-8 animate-fade-in-up items-start">
          
          {/* LEFT PANE: Premium Legal Document Reader Container (p-8 Padding) */}
          <div className="lg:col-span-7 bg-white border border-slate-200/90 rounded-2xl shadow-sm overflow-hidden flex flex-col h-[740px]">
            {/* Pane Header */}
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/75 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-navy-50 flex items-center justify-center text-navy-800 border border-navy-100">
                  <FileText className="w-4 h-4" />
                </div>
                <span className="text-xs font-bold text-slate-700 uppercase font-mono select-none">Mutual_NDA_Redlined.txt</span>
              </div>
              <div className="text-[11px] text-slate-600 font-semibold flex items-center gap-3">
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                  고위험
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                  중위험
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  조치완료
                </span>
              </div>
            </div>

            {/* Document Body with absolute 32px (p-8) padding constraint & legalpad margins */}
            <div className="flex-1 overflow-y-auto p-8 legal-text font-sans text-slate-900 whitespace-pre-line leading-relaxed space-y-6 select-none bg-white relative">
              {blocks.map((block) => {
                if (!block.isRisk) {
                  return (
                    <div key={block.id} className="opacity-75 pl-10 pr-4 transition-all duration-300 text-slate-700 hover:opacity-100 leading-relaxed text-[15px]">
                      {block.text}
                    </div>
                  );
                }

                const risk = sampleContract.risks.find(r => r.id === block.riskId);
                const isSelected = selectedRiskId === block.riskId;
                const isShining = shineBlockId === block.riskId;
                
                let highlightClass = "";
                let indicatorTag = "";
                
                if (block.isResolved) {
                  highlightClass = isSelected 
                    ? "bg-emerald-50/90 border-2 border-emerald-500 shadow-md text-emerald-950" 
                    : "bg-emerald-50/50 border border-emerald-300 text-emerald-900 opacity-90";
                  indicatorTag = "조치완료";
                } else if (risk?.severity === 'high') {
                  highlightClass = isSelected 
                    ? "bg-rose-50 border-2 border-rose-500 shadow-lg scale-[1.01] text-rose-950 font-medium" 
                    : "bg-rose-50/60 border border-rose-200 text-rose-900 hover:bg-rose-50/90 transition-all duration-200";
                  indicatorTag = "고위험";
                } else if (risk?.severity === 'medium') {
                  highlightClass = isSelected 
                    ? "bg-amber-50 border-2 border-amber-500 shadow-lg scale-[1.01] text-amber-950 font-medium" 
                    : "bg-amber-50/60 border border-amber-200 text-amber-900 hover:bg-amber-50/90 transition-all duration-200";
                  indicatorTag = "중위험";
                } else {
                  highlightClass = isSelected 
                    ? "bg-slate-100 border-2 border-slate-400 text-slate-900" 
                    : "bg-slate-50 border border-slate-200 text-slate-700";
                  indicatorTag = "저위험";
                }

                return (
                  <div
                    key={block.id}
                    onClick={() => risk && setSelectedRiskId(risk.id)}
                    className={`ml-10 p-4 rounded-xl cursor-pointer transition-all duration-300 relative select-none ${highlightClass} ${
                      isShining ? 'shine-overlay animate-shine bg-emerald-100 border-emerald-600 text-emerald-950' : ''
                    }`}
                  >
                    {/* Visual left edge dynamic active highlighter */}
                    {isSelected && (
                      <span className="absolute -left-2 top-4 w-1.5 h-12 bg-navy-800 rounded-r-full shadow"></span>
                    )}
                    
                    {/* Corner Tag Label */}
                    <span className={`absolute right-3.5 top-3.5 text-[9px] font-extrabold uppercase px-2 py-0.5 rounded-full select-none shadow-sm ${
                      block.isResolved ? 'bg-emerald-500 text-white' :
                      risk?.severity === 'high' ? 'bg-rose-600 text-white' :
                      risk?.severity === 'medium' ? 'bg-amber-500 text-white' : 'bg-slate-500 text-white'
                    }`}>
                      {indicatorTag}
                    </span>

                    {/* Block Text content */}
                    <div className="pr-12 text-[14.5px] leading-relaxed">
                      {block.text}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* RIGHT PANE: AI Redlining Feed Panel (p-6 Padding) */}
          <div className="lg:col-span-5 space-y-6">
            <Card variant="dashboard" className="border-l-4 border-l-navy-800 shadow-md radial-glow-navy p-6 flex flex-col justify-between">
              
              <div className="space-y-5">
                <CardHeader className="pb-3 border-b border-slate-100 p-0 mb-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] bg-navy-800/10 text-navy-800 px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider border border-navy-800/10">
                      AI Legal Audit feed
                    </span>
                    
                    {selectedBlock?.isResolved ? (
                      <Badge variant="low">조치 완료</Badge>
                    ) : (
                      selectedRisk && (
                        <Badge variant={selectedRisk.severity}>
                          {selectedRisk.severity === 'high' ? '고위험 조항' :
                           selectedRisk.severity === 'medium' ? '중위험 조항' : '저위험 조항'}
                        </Badge>
                      )
                    )}
                  </div>
                  
                  {selectedRisk && (
                    <CardTitle className="text-xl mt-3 font-bold text-slate-900 tracking-tight">
                      {selectedRisk.clauseName}
                    </CardTitle>
                  )}
                  {selectedRisk && (
                    <CardDescription className="text-xs text-slate-500 font-semibold mt-1 flex items-center gap-1.5">
                      <span>{selectedRisk.category}</span>
                      <span>•</span>
                      <span>조치 우선순위: <span className="font-bold text-slate-800">{selectedRisk.severity === 'high' ? '최우선' : selectedRisk.severity === 'medium' ? '권장' : '경미'}</span></span>
                    </CardDescription>
                  )}
                </CardHeader>

                {/* Risk Explanation */}
                <div className="space-y-1.5 p-3.5 bg-slate-50 border border-slate-200/60 rounded-xl">
                  <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wide">리스크 분석 요약</span>
                  <p className="text-xs font-bold text-slate-800 leading-relaxed">
                    {selectedRisk?.summary}
                  </p>
                </div>

                {/* Compare Clause Box with View Mode Slider Selector */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-700">비교 스크린 모드</span>
                    {/* Segmented control for diff views */}
                    <div className="inline-flex items-center p-0.5 bg-slate-100 rounded-lg border border-slate-200 shadow-inner">
                      <button
                        onClick={() => setDiffViewMode('side-by-side')}
                        className={`px-3 py-1 rounded-md text-[10px] font-bold tracking-wider transition-all duration-300 cursor-pointer ${
                          diffViewMode === 'side-by-side' 
                            ? 'bg-white text-navy-800 shadow-sm border border-slate-200/50' 
                            : 'text-slate-500 hover:text-slate-900'
                        }`}
                      >
                        양자 비교 (Side)
                      </button>
                      <button
                        onClick={() => setDiffViewMode('redline')}
                        className={`px-3 py-1 rounded-md text-[10px] font-bold tracking-wider transition-all duration-300 cursor-pointer ${
                          diffViewMode === 'redline' 
                            ? 'bg-white text-navy-800 shadow-sm border border-slate-200/50' 
                            : 'text-slate-500 hover:text-slate-900'
                        }`}
                      >
                        AI 레드라인 (Inline Diff)
                      </button>
                    </div>
                  </div>

                  {diffViewMode === 'side-by-side' ? (
                    <div className="space-y-3.5 animate-slide-in">
                      {/* Original text block */}
                      <div className="space-y-1">
                        <span className="text-[10px] font-extrabold text-rose-700 uppercase tracking-wide flex items-center gap-1">
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                          {koreanHeadings.originalClause}
                        </span>
                        <div className="p-3 bg-rose-50/30 border border-rose-200/60 rounded-xl text-[11.5px] font-sans text-slate-700 leading-relaxed max-h-32 overflow-y-auto">
                          {selectedBlock?.originalText}
                        </div>
                      </div>

                      {/* Recommendation block */}
                      {selectedRisk && (
                        <div className="space-y-1">
                          <span className="text-[10px] font-extrabold text-navy-800 uppercase tracking-wide flex items-center gap-1">
                            <Sparkles className="w-3.5 h-3.5 text-navy-800 shrink-0" />
                            {koreanHeadings.suggestedClause}
                          </span>
                          <div className="p-3 bg-navy-50/30 border border-navy-200/60 rounded-xl text-[11.5px] font-sans text-navy-950 leading-relaxed max-h-32 overflow-y-auto font-medium">
                            {selectedRisk.recommendation}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-1.5 animate-slide-in">
                      <span className="text-[10px] font-extrabold text-navy-800 uppercase tracking-wide flex items-center gap-1 select-none">
                        <Sparkles className="w-3.5 h-3.5 text-navy-800 shrink-0" />
                        AI 자동 수정 권고 레드라인 (Word-level Redline)
                      </span>
                      {selectedRisk && selectedBlock && renderWordDiff(selectedBlock.originalText || '', selectedRisk.recommendation)}
                    </div>
                  )}
                </div>

                {/* Direct Action Trigger CTAs */}
                <div className="pt-2 flex gap-2.5">
                  {selectedBlock?.isResolved ? (
                    <button
                      onClick={() => selectedRisk && handleRevertClause(selectedRisk.id)}
                      className="w-full bg-slate-100 hover:bg-slate-200 text-slate-900 text-xs font-bold py-2.5 px-4 rounded-xl transition-all duration-300 flex items-center justify-center gap-1.5 border border-slate-200 shadow-sm cursor-pointer active:scale-98"
                    >
                      <Undo className="w-3.5 h-3.5" />
                      원래 조항으로 복원
                    </button>
                  ) : (
                    selectedRisk && (
                      <button
                        onClick={() => handleApplyRecommendation(selectedRisk.id, selectedRisk.recommendation)}
                        className="w-full bg-navy-800 hover:bg-navy-900 text-white text-xs font-bold py-2.5 px-4 rounded-xl shadow-sm transition-all duration-300 hover:shadow flex items-center justify-center gap-1.5 animate-pulse-subtle cursor-pointer active:scale-98"
                      >
                        <FileCheck className="w-3.5 h-3.5" />
                        AI 추천 권고안 적용 (Direct Redline)
                      </button>
                    )
                  )}
                  
                  <button
                    onClick={() => {
                      if (selectedRisk) {
                        navigator.clipboard.writeText(selectedRisk.recommendation);
                        alert("추천 권고 수정문구가 클립보드에 성공적으로 복사되었습니다.");
                      }
                    }}
                    className="p-2.5 bg-white border border-slate-200 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-colors shrink-0 shadow-sm cursor-pointer"
                    title="권고안 복사"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>

                {/* Detailed Analysis Accordion */}
                {selectedRisk && (
                  <div className="pt-3.5 border-t border-slate-100">
                    <Accordion>
                      <AccordionItem id="detail-analysis" trigger={koreanHeadings.analysisDetail}>
                        <div className="space-y-3.5 pt-1">
                          <p className="text-[12.5px] leading-relaxed text-slate-600 font-medium select-text">{selectedRisk.analysisDetail}</p>
                          <div className="flex justify-between items-center bg-slate-50 border border-slate-200/50 p-3 rounded-xl text-xs">
                            <span className="font-bold text-slate-500">조치 난이도 및 비용:</span>
                            <Badge variant={
                              selectedRisk.remedyCost === 'High' ? 'high' :
                              selectedRisk.remedyCost === 'Medium' ? 'medium' : 'low'
                            }>
                              {selectedRisk.remedyCost} Risk
                            </Badge>
                          </div>
                        </div>
                      </AccordionItem>
                    </Accordion>
                  </div>
                )}
              </div>

              {/* Return link */}
              <button
                onClick={() => setActiveTab('overview')}
                className="text-xs font-bold text-slate-500 hover:text-slate-800 flex items-center gap-1 transition-colors pl-1 pt-6 cursor-pointer"
              >
                ← {koreanHeadings.backToDashboard}
              </button>

            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
