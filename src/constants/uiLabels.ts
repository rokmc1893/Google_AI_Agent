/** UI 라벨 (실서비스 화면 공통) */
export const koreanHeadings = {
  dashboardTitle: '계약 분석 리포트',
  riskSummary: '리스크 요약 현황',
  totalRisks: '총 발견 리스크',
  highRisks: '고위험 리스크',
  mediumRisks: '중위험 리스크',
  lowRisks: '저위험 리스크',
  clauseList: '검토 대상 조항 목록',
  clauseName: '조항명',
  severity: '위험도',
  category: '분야',
  summary: '요약',
  originalText: '계약서 본문 조항',
  recommendation: '추천 수정 조항',
  analysisDetail: '법무 검토 보조를 위한 분석 상세',
  remedyCost: '조치 난이도/비용',
  riskOverview: '리스크 오버뷰',
  uploadContract: '계약서 스크리닝 분석 요청',
  viewDetails: '상세 분석 보기',
  backToDashboard: '대시보드로 돌아가기',
  originalClause: '원본 조항',
  suggestedClause: '수정 권고안',
} as const;

export type KoreanHeadingKey = keyof typeof koreanHeadings;
