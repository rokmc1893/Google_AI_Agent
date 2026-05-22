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

const INITIAL_BLOCKS: ContractBlock[] = [
  { 
    id: 'intro', 
    text: `상호 비밀유지계약서 (Mutual NDA)\n\n본 상호 비밀유지계약서(이하 "본 계약")는 주식회사 딥글디자인(이하 "갑")과 글로벌벤처스 주식회사(이하 "을") 간에 체결되었습니다.\n\n제1조 (목적 및 비밀정보)\n양 당사자는 공동 사업 기회 모색(이하 "본 목적")을 희망합니다. 본 목적과 관련하여 양 당사자는 서면, 구두 또는 시각적 형태로 공개되는 독점적이고 민감한 정보로서 비밀로 표시되거나 성질상 비밀로 합리적으로 이해되어야 하는 정보(이하 "비밀정보")를 상대방에게 공개할 수 있습니다.\n\n제2조 (비밀유지 의무 및 사용 제한)\n비밀정보를 수령한 당사자(이하 "수령인")는 제공 당사자(이하 "공개자")의 비밀정보가 무단으로 공개되거나 사용되지 않도록 신의성실의 의무를 다하고, 합리적인 수준 이상의 주의를 기울여 비밀정보를 관리하여야 합니다. 수령인은 본 목적을 위해서만 비밀정보를 사용하여야 합니다.`,
    isRisk: false 
  },
  { 
    id: 'risk-1', 
    text: `제3조 (일방적 영구 비밀유지 의무)\n본 계약의 해지 또는 만료 여부에 관계없이, 본 계약에 따라 공개된 모든 비밀정보에 대한 수령인의 비밀유지 의무는 공개일로부터 영구적으로 존속합니다. 수령인은 해당 정보가 거래상의 비밀에 해당하지 않게 되거나, 수령인의 귀책 사유 없이 공공 영역에 공개되는지 여부와 관계없이 본 계약에 따른 모든 비밀유지 의무가 무기한 효력을 유지한다는 것에 동의합니다.`, 
    isRisk: true, 
    riskId: 'risk-1',
    isResolved: false,
    originalText: `제3조 (일방적 영구 비밀유지 의무)\n본 계약의 해지 또는 만료 여부에 관계없이, 본 계약에 따라 공개된 모든 비밀정보에 대한 수령인의 비밀유지 의무는 공개일로부터 영구적으로 존속합니다. 수령인은 해당 정보가 거래상의 비밀에 해당하지 않게 되거나, 수령인의 귀책 사유 없이 공공 영역에 공개되는지 여부와 관계없이 본 계약에 따른 모든 비밀유지 의무가 무기한 효력을 유지한다는 것에 동의합니다.`
  },
  { 
    id: 'risk-2', 
    text: `제4조 (손해배상 및 무제한 책임)\n수령인은 수령인의 본 계약 위반으로 인해 발생하거나 이와 관련하여 발생하는 모든 청구, 부채, 손실, 손해, 비용 또는 지출(합리적인 변호사 수임료 포함)로부터 공개자를 면책하고 방어하며 피해가 없도록 하는 것에 동의합니다. 또한 수령인은 본 제4조에 따른 책임을 전적으로 무제한으로 부담하며, 다른 합의사항에 따른 책임 제한이나 한도의 적용을 받지 않는다는 것에 동의합니다.`, 
    isRisk: true, 
    riskId: 'risk-2',
    isResolved: false,
    originalText: `제4조 (손해배상 및 무제한 책임)\n수령인은 수령인의 본 계약 위반으로 인해 발생하거나 이와 관련하여 발생하는 모든 청구, 부채, 손실, 손해, 비용 또는 지출(합리적인 변호사 수임료 포함)로부터 공개자를 면책하고 방어하며 피해가 없도록 하는 것에 동의합니다. 또한 수령인은 본 제4조에 따른 책임을 전적으로 무제한으로 부담하며, 다른 합의사항에 따른 책임 제한이나 한도의 적용을 받지 않는다는 것에 동의합니다.`
  },
  { 
    id: 'risk-3', 
    text: `제5조 (지식재산권 소유권 및 자동 양도)\n모든 비밀정보는 공개자의 단독 소유로 유지됩니다. 다만, 수령인이 본 계약 기간 동안 공개자의 기술 또는 사업에 대한 피드백, 개선 사항 또는 수정 제안을 제공하는 경우, 수령인은 추가적인 대가나 보상 없이 해당 피드백과 관련된 모든 권리, 권원, 지식재산권을 공개자에게 자동으로 그리고 취소 불가능하게 양도합니다.`, 
    isRisk: true, 
    riskId: 'risk-3',
    isResolved: false,
    originalText: `제5조 (지식재산권 소유권 및 자동 양도)\n모든 비밀정보는 공개자의 단독 소유로 유지됩니다. 다만, 수령인이 본 계약 기간 동안 공개자의 기술 또는 사업에 대한 피드백, 개선 사항 또는 수정 제안을 제공하는 경우, 수령인은 추가적인 대가나 보상 없이 해당 피드백과 관련된 모든 권리, 권원, 지식재산권을 공개자에게 자동으로 그리고 취소 불가능하게 양도합니다.`
  },
  { 
    id: 'risk-4', 
    text: `제6조 (준거법 및 관할합의)\n본 계약 및 이와 관련하여 발생하는 모든 청구 또는 소송 제기는 법률 저촉 원칙과 관계없이 대한민국 법률에 따라 해석되고 규율됩니다. 본 계약으로 인해 발생하거나 이와 관련된 모든 법적 소송 또는 절차는 서울중앙지방법원을 제1심 전속적 합의관할법원으로 지정합니다.`, 
    isRisk: true, 
    riskId: 'risk-4',
    isResolved: false,
    originalText: `제6조 (준거법 및 관할합의)\n본 계약 및 이와 관련하여 발생하는 모든 청구 또는 소송 제기는 법률 저촉 원칙과 관계없이 대한민국 법률에 따라 해석되고 규율됩니다. 본 계약으로 인해 발생하거나 이와 관련된 모든 법적 소송 또는 절차는 서울중앙지방법원을 제1심 전속적 합의관할법원으로 지정합니다.`
  },
  { 
    id: 'outro', 
    text: `\n본 계약의 체결을 증명하기 위해 양 당사자는 대표자를 통해 본 계약서를 작성하고 서명 날인합니다.`, 
    isRisk: false 
  }
];

