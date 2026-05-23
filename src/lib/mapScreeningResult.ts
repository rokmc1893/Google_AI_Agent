import type { ScreeningResult } from '../api/client';
import type { ContractData, LegalRisk } from '../types/contract';

export interface UploadMeta {
  filename: string;
  file_type: string;
  text_preview: string;
  char_count: number;
}

function inferCategory(title: string): LegalRisk['category'] {
  const t = title.toLowerCase();
  if (t.includes('지식재산') || t.includes('특허') || t.includes('ip')) return 'Intellectual Property';
  if (t.includes('비밀') || t.includes('nda') || t.includes('기밀')) return 'Confidentiality';
  if (t.includes('준거') || t.includes('관할') || t.includes('재판')) return 'Jurisdiction';
  if (t.includes('손해') || t.includes('배상') || t.includes('면책') || t.includes('책임')) return 'Liability';
  return 'Term & Termination';
}

function mapIssue(issue: ScreeningResult['verified_issues'][number], index: number): LegalRisk {
  const level = (issue.risk_level || 'MEDIUM').toLowerCase() as LegalRisk['severity'];
  const basis = issue.legal_basis_text || issue.legal_basis || '';
  const replacement = issue.replacement_clause?.trim();
  const recommendation =
    issue.recommendation?.trim() ||
    (replacement ? '아래 대체 조항을 기준으로 수정을 검토하세요.' : '') ||
    (basis
      ? `관련 법령(${issue.legal_basis || '검토'})에 맞게 조항을 조정하세요.`
      : '법무팀 검토 후 수정안을 확정하세요.');

  return {
    id: issue.id || issue.title || `issue-${index + 1}`,
    clauseName: issue.title || '계약 리스크',
    severity: level === 'high' || level === 'medium' || level === 'low' ? level : 'medium',
    category: inferCategory(`${issue.title} ${issue.description} ${basis}`),
    summary: issue.description || issue.title || '계약 조항 검토가 필요합니다.',
    originalText: issue.clause_text || issue.clause_anchor?.heading || issue.description || issue.title,
    recommendation: replacement || recommendation,
    analysisDetail: [
      issue.description,
      issue.legal_basis,
      issue.legal_basis_text,
      issue.clause_anchor?.heading ? `조항 위치: ${issue.clause_anchor.heading}` : '',
      ...(issue.citations || []),
    ]
      .filter(Boolean)
      .join('\n'),
    remedyCost: issue.risk_level === 'HIGH' ? 'High' : issue.risk_level === 'MEDIUM' ? 'Medium' : 'Low',
  };
}

export function mapResultToContractData(
  result: ScreeningResult,
  upload?: UploadMeta,
): ContractData {
  const risks = (result.verified_issues.length ? result.verified_issues : result.issues).map(mapIssue);
  const fullText =
    result.full_text?.trim() ||
    result.contract_masked?.trim() ||
    result.masked_text?.trim() ||
    upload?.text_preview ||
    result.output_report.slice(0, 3000);
  return {
    title: upload?.filename || '스크리닝 계약서',
    type: upload?.file_type?.toUpperCase() || 'Contract',
    lastUpdated: new Date().toISOString().slice(0, 10),
    fullText,
    maskedText: result.masked_text || result.contract_masked || null,
    risks,
  };
}

export interface ContractBlock {
  id: string;
  text: string;
  isRisk: boolean;
  riskId?: string;
  isResolved?: boolean;
  originalText?: string;
}

export function buildBlocksFromContract(data: ContractData): ContractBlock[] {
  const blocks: ContractBlock[] = [
    {
      id: 'intro',
      text: data.fullText.slice(0, Math.min(1200, data.fullText.length)),
      isRisk: false,
    },
  ];

  for (const risk of data.risks) {
    blocks.push({
      id: `block-${risk.id}`,
      text: risk.originalText,
      isRisk: true,
      riskId: risk.id,
      isResolved: false,
      originalText: risk.originalText,
    });
  }

  if (data.fullText.length > 1200) {
    blocks.push({
      id: 'outro',
      text: data.fullText.slice(1200),
      isRisk: false,
    });
  }

  return blocks;
}
