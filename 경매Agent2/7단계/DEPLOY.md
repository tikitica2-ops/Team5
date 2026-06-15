# 배포 가이드 (Streamlit Community Cloud)

이 앱을 무료로 공유 가능한 URL로 배포하는 방법입니다. (발표용 데모)

## 사전 점검
- `requirements.txt` 있음 ✅
- `app.py` 가 진입점 ✅
- `.env` 와 `chroma_db/` 는 `.gitignore` 로 제외됨 ✅ (키는 깃에 올라가면 안 됨)
- 앱 최초 실행 시 `chroma_db` 가 없으면 자동으로 구축됨 (별도 작업 불필요)

## 1. GitHub에 올리기
```bash
git init
git add .
git commit -m "auction edu rag MVP"
git branch -M main
git remote add origin https://github.com/<계정>/<레포>.git
git push -u origin main
```
> `.env` 가 커밋되지 않았는지 `git status` 로 꼭 확인하세요.

## 2. Streamlit Cloud 연결
1. https://share.streamlit.io 접속 → GitHub 로그인
2. **New app** → 레포지토리 / 브랜치(main) / **Main file path = `app.py`** 선택
3. **Advanced settings → Python version**은 3.11 권장

## 3. Secrets(키) 설정  ← 가장 중요
앱 설정의 **Secrets** 칸에 아래 형식(TOML)으로 입력합니다. (`.env` 가 아니라 여기에 넣음)
```toml
OPENAI_API_KEY = "sk-..."
LLM_PROVIDER = "openai"
EMBEDDING_PROVIDER = "openai"
```
> 앱이 시작될 때 이 Secrets를 환경변수로 자동 연결하도록 `app.py`에 처리해 두었습니다.

## 4. 배포(Deploy)
- Deploy 버튼 → 빌드(수 분) → 첫 접속 시 지식베이스 자동 구축(50청크라 보통 10~30초)
- 완료되면 `https://<앱이름>.streamlit.app` 공유 URL 발급

## 5. 자주 막히는 지점
- **인증 오류(401/Invalid API key)**: Secrets의 `OPENAI_API_KEY` 오타·따옴표 확인
- **빌드 실패**: `requirements.txt` 버전 충돌 → Python 3.11로 재시도
- **첫 응답이 느림**: 콜드스타트 + DB 최초 구축 때문. 두 번째부터는 빠름
- **앱이 재부팅되면** `chroma_db` 가 사라질 수 있으나, 자동 재구축되므로 문제 없음

## 6. 데모/비용 메모
- 데모 수준 사용량의 임베딩·생성 비용은 수백~수천 원 수준
- 키 사용량이 걱정되면 OpenAI 대시보드에서 사용 한도(usage limit)를 걸어두세요
- 공개 URL이므로 발표 후에는 앱을 **일시중지(또는 비공개 레포)** 하는 것을 권장
