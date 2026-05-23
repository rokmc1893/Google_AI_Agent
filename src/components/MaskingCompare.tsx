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
        <CardTitle className="text-sm font-bold text-slate-800">민감 정보 마스킹 비교</CardTitle>
        <CardDescription className="text-xs">
          분석에 사용되는 마스킹 텍스트와 원문 미리보기를 비교합니다. 마스킹은 개인정보 보호를 위한 보조 조치이며, 모든 민감 정보 제거를 보장하지는 않습니다.
        </CardDescription>
      </CardHeader>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <div className="text-[10px] font-semibold tracking-wide text-slate-500">
            {koreanHeadings.originalClause} 미리보기
          </div>
          <pre className="text-[11px] leading-relaxed p-3 rounded-lg bg-slate-50 border border-slate-200 max-h-48 overflow-y-auto whitespace-pre-wrap font-sans text-slate-800">
            {originalText.slice(0, 1500)}
            {originalText.length > 1500 ? '…' : ''}
          </pre>
        </div>
        <div className="space-y-2">
          <div className="text-[10px] font-semibold tracking-wide text-amber-700">마스킹 후 분석용</div>
          <pre className="text-[11px] leading-relaxed p-3 rounded-lg bg-amber-50/50 border border-amber-200/80 max-h-48 overflow-y-auto whitespace-pre-wrap font-sans text-slate-800">
            {maskedText.slice(0, 1500)}
            {maskedText.length > 1500 ? '…' : ''}
          </pre>
        </div>
      </div>
    </Card>
  );
};
