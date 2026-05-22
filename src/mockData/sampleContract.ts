/**
 * @deprecated 실서비스는 API 응답만 사용합니다.
 * 로컬 픽스처·스토리북 참고용 목업 데이터 (앱에서 import 금지).
 */
import type { ContractData } from '../types/contract';

export type { ContractData, LegalRisk } from '../types/contract';
export { koreanHeadings } from '../constants/uiLabels';

/** 개발·테스트 참고용 샘플 (프로덕션 Dashboard 미사용) */
export const sampleContract: ContractData = {
  title: '상호 비밀유지약정서 (Mutual NDA)',
  type: '비밀유지약정서',
  lastUpdated: '2026-05-22',
  fullText: '(목업 데이터 — API 업로드 결과로 대체됨)',
  risks: [],
};
