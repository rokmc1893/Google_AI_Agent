import React from 'react';
import { Card, CardDescription, CardHeader, CardTitle } from './Card';
import { koreanHeadings } from '../constants/uiLabels';

interface MaskingCompareProps {
  originalText: string;
  maskedText: string;
}

export const MaskingCompare: React.FC<MaskingCompareProps> = ({ originalText, maskedText }) => {
  if (!maskedText.trim()) return null;

  return (
    <Card variant="dashboard" className="p-5 border border-slate-200/80">
      <CardHeader className="p-0 mb-4">
        <CardTitle className="text-sm font-bold text-slate-800">PII 마스킹 Side-by-Side</CardTitle>
        <CardDescription className="text-xs">
          외부 LLM 전송 전 마스킹된 텍스트와 업로드 원문 미리보기를 비교합니다.
        </CardDescription>
      </CardHeader>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <div className="text-[10px] font-bold uppercase tracking-wide text-slate-500">
            {koreanHeadings.originalClause} (Preview)
          </div>
          <pre className="text-[11px] leading-relaxed p-3 rounded-lg bg-slate-50 border border-slate-200 max-h-48 overflow-y-auto whitespace-pre-wrap font-sans text-slate-800">
            {originalText.slice(0, 1500)}
            {originalText.length > 1500 ? '…' : ''}
          </pre>
        </div>
        <div className="space-y-2">
          <div className="text-[10px] font-bold uppercase tracking-wide text-amber-700">Masked (API 전송용)</div>
          <pre className="text-[11px] leading-relaxed p-3 rounded-lg bg-amber-50/50 border border-amber-200/80 max-h-48 overflow-y-auto whitespace-pre-wrap font-sans text-slate-800">
            {maskedText.slice(0, 1500)}
            {maskedText.length > 1500 ? '…' : ''}
          </pre>
        </div>
      </div>
    </Card>
  );
};
