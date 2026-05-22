# -*- coding: utf-8 -*-
import subprocess
import os
import sys

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True, cwd=cwd)
    if result.returncode != 0:
        return False, result.stdout, result.stderr
    return True, result.stdout, result.stderr

def main():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"[*] 저장소 디렉토리: {repo_dir}")
    
    # 1. 깃 상태 확인
    success, stdout, _ = run_cmd("git status", repo_dir)
    if not success:
        print("[-] Git이 설치되어 있지 않거나 Git 저장소가 아닙니다.")
        return

    # 현재 브랜치 확인
    success, stdout, _ = run_cmd("git branch --show-current", repo_dir)
    current_branch = stdout.strip()
    if not current_branch:
        # 분리된 HEAD 상태 등일 경우 기본값 main 설정
        current_branch = "main"
    print(f"[*] 현재 로컬 브랜치: {current_branch}")

    # 2. 원격 최신 변경사항 패치 (깃허브에 영향 없음)
    print("[*] 깃허브 원격 저장소의 최신 정보 패치 중...")
    success, _, _ = run_cmd("git fetch --all", repo_dir)
    if not success:
        print("[-] 원격 저장소 패치(fetch)에 실패했습니다.")
        return

    # 3. origin/main 기반 임시 병합용 로컬 브랜치 생성
    temp_branch = "temp-merged-dist-build"
    print(f"[*] origin/main 기준으로 임시 브랜치 '{temp_branch}' 생성 및 전환...")
    
    # 혹시 기존에 남아있던 동일 이름의 임시 브랜치 강제 삭제
    run_cmd(f"git branch -D {temp_branch}", repo_dir)
    
    success, _, stderr = run_cmd(f"git checkout -b {temp_branch} origin/main", repo_dir)
    if not success:
        print(f"[-] 임시 브랜치 생성에 실패했습니다: {stderr}")
        return

    # 4. 로컬 브랜치를 임시 브랜치에 병합 (로컬에서만 병합 진행)
    print(f"[*] 로컬 '{current_branch}' 코드를 임시 브랜치에 병합(Merge) 중...")
    success, stdout, stderr = run_cmd(f"git merge {current_branch} -m \"Temp merge for distribution\"", repo_dir)
    
    if not success:
        print("[-] 병합 중 충돌(Conflict)이 발생했습니다.")
        print("    안전하게 원래 브랜치로 복귀합니다.")
        run_cmd(f"git checkout {current_branch}", repo_dir)
        run_cmd(f"git branch -D {temp_branch}", repo_dir)
        return
    else:
        print("[+] 로컬 코드와 원격 코드 병합 완료 (원격 깃허브에는 반영되지 않음)")

    # 5. 병합된 소스코드를 ZIP으로 아카이브 (불필요한 파일 및 node_modules 자동 제외)
    zip_filename = "legal-screening-assistant-merged.zip"
    # 한 상위 폴더에 저장하여 빌드 폴더를 깨끗하게 유지
    zip_path = os.path.abspath(os.path.join(repo_dir, "..", zip_filename))
    print(f"[*] 병합된 코드를 아카이브 파일로 압축 중 -> {zip_path}")
    
    success, _, stderr = run_cmd(f"git archive --format=zip HEAD -o \"{zip_path}\"", repo_dir)
    if success:
        print(f"[+] 압축 파일 생성 성공: {zip_path}")
    else:
        print(f"[-] ZIP 아카이브 생성에 실패했습니다: {stderr}")
    
    # 6. 원래 로컬 브랜치로 복귀
    print(f"[*] 원래 로컬 브랜치 '{current_branch}'로 복귀 중...")
    run_cmd(f"git checkout {current_branch}", repo_dir)
    
    # 7. 임시로 만든 로컬 병합용 브랜치 삭제 (흔적 없음)
    print(f"[*] 임시 브랜치 '{temp_branch}' 삭제 중...")
    run_cmd(f"git branch -D {temp_branch}", repo_dir)
    
    print("\n[성공] 모든 작업이 안전하게 완료되었습니다!")
    print(f"-> 다른 사람에게 전달할 파일 경로: {zip_path}")

if __name__ == "__main__":
    main()
