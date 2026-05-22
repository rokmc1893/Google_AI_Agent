export interface LegalRisk {
  id: string;
  clauseName: string;
  severity: 'high' | 'medium' | 'low';
  category: string;
  summary: string;
  originalText: string;
  recommendation: string;
  analysisDetail: string;
  remedyCost: 'High' | 'Medium' | 'Low';
}

export interface ContractData {
  title: string;
  type: string;
  lastUpdated: string;
  fullText: string;
  risks: LegalRisk[];
}
