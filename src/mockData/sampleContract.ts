export interface LegalRisk {
  id: string;
  clauseName: string;
  severity: 'high' | 'medium' | 'low';
  category: 'Liability' | 'Confidentiality' | 'Jurisdiction' | 'Intellectual Property' | 'Term & Termination';
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

export const sampleContract: ContractData = {
  title: "Mutual Non-Disclosure Agreement (NDA)",
  type: "Confidentiality Agreement",
  lastUpdated: "2026-05-21",
  fullText: `MUTUAL NON-DISCLOSURE AGREEMENT

This Mutual Non-Disclosure Agreement (the "Agreement") is entered into by and between Deepgle Design LLC ("Company") and Global Ventures Inc. ("Partner").

1. PURPOSE & CONFIDENTIAL INFORMATION
The parties wish to explore a business opportunity of mutual interest (the "Purpose"). In connection with the Purpose, either party may disclose to the other party certain proprietary, sensitive, and confidential information, whether written, oral, or visual, labeled as confidential or which by its nature should be reasonably understood to be confidential.

2. STANDARD OF CARE & PERMITTED USE
The Receiving Party shall maintain the Confidential Information in strict confidence and shall use at least the same degree of care, but no less than a reasonable degree of care, to prevent the unauthorized disclosure or use of the Disclosing Party's Confidential Information. The Receiving Party shall use the Confidential Information solely for the Purpose.

3. UNILATERAL PERPETUAL OBLIGATION
Notwithstanding any termination of this Agreement, the Receiving Party’s obligations under this Agreement with respect to all Confidential Information disclosed shall continue in perpetuity from the date of disclosure. The Receiving Party agrees that all obligations of confidentiality shall remain binding indefinitely, regardless of whether the information ceases to be a trade secret or falls into the public domain through no fault of the Receiving Party.

4. INDEMNIFICATION AND UNLIMITED LIABILITY
The Receiving Party agrees to indemnify, defend, and hold harmless the Disclosing Party from and against any and all claims, liabilities, losses, damages, costs, or expenses (including reasonable attorneys' fees) arising out of or in connection with any breach of this Agreement by the Receiving Party. The Receiving Party agrees that its liability under this Section 4 shall be completely unlimited and shall not be subject to any caps or limitations of liability agreed upon elsewhere.

5. INTELLECTUAL PROPERTY OWNERSHIP AND AUTOMATIC ASSIGNMENT
All Confidential Information remains the sole property of the Disclosing Party. However, if the Receiving Party suggests any feedback, improvements, or modifications to the Disclosing Party's technology or business during the term of this Agreement, the Receiving Party hereby automatically and irrevocably assigns all right, title, and interest in and to such feedback, including all intellectual property rights therein, to the Disclosing Party without any requirement for further consideration or compensation.

6. GOVERNING LAW AND JURISDICTION
This Agreement, and all claims or causes of action arising hereunder, shall be governed by, and construed in accordance with, the laws of the State of New York, without regard to its conflict of laws principles. Any legal suit, action, or proceeding arising out of or relating to this Agreement shall be instituted exclusively in the federal courts of the United States or the courts of the State of New York, in each case located in the City of New York, County of New York, and each party irrevocably submits to the exclusive jurisdiction of such courts.

IN WITNESS WHEREOF, the parties hereto have executed this Mutual Non-Disclosure Agreement as of the date first written above.`,
  risks: [
    {
      id: "risk-1",
      clauseName: "Perpetual Obligations",
      severity: "medium",
      category: "Confidentiality",
      summary: "Indefinite confidentiality term creates an unreasonable, long-term compliance liability.",
      originalText: "Notwithstanding any termination of this Agreement, the Receiving Party’s obligations under this Agreement with respect to all Confidential Information disclosed shall continue in perpetuity from the date of disclosure. The Receiving Party agrees that all obligations of confidentiality shall remain binding indefinitely, regardless of whether the information ceases to be a trade secret or falls into the public domain through no fault of the Receiving Party.",
      recommendation: "The obligations of confidentiality under this Agreement shall survive the termination or expiration of this Agreement for a period of three (3) years; provided, however, that with respect to any Confidential Information that constitutes a trade secret under applicable law, such obligations shall survive for as long as such information remains a trade secret.",
      analysisDetail: "Standard commercial NDAs typically limit the survival of confidentiality obligations to a standard period (commonly 2 to 5 years after termination). A perpetual term is legally enforceable but imposes extreme administrative burdens on tracking the data, exposing the company to accidental breach claims decades later. Furthermore, specifying that confidentiality applies even if information falls into the public domain violates the very definition of confidential information.",
      remedyCost: "Medium"
    },
    {
      id: "risk-2",
      clauseName: "Unlimited Indemnification Liability",
      severity: "high",
      category: "Liability",
      summary: "Broad indemnification clause with carved-out unlimited liability exposes the company to extreme financial damages.",
      originalText: "The Receiving Party agrees to indemnify, defend, and hold harmless the Disclosing Party from and against any and all claims, liabilities, losses, damages, costs, or expenses (including reasonable attorneys' fees) arising out of or in connection with any breach of this Agreement by the Receiving Party. The Receiving Party agrees that its liability under this Section 4 shall be completely unlimited and shall not be subject to any caps or limitations of liability agreed upon elsewhere.",
      recommendation: "Either delete Section 4 (Indemnification) in its entirety—relying instead on standard common-law contract damages—or cap the total aggregate liability for breach of this Agreement to a reasonable dollar amount (e.g., $100,000 or the total fees paid under the relationship).",
      analysisDetail: "Indemnification is highly unusual in a standard Mutual NDA. Breaches of NDA are normally addressed by direct damages, not indemnity, which forces you to pay for third-party lawsuit defenses and covers broad indirect damages. Declaring that liability is completely unlimited and immune to overall contract liability caps is a significant 'red flag' that increases risk exposure exponentially.",
      remedyCost: "High"
    },
    {
      id: "risk-3",
      clauseName: "Automatic Feedback Assignment",
      severity: "high",
      category: "Intellectual Property",
      summary: "Automatic and irrevocable assignment of feedback transfers key intellectual property rights without compensation.",
      originalText: "However, if the Receiving Party suggests any feedback, improvements, or modifications to the Disclosing Party's technology or business during the term of this Agreement, the Receiving Party hereby automatically and irrevocably assigns all right, title, and interest in and to such feedback, including all intellectual property rights therein, to the Disclosing Party without any requirement for further consideration or compensation.",
      recommendation: "Any feedback, suggestions, or ideas provided by the Receiving Party are voluntary. The Disclosing Party is free to use, disclose, reproduce, or license such feedback without obligation or restriction, but the Receiving Party does not transfer or assign any intellectual property ownership in the feedback unless explicitly agreed in writing by both parties.",
      analysisDetail: "An automatic assignment clause acts as a hidden intellectual property grab. If your product team brainstorms or suggests modifications while discussing collaboration, this clause would immediately transfer ownership of those ideas to the other party. A standard 'Feedback License' is much safer as it grants them a license to use the ideas but lets you retain ownership.",
      remedyCost: "High"
    },
    {
      id: "risk-4",
      clauseName: "Governing Law & Exclusive Jurisdiction",
      severity: "low",
      category: "Jurisdiction",
      summary: "Governing law set to New York. Requires exclusive venue in New York courts, which may be inconvenient.",
      originalText: "This Agreement, and all claims or causes of action arising hereunder, shall be governed by, and construed in accordance with, the laws of the State of New York, without regard to its conflict of laws principles. Any legal suit, action, or proceeding arising out of or relating to this Agreement shall be instituted exclusively in the federal courts of the United States or the courts of the State of New York, in each case located in the City of New York, County of New York, and each party irrevocably submits to the exclusive jurisdiction of such courts.",
      recommendation: "If both parties are based in different jurisdictions, consider a neutral forum, or amend to the home jurisdiction of the party defending a claim. If New York is acceptable, keep as is.",
      analysisDetail: "New York law is standard and well-understood for commercial contracts, making it low risk. However, exclusive jurisdiction in New York federal/state courts means any dispute requires your team to travel and hire local New York counsel.",
      remedyCost: "Low"
    }
  ]
};

// Korean translation metadata to show beautiful Korean headings and tooltips
export const koreanHeadings = {
  dashboardTitle: "법률 검토 스크리닝 어시스턴트",
  showroomTitle: "디자인 시스템 쇼룸",
  riskSummary: "리스크 요약 현황",
  totalRisks: "총 발견 리스크",
  highRisks: "고위험 리스크",
  mediumRisks: "중위험 리스크",
  lowRisks: "저위험 리스크",
  clauseList: "검토 대상 조항 목록",
  clauseName: "조항명",
  severity: "위험도",
  category: "분야",
  summary: "요약",
  originalText: "계약서 본문 조항",
  recommendation: "AI 추천 수정 조항",
  analysisDetail: "법률 분석 상세 리포트",
  remedyCost: "조치 난이도/비용",
  riskOverview: "리스크 오버뷰",
  uploadContract: "계약서 스크리닝 분석 요청",
  viewDetails: "상세 분석 보기",
  backToDashboard: "대시보드로 돌아가기",
  originalClause: "원본 조항",
  suggestedClause: "수정 권고안"
};
