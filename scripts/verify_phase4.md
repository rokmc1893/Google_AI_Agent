# Phase 4 검증

```bash
npm run build
PYTHONPATH=. .venv/bin/python -c "from fastapi.testclient import TestClient; from backend.main import app; c=TestClient(app); print(c.get('/api/health').json())"
npm run dev
```

브라우저:
1. 파일 업로드 → Overview에 **API 연동** 표시
2. 리스크 테이블이 백엔드 `verified_issues` 기반으로 갱신
3. Viewer → **PII 마스킹 Side-by-Side** (contract_masked 있을 때)

Expected console: `OK P4` — `npm run build` exit 0