export const Dashboard: React.FC = () => {
  const [isAnalyzed, setIsAnalyzed] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'viewer'>('overview');
  const [selectedRiskId, setSelectedRiskId] = useState<string>('risk-2'); // default highlight high risk
  const [searchTerm, setSearchTerm] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadStep, setUploadStep] = useState<number>(0);
  const [diffViewMode, setDiffViewMode] = useState<'side-by-side' | 'redline'>('redline');
  const [shineBlockId, setShineBlockId] = useState<string | null>(null);

  // Stateful text blocks for direct interactive redlining
  const [blocks, setBlocks] = useState<ContractBlock[]>(INITIAL_BLOCKS);

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
              setIsAnalyzed(true);
              setActiveTab('overview');
            }, 1200);
          }, 950);
        }, 800);
      }, 750);
    }, 850);
  };

  // Reset to home view to analyze another contract
  const handleReset = () => {
    setIsAnalyzed(false);
    setBlocks(INITIAL_BLOCKS);
    setSelectedRiskId('risk-2');
    setSearchTerm('');
    setUploadStep(0);
    setUploadSuccess(false);
  };

  // Direct edit: apply AI recommendation to the document block text
  const handleApplyRecommendation = (riskId: string, recommendationText: string) => {
    setBlocks(prev => prev.map(block => {
      if (block.riskId === riskId) {
        // Find clause number from original block text to prefix
        const originalFirstLine = block.originalText?.split('\n')[0] || '';
        const match = originalFirstLine.match(/^(제\d+조\s*(\([^)]+\))?)/);
        const prefix = match ? match[1] + '\n' : '';
        
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

  if (!isAnalyzed) {
    return (
      <div className="w-full max-w-4xl mx-auto space-y-12 py-8 animate-fade-in-up">
        {/* 헤더 안내 영역 */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center gap-1.5 bg-navy-50 text-navy-800 px-3.5 py-1.5 rounded-full border border-navy-100 text-xs font-semibold uppercase tracking-wider mb-2">
            <Activity className="w-3.5 h-3.5" />
            AI 법률 스크리닝 플랫폼
          </div>
          <h1 className="text-4xl font-extrabold text-slate-900 leading-tight tracking-tight">
            계약서 검토를 더 쉽고, 빠르고, 안전하게
          </h1>
          <p className="text-sm text-slate-600 max-w-xl mx-auto leading-relaxed">
            비밀유지계약서(NDA) 등 상거래 계약서를 업로드해 보세요. AI 엔진이 독소 조항과 면책 범위를 분석하여 실시간 대안 문구를 제안합니다.
          </p>
        </div>

        {/* 대형 업로드 영역 */}
        <div className="max-w-2xl mx-auto">
          <Card variant="dashboard" className="flex flex-col justify-between border-dashed border-2 hover:border-navy-800/40 p-8 min-h-[380px] radial-glow-navy transition-all duration-300 group shadow-md bg-white">
            <div className="space-y-6">
              <CardHeader className="p-0 text-center">
                <div className="mx-auto w-12 h-12 rounded-xl bg-navy-800/5 text-navy-800 flex items-center justify-center mb-3 group-hover:scale-105 group-hover:bg-navy-800/10 transition-all duration-300">
                  <Upload className="w-6 h-6" />
                </div>
                <CardTitle className="text-xl font-bold text-slate-800">계약서 파일 분석 시작하기</CardTitle>
                <CardDescription className="text-xs leading-relaxed max-w-md mx-auto mt-1">
                  PDF, DOCX 등의 계약서 파일을 드래그 앤 드롭하거나 아래 영역을 클릭하여 업로드하면 AI 법률 분석 검토 프로세스가 시작됩니다.
                </CardDescription>
              </CardHeader>
              
              {/* Interactive Upload Dropzone or Sequential Process Loading State */}
              <div 
                className="border border-slate-200 border-dashed rounded-2xl p-6 bg-slate-50/50 text-center flex flex-col items-center justify-center cursor-pointer transition-all duration-300 hover:bg-slate-100/50 focus-within:ring-2 focus-within:ring-navy-800/20"
                onClick={handleUpload}
              >
                {isUploading ? (
                  <div className="flex flex-col items-start w-full gap-4 py-2 px-1 select-none animate-slide-in">
                    <div className="flex items-center gap-2 w-full justify-center">
                      <RefreshCw className="w-4 h-4 text-navy-800 animate-spin shrink-0" />
                      <span className="text-xs font-bold text-slate-700">AI 정밀 계약서 분석 중...</span>
                    </div>
                    {/* Shimmering Timeline Steps */}
                    <div className="space-y-3.5 w-full max-w-md mx-auto text-left py-2">
                      <div className="flex items-center gap-2.5">
                        <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                          uploadStep > 1 ? 'bg-emerald-500 text-white' : 'bg-navy-800 text-white animate-pulse'
                        }`}>
                          {uploadStep > 1 ? <Check className="w-3 h-3" /> : '1'}
                        </span>
                        <span className={`text-[11.5px] font-semibold transition-colors duration-300 ${uploadStep === 1 ? 'text-navy-800' : uploadStep > 1 ? 'text-slate-400' : 'text-slate-300'}`}>
                          계약서 구조 파악 및 문서 벡터화
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2.5">
                        <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                          uploadStep > 2 ? 'bg-emerald-500 text-white' : uploadStep === 2 ? 'bg-navy-800 text-white animate-pulse' : 'bg-slate-200 text-slate-500'
                        }`}>
                          {uploadStep > 2 ? <Check className="w-3 h-3" /> : '2'}
                        </span>
                        <span className={`text-[11.5px] font-semibold transition-colors duration-300 ${uploadStep === 2 ? 'text-navy-800' : uploadStep > 2 ? 'text-slate-400' : 'text-slate-300'}`}>
                          법률 위반 및 표준 조항 대비 검색
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2.5">
                        <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                          uploadStep > 3 ? 'bg-emerald-500 text-white' : uploadStep === 3 ? 'bg-navy-800 text-white animate-pulse' : 'bg-slate-200 text-slate-500'
                        }`}>
                          {uploadStep > 3 ? <Check className="w-3 h-3" /> : '3'}
                        </span>
                        <span className={`text-[11.5px] font-semibold transition-colors duration-300 ${uploadStep === 3 ? 'text-navy-800' : uploadStep > 3 ? 'text-slate-400' : 'text-slate-300'}`}>
                          책임 한도액 및 면책 위험도 분류
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2.5">
                        <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                          uploadStep > 4 ? 'bg-emerald-500 text-white' : uploadStep === 4 ? 'bg-navy-800 text-white animate-pulse' : 'bg-slate-200 text-slate-500'
                        }`}>
                          {uploadStep > 4 ? <Check className="w-3 h-3" /> : '4'}
                        </span>
                        <span className={`text-[11.5px] font-semibold transition-colors duration-300 ${uploadStep === 4 ? 'text-navy-800' : 'text-slate-300'}`}>
                          AI 최적 수정 권고 조항 최종 검토
                        </span>
                      </div>
                    </div>
                    {/* Shimmer line bar */}
                    <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden mt-1 max-w-md mx-auto">
                      <div className="bg-navy-800 h-full transition-all duration-300" style={{ width: `${(uploadStep - 1) * 25}%` }}></div>
                    </div>
                  </div>
                ) : uploadSuccess ? (
                  <div className="flex flex-col items-center gap-3 py-6 animate-scale-in">
                    <div className="w-14 h-14 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-500 animate-pulse-ring">
                      <Check className="w-7 h-7" />
                    </div>
                    <span className="text-sm font-bold text-slate-800">계약서 분석 완료!</span>
                    <span className="text-xs text-emerald-700 font-semibold bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full">
                      분석 결과 리포트 준비 완료
                    </span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-10">
                    <FileText className="w-12 h-12 text-slate-400 group-hover:text-navy-800 group-hover:scale-105 transition-all duration-300 mb-4" />
                    <span className="text-sm font-bold text-slate-800">마우스 클릭 또는 드래그하여 계약서 업로드</span>
                    <span className="text-[11px] text-slate-500 mt-2">지원 형식: PDF, DOCX, TXT (최대 10MB)</span>
                  </div>
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 mt-6 flex items-center justify-center gap-1.5 text-xs text-slate-600 font-semibold">
              <Info className="w-4 h-4 text-navy-800 shrink-0" />
              <span>보안 규정: 민감 계약 정보 암호화 처리 및 외부 서버 비저장</span>
            </div>
          </Card>
        </div>

        {/* 주요 핵심 기능 그리드 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 pt-6">
          <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm text-center space-y-2.5">
            <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto border border-rose-100">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-sm">독소 조항 실시간 검출</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              면책 조항, 무제한 손해배상 등 편면적인 계약 요소를 실시간 분석 및 탐지합니다.
            </p>
          </div>

          <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm text-center space-y-2.5">
            <div className="w-10 h-10 rounded-xl bg-navy-50 text-navy-800 flex items-center justify-center mx-auto border border-navy-100">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-sm">AI 맞춤 수정 권고</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              상법 및 표준 계약서를 바탕으로 즉시 반영 가능한 고품질 합의안을 작성합니다.
            </p>
          </div>

          <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm text-center space-y-2.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto border border-emerald-100">
              <FileCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-sm">단어 단위 레드라인</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              수정 전후 계약 조항의 삭제/추가된 문구를 색상별 인라인 비교로 쉽게 대조합니다.
            </p>
          </div>

          <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm text-center space-y-2.5">
            <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center mx-auto border border-sky-100">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-sm">안전성 점수 진단</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              리스크 심각도를 합산하여 직관적인 계약 종합 안전 점수(0~100점)를 계산합니다.
            </p>
          </div>
        </div>
      </div>
    );
  }

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

        {/* View Switcher Controls & Reset Button */}
        <div className="flex flex-wrap items-center gap-3 self-start">
          <div className="flex items-center gap-1.5 bg-slate-200/50 p-1.5 rounded-xl border border-slate-200/60 shadow-sm">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 rounded-lg text-xs font-bold tracking-wide transition-all duration-300 cursor-pointer ${
                activeTab === 'overview'
                  ? 'bg-white text-navy-800 shadow-sm border border-slate-200/50'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              분석 요약
            </button>
            <button
              onClick={() => setActiveTab('viewer')}
              className={`px-4 py-2 rounded-lg text-xs font-bold tracking-wide transition-all duration-300 flex items-center gap-2 cursor-pointer ${
                activeTab === 'viewer'
                  ? 'bg-white text-navy-800 shadow-sm border border-slate-200/50'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              실시간 문서 검토
              {activeRisks.length > 0 && (
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
                </span>
              )}
            </button>
          </div>
          
          <button
            onClick={handleReset}
            className="px-4 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 hover:border-slate-300 text-slate-700 rounded-xl text-xs font-bold transition-all duration-300 shadow-sm flex items-center gap-1.5 cursor-pointer active:scale-98"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
            다른 계약서 분석하기
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
                    <span className="text-[10px] text-slate-500 font-bold mt-0.5 uppercase tracking-wide">안전 점수</span>
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

          {/* Interactive Screen: Detailed interactive report summary table (Taking full 12 Cols) */}
          <div className="space-y-4 pt-2">
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
            <div className="overflow-hidden bg-white border border-slate-200/90 rounded-2xl shadow-sm">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-2/5">검출 조항</TableHead>
                    <TableHead>위험 수준</TableHead>
                    <TableHead>분야</TableHead>
                    <TableHead className="text-right">상세 분석</TableHead>
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
      )}

      {/* VIEW 2: HIGH-FIDELITY SCREENING VIEWER */}
      {activeTab === 'viewer' && (
        <div className="grid lg:grid-cols-12 gap-8 animate-fade-in-up items-start">
          
          {/* LEFT PANE: Premium Legal Document Reader Container */}
          <div className="lg:col-span-7 bg-white border border-slate-200/90 rounded-2xl shadow-sm overflow-hidden flex flex-col h-[740px]">
            {/* Pane Header */}
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/75 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-navy-50 flex items-center justify-center text-navy-800 border border-navy-100">
                  <FileText className="w-4 h-4" />
                </div>
                <span className="text-xs font-bold text-slate-700 uppercase font-mono select-none">상호비밀유지계약서_검토본.txt</span>
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

          {/* RIGHT PANE: AI Redlining Feed Panel */}
          <div className="lg:col-span-5 space-y-6">
            <Card variant="dashboard" className="border-l-4 border-l-navy-800 shadow-md radial-glow-navy p-6 flex flex-col justify-between">
              
              <div className="space-y-5">
                <CardHeader className="pb-3 border-b border-slate-100 p-0 mb-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] bg-navy-800/10 text-navy-800 px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider border border-navy-800/10">
                      AI 법률 분석 피드
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
                    <span className="text-xs font-bold text-slate-700">비교 모드</span>
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
                        좌우 비교
                      </button>
                      <button
                        onClick={() => setDiffViewMode('redline')}
                        className={`px-3 py-1 rounded-md text-[10px] font-bold tracking-wider transition-all duration-300 cursor-pointer ${
                          diffViewMode === 'redline' 
                            ? 'bg-white text-navy-800 shadow-sm border border-slate-200/50' 
                            : 'text-slate-500 hover:text-slate-900'
                        }`}
                      >
                        레드라인 비교
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
                        AI 자동 수정 권고 레드라인 (단어 비교)
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
                      원본 조항으로 복원
                    </button>
                  ) : (
                    selectedRisk && (
                      <button
                        onClick={() => handleApplyRecommendation(selectedRisk.id, selectedRisk.recommendation)}
                        className="w-full bg-navy-800 hover:bg-navy-900 text-white text-xs font-bold py-2.5 px-4 rounded-xl shadow-sm transition-all duration-300 hover:shadow flex items-center justify-center gap-1.5 animate-pulse-subtle cursor-pointer active:scale-98"
                      >
                        <FileCheck className="w-3.5 h-3.5" />
                        AI 수정 권고안 본문 반영
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
                              {selectedRisk.remedyCost === 'High' ? '난이도 상' :
                               selectedRisk.remedyCost === 'Medium' ? '난이도 중' : '난이도 하'}
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
                ← 분석 요약으로 돌아가기
              </button>

            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
