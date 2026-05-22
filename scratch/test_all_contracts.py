import os
import subprocess
import sys
from pathlib import Path

# Files to test
test_files = [
    ("scratch/contract_fair.pdf", "안전/공정 계약서"),
    ("scratch/contract_unfair.pdf", "독소/위험 계약서"),
    ("scratch/contract_subtle.pdf", "교묘한 독소 계약서"),
    ("scratch/contract_random_nda.pdf", "일반 비밀유지 계약서"),
    ("scratch/contract_random_supply.pdf", "일반 물품 공급 계약서")
]

print("========================================================")
# Check python path
python_exe = sys.executable

results_summary = []

for file_path, label in test_files:
    if not os.path.exists(file_path):
        print(f"Error: {file_path} does not exist.")
        continue
    
    print(f"\n[실행 중] {label} 검토 ({file_path})...")
    
    # Run run_review.py using subprocess
    cmd = [python_exe, "run_review.py", "--file", file_path]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        output = res.stdout
        
        # Parse output for overall risk
        overall_risk = "LOW"
        risk_count = 0
        
        for line in output.splitlines():
            if "종합 위험도" in line:
                # e.g., "  종합 위험도  : HIGH" or similar
                overall_risk = line.split(":")[-1].strip()
            if "감지된 위험 조항" in line and "총" in line:
                # e.g., "[!] 감지된 위험 조항: 총 3건"
                try:
                    risk_count = int(line.split("총")[-1].replace("건", "").strip())
                except:
                    pass
        
        # If the overall risk wasn't parsed correctly, search for badges in text
        if "HIGH" in output:
            overall_risk = "HIGH"
        elif "MEDIUM" in output:
            overall_risk = "MEDIUM"
            
        print(f"   -> 종합 위험도: {overall_risk}, 감지 건수: {risk_count}건")
        results_summary.append({
            "label": label,
            "file": file_path,
            "risk": overall_risk,
            "count": risk_count
        })
        
    except Exception as e:
        print(f"Execution failed for {file_path}: {e}")

# Display comparative summary table
print("\n========================================================")
print("             5개 테스트 계약서 검토 결과 요약")
print("========================================================")
print(f"{'계약서 종류':25s} | {'종합 위험도':10s} | {'감지 건수'}")
print("-" * 55)
for r in results_summary:
    print(f"{r['label']:25s} | {r['risk']:10s} | {r['count']}건")
print("========================================================")
